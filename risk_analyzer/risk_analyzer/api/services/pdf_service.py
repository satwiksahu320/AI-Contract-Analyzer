from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

MAX_PDF_PAGES = 20
MAX_EXTRACTED_CHARACTERS = 20000


def extract_pdf_text(pdf_file):
    text = ""

    try:
        reader = PdfReader(pdf_file)
    except PdfReadError as exc:
        raise ValueError("The uploaded PDF could not be read.") from exc

    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported.")

    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError(f"PDFs are limited to {MAX_PDF_PAGES} pages.")

    for page in reader.pages:
        extracted = page.extract_text()

        if extracted:
            text += extracted + "\n"

        if len(text) > MAX_EXTRACTED_CHARACTERS:
            text = text[:MAX_EXTRACTED_CHARACTERS]
            break

    text = text.strip()

    if not text:
        raise ValueError("No readable text was found in the PDF.")

    return text
