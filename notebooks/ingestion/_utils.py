from __future__ import annotations

import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


def ingest_via_pdf(
    file_path: str, metadata: dict[str, str], apply_cleaning: bool = True
) -> list[dict[str, str]]:
    """
    Ingests a PDF file, extracts text, cleans it, splits it into chunks,
    and adds specified metadata to each chunk.

    Args:
        file_path (str): The path to the PDF file.
        metadata (dict): A dictionary containing manual metadata:
                         'source', 'date', 'description', 'language', 'title'.

    Returns:
        list: A list of dictionaries, where each dictionary represents a chunk
              with 'content' and 'metadata' fields.
    """
    reader = PdfReader(file_path)
    all_chunks = []

    # Initialize text splitter for effective chunking
    # These parameters can be tuned based on the nature of your text and desired chunk size
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if not page_text:
            continue

        # Clean and optimize text
        cleaned_text = page_text
        if apply_cleaning:
            cleaned_text = clean_text(
                page_text
            )  # TODO: This function needs to refactor to be scalable to other PDFs

        # Split the cleaned text into chunks
        chunks = text_splitter.create_documents([cleaned_text])

        for chunk in chunks:
            chunk_metadata = {
                "page_number": page_num + 1,
                **metadata,  # Add the manually defined metadata
            }
            all_chunks.append(
                {"content": chunk.page_content, "metadata": chunk_metadata}
            )
    return all_chunks


def clean_text(text: str) -> str:
    """
    Cleans the extracted text by removing common PDF artifacts,
    excessive whitespace, and potentially irrelevant headers/footers
    (based on common patterns).

    Args:
        text (str): The raw text extracted from a PDF page.

    Returns:
        str: The cleaned text.
    """
    # Remove common page headers/footers like 'Diário da República', page numbers, and dates
    # These patterns are observed in your provided PDF
    text = text.replace("Diário da República, 1.ª série", "").replace("Pág.", "")
    text = text.replace("9 de dezembro de 2020", "").replace("Ν.° 238", "")

    # Remove multiple spaces, newlines, and tabs
    text = " ".join(text.split())

    # You might want to add more specific cleaning rules here
    # For instance, removing LaTeX-like citation markers if they are not useful for your RAG
    # However, the provided citation guidelines suggest keeping ""

    return text


def ingest_markdown_questions(md_file_path: str, metadata: dict[str, str]):
    """
    Ingests a markdown file with questions, images, options, and correct answers.
    Extracts each question block and prepares it for embedding.
    The image path is stored in metadata.
    """
    with open(md_file_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Split on question blocks (handles both 1. and 11. etc)
    question_blocks = re.split(r"\n\d+\.\s+\*\*Pergunta:\*\*", md_content)[1:]

    documents = []
    for idx, block in enumerate(question_blocks):
        # Extract question text (up to image)
        question_match = re.match(
            r"(.*?)(\*\*Imagem Associada:\*\*|$)", block, re.DOTALL
        )
        question_text = question_match.group(1).strip() if question_match else ""

        # Extract image path
        image_match = re.search(r"!\[.*?\]\((.*?)\)", block)
        image_path = image_match.group(1).strip() if image_match else None

        # Extract options
        options_match = re.search(
            r"\*\*Opções:\*\*\s*(A\..*?)(\*\*Resposta Correta:\*\*|$)", block, re.DOTALL
        )
        options_text = options_match.group(1).strip() if options_match else ""
        # Remove all newlines in options
        options_text = options_text.replace("\n", " ")

        # Extract correct answer
        correct_match = re.search(r"\*\*Resposta Correta:\*\*\s*([A-Z])", block)
        correct_answer = correct_match.group(1).strip() if correct_match else ""

        # Compose content for embedding (text only)
        content = f"Pergunta: {question_text} Opções: {options_text}Resposta Correta: {correct_answer}"

        # Add image path to metadata if present
        doc_metadata = metadata.copy()
        if image_path:
            doc_metadata["image_path"] = image_path

        documents.append(Document(page_content=content, metadata=doc_metadata))

    return documents
