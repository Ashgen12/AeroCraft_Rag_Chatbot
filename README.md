# ✈️ AeroCraft ACE-900 RAG Chatbot with Knowledge Graph

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Ashgen12/AeroCraft_Rag_Chatbot)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-integrated-brightgreen)](https://python.langchain.com/)

**Answer questions about the AeroCraft ACE-900 Takeoff Procedures using a Retrieval-Augmented Generation (RAG) system enhanced by a dynamically built Knowledge Graph.**

---

## Overview

This project demonstrates building a sophisticated chatbot application using modern AI techniques. It leverages a specific section of the fictional AeroCraft ACE-900 Operations Manual (focused on Normal Takeoff Procedures) to answer user questions.

The core idea is to combine:

1.  **Retrieval-Augmented Generation (RAG):** Using a vector store (FAISS with Hugging Face embeddings) to find relevant text chunks from the manual based on the user's query.
2.  **Knowledge Graph (KG):** Automatically extracting key concepts (Phases, Steps, Parameters, Values) and their relationships from the manual text into a structured graph (using NetworkX). This graph provides additional, structured context to the AI.
3.  **Large Language Model (LLM):** Using an LLM (via OpenRouter, e.g., Llama models) to synthesize the retrieved text chunks and the KG context into a coherent, accurate answer.
4.  **Interactive Frontend:** A user-friendly chat interface built with Streamlit.
5.  **Monitoring:** Transparency into the RAG process through logging of intermediate steps.

## ✨ Live Demo

Experience the chatbot live on Hugging Face Spaces:

[➡️ Launch AeroCraft Chatbot Demo](https://huggingface.co/spaces/Ashgen12/AeroCraft_Rag_Chatbot)

## Key Features

*   **Conversational Interface:** Ask questions in natural language.
*   **Contextual Answers:** Responses are grounded in the provided AeroCraft ACE-900 Takeoff Procedures manual section.
*   **Knowledge Graph Enhancement:** Utilizes a KG built from the manual to improve retrieval relevance and answer accuracy by providing structured context.
*   **Interactive KG Visualization:** View the extracted knowledge graph using Plotly directly in the sidebar.
*   **Vector Embeddings:** Employs Hugging Face Inference API for efficient text embeddings.
*   **Flexible LLM Backend:** Uses OpenRouter to connect to various LLMs (configured for `meta-llama/llama-4-scout:free` by default).
*   **Transparent Processing:** Monitor key steps (entity extraction, KG query, LLM input) via expandable logs in the UI.
*   **Modular Codebase:** Organized Python code for better maintainability.

## 🛠️ Technology Stack

*   **Frontend:** Streamlit
*   **Backend & Orchestration:** Python, LangChain
*   **Knowledge Graph:** NetworkX (Graph structure), Regex (Extraction), Plotly (Visualization)
*   **Embeddings:** Hugging Face Inference API (`sentence-transformers/all-MiniLM-L6-v2`)
*   **Vector Store:** FAISS (In-memory)
*   **LLM:** OpenRouter API (e.g., `meta-llama/llama-4-scout:free`)
*   **Environment:** `python-dotenv`

## 📂 Project Structure

```text
aerocraft_chatbot/
├── data/
│   └── ace900_takeoff_manual.txt # Manual text fragment
├── static/
│   └── kg_visualization.html     # Generated Plotly graph HTML (optional, if saved)
├── .env                          # API Keys (DO NOT COMMIT)
├── .gitignore                    # Git ignore file
├── app.py                        # Main Streamlit application
├── kg_builder.py                 # Knowledge Graph creation & visualization (Plotly)
├── rag_chain.py                  # RAG chain implementation (LangChain)
├── utils.py                      # Helper functions (logging, config)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```
## ⚙️ Setup Instructions

**1. Prerequisites:**
    *   Python (3.10 or later recommended)
    *   pip (Python package installer)
    *   Git

**2. Clone Repository:**
    
    git clone https://github.com/Ashgen12/AeroCraft_Rag_Chatbot.git
    cd aerocraft_chatbot
    

**3. Create Virtual Environment (Recommended):**
    ```
    python -m venv venv
    ```
    Activate the environment:
    *   On Windows:
        ```
        venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```
        source venv/bin/activate
        ```

**4. Install Dependencies:**
    ```
    pip install -r requirements.txt
    ```

**5. Obtain API Keys:**
    *   **OpenRouter:** Sign up at [OpenRouter.ai](https://openrouter.ai/) and get an API key. This allows access to various LLMs.
    *   **Hugging Face:** Sign up at [HuggingFace.co](https://huggingface.co/). Create an API Token with read access (usually sufficient for public embedding models). Go to `Settings` -> `Access Tokens` -> `New token`.

**6. Configure Environment Variables:**
    *   Create a file named `.env` in the root `aerocraft_chatbot/` directory.
    *   Add your API keys to the `.env` file like this:
    ```
    OPENROUTER_API_KEY="your_openrouter_api_key_here"
    HUGGINGFACEHUB_API_TOKEN="hf_your_huggingface_token_here"
    ```
    *   **Important:** Ensure `.env` is listed in your `.gitignore` file to avoid committing your secret keys.

## 🚀 Running the Application

1.  Make sure your virtual environment is activated.
2.  Navigate to the project's root directory (`aerocraft_chatbot/`).
3.  Run the Streamlit application:
   
    ```bash
    streamlit run app.py
    ```
5.  Streamlit will typically open the application automatically in your web browser (usually at `http://localhost:8501`).

## 💬 How to Use

1.  **Wait for Initialization:** Allow the application to start up. It needs to build the Knowledge Graph and set up the RAG chain on the first run or if the manual changes. Check the sidebar for status messages like "Building Knowledge Graph..." and "Initializing RAG chain...".
2.  **Ask a Question:** Once the sidebar indicates "✅ Ready", type your question about the AeroCraft ACE-900 Takeoff Procedures into the chat input box at the bottom (e.g., "What is the rotate speed?", "Describe the pre-takeoff checklist", "What flap setting for takeoff?").
3.  **Get Answer:** Press Enter or click the send button. The assistant will process your query using the RAG chain (fetching relevant text and KG context) and generate an answer using the LLM.
4.  **Explore Sidebar:**
    *   **Knowledge Graph Status:** See the initialization status.
    *   **View Interactive Knowledge Graph:** Expand this section to see the Plotly visualization of the extracted concepts (nodes) and their relationships (edges). You can pan, zoom, and hover over nodes.
    *   **⚙️ View Processing Logs:** Expand this section *after* asking a question to see the internal steps taken to generate the answer (see Monitoring section below).

## 📊 Knowledge Graph Details

*   **Automatic Construction:** The Knowledge Graph is automatically built on startup by parsing the `data/ace900_takeoff_manual.txt` file. The `kg_builder.py` script uses regular expressions to identify key entities (Phases, Steps, Parameters, Values) and their relationships based on patterns in the text.
*   **Structure:**
    *   **Nodes:** Represent concepts like takeoff phases (e.g., "Pre-Takeoff"), checklist items/steps (e.g., "Flaps Set"), parameters (e.g., "Rotation Speed (Vr)"), and specific values (e.g., "145 KIAS", "15 degrees").
    *   **Edges:** Represent relationships between nodes (e.g., `Phase --includes--> Step`, `Step --has_parameter--> Parameter`, `Parameter --has_value--> Value`).
*   **Visualization:** The graph is visualized using Plotly, generating an interactive HTML graph embedded in the Streamlit sidebar (`static/kg_visualization.html` is generated if saving is enabled, but primarily it's shown directly).
*   **Query Enhancement:** During query processing, relevant entities (keywords matching node names or types) are extracted from your question. These entities are used to query the NetworkX graph. The context retrieved from the KG (information about the matched nodes and their immediate neighbors) is then added to the prompt sent to the LLM, alongside the text chunks retrieved from the vector store. This structured context helps the LLM provide more accurate, specific, and grounded answers.

## 🔍 Monitoring

The "⚙️ View Processing Logs" expander provides insight into the RAG pipeline for the *most recent* query:

*   `Query Received:` Logs the exact question you asked and when processing started.
*   `Entities Extracted:` Shows the keywords or concepts identified in your question that might correspond to nodes in the KG.
*   `KG Query:` Logs which of the extracted entities were actually found in the Knowledge Graph.
*   `KG Context:` Displays the structured information retrieved from the Knowledge Graph based on the found entities (e.g., details about related nodes and their connections).
*   `LLM Input:` Shows the final combined context (KG context + relevant text chunks from the manual) and the user question that is being sent to the Large Language Model for synthesizing the answer.
*   `Final Answer:` Logs when the LLM has finished generating the response displayed in the chat.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Ashgen12/AeroCraft_Rag_Chatbot/issues) (if you have one) or open a new issue to discuss changes. Pull requests are also appreciated.

## 📧 Contact

*   **GitHub:** [Ashgen12](https://github.com/Ashgen12)
*   **Email:** ashunaukari01@gmail.com
