import json

import requests

from config import settings

PROMPT_TEMPLATE_COMPARE = """
You will compare the meaning of two texts.

Answer strictly with one word: "yes" if the meanings are similar, or "no" if they are different. Do not explain or add anything else.

First text: "{text1}"
Second text: "{text2}"
"""


class LLAMA:
    """
    Класс для взаимодействия с языковой моделью LLaMA через библиотеку ctransformers.
    """

    def __init__(self):
        """
        Инициализация модели LLAMA.
        """
        self.model_url = settings.LLAMA_URL
        self.payload = {
            "model": "llama3",
            "prompt": PROMPT_TEMPLATE_COMPARE,
            "stream": False,
        }
        self.headers = {
            "Content-Type": "application/json",
        }

    def llama_prompt_compare(self, first: str, second: str) -> bool:
        """
        Отправка запроса к LLM для распознавания схожести текста

        Args:
            first (str): Первая строка для сравнения
            second (str): Вторая строка для сравнения

        Returns:
            bool: сходятся ли строки по смыслу
        """
        self.payload["prompt"] = PROMPT_TEMPLATE_COMPARE.format(
            text1=first, text2=second
        )
        response = requests.post(
            self.model_url, headers=self.headers, data=json.dumps(self.payload)
        )
        result = response.json()
        return result["response"]
