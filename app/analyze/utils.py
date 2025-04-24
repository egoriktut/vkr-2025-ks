import subprocess
from typing import List, Optional, TypedDict

import camelot
import pandas as pd
import pdfplumber


class PageData(TypedDict, total=False):
    text: Optional[str]
    table: Optional[List[List[List[str]]]]
    inversed_text: Optional[str]
    inversed_table: Optional[List[List[List[str]]]]


pd.set_option("display.max_colwidth", None)

import os


def parse_pdf_tables(pdf_path):
    output_dir = os.path.join(os.path.dirname(pdf_path))
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, os.path.basename(pdf_path) + ".decrypt")

    tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
    # print("rel tables", len(tables), tables)
    horizontal_tables = []
    vertical_tables = []

    with open(output_file_path, "w") as answer:
        for i, table in enumerate(tables):
            df = table.df
            if df.shape[1] > df.shape[0]:
                horizontal_tables.append(df)
                answer.write(
                    df.to_string(index=False, header=False)
                    .replace("\n", " ")
                    .replace("  ", " ")
                    + "\n"
                )
            else:
                vertical_df = df.transpose()
                vertical_tables.append(vertical_df)
                answer.write(
                    vertical_df.to_string(index=False, header=False)
                    .replace("\n", " ")
                    .replace("  ", " ")
                    + "\n"
                )
    # print("horizontal_tables", horizontal_tables)
    # print("vertical_tables", vertical_tables)
    return tables


def read_plain_text(path: str) -> str:
    read_text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text().replace("\n", " ").strip()
            read_text += text
    return read_text


def doc_to_pdf(docpath) -> str:
    arr = docpath.split("/")
    dirname = "/".join(arr[:-1])
    filename = arr[-1].replace(".docx", ".pdf")
    filename = filename.replace(".doc", ".pdf")
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", docpath, "--outdir", dirname]
    )
    return dirname + "/" + filename


def read_file(path: str):
    if path.endswith(".doc") or path.endswith(".docx"):
        path_docx = path
        path = doc_to_pdf(path)
        # os.remove(path_docx)
    try:
        parsed_plaint_text = read_plain_text(path)
        tables = parse_pdf_tables(path)
        parsed_data = {}
        with open(path + ".decrypt", "r") as file:
            parsed_data = file.read()
        # os.remove(path + ".decrypt")
        return parsed_data, parsed_plaint_text, tables
    except Exception as e:
        return None, None, None
