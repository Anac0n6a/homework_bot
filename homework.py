import logging
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
import telegram

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

logging.basicConfig(
    level=logging.DEBUG,
    filename="main.py",
    format="%(asctime)s, %(levelname)s, %(message)s, %(name)s",
)


def send_message(bot, message):
    """Отправка сообщений через бот Телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(
            f'Сообщение в телеграмм отправленно: {message}'
        )
    except Exception as error:
        logging.error(f"Ошибка при подключении к API Telegram: {error}")


def get_api_answer(timestamp):
    """Функция обращения к API Практикум."""
    timestamp = int(time.time())
    params = {"from_date": timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        content = response.json()
    except requests.exceptions.RequestException as request_error:
        logging.error(f'Код ответа не OK: {request_error}')
        raise exceptions.RequestError(f'Код ответа не OK: {request_error}')
    if response.status_code == HTTPStatus.OK:
        return content
    else:
        raise exceptions.InvalidHttp("Ошибка API Яндекс.Практикума")


def check_response(response):
    """Прверка ответа API Яндекс.Практикума."""
    try:
        timestamp = response["current_date"]
    except KeyError:
        logging.error("Ключ homeworks в Яндекс.Практикуме отсутсвует")
    try:
        homeworks = response["homeworks"]
    except KeyError:
        logging.error("Ключ homeworks в Яндекс.Практикуме отсутсвует")

    if isinstance(timestamp, int) and isinstance(homeworks, list):
        return homeworks
    else:
        raise TypeError


def parse_status(homework):
    """Проверка статуса ДЗ."""
    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")
    if homework_status is None:
        raise exceptions.HomeworkStatus(
            'Ошибка, пустое значение status: ', homework_status
        )
    if homework_name is None:
        raise exceptions.HomeworkName(
            'Ошибка, пустое значение в homework_name: ', homework_name
        )
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS.get(homework_status)
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        raise exceptions.HomeworkStatusIsNone(
            'Ошибка, отсутсвует статус ДЗ'
        )


def check_tokens():
    """Функция проверка токена и id чата."""
    tokens = {
        "practicum_token": PRACTICUM_TOKEN,
        "telegram_token": TELEGRAM_TOKEN,
        "telegram_id": TELEGRAM_CHAT_ID,
    }
    for key, value in tokens.items():
        if value is None:
            logging.critical(f"{key}, Отсутсвует")
            return False
    return True


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        timestamp = int(time.time())

        while True:
            try:
                response = get_api_answer(timestamp)
                homeworks = check_response(response)
                count_works = len(homeworks)
                while count_works > 0:
                    message = parse_status(homeworks[count_works - 1])
                    send_message(bot, message)
                    count_works -= 1
                timestamp = int(time.time())
                time.sleep(RETRY_PERIOD)

            except Exception as error:
                message = f"Сбой в работе программы: {error}"
                send_message(bot, message)
                time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
