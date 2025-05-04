import io
import os
import re
import subprocess
from pathlib import Path
from typing import Callable, Dict

import pandas as pd
from PyPDF2 import PdfReader

pd.set_option("display.max_colwidth", None)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    pdf_stream = io.BytesIO(pdf_bytes)
    reader = PdfReader(pdf_stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def extract_text_from_xlsx(xlsx_bytes: bytes) -> str:
    """Извлекает текст из XLSX (Excel)."""
    xlsx_stream = io.BytesIO(xlsx_bytes)
    # Читаем все листы и объединяем текст
    text = []
    df_dict = pd.read_excel(xlsx_stream, sheet_name=None)  # Все листы
    for sheet_name, df in df_dict.items():
        text.append(f"--- Лист: {sheet_name} ---")
        text.append(df.to_string(index=False))
    return "\n".join(text).strip()


def extract_text_from_file(file_bytes: bytes, file_extension: str) -> str:
    """Основная функция для извлечения текста из файла."""
    handlers: Dict[str, Callable[[bytes], str]] = {
        "pdf": extract_text_from_pdf,
        "xlsx": extract_text_from_xlsx,
        "xls": extract_text_from_xlsx,
    }

    file_extension = file_extension.lower()

    if file_extension in handlers:
        return handlers[file_extension](file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


def convert_to_pdf(input_path: str) -> tuple:
    """
    Converts DOC/DOCX to PDF using LibreOffice.
    Returns path to the generated PDF.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir = input_path.parent

    subprocess.run(
        [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            str(input_path),
            "--outdir",
            str(output_dir),
        ]
    )

    pdf_path = output_dir / f"{input_path.stem}.pdf"
    return (str(pdf_path) if pdf_path.exists() else None), pdf_path


def clear_text(text: str) -> str:
    cleaned_string = re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9\s]", "", text)
    cleaned_string = re.sub(r"\s+", " ", cleaned_string).strip()
    return cleaned_string.lower().replace("nan", "").replace("unnamed", "")


def read_file(file_path: str) -> str:
    if file_path.endswith(".doc") or file_path.endswith(".docx"):
        convert_to_pdf(file_path)
        os.remove(file_path)
        file_path = file_path.replace(".docx", ".pdf").replace(".doc", ".pdf")
    file_bytes = Path(file_path).read_bytes()
    os.remove(file_path)
    ext = file_path.split(".")[-1]
    text = extract_text_from_file(file_bytes, ext)
    return clear_text(text)
