# Ollama AI
import fitz  # PyMuPDF
import requests

# Remote AI
import anthropic
import argparse
import base64
import os
import re
from dotenv import load_dotenv
from pathlib import Path
from typing import List


#
# OLLAMA AI FUNCTIONS
#

def extract_pdf_text_for_ollama_ai(file_path):
    """Load PDF text from a file path."""
    doc = fitz.open(file_path)
    pdf_text = ""

    for page in doc:
        pdf_text += page.get_text()

    return pdf_text


def ask_ollama_for_date(text, model):
    """Determine the invoice date from PDF data using Ollama AI."""
    prompt = f"""The following is the text of an invoice. Extract the **invoice date** only and return nothing but the invoice date in format YYMMDD.

--- BEGIN INVOICE TEXT ---
{text}
--- END INVOICE TEXT ---"""

    response = requests.post(
        os.getenv("OLLAMA_API_URL") + "/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json()['response'].strip()


def is_ollama_running() -> bool:
    """Check if Ollama API is running."""
    try:
        response = requests.get(os.getenv("OLLAMA_API_URL") + "/version", timeout=2)
        return response.status_code == 200

    except:
        return False


#
# REMOTE AI FUNCTIONS
#

def load_pdf_data_for_remote_ai(pdf_file_path: str) -> str:
    """Load and encode PDF data from a file path."""
    with open(pdf_file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode("utf-8")
    return pdf_data


def determine_invoice_date_remote_ai(ai_client, pdf_data: str) -> str:
    """Determine the invoice date from PDF data using AI."""
    message = ai_client.beta.messages.create(
        model=os.getenv("ANTHROPIC_MODEL"),
        betas=["pdfs-2024-09-25"],
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": "What's the invoice date of this document? Return nothing but the invoice date in format YYMMDD."
                    }
                ]
            }
        ],
    )

    return message.content[0].text


def get_remote_ai_client():
    """Create and return an Anthropic AI client."""
    load_dotenv()
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


#
# GENERAL FUNCTIONS
#

def get_pdf_files(directory: str) -> List[Path]:
    """Get all PDF files from a directory."""
    directory_path = Path(directory)
    return list(directory_path.glob("*.pdf")) + list(directory_path.glob("*.PDF"))


def to_kebab_case(filename: str) -> str:
    """Convert a filename to lowercase kebab case."""
    # Remove file extension
    base_name = os.path.splitext(filename)[0]

    # Replace spaces and special characters with hyphens
    kebab = re.sub(r'[^a-zA-Z0-9]', '-', base_name)

    # Replace multiple consecutive hyphens with a single one
    kebab = re.sub(r'-+', '-', kebab)

    # Remove leading and trailing hyphens
    kebab = kebab.strip('-')

    # Convert to lowercase
    return kebab.lower()


def is_already_formatted(filename: str) -> bool:
    """Check if a filename already follows the required format (YYMMDD-kebab-case.pdf)."""
    # Check if the filename matches the pattern: 6 digits followed by a hyphen, then kebab case
    pattern = r'^(\d{6})-([a-z0-9]+-)*[a-z0-9]+\.pdf$'
    return bool(re.match(pattern, filename.lower()))


def rename_pdf_with_date(pdf_path: Path, invoice_date: str) -> None:
    """Rename a PDF file with the invoice date and kebab case."""
    # Get the directory and filename
    directory = pdf_path.parent
    filename = pdf_path.name

    # Convert filename to kebab case
    kebab_name = to_kebab_case(filename)

    # Create new filename with date prefix
    new_filename = f"{invoice_date}-{kebab_name}.pdf"

    # Create full path for the new file
    new_path = directory / new_filename

    # Rename the file
    pdf_path.rename(new_path)
    print(f"Renamed: {pdf_path} -> {new_path}")


def process_pdf_directory(directory: str) -> None:
    """Process all PDFs in a directory to rename them with invoice dates."""
    # Get AI client
    client = get_remote_ai_client()

    # Get all PDF files in the directory
    pdf_files = get_pdf_files(directory)

    if not pdf_files:
        print(f"No PDF files found in directory: {directory}")
        return

    print(f"Found {len(pdf_files)} PDF files to process")

    ollama_is_available = (
            os.getenv("OLLAMA_API_URL") and
            os.getenv("OLLAMA_MODEL") and
            is_ollama_running()
    )

    # Process each PDF file
    for pdf_path in pdf_files:
        try:
            # Check if the file already follows the required format
            if is_already_formatted(pdf_path.name):
                print(f"Skipping {pdf_path}: File already follows the required format")
                continue

            if ollama_is_available:
                text = extract_pdf_text_for_ollama_ai(str(pdf_path))
                invoice_date = ask_ollama_for_date(text, os.getenv("OLLAMA_MODEL"))

            else:
                # Load PDF data
                pdf_data = load_pdf_data_for_remote_ai(str(pdf_path))

                # Determine invoice date
                invoice_date = determine_invoice_date_remote_ai(client, pdf_data)

            # Rename the PDF file
            rename_pdf_with_date(pdf_path, invoice_date)

        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Process PDF invoices and rename them with dates.")
    parser.add_argument("directory", help="Directory containing PDF files to process")
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_arguments()
    process_pdf_directory(args.directory)


if __name__ == "__main__":
    main()
