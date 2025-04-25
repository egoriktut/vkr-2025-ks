# from app.validation import KSValidator
# from app.utils.file_util import read_file
# import camelot
# import pandas as pd
#
#
#
# validator = KSValidator()
#
# tz_name = "tz.pdf"
# pk_name = "pk.doc"
# reference_col_name = {
#     "name": ["Наименование", "Название"],
#     "quantity": ["Кол.", "Кол-", "Кол-во", "Количество"],
#     "date": ["сроки", "срок", "Дата"],
#     "cost": ["Стоимость", "Цена", "Стоим"],
# }
#
# #validator.download_file("https://zakupki.mos.ru/newapi/api/FileStorage/Download?id=233468189", pk_name, 1)
# # validator.download_file("https://zakupki.mos.ru/newapi/api/FileStorage/Download?id=233468193", tz_name, 1)
#
#
# print("done bro")
#
# tables = camelot.read_pdf("./resources/_1_pk.pdf", pages="all", flavor="stream")
#
# print(tables)
# if tables is None:
#     print("NULL PAGES")
#
# all_doc_specs = []
# start_id = None
# prev_item_id = None
# table_wid = 0
#
# for table in tables:
#     df = table.df
#     specs = ["" for i in range(table_wid)]
#
#     if (start_id is None and df.shape[1] > 4 or start_id is not None and df.shape[1] >= table_wid) and not df.isnull().any().any():
#         print('READING TABLE')
#         for i in range(df.shape[0]):
#             print(list(df.iloc[i]))
#             if prev_item_id == None:
#                 sid = validator.find_start_id(df)
#                 if sid > -1:
#                     prev_item_id = 0
#
#                     specs = list(df.iloc[prev_item_id])
#                     table_wid = len(specs)
#                     all_doc_specs.append(["" for i in range(table_wid)])
#
#                     print("POBEDA READ ALL FILE TO END", specs, table_wid, prev_item_id)
#
#             else:
#                 # ширина равна шир табл
#                 if table_wid == len(list(df.iloc[i])):
#                     if list(df.iloc[i])[0] != '' and list(df.iloc[i])[0].isdigit():
#                         try:
#                             print("wanna new prev id [", list(df.iloc[i])[0], "]")
#                             prev_item_id = int(list(df.iloc[i])[0]) - 1
#                             for i in range(len(all_doc_specs), prev_item_id + 1):
#                                 all_doc_specs.append(["" for i in range(table_wid)])
#
#
#                         except:
#                             print("error parsing table col 0 for item id")
#                             # print("wanna new prev id [", list(df.iloc(i))[0], "]")
#                             # print(df.iloc(i))
#                     for col_id in range (table_wid):
#                         all_doc_specs[prev_item_id][col_id] += " " + list(df.iloc[i])[col_id]
#     if len(specs) == table_wid and specs != ["" for i in range(table_wid)]:
#         all_doc_specs.append(specs)
#
# for item in all_doc_specs:
#     print(item)
# # print(all_doc_specs)
#             #col_name_mapper: dict = validator.map_pdf_columns(reference_col_name, table.df.iloc[0])
#             #print("col mapa", col_name_mapper)

# import requests
# import json
#
# url = "http://localhost:5252/api/generate"
# text1 = "Yes! Today is weekend"
# text2 = "Oh, monday today"
# prompt = f"""
# You will compare the meaning of two texts.
#
# Answer strictly with one word: "yes" if the meanings are similar, or "no" if they are different. Do not explain or add anything else.
#
# First text: "{text1}"
# Second text: "{text2}"
# """
# payload = {
#     "model": "llama3",
#     "prompt": prompt,
#     "stream": False  # <<< ВАЖНО: отключаем потоковый режим
# }
#
# headers = {
#     "Content-Type": "application/json",
# }
#
# response = requests.post(url, headers=headers, data=json.dumps(payload))
#
# # Теперь весь ответ будет цельный
# result = response.json()
#
# # Печатаем только текст ответа
# print(result["response"])


import io
from pathlib import Path
from typing import Callable, Dict, Union
from PyPDF2 import PdfReader
import pandas as pd  # Для Excel



# --- Функции для извлечения текста ---

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Извлекает текст из PDF."""
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


# --- Роутер для выбора обработчика ---

def extract_text_from_file(file_bytes: bytes, file_extension: str) -> str:
    """Основная функция для извлечения текста из файла."""
    handlers: Dict[str, Callable[[bytes], str]] = {
        ".pdf": extract_text_from_pdf,
        ".xlsx": extract_text_from_xlsx,
        ".xls": extract_text_from_xlsx,
    }

    file_extension = file_extension.lower()

    if file_extension in handlers:
        return handlers[file_extension](file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


# --- Пример использования ---

if __name__ == "__main__":
    # Тестируем на разных файлах
    test_files = [
        ("1.pdf", ".pdf"),
        ("1.docx", ".docx"),
        ("1.doc", ".doc"),
        ("1.xlsx", ".xlsx"),
    ]

    for filename, ext in test_files:
        try:
            file_path = Path(filename)
            if not file_path.exists():
                print(f"Файл {filename} не найден, пропускаем...")
                continue

            file_bytes = file_path.read_bytes()
            text = extract_text_from_file(file_bytes, ext)
            print(f"\n--- Текст из {filename} ---\n{text}...")  # Выводим первые 500 символов
        except Exception as e:
            print(f"Ошибка при обработке {filename}: {e}")
#

import subprocess
from pathlib import Path

def convert_to_pdf(input_path: str) -> str:
    """
    Converts DOC/DOCX to PDF using LibreOffice.
    Returns path to the generated PDF.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir = input_path.parent  # Save PDF in the same folder as input

    subprocess.run([
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        str(input_path),
        "--outdir", str(output_dir)
    ])

    # Generated PDF path (e.g., "document.docx" → "document.pdf")
    pdf_path = output_dir / f"{input_path.stem}.pdf"
    return str(pdf_path) if pdf_path.exists() else None

# Example usage
pdf_file = convert_to_pdf("1.doc")
print(f"PDF generated at: {pdf_file}")