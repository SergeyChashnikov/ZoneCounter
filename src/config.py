import os
import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1) Папки для базы данных и модели
DATABASE_DIR = os.path.join(BASE_DIR, "..", "database")
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")

# Автоматическое создание папок, если их нет
os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# 2) Путь к файлу базы данных
DB_PATH = os.path.join(DATABASE_DIR, "database.sqlite3")

# 3) Формируем строку подключения для SQLAlchemy (SQLite)
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
SQLALCHEMY_ECHO = False  # Если нужно выводить SQL-запросы в консоль

# 4) Путь к весам модели (например, yolov5s.pt)
MODEL_FILE = os.path.join(MODELS_DIR, "yolov5s.pt")

# Порог детекции YOLOv5
CONFIDENCE_THRESHOLD = 0.5

# Устройство для инференса
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Координаты зоны
ZONE_COORDS = (761, 9, 1141, 352)

# Логи
LOG_DIR = os.path.join(BASE_DIR, '..', 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, 'zonecounter.log')

# Режим отладки
DEBUG = True
