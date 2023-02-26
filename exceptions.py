class HomeworkStatus(Exception):
    """Проверка ключа status в homework."""

    pass


class HomeworkName(Exception):
    """Проверка ключа homework_name."""

    pass


class HomeworkStatusIsNone(Exception):
    """Неизвестный статус проверки ДЗ."""

    pass


class InvalidHttp(Exception):
    """Проверка статуса Http."""

    pass


class RequestError(Exception):
    """Проверка ошибки RequestError."""

    pass


class NoDictCurrentDate(Exception):
    """Проверка что в curent_date передан словарь."""

    pass
