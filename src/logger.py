import logging
from config import LOG_FILE

def setup_logger():
    """
    Настраивает логирование в файл и на консоль.
    Возвращает объект логгера.
    """
    logger = logging.getLogger("ZoneCounter")
    logger.setLevel(logging.DEBUG)  # уровень логирования

    # Формат сообщений
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # Хендлер для файла
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Хендлер для консоли
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
