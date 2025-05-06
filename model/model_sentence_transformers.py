import numpy as np
from sentence_transformers import SentenceTransformer, util


class TransformerC:
    """Класс для работы с моделью SentenceTransformer"""

    def __init__(self):
        """Инициализация модели SentenceTransformer"""
        self.model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2", device="cpu"
        )

    def text_to_vector(self, text: str):
        """
        Преобразование текста в вектор.

        Args:
            text (str): Входной текст.

        Returns:
            torch.Tensor: Векторное представление текста.
        """
        return self.model.encode(text, convert_to_tensor=True)

    def get_vector(self, text: str):
        """
        Получение numpy-вектора без конвертации в Tensor.

        Args:
            text (str): Входной текст.

        Returns:
            np.ndarray: Векторное представление текста в формате numpy-массива.
        """
        return self.model.encode(text)

    @staticmethod
    def cost_similarity(first, second):
        """
        Вычисление косинусного сходства между двумя векторами.

        Args:
            first (torch.Tensor): Первый вектор.
            second (torch.Tensor): Второй вектор.

        Returns:
            float: Значение косинусного сходства от -1 до 1.
        """
        return util.cos_sim(first, second).item()

    def check_similarity_transformer(self, first: str, second: str):
        """
        Вычисление косинусного сходства между двумя строками.

        Args:
            first (str): Первая строка.
            second (str): Вторая строка.

        Returns:
            float: Значение косинусного сходства от -1 до 1.
        """
        interface_embedding = self.model.encode(first, convert_to_tensor=True)
        td_embedding = self.model.encode(second, convert_to_tensor=True)

        similarity_score = util.cos_sim(
            interface_embedding, td_embedding
        ).item()

        return similarity_score

    def check_similarity2_transformer(self, first: str, second: str):
        """
        Вычисление евклидова расстояния между двумя строками.

        Args:
            first (str): Первая строка.
            second (str): Вторая строка.

        Returns:
            float: Евклидово расстояние между двумя векторами.
        """
        interface_embedding = self.model.encode(first)
        td_embedding = self.model.encode(second)

        euclidean_distance = np.linalg.norm(interface_embedding - td_embedding)
        return float(euclidean_distance)
