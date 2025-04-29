# utils.py

import logging
import streamlit as st
import os
from dotenv import load_dotenv

# --- Configuration ---
def load_config():
    """Loads API keys and other config from .env file."""
    load_dotenv()
    config = {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "openrouter_base_url": "https://openrouter.ai/api/v1",
        "openrouter_chat_model": "meta-llama/llama-4-scout:free",
        # Removed openrouter_embedding_model as we'll use HF
        "huggingface_api_token": os.getenv("HUGGINGFACEHUB_API_TOKEN"), # Load HF token
        "huggingface_embedding_model": "sentence-transformers/all-MiniLM-L6-v2" # Define HF model
    }
    if not config["openrouter_api_key"]:
        st.error("🚨 OpenRouter API key not found! Please set OPENROUTER_API_KEY in the .env file.")
        st.stop()
    if not config["huggingface_api_token"]:
        st.warning(
            "⚠️ Hugging Face API token (HUGGINGFACEHUB_API_TOKEN) not found in .env file. "
            "Inference API Embeddings might fail if the model requires authentication or hits rate limits. "
            "Consider using local embeddings (HuggingFaceEmbeddings) if issues persist."
        )
        # Depending on the model, the API might work without a key for public models under rate limits
        # Set it to None if not found, the HuggingFaceInferenceAPIEmbeddings class might handle it.
        config["huggingface_api_token"] = None # Allow proceeding without key, but with warning

    return config

# --- Logging Setup --- (Keep the rest of the logging code as is)
class StreamlitLogHandler(logging.Handler):
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.log_records = []
    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_records.append(msg)
        except Exception:
            self.handleError(record)
    def get_logs(self): return "\n".join(self.log_records)
    def clear_logs(self): self.log_records = []

logger = logging.getLogger("RAG_APP")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
if not logger.handlers: pass

def setup_streamlit_logging(log_container):
    for handler in logger.handlers[:]:
        if isinstance(handler, StreamlitLogHandler): logger.removeHandler(handler)
    st_handler = StreamlitLogHandler(log_container)
    st_handler.setFormatter(formatter)
    logger.addHandler(st_handler)
    return st_handler

# --- Helper Functions ---
def get_manual_text(filepath="data/ace900_takeoff_manual.txt"):
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return f.read()
    except FileNotFoundError:
        st.error(f"🚨 Manual file not found at: {filepath}")
        st.stop()
    except Exception as e:
        st.error(f"🚨 Error reading manual file: {e}")
        st.stop()