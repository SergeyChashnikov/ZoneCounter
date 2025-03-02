import os
import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Порог детекции YOLOv5
CONFIDENCE_THRESHOLD = 0.5

# Устройство для инференса
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Координаты зоны
ZONE_COORDS = (100, 100, 400, 400)

# Параметры для БД (SQLite, например)
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, '..', 'database.sqlite3')}"
SQLALCHEMY_ECHO = False

# Логи
LOG_DIR = os.path.join(BASE_DIR, '..', 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, 'zonecounter.log')

# Режим отладки
DEBUG = True
