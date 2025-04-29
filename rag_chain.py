# rag_chain.py

import streamlit as st
from langchain_openai import ChatOpenAI 
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain.schema.output_parser import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.load import dumps, loads
from langchain_core.documents import Document
import re
import os 
from operator import itemgetter
from langchain_core.runnables import RunnableParallel

from utils import logger, load_config
from kg_builder import query_kg_for_entities

# --- Configuration & Initialization ---
config = load_config() # Load config including OpenRouter and HF details

# --- Initialize LLM using OpenRouter (No change here) ---
logger.info(f"Initializing LLM with OpenRouter model: {config['openrouter_chat_model']}")
try:
    llm = ChatOpenAI(
        model=config["openrouter_chat_model"],
        openai_api_key=config["openrouter_api_key"],
        openai_api_base=config["openrouter_base_url"],
        temperature=0.8,
    )
    logger.info("LLM initialized successfully via OpenRouter.")
except Exception as e:
    logger.error(f"Failed to initialize LLM via OpenRouter: {e}", exc_info=True)
    st.error(f"🚨 Failed to initialize Chat Model via OpenRouter: {e}")
    st.stop()

# --- Initialize Embeddings using Hugging Face Inference API ---
logger.info(f"Initializing Embeddings via HuggingFace Inference API: {config['huggingface_embedding_model']}")
try:
    # Use HuggingFaceInferenceAPIEmbeddings
    embeddings = HuggingFaceInferenceAPIEmbeddings(
        api_key=config["huggingface_api_token"], # Pass the key from config (can be None)
        model_name=config["huggingface_embedding_model"] # Specify the model
    )
    # Perform a quick test embed to ensure connectivity (optional but recommended)
    _ = embeddings.embed_query("Test embedding query")
    logger.info("HuggingFace Inference API Embeddings initialized and tested successfully.")

except ImportError:
     logger.error("ImportError: `huggingface_hub` or related libraries not found. Please run `pip install huggingface-hub`.")
     st.error("🚨 Required library for Hugging Face embeddings is missing. Please install `huggingface-hub`.")
     st.stop()
except Exception as e:
    logger.error(f"Failed to initialize HuggingFace Inference API Embeddings: {e}", exc_info=True)
    st.error(f"🚨 Failed to initialize HuggingFace Inference API Embeddings for model '{config['huggingface_embedding_model']}': {e}")
    st.info("Consider checking your HUGGINGFACEHUB_API_TOKEN, the model name, or try using local HuggingFace embeddings (`HuggingFaceEmbeddings`) as an alternative if API issues persist.")
    st.stop() # Stop if primary embedding method fails and fallback is not used/fails


# Global variables for vector store and KG (keep as is)
vector_store = None
knowledge_graph = None

# --- Core RAG Components ---

def setup_vector_store(manual_text):
    """Creates or loads the vector store from the manual text."""
    global vector_store
    if vector_store is None:
        # Now uses the HuggingFace embeddings object initialized above
        logger.info("Setting up vector store using HuggingFace Inference API embeddings...")
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, # Adjust chunk size based on model/performance
                chunk_overlap=150,
                length_function=len,
                add_start_index=True,
            )
            docs = text_splitter.create_documents([manual_text])
            logger.info(f"Split manual into {len(docs)} documents.")

            # Create FAISS index using the configured HuggingFace embeddings
            vector_store = FAISS.from_documents(docs, embeddings) # FAISS uses the 'embeddings' object automatically
            logger.info("FAISS vector store created successfully with HuggingFace embeddings.")
        except Exception as e:
            logger.error(f"Error setting up vector store with HuggingFace embeddings: {e}", exc_info=True)
            st.error(f"🚨 Failed to initialize vector store: {e}")
            st.stop()
    return vector_store.as_retriever(search_kwargs={'k': 4}) # Adjust k if needed


def setup_knowledge_graph(graph):
    """Sets the global knowledge graph."""
    global knowledge_graph
    knowledge_graph = graph
    logger.info("Knowledge graph loaded into RAG chain.")

# --- Entity Extraction Function (Add Debug Logging) ---
def extract_entities_simple(query: str) -> list[str]:
    logger.debug(f"Inside extract_entities_simple, received input type: {type(query)}")
    if not isinstance(query, str):
        logger.error(f"extract_entities_simple received non-string input: {query}")
        # Return empty list or raise error? Let's return empty to be slightly more robust.
        return []
    potential_entities = []
    try:
        potential_entities.extend(re.findall(r'\b[A-Z][a-zA-Z]*\b', query))
        query_lower = query.lower()
        known_terms = ["takeoff", "flaps", "engine", "power", "speed", "checklist", "taxi", "rotate", "climb", "gear", "vr", "vy", "n1", "knots", "degrees", "agl"]
        for term in known_terms:
            if term in query_lower:
                 try:
                     match = re.search(r'\b' + re.escape(term) + r'\b', query, re.IGNORECASE)
                     if match: potential_entities.append(match.group(0))
                     else: potential_entities.append(term)
                 except Exception: potential_entities.append(term)
        entities = list(set([e.strip(".,!?;:") for e in potential_entities if len(e) > 2]))
        logger.info(f"Extracted entities (simple): {entities}")
        return entities
    except TypeError as te:
        logger.error(f"TypeError inside extract_entities_simple! Input type was: {type(query)}. Error: {te}", exc_info=True)
        raise te # Re-raise for clarity during debugging
    except Exception as e:
        logger.error(f"Unexpected error in extract_entities_simple: {e}", exc_info=True)
        return []

# --- RAG Chain Definition ---

# Prompt Template (Keep as is)
template = """
You are an expert assistant for the AeroCraft ACE-900 aircraft, specializing in its operations manual.
Answer the user's question based *only* on the provided context information from the manual and the knowledge graph.
Be precise and refer to specific procedures, values, or steps mentioned.
If the context doesn't contain the answer, state clearly that the information is not available in the provided section of the manual.
Do not make up information or answer based on general knowledge outside the context.

Knowledge Graph Context:
{kg_context}

Manual Text Context:
{manual_context}

User Question: {question}

Answer:
"""
prompt = ChatPromptTemplate.from_template(template)


def format_docs(docs):
    # Add a check for empty or invalid input
    if not docs or not isinstance(docs, list):
        logger.warning(f"format_docs received invalid input: {docs}")
        return "No relevant documents found."
    return "\n\n".join(doc.page_content for doc in docs if hasattr(doc, 'page_content'))

def get_kg_context(query_entities):
    if not knowledge_graph:
        logger.warning("KG not available for context retrieval.")
        return "N/A"
    kg_results = query_kg_for_entities(knowledge_graph, query_entities)
    if not kg_results:
        return "No specific information found in Knowledge Graph for these entities."
    return "\n".join(f"- KG Node: {item}" for item in kg_results)



def create_rag_chain(retriever):
    """Builds the complete RAG chain with KG integration."""
    logger.info("Creating RAG chain with restructured input handling...")

    # Define the sequence step-by-step for clarity

    # Step 1: Extract the question string from the initial input dictionary
    # Input: {"question": q_str} -> Output: q_str
    _get_question = itemgetter("question")

    # Step 2: Define how to calculate entities based on the question string
    # Input: q_str -> Output: list_of_entities
    _get_entities = RunnableLambda(extract_entities_simple)

    # Step 3: Define how to get KG context based on entities
    # Input: list_of_entities -> Output: kg_context_str
    _get_kg_context = RunnableLambda(get_kg_context)

    # Step 4: Define how to get manual context based on the question string
    # Input: q_str -> Output: manual_context_str
    _get_manual_context = retriever | RunnableLambda(format_docs)

    # Step 5: Combine calculations using RunnablePassthrough.assign
    # This structure ensures each calculation gets the correct input from the preceding state.
    rag_chain_sequence = (
        # Start with the initial input {"question": q_str}
        RunnablePassthrough.assign( # Calculate entities and add to the dict
            entities=_get_question | _get_entities
        )
        # Now the context is {"question": q_str, "entities": list_of_e}
        | RunnablePassthrough.assign( # Calculate kg_context and manual_context in parallel
            kg_context=itemgetter("entities") | _get_kg_context,
            manual_context=_get_question | _get_manual_context
          )
        # Context: {"question": q_str, "entities": list_of_e, "kg_context": kg_str, "manual_context": manual_str}
        | RunnablePassthrough.assign( # Log the context before the prompt
              llm_input=lambda x: logger.info(f"--- LLM Input ---\nKG Context: {x.get('kg_context', 'N/A')}\nManual Context: {x.get('manual_context', 'N/A')[:500]}...\nQuestion: {x.get('question', 'N/A')}\n------") or x
          )
        | prompt # Format the prompt using the context dictionary
        | llm
        | StrOutputParser()
    )

    logger.info("RAG chain created successfully with new structure.")
    return rag_chain_sequence