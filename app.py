# app.py

import streamlit as st
import streamlit.components.v1 as components
import os
from utils import logger, load_config, get_manual_text, setup_streamlit_logging
from kg_builder import build_knowledge_graph, visualize_knowledge_graph_plotly 
from rag_chain import setup_vector_store, setup_knowledge_graph, create_rag_chain

# --- Page Configuration ---
st.set_page_config(
    page_title="AeroCraft ACE-900 Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Load Configuration and Manual ---
config = load_config()
manual_text = get_manual_text()

# --- Theme & Styling --- (Keep as is)
st.markdown("""
<style>
    /* Chat bubble styling */
    .stChatMessage {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
         box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stChatMessage[data-testid="stChatMessageContent"] {
         /* background-color: #f0f2f6; /* Lighter background for user messages */
         /* color: #333; */
         border: 1px solid #e0e0e0;
    }

     /* Make expander headers slightly bolder */
    .streamlit-expanderHeader {
        font-weight: bold;
        font-size: 1.1em;
         color: #265D94; /* A nice blue */
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
         /* background-color: #f8f9fa; */
         /* padding: 15px; */
    }
    [data-testid="stSidebar"] h2 {
         color: #1E88E5; /* Sidebar title color */
    }
     /* Style the chat input */
    [data-testid="stChatInput"] {
        /* background-color: #ffffff; */
        /* border-top: 1px solid #e0e0e0; */
         /* padding: 10px 20px; */
    }

</style>
""", unsafe_allow_html=True)


# --- Initialize Session State ---
# Ensure ALL session state keys used later are initialized here
if "messages" not in st.session_state:
    st.session_state.messages = []
if "log_handler" not in st.session_state:
    st.session_state.log_handler = None
if "current_logs" not in st.session_state:
    st.session_state.current_logs = ""
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None
if "knowledge_graph" not in st.session_state:
    st.session_state.knowledge_graph = None
if "kg_viz_path" not in st.session_state:
    st.session_state.kg_viz_path = None
# --- ADDED INITIALIZATION ---
if "kg_error_message" not in st.session_state:
    st.session_state.kg_error_message = "" # Initialize state for KG errors
if "kg_info_message" not in st.session_state:
    st.session_state.kg_info_message = "" # Initialize state for KG info
# --- END ADDED INITIALIZATION ---


# --- Sidebar ---
with st.sidebar:
    # st.image("https://www.istockphoto.com/photo/passenger-airplane-flying-above-clouds-during-sunset-gm155439315-21435411", width=150)
    st.markdown("## ✈️ AeroCraft ACE-900 Assistant")
    st.markdown("Ask questions about the **Takeoff Procedures** section of the operations manual.")
    st.markdown("---")
    st.markdown("### Knowledge Graph Status")

    
    # --- KG Build and Visualize Logic (Uses new function) ---
    if st.session_state.knowledge_graph is None and not st.session_state.kg_error_message:
        with st.spinner("Building Knowledge Graph..."):
            try:
                temp_kg = build_knowledge_graph(manual_text)
                if temp_kg is not None and temp_kg.number_of_nodes() > 0:
                    st.session_state.knowledge_graph = temp_kg
                    logger.info("Knowledge Graph built successfully.")
                    st.session_state.kg_info_message = f"Graph built ({temp_kg.number_of_nodes()} nodes, {temp_kg.number_of_edges()} edges)."

                    # --- CALL PLOTLY VISUALIZATION ---
                    temp_viz_path = visualize_knowledge_graph_plotly(st.session_state.knowledge_graph)
                    # --- END CALL PLOTLY VISUALIZATION ---

                    if temp_viz_path and os.path.exists(temp_viz_path):
                        st.session_state.kg_viz_path = temp_viz_path
                        setup_knowledge_graph(st.session_state.knowledge_graph)
                        logger.info(f"Knowledge Graph visualization successful: {temp_viz_path}")
                        st.session_state.kg_info_message += " Visualization generated."
                    else:
                        logger.error("Knowledge Graph visualization failed (Plotly visualize function returned None or file not found).")
                        setup_knowledge_graph(st.session_state.knowledge_graph)
                        st.session_state.kg_info_message += " Visualization failed."
                elif temp_kg is not None and temp_kg.number_of_nodes() == 0:
                     logger.error("Knowledge Graph built but contains 0 nodes.")
                     st.session_state.kg_error_message = "Knowledge Graph built but is empty."
                else:
                    logger.error("Knowledge Graph build failed.")
                    st.session_state.kg_error_message = "Failed to build Knowledge Graph."
            except Exception as e:
                logger.error(f"Exception during Knowledge Graph build/visualize (Plotly): {e}", exc_info=True)
                st.session_state.kg_error_message = f"Error during KG processing: {e}"

    # --- Display KG Status and Visualization ---
    if st.session_state.kg_error_message:
        st.error(st.session_state.kg_error_message)
    elif st.session_state.kg_info_message:
        st.info(st.session_state.kg_info_message)

    if st.session_state.kg_viz_path:
         with st.expander("View Interactive Knowledge Graph", expanded=True):
             try:
                 with open(st.session_state.kg_viz_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                 # --- UPDATED CHECK FOR PLOTLY CONTENT ---
                 if html_content and ('plotly-graph-div' in html_content or 'Plotly.newPlot' in html_content):
                    components.html(html_content, height=600, scrolling=True) # Increased height for Plotly
                    st.caption("Interactive graph (Plotly) showing concepts and relationships.")
                 else:
                    st.warning("Plotly visualization file appears empty or invalid.")
                    logger.warning(f"Plotly viz file ({st.session_state.kg_viz_path}) seems empty/malformed.")
             except FileNotFoundError:
                 st.warning("Plotly visualization file not found.")
                 logger.warning(f"Plotly viz file not found at: {st.session_state.kg_viz_path}")
             except Exception as e:
                 st.warning(f"Could not load Plotly visualization: {e}")
                 logger.warning(f"Error loading Plotly viz file: {e}", exc_info=True)
    elif st.session_state.knowledge_graph is not None:
        pass # Info/error message above covers this case
    elif not st.session_state.kg_error_message:
         st.caption("Knowledge Graph processing...")

    st.markdown("---")
    st.info("ℹ️ This app uses Retrieval-Augmented Generation (RAG) enhanced with a Knowledge Graph to answer questions based on the provided manual text.")


# --- Main Chat Interface ---
st.title("AeroCraft ACE-900 Chat Assistant")
st.caption("Powered by LangChain, HuggingFace, OpenRouter,Knowledge Graphs and Ashgen12")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Processing Log Area
log_expander = st.expander("⚙️ View Processing Logs")
log_container = log_expander.empty()

if st.session_state.log_handler is None:
    st.session_state.log_handler = setup_streamlit_logging(log_container)

# --- Initialize RAG Chain ---
if st.session_state.rag_chain is None and st.session_state.knowledge_graph is not None:
     # Add a check to prevent RAG init if KG build failed previously
     if not st.session_state.kg_error_message:
        with st.spinner("Initializing RAG system..."):
            try:
                retriever = setup_vector_store(manual_text)
                if retriever:
                    st.session_state.rag_chain = create_rag_chain(retriever)
                    st.success("RAG system initialized successfully!")
                    log_container.code(st.session_state.log_handler.get_logs(), language="log")
                else:
                    st.error("Failed to initialize the document retriever.")
                    st.session_state.kg_error_message = "RAG retriever setup failed."
            except Exception as e:
                st.error(f"Error initializing RAG chain: {e}")
                logger.error(f"RAG Chain init failed: {e}", exc_info=True)
                st.session_state.kg_error_message = f"RAG init failed: {e}"
     # else: logger.info("Skipping RAG initialization because KG build failed.") # Optional log

# Display initial logs if handler is ready
if st.session_state.log_handler:
    log_container.code(st.session_state.current_logs or st.session_state.log_handler.get_logs(), language="log")


# --- Handle User Input ---
if prompt := st.chat_input("Ask about takeoff procedures (e.g., 'What is the rotate speed?', 'Describe the pre-takeoff checklist')"):
    if st.session_state.log_handler:
        st.session_state.log_handler.clear_logs()
        st.session_state.current_logs = ""
        logger.info(f"--- New Query Received ---")

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.rag_chain:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            with st.spinner("Thinking..."):
                 try:
                     logger.info(f"Processing query: {prompt}")
                     chain_input = {"question": prompt}
                     response = st.session_state.rag_chain.invoke(chain_input)
                     full_response = response
                     if not isinstance(full_response, str):
                         logger.warning(f"Expected string response from chain, got {type(full_response)}. Converting.")
                         full_response = str(full_response)
                     message_placeholder.markdown(full_response)
                     logger.info("Final answer generated and displayed.")
                 except Exception as e:
                     logger.error(f"Error during RAG chain invocation for query '{prompt}': {e}", exc_info=True)
                     full_response = f"Sorry, I encountered an error processing your request.\n\n**Error details:**\n```\n{e}\n```"
                     message_placeholder.error(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})
            if st.session_state.log_handler:
                 st.session_state.current_logs = st.session_state.log_handler.get_logs()
                 log_container.code(st.session_state.current_logs, language="log")
    else:
        st.error("RAG system not initialized. Cannot process query (KG or Retriever might have failed).")
        if st.session_state.log_handler:
            st.session_state.current_logs = st.session_state.log_handler.get_logs()
            log_container.code(st.session_state.current_logs, language="log")

# Update log display on reruns if needed
if st.session_state.log_handler and not prompt:
     log_container.code(st.session_state.current_logs or st.session_state.log_handler.get_logs(), language="log")