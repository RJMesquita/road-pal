import json
import os

import gradio as gr
import openai
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from loguru import logger
from supabase import Client, create_client

from src.constants import CHATBOT_AVATAR_URL, GRADIO_THEME

# Load environment variables from .env file
load_dotenv(override=True)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY")

# Read system prompt from a file
SYSTEM_PROMPT_PATH = (
    "/Users/ricardo.mesquita/Documents/Trainings/code4all/road_pal/system_prompt.txt"
)
with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Initialize Supabase and Embeddings Globally
supabase: Client = None
embeddings_model: OpenAIEmbeddings = None

if SUPABASE_URL and SUPABASE_API_KEY and OPENAI_API_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
        embeddings_model = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small"
        )
        logger.success("Supabase client and OpenAI embeddings initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase or OpenAI embeddings: {e}")
        supabase = None
        embeddings_model = None
else:
    logger.warning(
        "Warning: Supabase or OpenAI environment variables not set. RAG functionality will be disabled."
    )


def retrieve_relevant_documents(query: str, top_k: int = 5) -> list:
    """
    Retrieves the most relevant documents from Supabase using vector similarity search.
    """
    if not supabase or not embeddings_model:
        return []

    try:
        # Generate embedding for the user's query
        query_embedding = embeddings_model.embed_query(query)

        # Perform similarity search in Supabase
        response = supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_count": top_k,
            },
        ).execute()

        if response.data:
            # Parse metadata if it's stored as a JSON string
            for doc in response.data:
                if isinstance(doc.get("metadata"), str):
                    doc["metadata"] = json.loads(doc["metadata"])
            return response.data
        elif response.error:
            logger.error(f"Supabase RLS or RPC error: {response.error}")
            return []
        else:
            return []

    except Exception as e:
        logger.error(f"Error during document retrieval: {e}")
        return []


def openai_chatbot_logic(message, history):
    """
    Uses OpenAI's API and RAG to generate a chatbot response.
    """
    if not OPENAI_API_KEY:
        return "OpenAI API key not found. Please set OPENAI_API_KEY in your .env file."

    # Retrieve relevant documents
    context_text = ""
    if supabase and embeddings_model:  # Only run RAG if Supabase is initialized
        relevant_docs = retrieve_relevant_documents(
            message, top_k=5
        )  # Retrieve top 5 docs
        if relevant_docs:
            context_text = "Context Information:\n"
            for i, doc in enumerate(relevant_docs):
                source_info = "Source: Unknown"
                if doc.get("metadata"):
                    # Accessing metadata fields
                    source = doc["metadata"].get("source", "N/A")
                    page = doc["metadata"].get("page_number", "N/A")
                    source_info = f"Source: {source}, Page: {page}"

                context_text += (
                    f"--- Document {i + 1} ---\n{doc['content']}\n[{source_info}]\n\n"
                )
            context_text += "--- End Context Information ---\n\n"
        else:
            context_text = "No specific context found in the knowledge base."

    # Prepare the conversation for OpenAI
    messages = []
    # Add the retrieved context to the system message or as a preliminary user message
    if context_text:
        messages.append(
            {
                "role": "system",
                "content": f"{SYSTEM_PROMPT}\n--- Contexto ---\n{context_text}",
            }
        )
    else:
        messages.append(
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        )

    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if bot_msg:
            messages.append({"role": "assistant", "content": bot_msg})
    # Add the latest user message
    messages.append({"role": "user", "content": message})

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.3,
        )
        bot_response = response.choices[0].message.content.strip()
    except Exception as e:
        bot_response = f"Error communicating with OpenAI API: {e}"

    return bot_response


chat_interface = gr.ChatInterface(
    fn=openai_chatbot_logic,
    title="Road Pal 🚗🏍️",
    description="Pergunta-me o que quiseres sobre o Código da Estrada e outras regras de trânsito...",
    theme=GRADIO_THEME,
    chatbot=gr.Chatbot(
        height=700,
        avatar_images=(
            None,
            CHATBOT_AVATAR_URL,
        ),
    ),
    textbox=gr.Textbox(
        placeholder="Tens alguma pergunta sobre o Código da Estrada?",
        container=False,
        scale=7,
    ),
    examples=[
        "Qual é a velocidade máxima permitida em autoestradas?",
        "Quais são as regras para ultrapassagens?",
        "O que devo fazer se um veículo de emergência se aproximar?",
        "Quais são as penalizações por conduzir sob o efeito de álcool?",
    ],
    cache_examples=False,
)

if __name__ == "__main__":
    chat_interface.launch(debug=True)
