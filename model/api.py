from fastapi import APIRouter

from model_llama import LLAMA
from model_sentence_transformers import TransformerC
from schemas import TwoTextsInput

router = APIRouter()

model_llama = LLAMA()
model_transformer = TransformerC()


@router.get("/")
async def ping():
    """Проверка подключения сервиса моделей."""
    return {"message": "Model api service successfully connected"}


@router.post("/llama_prompt")
async def llama_prompt(data: TwoTextsInput):
    """Отправка промпта в модель Llama и получение ответа о схожести строк"""
    result = model_llama.llama_prompt_compare(data.first, data.second)
    return {"result": result}


@router.post("/check_similarity_transformer")
async def check_similarity_transformer(data: TwoTextsInput):
    """Расчет косинусного сходства между двумя текстами с помощью Sentence Transformers."""
    similarity = model_transformer.check_similarity_transformer(data.first, data.second)
    return {"result": similarity}


@router.post("/check_similarity2_transformer")
async def check_similarity2_transformer(data: TwoTextsInput):
    """Расчет евклидова расстояния между векторами текстов с помощью Sentence Transformers."""
    similarity = model_transformer.check_similarity2_transformer(
        data.first, data.second
    )
    return {"result": similarity}
