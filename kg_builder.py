# kg_builder.py

import networkx as nx
import plotly.graph_objects as go
import re
import os
import streamlit as st
from utils import logger

# Define node types/colors for visualization
NODE_COLORS = {
    "Procedure": "#FFB347",  # Orange
    "Phase": "#87CEEB",      # Sky Blue
    "Action": "#98FB98",     # Pale Green
    "Parameter": "#FFD700",  # Gold
    "Item": "#E6E6FA",       # Lavender
    "Value": "#FFB6C1",      # Light Pink
    "Condition": "#F0E68C",  # Khaki
    "Control": "#ADD8E6",    # Light Blue
    "Status": "#D3D3D3",     # Light Grey
    "Section": "#FFA07A",    # Light Salmon
    "Unknown": "#D2B48C",    # Tan (Default)
}
DEFAULT_COLOR = "#D2B48C" # Tan

def extract_entities_from_manual(text):
    """
    Simplified manual extraction of entities and relationships based on patterns.
    Returns: List of tuples representing nodes and edges.
    Example tuple: ('node_id', 'label', {'type': 'NodeType', 'details': '...'})
                   ('source_id', 'target_id', {'label': 'relationship_type'})
    """
    logger.info("Starting entity extraction from manual text...")
    nodes = []
    edges = []

    # Find Section
    section_match = re.search(r"\*\*Section ID: (NP-TO)\*\*", text)
    if section_match:
        section_id = section_match.group(1)
        nodes.append((section_id, "Normal Procedures - Takeoff", {"type": "Section"}))
        logger.debug(f"Found Section: {section_id}")
    else:
        section_id = "AeroCraft ACE-900 Manual" # Fallback
        nodes.append((section_id, section_id, {"type": "Document"}))
        logger.warning("Could not find Section ID, using fallback.")


    # Find Phases
    phases = re.findall(r"\*\*Phase \d+: (.*?) \(ID: (NP-TO-P\d+)\)\*\*", text)
    logger.info(f"Found {len(phases)} phases.")
    for phase_name, phase_id in phases:
        nodes.append((phase_id, phase_name.strip(), {"type": "Phase"}))
        edges.append((section_id, phase_id, {"label": "has_phase"}))
        logger.debug(f"Processing Phase: {phase_id} - {phase_name.strip()}")

        # Find content within each phase (simplified)
        phase_content_match = re.search(rf"\*\*Phase \d+:.*?\(ID: {phase_id}\)\*\*(.*?)(?=\*\*Phase|\*\*End of Section)", text, re.DOTALL)
        if phase_content_match:
            phase_content = phase_content_match.group(1)

            # Items (e.g., checklist items)
            items = re.findall(r"\*   \*\*(\w+?) \(ID: (.*?)\): (.*?)\. (?:Target Value: (.*?)\.|Status: (.*?)\.|Mode: (.*?)\.)?", phase_content)
            logger.debug(f"Phase {phase_id}: Found {len(items)} items.")
            for item_name, item_id, item_desc, item_val, item_status, item_mode in items:
                nodes.append((item_id, item_name.strip(), {"type": "Item", "description": item_desc.strip()}))
                edges.append((phase_id, item_id, {"label": "includes"}))
                if item_val:
                    val_node_id = f"{item_id}-val"
                    nodes.append((val_node_id, item_val.strip(), {"type": "Value"}))
                    edges.append((item_id, val_node_id, {"label": "has_target_value"}))
                if item_status:
                    status_node_id = f"{item_id}-status"
                    nodes.append((status_node_id, item_status.strip(), {"type": "Status"}))
                    edges.append((item_id, status_node_id, {"label": "has_status"}))
                if item_mode:
                    mode_node_id = f"{item_id}-mode"
                    nodes.append((mode_node_id, item_mode.strip(), {"type": "Value"})) # Treat mode as a value here
                    edges.append((item_id, mode_node_id, {"label": "has_mode"}))

            # Parameters (e.g., Taxi Speed)
            params = re.findall(r"\*   \*\*(\w+?) \(ID: (.*?)\): (.*?)\. (?:Limit: (.*?)\.|Control: (.*?)\.|Action: (.*?)\.)", phase_content)
            logger.debug(f"Phase {phase_id}: Found {len(params)} parameters.")
            for param_name, param_id, param_desc, param_limit, param_control, param_action in params:
                 nodes.append((param_id, param_name.strip(), {"type": "Parameter", "description": param_desc.strip()}))
                 edges.append((phase_id, param_id, {"label": "includes"}))
                 if param_limit:
                     limit_node_id = f"{param_id}-limit"
                     nodes.append((limit_node_id, param_limit.strip(), {"type": "Value"}))
                     edges.append((param_id, limit_node_id, {"label": "has_limit"}))
                 if param_control:
                     control_node_id = f"{param_id}-control"
                     nodes.append((control_node_id, param_control.strip(), {"type": "Control"}))
                     edges.append((param_id, control_node_id, {"label": "controlled_by"}))
                 if param_action:
                     action_node_id = f"{param_id}-action"
                     nodes.append((action_node_id, param_action.strip(), {"type": "Action"}))
                     edges.append((param_id, action_node_id, {"label": "involves_action"}))

            # Steps (e.g., Before Takeoff steps)
            steps = re.findall(r"\*   \*\*(\w+?) \(ID: (.*?)\): (.*?)\. (?:Action: (.*?)\.|Target Value: (.*?)\.|Status: (.*?)\.|Condition: (.*?)\.)", phase_content)
            logger.debug(f"Phase {phase_id}: Found {len(steps)} steps.")
            for step_name, step_id, step_desc, step_action, step_val, step_status, step_condition in steps:
                node_type = "Action" if step_action else "Item"
                nodes.append((step_id, step_name.strip(), {"type": node_type, "description": step_desc.strip()}))
                edges.append((phase_id, step_id, {"label": "has_step"}))
                if step_action:
                     action_node_id = f"{step_id}-action"
                     nodes.append((action_node_id, step_action.strip(), {"type": "Action"}))
                     edges.append((step_id, action_node_id, {"label": "involves_action"}))
                if step_val:
                    val_node_id = f"{step_id}-val"
                    nodes.append((val_node_id, step_val.strip(), {"type": "Value"}))
                    edges.append((step_id, val_node_id, {"label": "has_target_value"}))
                if step_status:
                    status_node_id = f"{step_id}-status"
                    nodes.append((status_node_id, step_status.strip(), {"type": "Status"}))
                    edges.append((step_id, status_node_id, {"label": "has_status"}))
                if step_condition:
                    condition_node_id = f"{step_id}-condition"
                    nodes.append((condition_node_id, step_condition.strip(), {"type": "Condition"}))
                    edges.append((step_id, condition_node_id, {"label": "requires_condition"}))

            # Procedures (e.g., Takeoff Roll procedures)
            procs = re.findall(r"\*   \*\*(\w+?) \((?:Vr|Vy)\) \(ID: (.*?)\): (.*?)\. (?:Target Value: (.*?)\.|Action: (.*?)\.|Control: (.*?)\.)", phase_content)
            logger.debug(f"Phase {phase_id}: Found {len(procs)} procedures.")
            for proc_name, proc_id, proc_desc, proc_val, proc_action, proc_control in procs:
                 node_type = "Parameter"
                 nodes.append((proc_id, proc_name.strip(), {"type": node_type, "description": proc_desc.strip()}))
                 edges.append((phase_id, proc_id, {"label": "includes_procedure"}))
                 if proc_val:
                     val_node_id = f"{proc_id}-val"
                     nodes.append((val_node_id, proc_val.strip(), {"type": "Value"}))
                     edges.append((proc_id, val_node_id, {"label": "has_target_value"}))
                 if proc_action:
                     action_node_id = f"{proc_id}-action"
                     nodes.append((action_node_id, proc_action.strip(), {"type": "Action"}))
                     edges.append((proc_id, action_node_id, {"label": "involves_action"}))
                 if proc_control:
                     control_node_id = f"{proc_id}-control"
                     nodes.append((control_node_id, proc_control.strip(), {"type": "Control"}))
                     edges.append((proc_id, control_node_id, {"label": "controlled_by"}))
        else:
            logger.warning(f"Could not find content for Phase {phase_id}")

    logger.info(f"Entity extraction finished. Found {len(nodes)} potential nodes and {len(edges)} potential edges.")
    return nodes, edges


def build_knowledge_graph(manual_text):
    """Builds a NetworkX graph from the extracted entities."""
    logger.info("Starting Knowledge Graph construction.")
    nodes_data, edges_data = extract_entities_from_manual(manual_text)

    if not nodes_data:
        logger.error("Entity extraction returned no nodes. Knowledge Graph cannot be built. Check text file and regex patterns.")
        return None # Explicitly return None if extraction fails

    G = nx.Graph()
    added_nodes = set()
    for node_id, label, attrs in nodes_data:
        if node_id not in added_nodes:
            try:
                # Use the corrected add_node call relying on **attrs
                G.add_node(
                    node_id,
                    label=label,
                    title=f"{attrs.get('type', 'Unknown')}: {label}\n{attrs.get('description', '')}",
                    **attrs
                )
                added_nodes.add(node_id)
            except Exception as e:
                 logger.error(f"Failed to add node {node_id} with label '{label}' and attrs {attrs}: {e}", exc_info=True)
        else:
             logger.warning(f"Duplicate node ID detected and skipped: {node_id}")

    for source_id, target_id, attrs in edges_data:
        if source_id in G.nodes and target_id in G.nodes:
           G.add_edge(source_id, target_id, title=attrs.get('label', ''), **attrs)
        else:
            logger.warning(f"Skipping edge due to missing node(s): {source_id} -> {target_id}")

    node_count = G.number_of_nodes()
    edge_count = G.number_of_edges()
    logger.info(f"Knowledge Graph built with {node_count} nodes and {edge_count} edges.")

    if node_count == 0:
        # This check is important! If extraction found data but graph is empty, something went wrong adding nodes/edges.
        logger.error("Knowledge Graph construction resulted in 0 nodes despite having node data. Check node/edge addition logic or potential data issues.")
        return None # Return None if graph ends up empty unexpectedly

    return G

# --- ADDED: Sanitization Helper ---
def sanitize_for_pyvis(input_obj):
    """Converts input to string and sanitizes for pyvis JS/HTML."""
    if input_obj is None:
        return ""
    # Ensure it's a string first
    text = str(input_obj)
    # Replace backslashes (escape them for JS)
    text = text.replace('\\', '\\\\')
    # Escape double quotes for JS strings
    text = text.replace('"', '\\"')
    # Replace newlines and carriage returns with spaces (can break JS strings)
    text = text.replace('\n', ' ').replace('\r', ' ')
    # Optional: Remove other potentially problematic chars if needed
    # text = re.sub(r'[^\w\s\-\.:\(\)]', '', text) # Example: Keep only word chars, space, -, ., :, (, )
    return text

# --- NEW Visualization function using Plotly ---
def visualize_knowledge_graph_plotly(G, filename="static/kg_visualization.html"):
    """Creates an interactive HTML visualization of the graph using Plotly."""
    if not isinstance(G, nx.Graph):
        logger.error(f"Cannot visualize Plotly graph: Expected networkx.Graph, got {type(G)}.")
        return None
    if G.number_of_nodes() == 0:
        logger.error("Cannot visualize Plotly graph: Graph has 0 nodes.")
        return None

    logger.info(f"Generating Plotly graph visualization to {filename} for graph with {G.number_of_nodes()} nodes...")

    try:
        # 1. Calculate node positions using a NetworkX layout
        # Increase k for more spread, adjust iterations
        pos = nx.spring_layout(G, k=0.75, iterations=50, seed=42) # Play with layout params

        # 2. Create Edge Trace
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None]) # None separates line segments
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines')

        # 3. Create Node Trace
        node_x = []
        node_y = []
        node_text = [] # Hover text
        node_colors = []
        node_sizes = []
        node_info = [] # Store labels/ids for potential click events later

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_info.append(f"ID: {node}") # Basic info

            # Get attributes and apply sanitization
            attrs = G.nodes[node]
            node_type = attrs.get('type', 'Unknown')
            color = NODE_COLORS.get(node_type, DEFAULT_COLOR)
            node_colors.append(color)
            node_sizes.append(15) # Adjust size as needed

            # Build hover text (sanitize components)
            label = sanitize_for_pyvis(attrs.get('label', node))
            desc = sanitize_for_pyvis(attrs.get('description', ''))
            hover_text = f"<b>{label}</b><br>Type: {node_type}<br>ID: {sanitize_for_pyvis(node)}"
            if desc:
                 hover_text += f"<br>Desc: {desc}"
            # Add other attributes if desired
            # for k, v in attrs.items():
            #      if k not in ['label', 'description', 'type', 'title']: # Avoid redundancy
            #          hover_text += f"<br>{k}: {sanitize_for_pyvis(v)}"

            node_text.append(hover_text)


        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text', # Show markers, optionally add text labels
            hoverinfo='text',
            text=node_text, # Assign hover text
            textposition='top center', # Position for node labels if shown
            # textfont=dict(size=9, color='#fff'), # Style for node labels if shown
            marker=dict(
                showscale=False,
                color=node_colors,
                size=node_sizes,
                line_width=1,
                line_color='rgb(50,50,50)'
                ),
            # customdata=node_info # Store extra data for callbacks if needed
            )

        # 4. Create the Figure
        fig = go.Figure(data=[edge_trace, node_trace],
                     layout=go.Layout(
                        title=dict(text='AeroCraft Knowledge Graph', font=dict(size=16)),
                        # titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        # annotations=[ dict( # Optional annotation
                        #    text="KG from AeroCraft Manual",
                        #    showarrow=False,
                        #    xref="paper", yref="paper",
                        #    x=0.005, y=-0.002 ) ],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        paper_bgcolor='rgba(34,34,34,1)', # Match pyvis dark bg
                        plot_bgcolor='rgba(34,34,34,1)',
                        font=dict(color="white")
                        )
                    )

        # 5. Save to HTML
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        fig.write_html(filename, full_html=True, include_plotlyjs='cdn') # Use Plotly CDN

        # 6. Check file size (optional but good)
        try:
            file_size = os.path.getsize(filename)
            logger.info(f"Plotly graph visualization saved successfully to {filename} (Size: {file_size} bytes).")
            if file_size < 1000: # Plotly files are larger than pyvis usually
                 logger.warning(f"Written Plotly file {filename} is unexpectedly small.")
        except OSError as size_err:
            logger.error(f"Could not get size of written Plotly file {filename}: {size_err}")

        return filename

    except Exception as e:
        logger.error(f"Critical error during Plotly graph visualization generation: {e}", exc_info=True)
        return None

def query_kg_for_entities(G, entities):
    """
    Finds nodes related to the given entities and retrieves context.
    Context can be node labels, attributes, or neighbors.
    """
    if not G:
        logger.warning("Knowledge graph is not available for querying (was None).")
        return []
    if not isinstance(G, nx.Graph):
         logger.error(f"query_kg_for_entities received non-Graph object: {type(G)}")
         return []
    if G.number_of_nodes() == 0:
         logger.warning("Querying an empty knowledge graph.")
         return []


    related_nodes = set()
    entity_list = [str(e).lower() for e in entities if e] # Ensure entities are strings and normalize

    logger.info(f"Querying KG for entities: {entity_list}")

    # Direct match on labels or IDs (case-insensitive)
    for node_id, data in G.nodes(data=True):
        label = data.get('label', '').lower()
        node_id_lower = str(node_id).lower() # Ensure node_id is string for comparison
        for entity in entity_list:
            if entity in label or entity == node_id_lower:
                related_nodes.add(node_id)
                logger.debug(f"KG direct match found: Node '{node_id}' (Label: '{data.get('label')}') related to entity '{entity}'")

    # Expand to neighbors of matched nodes (1 hop)
    kg_context_nodes = set(related_nodes)
    for node_id in related_nodes:
        try:
           neighbors = list(G.neighbors(node_id))
           kg_context_nodes.update(neighbors)
           logger.debug(f"Adding neighbors of '{node_id}': {neighbors}")
        except nx.NetworkXError:
             logger.warning(f"Node {node_id} not found in graph when trying to get neighbors.")
        except Exception as e:
             logger.error(f"Error getting neighbors for node {node_id}: {e}")

    # Extract text context from the identified nodes
    context_texts = []
    added_node_labels = set()
    for node_id in kg_context_nodes:
        if node_id in G.nodes:
            data = G.nodes[node_id]
            label = data.get('label', '')
            desc = data.get('description', '')
            node_type = data.get('type', '')

            node_context = f"{node_type}: {label}"
            if desc:
                 node_context += f" ({desc})"

            try:
                for neighbor_id in G.neighbors(node_id):
                    if neighbor_id in G.nodes:
                        neighbor_data = G.nodes[neighbor_id]
                        neighbor_type = neighbor_data.get('type')
                        neighbor_label = neighbor_data.get('label')
                        edge_data = G.get_edge_data(node_id, neighbor_id)
                        edge_label = edge_data.get('label', 'related to') if edge_data else 'related to'

                        if neighbor_type in ["Value", "Status", "Condition", "Limit", "Mode"]:
                            node_context += f" [{edge_label}: {neighbor_label}]"
            except Exception as e:
                logger.error(f"Error retrieving neighbor context for {node_id}: {e}")

            if label and label.lower() not in added_node_labels: # Ensure label exists before adding
                context_texts.append(node_context)
                added_node_labels.add(label.lower())
                logger.debug(f"Adding KG context: {node_context}")
            elif not label:
                logger.warning(f"Node {node_id} has no label, skipping context addition.")


    logger.info(f"Found {len(context_texts)} context snippets from KG for entities {entity_list}.")
    return context_texts