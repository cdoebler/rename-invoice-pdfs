# PDF Invoice Date Extractor

This script processes PDF invoices, extracts their invoice dates using Ollama API or Claude AI as fallback if Ollama is
not available, and renames the files
with the date prefix in the format YYMMDD-filename.pdf.

## Requirements

- Python 3.6+
- Required packages: anthropic, dotenv, pymupdf

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with Ollama info and your Anthropic API key:
   ```
   ANTHROPIC_API_KEY="your_api_key_here"
   ANTHRIPIC_MODEL="claude-3-5-sonnet-20241022"

   OLLAMA_API_URL="http://localhost:11434/api"
   OLLAMA_API_URL="gemma3:27b"
   ```

   If OLLAMA_API_URL or OLLAMA_API_URL are not set the script will automatically use Claude AI.

## Usage

Run the script with a directory path as an argument:

```bash
python main.py /path/to/pdf/directory
```

For example, to process all PDFs in the current directory:

```bash
python main.py .
```

## How it works

1. The script reads all PDF files from the specified directory
2. It checks if each file already follows the required format (YYMMDD-kebab-case.pdf)
3. Files that already follow the format are skipped with a message
4. For files that need processing, it uses Ollama API or Claude AI as fallback if Ollama is not available, to determine
   the invoice date
5. It renames these files to lowercase kebab case and prepends the determined invoice date

Example: "A file.PDF" with invoice date 21/03/2025 will become "250321-a-file.pdf"

## Error Handling

If any errors occur during processing, they will be reported but won't stop the script from processing other files.
