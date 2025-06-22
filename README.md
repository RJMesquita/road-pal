# Road Pal
<p align="center">
  <img src="img/avatar_1.jpeg" alt="Road Pal" height="120"/>
</p>

Road Pal is an AI-powered assistant specialized in the Portuguese Highway Code ("Código da Estrada"). It helps users—especially those preparing for their driving license—by answering questions, providing explanations, and supporting learning with both official legislation and practical questions.

## Features

- **Chatbot interface** using Gradio for interactive Q&A.
- **Retrieval-Augmented Generation (RAG):** Combines OpenAI LLMs with a vector database for context-aware answers.
- **Document ingestion:** Supports both PDF (official code) and Markdown (practice questions).
- **Supabase vector store:** Stores document embeddings for fast search.

## How it works

1. **Ingestion**
   - PDF documents (e.g., Código da Estrada) are parsed and chunked.
   - Markdown files with questions, options, correct answers, and associated images are parsed.
   - Each chunk/question is embedded and stored in Supabase.

2. **Chatbot**
   - User asks a question via the Gradio interface.
   - The question is embedded and used to retrieve the most relevant documents from Supabase.
   - Retrieved context is sent to the OpenAI LLM to generate a final answer.


## Setup

1. **Clone the repo and install dependencies**
   ```bash
   git clone <repo-url>
   cd road_pal
   uv venv
   source .venv/bin/activate or .\.venv\Scripts\activate.bat
   uv pip install .

2. **Configure environment variables**  
Create a .env file with your OpenAI and Supabase credentials:   
    ```
    OPENAI_API_KEY=sk-...
    SUPABASE_URL=https://xxxx.supabase.co
    SUPABASE_API_KEY=...
    ```
3. **Ingest documents**  
    - Run the ingestion notebook:
    notebooks/ingestion/ingestion.ipynb  
    - This will parse PDFs and Markdown, create embeddings, and populate Supabase.
    Run the chatbot
4. **Run the chatbot**  
    `python app.py`

    Access the Gradio interface in your browser.

## TODO

- **Refactor for Scalability:** Enhance the existing codebase to ensure greater scalability and maintainability for future growth.
- **Improve User Interface:** Refine the application's interface to effectively present tests and provide comprehensive assistance to students.
- **Integrate Multimodal Support:** (Optional) Implement the capability to embed both text and images, leveraging advanced models such as OpenAI GPT-4o for comprehensive data representation.