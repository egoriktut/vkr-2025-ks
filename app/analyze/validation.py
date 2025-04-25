import os
import re
from datetime import datetime
from typing import Dict, List, Optional

import requests
from analyze.schemas import (FileSchema, KSAttributes, TwoTextsInput,
                             ValidationOption, ValidationOptionResult)
from analyze.utils import read_file
from fuzzywuzzy import fuzz
from num2words import num2words

DIR_NAME = "resources"
DIR_PATH = "./resources/_"
FILE_PATH = DIR_PATH + "{auction_id}_{file_name}"


class ModelRequest:
    def __init__(self, model_url: str) -> None:
        self.model_url = model_url

    def ping(self) -> Dict:
        return requests.get(self.model_url).json()

    def post_request(self, url_path: str, data: TwoTextsInput) -> Optional[str]:
        try:
            return requests.post(f"{self.model_url}/{url_path}", json=data).json()[
                "result"
            ]
        except (KeyError, TimeoutError) as error:
            print(error)
            return None

    def llama_prompt(self, data: TwoTextsInput) -> bool:
        result = self.post_request("llama_prompt", data.model_dump())
        return result.lower() == "yes"

    def check_similarity_transformer(self, data: TwoTextsInput) -> float:
        result = self.post_request("check_similarity_transformer", data.model_dump())
        return float(result) if result is not None else None

    def check_similarity2_transformer(self, data: TwoTextsInput) -> float:
        result = self.post_request("check_similarity2_transformer", data.model_dump())
        return float(result) if result is not None else None


class KSValidator:
    def __init__(self, model_url: Optional[str] = None) -> None:
        self.model_requests = ModelRequest(model_url)
        self.reference_col_name = {
            "name": ["Наименование", "Название"],
            "quantity": ["Кол.", "Кол-", "Кол-во", "Количество"],
            "date": ["сроки", "срок", "Дата"],
            "cost": ["Стоимость", "Цена", "Стоим"],
        }
        self.validation_checks = {
            ValidationOption.VALIDATE_NAMING: self.validate_naming,
            ValidationOption.VALIDATE_PERFORM_CONTRACT_REQUIRED: self.validate_perform_contract_required,
            ValidationOption.VALIDATE_LICENSE: self.validate_license,
            ValidationOption.VALIDATE_DELIVERY_GRAPHIC: self.validate_delivery_graphic,
            ValidationOption.VALIDATE_PRICE: self.validate_price,
            ValidationOption.VALIDATE_SPECIFICATIONS: self.validate_specifications,
        }
        self.page_data = None

    @staticmethod
    def download_file(download_link: str, file_name: str, auction_id: int) -> None:
        response = requests.get(download_link, stream=True)
        response.raise_for_status()

        os.makedirs(DIR_NAME, exist_ok=True)

        file_path = FILE_PATH.format(auction_id=auction_id, file_name=file_name)
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        print(f"written {file_name}")

    @staticmethod
    def parse_file_data(file_name: str, auction_id: int) -> str:
        file_path = FILE_PATH.format(auction_id=auction_id, file_name=file_name)
        file_text = read_file(file_path)
        return file_text

    def process_file(self, download_link, file_name, auction_id) -> str:
        self.download_file(download_link, file_name, auction_id)
        return self.parse_file_data(file_name, auction_id)

    def validate_content(
        self, page_data: KSAttributes, validate_params: List[ValidationOption]
    ) -> Dict[ValidationOption, ValidationOptionResult]:
        for file in page_data.files:
            page_data.files_parsed.append(
                self.process_file(
                    file["downloads_link"], file["name"], page_data.auction_id
                )
            )

        return {
            option: self.validation_checks[option](page_data)
            for option in validate_params
            if option in self.validation_checks
        }

    def validate_price(self, page_data: KSAttributes) -> ValidationOptionResult:
        print(page_data.startCost)
        print(page_data.contractCost)
        for file_text in page_data.files_parsed:
            if not file_text:
                continue
            pattern = r"\b(цена(?:ми|х|м|ми|у|ы|е|ой|ю)?|стоимость(?:ю|и|ям|ей|ями)?)\b"
            matches = [
                (match.start(), match.group())
                for match in re.finditer(pattern, file_text, flags=re.IGNORECASE)
            ]
            prompts = []
            for position, match in matches:
                start = max(0, position - 50)
                end = min(len(file_text) - 1, position + len(match) + 50)
                context_text = file_text[start:end]
                prompt = TwoTextsInput(
                    first=f"""
                        Initial Contract Price: {page_data.startCost}
                        Maximum Contract Price: {page_data.contractCost}
                        """,
                    second=context_text,
                )
                prompts.append(prompt)
            for prompt in prompts:
                result = self.model_requests.llama_prompt(prompt)
                print(prompt)
                print(result)
                if result:
                    return ValidationOptionResult(
                        status=True, description="Упоминание найдено"
                    )
                else:
                    continue
        return ValidationOptionResult(status=False, description="Упоминание не найдено")

    def validate_delivery_graphic(
        self, page_data: KSAttributes
    ) -> ValidationOptionResult:
        print(page_data.deliveries)
        print(page_data.files)
        print(len(page_data.files_parsed))
        result = []
        for delivery in page_data.deliveries:
            date_start_raw = delivery["periodDateFrom"]
            date_end_raw = delivery["periodDateTo"]
            day_start_raw = delivery["periodDaysFrom"]
            day_end_raw = delivery["periodDaysTo"]
            date_format = "%d.%m.%Y %H:%M:%S"
            duration = 0
            date_start, date_end = None, None
            print(date_end_raw, date_start_raw)
            print(day_start_raw, day_end_raw)
            date_found = False
            try:
                if isinstance(day_start_raw, int) and isinstance(day_end_raw, int):
                    duration = abs(day_end_raw - day_start_raw)

                if isinstance(date_start_raw, str) and isinstance(date_end_raw, str):
                    date_start = datetime.strptime(date_start_raw, date_format)
                    date_end = datetime.strptime(date_end_raw, date_format)
                    duration = abs((date_start - date_end).days)
            except:
                print("EXCEPTION")
                return ValidationOptionResult(
                    status=False, description="Упоминание не найдено"
                )

            if date_start is None and date_end is None and duration == 0:
                print("NO DATA")
                return ValidationOptionResult(
                    status=False, description="Упоминание не найдено"
                )

            matched_dates = []
            for file_text in page_data.files_parsed:
                if date_start is not None and date_end is not None:
                    print("DATE MATCHING")
                    pattern = r"\b(\d{2})[-.](\d{2})[-.](\d{4})\b"
                    file_text = file_text
                    if not file_text:
                        continue
                    matches = re.findall(pattern, file_text)
                    print("PATTTRNS")
                    print(matches)
                    matched_date = []
                    for match in matches:
                        day, month, year = match
                        try:
                            matched_date = datetime.strptime(
                                f"{day}.{month}.{year}", "%d.%m.%Y"
                            )
                            matched_dates.append(matched_date)
                        except ValueError:
                            pass  # Skip if the date is invalid
                    print("CHECK IN")
                    print(matched_date)
                    for matched_date in matched_dates:
                        if date_start <= matched_date <= date_end:
                            print("FOUND")
                            date_found = True
                            break
                print("DURATION 1")
                print(file_text)
                for dur in range(max(1, duration - 1), duration + 2):
                    print(dur)
                    duration_pattern = (
                        rf"{dur}\s*(?:[^\s\d].{{0,40}})?\s*(дней|дня|день)"
                    )
                    duration_matches = re.findall(duration_pattern, file_text)
                    print(duration_matches)
                    if duration_matches:
                        date_found = True
                        break
                print("DURATION 2")
                print(duration)
                duration_pattern = (
                    rf"{duration // 28}\s*(?:[^\s\d].{{0,40}})?\s*(дней|дня|день)"
                )
                duration_matches = re.findall(duration_pattern, file_text)
                print(duration_matches)
                if duration_matches:
                    date_found = True

                result.append(date_found)
        print(f"RESULSTSTSTS {result}")
        if all(result):
            return ValidationOptionResult(status=True, description="Упоминание найдено")
        return ValidationOptionResult(status=False, description="Упоминание не найдено")

    @staticmethod
    def number_to_words(number: float) -> str:
        rubles = int(number)
        kopecks = int((number - rubles) * 100)

        rubles_formatted = f"{rubles:,}".replace(",", " ")
        rubles_in_words = num2words(rubles, lang="ru").replace(" ", " ")
        kopecks_in_words = num2words(kopecks, lang="ru").replace(" ", " ")

        return f"{rubles_formatted} ({rubles_in_words}) рублей {kopecks:02d} ({kopecks_in_words}) копеек"

    def validate_perform_contract_required(
        self, page_data: KSAttributes
    ) -> ValidationOptionResult:
        if isinstance(page_data.isContractGuaranteeRequired, bool):
            for file_text in page_data.files_parsed:
                if file_text is None:
                    continue

                pattern = r"размер обеспечения исполнения Контракта составляет\s+\d+(?:\s\d+)*\sрублей\s\d{2}\sкопеек".lower()
                if re.search(pattern, file_text):
                    return ValidationOptionResult(status=False, description="")
            return ValidationOptionResult(status=True, description="")

        else:
            for file_text in page_data.files_parsed:
                if file_text is None:
                    continue
                expected_text = self.number_to_words(
                    page_data.isContractGuaranteeRequired
                )
                pattern = (
                    r"размер\s*обеспечения\s*исполнения\s*контракта\s*составляет\s*"
                    + re.escape(expected_text.lower())
                )
                if re.search(pattern, file_text):
                    return ValidationOptionResult(status=True, description="")
            return ValidationOptionResult(status=False, description="")

    def validate_naming(self, page_data: KSAttributes) -> ValidationOptionResult:
        for file_text in page_data.files_parsed:
            if not file_text:
                continue

            target_phrase_start = "ТЕХНИЧЕСКОЕ ЗАДАНИЕ"
            match_start = re.search(target_phrase_start, file_text[:250], re.IGNORECASE)
            start_index = 0
            if match_start:
                start_index = match_start.start() + len(target_phrase_start)

            target_phrase_end = "Общая информация об объекте закупки"
            match_end = re.search(target_phrase_end, file_text[:250], re.IGNORECASE)
            end_index = start_index + len(page_data.name) + 100
            if match_end:
                end_index = match_end.start()

            print(
                f"Start {start_index} end {end_index}\n"
                f"Name {page_data.name}\n"
                f"Text {file_text[start_index:end_index]}"
            )

            pairs_to_compare = TwoTextsInput(
                first=page_data.name, second=file_text[start_index:end_index]
            )

            similarity_score_fuzz = fuzz.partial_ratio(
                page_data.name.lower(), file_text[start_index:end_index].lower()
            )
            print(f"similarity_score_fuzz: {similarity_score_fuzz}")
            if similarity_score_fuzz > 70:
                return ValidationOptionResult(
                    status=True, description=f"{similarity_score_fuzz}%"
                )

            tf1_score = self.model_requests.check_similarity_transformer(
                pairs_to_compare
            )
            print(f"check_similarity_transformer: {tf1_score}")
            if tf1_score >= 0.75:
                return ValidationOptionResult(
                    status=True, description=f"{tf1_score:.1%}"
                )

            tf2_score = self.model_requests.check_similarity2_transformer(
                pairs_to_compare
            )
            print(f"check_similarity2_transformer: {tf2_score}")
            if tf2_score <= 4:
                return ValidationOptionResult(
                    status=True, description=f"Отклонение {tf2_score}"
                )

            llama_verdict = self.model_requests.llama_prompt(pairs_to_compare)
            print(f"llama_prompt: {llama_verdict}")
            if llama_verdict:
                return ValidationOptionResult(status=True, description=f"LLM")

        return ValidationOptionResult(status=False, description="Упоминания не найдено")

    def validate_specifications(self, api_data: KSAttributes) -> ValidationOptionResult:
        validation_checks = []
        for file, file_text in zip(api_data.files, api_data.files_parsed):
            print(file["name"].lower())
            if not (
                "тз" in file["name"].lower()
                or "т3" in file["name"].lower()
                or (
                    "техническое" in file["name"].lower()
                    and "задание" in file["name"].lower()
                )
            ):
                continue

            deliveries = api_data.deliveries
            from collections import defaultdict

            aggregated_items = defaultdict(
                lambda: {"sum": 0.0, "quantity": 0.0, "costPerUnit": 0.0, "name": ""}
            )

            for delivery in deliveries:
                for item in delivery.get("items", []):
                    name = item["name"]

                    aggregated_items[name]["name"] = name
                    aggregated_items[name]["sum"] += item["sum"]
                    aggregated_items[name]["quantity"] += item["quantity"]
                    aggregated_items[name]["costPerUnit"] = item["costPerUnit"]
            print("AGGREEGATED")
            print(aggregated_items)
            unique_items = list(aggregated_items.values())

            for item in unique_items:
                print(item)

            # tables = file["pandas_tables"]
            # print("tablee", tables)
            validated_items: List = []
            #
            # pdf_spec_items = self.get_pdf_spec_items(tables)
            # full_pdf_spec_str = " ".join(
            #     item for sublist in pdf_spec_items for item in sublist
            # )
            normalized_text = re.sub(r'[^a-zA-Zа-яА-Я0-9.,;:"\'\s-]', "", file_text)
            normalized_text = re.sub(r"\s+", " ", normalized_text)
            full_pdf_spec_str = normalized_text.strip()
            # print(full_pdf_spec_str)

            unique_items_str = " ".join(
                item for sublist in unique_items for item in sublist
            )
            normalized_text = re.sub(
                r'[^a-zA-Zа-яА-Я0-9.,;:"\'\s-]', "", unique_items_str
            )
            normalized_text = re.sub(r"\s+", " ", normalized_text)
            unique_items_str = normalized_text.strip()

            print(unique_items_str)
            print(full_pdf_spec_str)

            pairs_compare = TwoTextsInput(
                first=unique_items_str.lower(), second=full_pdf_spec_str.lower()
            )

            similarity_score = self.model_requests.check_similarity2_transformer(
                pairs_compare
            )
            print(f"res sim {similarity_score}")

            validation_checks.append(len(validated_items) == len(unique_items))
            return ValidationOptionResult(status=similarity_score <= 5, description="")
        return ValidationOptionResult(status=False, description="нет ТЗ")

    def checkSpecDate(self, pdf_date: str, api_date: str) -> bool:
        if pdf_date is None or api_date is None:
            return False
        return api_date in pdf_date

    def checkSpecCost(self, pdf_cost: str, api_cost: str) -> bool:
        if pdf_cost is None or api_cost is None:
            return False
        return pdf_cost == api_cost

    def checkSpecEquantity(self, pdf_eq: str, api_eq: str) -> bool:
        if pdf_eq is None or api_eq is None:
            return False
        return pdf_eq == api_eq

    # map columns name to col id
    @staticmethod
    def map_pdf_columns(column_name_map, pdf_columns):
        mapped_columns = {}
        # for std_name, alternatives in column_name_map.items():
        #     found_mapping = False
        #     i = 0
        #     for pdf_col in pdf_columns:
        #         if found_mapping:
        #             break
        #         for alt in alternatives:
        #             if alt.lower() in pdf_col.lower():
        #                 mapped_columns[std_name] = i
        #                 found_mapping = True
        #         i += 1
        # if len(mapped_columns) < 3:
        #     return None
        return mapped_columns

    @staticmethod
    def is_mappable_pdf_columns(column_name_map, pdf_columns):
        mapped_columns = {}
        # for std_name, alternatives in column_name_map.items():
        #     found_mapping = False
        #     i = 0
        #     for pdf_col in pdf_columns:
        #         if found_mapping:
        #             break
        #         for alt in alternatives:
        #             if alt.lower() in pdf_col.lower():
        #                 mapped_columns[std_name] = i
        #                 found_mapping = True
        #         i += 1
        # if len(mapped_columns) < 3:
        #     return False
        return True

    @staticmethod
    def is_start_id(column_name_map, pdf_columns):
        mapped_columns = {}
        for std_name, alternatives in column_name_map.items():
            found_mapping = False
            i = 0
            for pdf_col in pdf_columns:
                if found_mapping:
                    break
                for alt in alternatives:
                    if alt.lower() in pdf_col.lower():
                        mapped_columns[std_name] = i
                        found_mapping = True
                i += 1
        if len(mapped_columns) < 2:
            return False
        return True

    def find_start_id(self, df):
        for i in range(df.shape[0]):
            if self.is_start_id(self.reference_col_name, list(df.iloc[i])):
                return i
        return -1

    def get_pdf_spec_items(self, tables):
        if tables is None:
            print("NULL PAGES")
        return []

        # all_doc_specs = []
        # start_id = None
        # prev_item_id = None
        # table_wid = 0
        # # try:
        # for table in tables:
        #     df = table.df
        #     specs = ["" for i in range(table_wid)]
        #
        #     if (
        #         start_id is None
        #         and df.shape[1] > 4
        #         or start_id is not None
        #         and df.shape[1] >= table_wid
        #     ) and not df.isnull().any().any():
        #         print("READING TABLE")
        #         for i in range(df.shape[0]):
        #             print(list(df.iloc[i]))
        #             if prev_item_id == None:
        #                 sid = self.find_start_id(df)
        #                 if sid > -1:
        #                     prev_item_id = 0
        #
        #                     specs = list(df.iloc[prev_item_id])
        #                     table_wid = len(specs)
        #                     all_doc_specs.append(["" for i in range(table_wid)])
        #
        #                     print(
        #                         "POBEDA READ ALL FILE TO END",
        #                         specs,
        #                         table_wid,
        #                         prev_item_id,
        #                     )
        #
        #             else:
        #                 # ширина равна шир табл
        #                 if table_wid == len(list(df.iloc[i])):
        #                     if (
        #                         list(df.iloc[i])[0] != ""
        #                         and list(df.iloc[i])[0].isdigit()
        #                     ):
        #                         try:
        #                             print(
        #                                 "wanna new prev id [", list(df.iloc[i])[0], "]"
        #                             )
        #                             prev_item_id = int(list(df.iloc[i])[0]) - 1
        #                             for i in range(
        #                                 len(all_doc_specs), prev_item_id + 1
        #                             ):
        #                                 all_doc_specs.append(
        #                                     ["" for i in range(table_wid)]
        #                                 )
        #
        #                         except:
        #                             print("error parsing table col 0 for item id")
        #                             # print("wanna new prev id [", list(df.iloc(i))[0], "]")
        #                             # print(df.iloc(i))
        #                     for col_id in range(table_wid):
        #                         all_doc_specs[prev_item_id][col_id] += (
        #                             " " + list(df.iloc[i])[col_id]
        #                         )
        #     if len(specs) == table_wid and specs != ["" for i in range(table_wid)]:
        #         all_doc_specs.append(specs)

        # return all_doc_specs
        # except:
        #     return []

    # @staticmethod
    # def check_specification_name_equality(pdf_text: str, api_text: str) -> bool:
    #     similarity_score = fuzz.partial_ratio(pdf_text.lower(), api_text.lower())
    #     inversed_similarity_score = fuzz.partial_ratio(
    #         pdf_text.lower(), api_text.lower()
    #     )
    #     print(
    #         pdf_text,
    #         api_text,
    #         "similarity",
    #         similarity_score,
    #         inversed_similarity_score,
    #     )
    #     return similarity_score > 80 or inversed_similarity_score > 80

    def validate_license(self, page_data: KSAttributes):
        license_text = page_data.isLicenseProduction
        print(license_text)
        if isinstance(license_text, bool):
            for file_text in page_data.files_parsed:
                if not file_text:
                    continue
                pattern1 = r"\s*лицензи\s*"
                pattern2 = r"\s*сертификат\s*"
                if re.search(pattern1, file_text) and re.search(pattern2, file_text):
                    ValidationOptionResult(
                        status=False, description="Найдены совпадения"
                    )
            return ValidationOptionResult(status=True, description="не найдено")

        else:
            max_similarity = 0
            for file_text in page_data.files_parsed:
                if not file_text:
                    continue
                licenses_indices = [
                    i.start() for i in re.finditer("лицензи", file_text)
                ]
                certificate_indices = [
                    i.start() for i in re.finditer("сертификат", file_text)
                ]
                for index in licenses_indices + certificate_indices:
                    start_index = max(0, index - 5)
                    end_index = min(len(file_text), index + len(license_text) - 5)
                    substring = file_text[start_index:end_index]
                    similarity_score = fuzz.partial_ratio(
                        license_text.lower(), substring.lower()
                    )
                    max_similarity = max(max_similarity, similarity_score)
                    if similarity_score > 80:
                        return ValidationOptionResult(
                            status=True, description=f"{max_similarity}%"
                        )
            return ValidationOptionResult(
                status=False, description=f"{max_similarity}%"
            )
