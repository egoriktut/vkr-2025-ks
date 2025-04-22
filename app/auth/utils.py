import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from uuid import uuid4

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_token():
    """
    Генерация токена
    """
    return str(uuid4())


def generate_verification_code(length=4):
    return secrets.token_hex(length)[:length].upper()


def send_verification_email(email, code):
    """
    Отправка Email подтверждения
    """
    addr_from = "gorg52@bk.ru"
    # password = "A3y$teriARR7"
    password = "BbG55sm9ybHbkhHvALZr"
    msg = MIMEMultipart()
    msg["From"] = addr_from
    msg["To"] = email
    msg["Subject"] = (
        "Код подтверждения регистрации в системе мониторинга котировочных сессий"
    )
    html_body = " ".join(
        (
            "<html>",
            "  <head></head>",
            "    <body>",
            f"Проверочный код: <p> {code}</p>",
            "    </body>",
            "</html>",
        )
    )
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    server = smtplib.SMTP_SSL("smtp.mail.ru", 465)
    try:
        server.login(addr_from, password)
        server.send_message(msg)
        server.close()
        return True
    except Exception as e:
        server.close()
        print("Send email error:", str(e))
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля и его хеша.

    :param plain_password: Пароль в чистом виде (или клиентский хеш, если используется)
    :param hashed_password: Хеш пароля из базы данных
    :return: bool - Соответствует ли пароль хешу
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Генерирует хеш пароля для хранения в БД.

    :param password: Пароль в чистом виде (или клиентский хеш)
    :return: str - Хеш пароля
    """
    return pwd_context.hash(password)
