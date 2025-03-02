# ZoneCounter

Проект ZoneCounter позволяет анализировать количество людей в заданной области (ROI) на видео или потоке с камеры, используя детекцию (YOLOv5), простой трекинг (на основе центроидов) и учёт времени нахождения в зоне. Предусмотрены:

- **Автосоздание** папок (database/ и models/), если их нет.  
- **Автозагрузка** весов модели YOLOv5 в models/yolov5s.pt, если локальный файл отсутствует.  
- **Сохранение данных** в БД (SQLite), позволяющее вести логирование обнаруженных треков.  
- **Два способа запуска**:
   1. **CLI** (через main.py).\
   2. **Flask** – API (api.py) и Web-интерфейс (app.py).\

---

## 1. Основные возможности

1. **Детекция людей**: Используется [ultralytics/YOLO](https://github.com/ultralytics/ultralytics), детектор класса person (ID = 0).  
2. **Трекинг**: Простой модуль на основе «centroid tracker», сопоставляющий детекции между кадрами по расстоянию центроидов.  
3. **Подсчёт времени в зоне**: Модуль `ZoneCounter` фиксирует вход/выход треков в зону (ROI) и суммарное время нахождения внутри.  
4. **Автоматическое создание папок**:  
   - **database/** (для `database.sqlite3`)  
   - **models/** (для локального `yolov5s.pt`)  
5. **Автоматическая загрузка** модели YOLOv5s: при первом запуске скачивает вес `yolov5s.pt`, сохраняет его в `models/` и далее использует локальную копию.  
6. **Сохранение логов в БД**: В таблице `detection_logs` хранится информация о каждом треке (track_id, total_time, is_inside).  
7. **Логирование** (в консоль и файл) для отладки и аудита.

---

## 2. Структура репозитория
ZoneCounter/\
├── README.md
├── requirements.txt
├── .gitignore
├── Dockerfile                      # (Опционально) для контейнеризации
├── database/                      # Автосоздаётся (для database.sqlite3)
├── models/                        # Автосоздаётся (для yolov5s.pt)
├── src/
│   ├── __init__.py
│   ├── config.py                  # Настройки (папки, пути к БД/модели, пороги)
│   ├── database.py                # Инициализация SQLAlchemy
│   ├── detection.py               # Логика детекции (YOLO)
│   ├── tracking.py                # Простой трекер
│   ├── zone_counter.py            # Учёт времени в зоне
│   ├── models.py                  # SQLAlchemy-модели
│   ├── logger.py                  # Настройка логирования
│   ├── main.py                    # CLI-сценарий
│   ├── api.py                     # Flask API (REST)
│   └── app.py                     # Flask Web (HTML-интерфейс)
├── templates/                     # HTML-шаблоны (для app.py)
│   ├── index.html
│   └── results.html
├── notebooks/                     # (Опционально) Демонстрационные Jupyter-ноутбуки
│   └── experiments.ipynb
├── tests/                         # Тесты (pytest)
│   ├── __init__.py
│   ├── test_detection.py
│   ├── test_zone_counter.py
│   ├── test_api.py
│   └── test_models.py
└── data/
    ├── images/
    └── videos/
    

### Ключевые файлы

1. **config.py**  
   - Пути к папкам `database/`, `models/`,  
   - Настройки `SQLALCHEMY_DATABASE_URI`,  
   - `MODEL_FILE` (yolov5s.pt),  
   - Порог уверенности (`CONFIDENCE_THRESHOLD`),  
   - Устройство (CPU/GPU),  
   - Координаты зоны (ROI).  

2. **database.py**  
   - Создаёт движок SQLAlchemy и фабрику сессий.  

3. **detection.py**  
   - Функция `load_yolov5()`: если `models/yolov5s.pt` нет, скачивает и сохраняет в папку models/.  
   - Функция `detect_people(...)`: выполняет инференс, возвращая bounding box’ы людей.  

4. **tracking.py**  
   - Простой «centroid tracker» для сопоставления детекций между кадрами.  

5. **zone_counter.py**  
   - Следит за входом/выходом каждого трека в заданную ROI и считает суммарное время.  

6. **models.py**  
   - SQLAlchemy-модель (например, `DetectionLog`) для хранения логов.  

7. **logger.py**  
   - Настраивает логирование в консоль и в файл (logs/zonecounter.log).  

8. **main.py**  
   - CLI-скрипт:  
     1) Создает таблицы БД,  
     2) Загружает модель (`load_yolov5()`),  
     3) Запускает чтение видео (или камеры), детекцию, трекинг, подсчёт времени.  

9. **api.py**  
   - Flask-приложение (REST API), принимает видео через POST, анализирует, возвращает JSON.  

10. **app.py**  
    - Flask Web-приложение (HTML), с формой загрузки видео, рендером страниц (templates/index.html и templates/results.html).  

11. **tests/**  
    - Юнит-тесты для каждого ключевого модуля (детектор, зона, API, модели).  

---

## 3. Установка и настройка

1. **Клонировать** репозиторий:
   ```bash
   git clone https://github.com/yourname/ZoneCounter.git
   cd ZoneCounter
