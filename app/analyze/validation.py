import re
from datetime import datetime
from typing import Dict, List, Optional

import requests
from analyze.schemas import (
    FileSchema,
    KSAttributes,
    TwoTextsInput,
    ValidationOption,
    ValidationOptionResult,
)
from fuzzywuzzy import fuzz
from num2words import num2words


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

    def validate_content(self, page_data, validate_params: List[ValidationOption]):
        return {
            option: self.validation_checks[option](page_data)
            for option in validate_params
            if option in self.validation_checks
        }

    def validate_price(self, page_data: KSAttributes) -> ValidationOptionResult:
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
                if result:
                    return ValidationOptionResult(
                        status=True, description="Упоминание найдено"
                    )
                else:
                    continue
        return ValidationOptionResult(status=False, description="Упоминание не найдено")

    @staticmethod
    def validate_delivery_graphic(page_data: KSAttributes) -> ValidationOptionResult:
        result = []
        for delivery in page_data.deliveries:
            date_start_raw = delivery["periodDateFrom"]
            date_end_raw = delivery["periodDateTo"]
            day_start_raw = delivery["periodDaysFrom"]
            day_end_raw = delivery["periodDaysTo"]
            date_format = "%d.%m.%Y %H:%M:%S"
            duration = 0
            date_start, date_end = None, None
            date_found = False
            try:
                if isinstance(day_start_raw, int) and isinstance(day_end_raw, int):
                    duration = abs(day_end_raw - day_start_raw)

                if isinstance(date_start_raw, str) and isinstance(date_end_raw, str):
                    date_start = datetime.strptime(date_start_raw, date_format)
                    date_end = datetime.strptime(date_end_raw, date_format)
                    duration = abs((date_start - date_end).days)
            except Exception as error:
                print(error)
                return ValidationOptionResult(
                    status=False, description="Упоминание не найдено"
                )

            if date_start is None and date_end is None and duration == 0:
                return ValidationOptionResult(
                    status=False, description="Упоминание не найдено"
                )

            matched_dates = []
            for file_text in page_data.files_parsed:
                if date_start is not None and date_end is not None:
                    pattern = r"\b(\d{2})[-.](\d{2})[-.](\d{4})\b"
                    file_text = file_text
                    if not file_text:
                        continue
                    matches = re.findall(pattern, file_text)
                    matched_date = []
                    for match in matches:
                        day, month, year = match
                        try:
                            matched_date = datetime.strptime(
                                f"{day}.{month}.{year}", "%d.%m.%Y"
                            )
                            matched_dates.append(matched_date)
                        except ValueError:
                            pass
                    for matched_date in matched_dates:
                        if date_start <= matched_date <= date_end:
                            date_found = True
                            break
                for dur in range(max(1, duration - 1), duration + 2):
                    duration_pattern = (
                        rf"{dur}\s*(?:[^\s\d].{{0,40}})?\s*(дней|дня|день)"
                    )
                    duration_matches = re.findall(duration_pattern, file_text)
                    if duration_matches:
                        date_found = True
                        break
                duration_pattern = (
                    rf"{duration // 28}\s*(?:[^\s\d].{{0,40}})?\s*(дней|дня|день)"
                )
                duration_matches = re.findall(duration_pattern, file_text)
                if duration_matches:
                    date_found = True

                result.append(date_found)
        if all(result):
            return ValidationOptionResult(
                status=True, description="График поставки совпадает"
            )
        return ValidationOptionResult(
            status=False, description="График поставки не совпадает"
        )

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
                    return ValidationOptionResult(
                        status=False, description="Упоминание не найдено"
                    )
            return ValidationOptionResult(status=True, description="Упоминание найдено")

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
                    return ValidationOptionResult(
                        status=True, description="Упоминание найдено"
                    )
                return ValidationOptionResult(
                    status=False, description="Упоминание не найдено"
                )

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

            pairs_to_compare = TwoTextsInput(
                first=page_data.name, second=file_text[start_index:end_index]
            )

            similarity_score_fuzz = fuzz.partial_ratio(
                page_data.name.lower(), file_text[start_index:end_index].lower()
            )
            if similarity_score_fuzz > 70:
                return ValidationOptionResult(
                    status=True, description=f"{similarity_score_fuzz}%"
                )

            tf1_score = self.model_requests.check_similarity_transformer(
                pairs_to_compare
            )
            if tf1_score >= 0.75:
                return ValidationOptionResult(
                    status=True, description=f"{tf1_score:.1%}"
                )

            tf2_score = self.model_requests.check_similarity2_transformer(
                pairs_to_compare
            )
            if tf2_score <= 4:
                return ValidationOptionResult(
                    status=True, description=f"Отклонение {tf2_score}"
                )

            llama_verdict = self.model_requests.llama_prompt(pairs_to_compare)
            if llama_verdict:
                return ValidationOptionResult(status=True, description=f"LLM")

        return ValidationOptionResult(status=False, description="Упоминания не найдено")

    def validate_specifications(self, api_data: KSAttributes) -> ValidationOptionResult:
        validation_checks = []
        for file, file_text in zip(api_data.files, api_data.files_parsed):
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
            unique_items = list(aggregated_items.values())

            validated_items: List = []

            normalized_text = re.sub(r'[^a-zA-Zа-яА-Я0-9.,;:"\'\s-]', "", file_text)
            normalized_text = re.sub(r"\s+", " ", normalized_text)
            full_pdf_spec_str = normalized_text.strip()

            unique_items_str = " ".join(
                item for sublist in unique_items for item in sublist
            )
            normalized_text = re.sub(
                r'[^a-zA-Zа-яА-Я0-9.,;:"\'\s-]', "", unique_items_str
            )
            normalized_text = re.sub(r"\s+", " ", normalized_text)
            unique_items_str = normalized_text.strip()

            pairs_compare = TwoTextsInput(
                first=unique_items_str.lower(), second=full_pdf_spec_str.lower()
            )

            similarity_score = self.model_requests.check_similarity2_transformer(
                pairs_compare
            )

            validation_checks.append(len(validated_items) == len(unique_items))
            return ValidationOptionResult(
                status=similarity_score <= 5,
                description=f"Спецификация {'не ' if similarity_score > 5 else ''}совпадает",
            )
        return ValidationOptionResult(
            status=False, description="Спецификация не соответствует"
        )

    @staticmethod
    def validate_license(page_data: KSAttributes):
        license_text = page_data.isLicenseProduction
        if isinstance(license_text, bool):
            for file_text in page_data.files_parsed:
                if not file_text:
                    continue
                pattern1 = r"\s*лицензи\s*"
                pattern2 = r"\s*сертификат\s*"
                if re.search(pattern1, file_text) and re.search(pattern2, file_text):
                    ValidationOptionResult(
                        status=True, description="Найдены совпадения"
                    )
            return ValidationOptionResult(
                status=False, description="Совпадений не найдено"
            )

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
