# src/main.py
import os
import time
import json

from nodes.VideoReaderNode import VideoReaderNode
from nodes.DetectionNode import DetectionNode
from nodes.TrackingNode import TrackingNode
from nodes.ZoneCountingNode import ZoneCountingNode
from nodes.DataWriterNode import DataWriterNode
from nodes.ShowNode import ShowNode
from nodes.VideoSaverNode import VideoSaverNode
from nodes.FlaskServerVideoNode import FlaskServerVideoNode

# === Чтение настроек ===
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "test_videos/sample.mp4")
MODEL_TYPE = os.getenv("MODEL", "YOLOv8n")
if MODEL_TYPE == "YOLOv5n":
    MODEL_PATH = os.getenv("MODEL_PATH", "models/yolov5nu_openvino_model/yolov5nu.xml")
else:
    MODEL_PATH = os.getenv("MODEL_PATH", "models/yolov8n_openvino_model/yolov8n.xml")
CONF_THRESH = float(os.getenv("CONF_THRESH", 0.3))
NMS_THRESH = float(os.getenv("NMS_THRESH", 0.4))
ZONES_FILE = os.getenv("ZONES_FILE", "configs/zones_sample.json")
SAVE_VIDEO = os.getenv("SAVE_VIDEO", "True").lower() in ("true", "1", "yes")
OUTPUT_VIDEO = os.getenv("OUTPUT_VIDEO", "output.mp4")
INFLUX_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "PeopleCounterOrg")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "people_counter")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN", "5O-KBS5XW2gXO2gl1i906zwN35Bay0dMXHK580tGFHNQoohQcg5u9IQv3PyQ9RThTHLUlYIvH5FP18qH1VVG2g==")
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# Загружаем конфигурацию зон из файла
with open(ZONES_FILE, 'r') as f:
    zones_config = json.load(f).get("zones", [])

# === Инициализация узлов ===
reader = VideoReaderNode(VIDEO_SOURCE)
detector = DetectionNode(MODEL_PATH, conf_threshold=CONF_THRESH, nms_threshold=NMS_THRESH)
tracker = TrackingNode(frame_rate=30)   # frame_rate можно задать реальный или fps видео
zone_counter = ZoneCountingNode(zones_config=zones_config)
data_writer = DataWriterNode(influx_url=INFLUX_URL, influx_org=INFLUX_ORG, influx_bucket=INFLUX_BUCKET, influx_token=INFLUX_TOKEN)
shower = ShowNode()
# Передаем зоны в ShowNode для отрисовки (чтобы он знал координаты и названия)
shower.zones = zone_counter.zones  
video_saver = None
if SAVE_VIDEO:
    # Нужно знать размер кадра; считаем что reader.cap доступен:
    frame_width = int(reader.cap.get(3))
    frame_height = int(reader.cap.get(4))
    fps = reader.cap.get(5) if reader.cap.get(5) > 0 else 30.0
    video_saver = VideoSaverNode(output_path=OUTPUT_VIDEO, frame_size=(frame_width, frame_height), fps=fps)
# Запуск Flask сервера
flask_server = FlaskServerVideoNode(host=FLASK_HOST, port=FLASK_PORT)

# === Цикл обработки кадров ===
prev_time = time.time()
fps_smoothed = 0.0
while True:
    frame_element = reader.read_frame()
    if frame_element is None:  # конец видео
        break
    # Детекция
    frame_element = detector.process(frame_element)
    # Трекинг
    frame_element = tracker.process(frame_element)
    # Подсчет по зонам
    frame_element = zone_counter.process(frame_element)
    # FPS вычисляем (берем текущее время и предыдущую метку времени)
    current_time = time.time()
    elapsed = current_time - prev_time
    prev_time = current_time
    instant_fps = 1.0 / elapsed if elapsed > 0 else 0.0
    # немного сглаживаем FPS для отображения
    fps_smoothed = fps_smoothed * 0.9 + instant_fps * 0.1
    frame_element.fps = fps_smoothed
    frame_element.timestamp = current_time

    # Отправка данных в InfluxDB
    frame_element = data_writer.process(frame_element)
    # Визуализация на кадре
    frame_element = shower.process(frame_element)
    # Вывод в веб-интерфейс
    frame_element = flask_server.process(frame_element)
    # Запись в видеофайл (если включена)
    if video_saver:
        frame_element = video_saver.process(frame_element)

# Выход из цикла – освобождаем ресурсы
reader.release()
if video_saver:
    video_saver.release()
print("Processing finished. Exiting.")
