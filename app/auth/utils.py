import json
import secrets
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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


def send_email(email, subject, html_content):
    addr_from = "gorg52@bk.ru"
    # password = "A3y$teriARR7"
    password = "BbG55sm9ybHbkhHvALZr"
    msg = MIMEMultipart()
    msg["From"] = addr_from
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html", "utf-8"))
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


def send_verification_email(email, code):
    """
    Отправка Email подтверждения
    """
    subject = "Код подтверждения регистрации в системе мониторинга котировочных сессий"
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
    send_email(email, subject, html_body)


def send_task_to_user_email(email, task):
    analysis_data = json.loads(task.result)
    subject = f"Результат анализа КС {task.url}"
    html_content = generate_html_report(task, analysis_data)
    send_email(email, subject, html_content)


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


def generate_html_report(task_data, analysis_data: dict) -> str:
    """Генерирует HTML отчет на основе данных задачи"""

    # Форматируем даты
    created_at = task_data.created_at
    completed_at = task_data.completed_at

    # Подсчитываем результаты анализа
    total_checks = len(analysis_data["analysis"])
    passed_checks = sum(
        1 for item in analysis_data["analysis"].values() if item["status"]
    )

    # Получаем названия критериев (замените на свои)
    criteria_names = {
        1: "Наименование закупки совпадает с наименованием в техническом задании и/или в проекте контракта",
        2: "Обеспечение исполнения контракта - требуется",
        3: "Наличие сертификатов/лицензий",
        4: "График поставки И этап поставки",
        5: "Максимальное значение цены контракта ИЛИ начальная цена",
        6: "Спецификации",
    }

    # Генерируем HTML
    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Отчет по проверке КС</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 8px 8px 0 0;
                text-align: center;
            }}
            .report-container {{
                background-color: white;
                border-radius: 0 0 8px 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
                margin-bottom: 20px;
            }}
            .task-info h2 {{
                color: #2c3e50;
                margin-top: 0;
            }}
            .task-url {{
                display: inline-block;
                background-color: #f0f7ff;
                color: #0066cc;
                padding: 8px 12px;
                border-radius: 4px;
                text-decoration: none;
                margin: 10px 0;
                word-break: break-all;
            }}
            .status-badge {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 12px;
                font-size: 0.9em;
                font-weight: bold;
                margin-left: 10px;
            }}
            .status-success {{
                background-color: #d4edda;
                color: #155724;
            }}
            .analysis-item {{
                display: flex;
                align-items: flex-start;
                margin-bottom: 12px;
                padding: 12px;
                border-radius: 6px;
                background-color: #f8f9fa;
            }}
            .icon {{
                margin-right: 10px;
                font-weight: bold;
                font-size: 1.2em;
            }}
            .icon-valid {{
                color: #28a745;
            }}
            .icon-invalid {{
                color: #dc3545;
            }}
            .criteria {{
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 5px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #6c757d;
                font-size: 0.9em;
            }}
            .timestamp {{
                color: #6c757d;
                font-size: 0.9em;
                margin-bottom: 15px;
            }}
            .summary {{
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
                font-weight: bold;
                text-align: center;
            }}
            .summary-valid {{
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Отчет по проверке конкурсной ситуации</h1>
        </div>

        <div class="report-container">
            <div class="task-info">
                <h2>{task_data.description} <span class="status-badge status-success">{task_data.status}</span></h2>
                <div class="timestamp">Дата проверки: {completed_at.strftime('%d.%m.%Y %H:%M:%S')}</div>
                <a href="{analysis_data['url']}" class="task-url" target="_blank">{analysis_data['url']}</a>

                <div class="summary {'summary-valid' if passed_checks > total_checks / 2 else 'summary-invalid'}">
                    {'✓' if passed_checks > total_checks / 2 else '✗'} Результат: {passed_checks} из {total_checks} критериев выполнено
                </div>
            </div>

            <div class="analysis-section">
                <h3>Детали анализа:</h3>
                {generate_analysis_items(analysis_data['analysis'], criteria_names)}
            </div>
        </div>

        <div class="footer">
            <p>Это письмо сформировано автоматически. Пожалуйста, не отвечайте на него.</p>
            <p>ID задачи: {task_data.id} | Дата создания: {created_at.strftime('%d.%m.%Y %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """


def generate_analysis_items(analysis: dict, criteria_names: dict) -> str:
    """Генерирует HTML для пунктов анализа"""
    items_html = ""
    for key, item in analysis.items():
        criteria_name = criteria_names.get(key, f"Критерий {key}")
        icon_class = "icon-valid" if item["status"] else "icon-invalid"
        icon = "✓" if item["status"] else "✗"

        items_html += f"""
        <div class="analysis-item">
            <div class="icon {icon_class}">{icon}</div>
            <div class="analysis-content">
                <div class="criteria">{criteria_name}</div>
                <div>{item['description']}</div>
            </div>
        </div>
        """
    return items_html
