import torch
import cv2
from ultralytics import YOLO
import numpy as np
import os
from config import MODELS_DIR, CONFIDENCE_THRESHOLD, DEVICE, MODEL_FILE
from logger import setup_logger

logger = setup_logger()

def load_yolov5():
    """
    Загружает модель YOLOv5:
      - Если локальный файл MODEL_FILE (models/yolov5s.pt) уже существует, 
        просто подгружаем его.
      - Если нет, то переходим в папку models/ (MODELS_DIR) и 
        создаём модель YOLO('yolov5s.pt').
        ultralytics автоматически скачает вес, если он не найден в кэше,
        и сохранит в папку models/.
      - Далее сохраняем итоговую модель ещё раз в MODEL_FILE (для надёжности).
      - Возвращаем объект модели, переведённый на устройство (CPU/GPU).
    """

    if os.path.exists(MODEL_FILE):
        # Файл модели уже лежит в models/, просто загружаем
        logger.info(f"Локальный файл модели найден: {MODEL_FILE}")
        model = YOLO(MODEL_FILE)
    else:
        logger.info(f"Локальный файл модели НЕ найден. Пытаемся скачать в {MODELS_DIR}...")

        # Сохраняем текущую директорию, чтобы потом вернуться
        original_dir = os.getcwd()

        try:
            # Переходим в папку models/
            os.chdir(MODELS_DIR)
            logger.info(f"Текущая директория изменена на {os.getcwd()}")

            # Это вызов, который скачает yolov5s.pt, если не найдено в локальном кэше ultralytics
            # В результате скачанный файл появится именно в папке models/
            model = YOLO('yolov5s.pt')

            # При желании ещё раз явно сохраняем модель в MODEL_FILE
            logger.info(f"Сохраняем модель в {MODEL_FILE}")
            model.save(MODEL_FILE)

        finally:
            # Возвращаемся в исходную директорию в любом случае
            os.chdir(original_dir)

    # Переводим модель на нужное устройство
    model.to(DEVICE)
    return model

def detect_people(frame, model):
    """
    Детекция людей (class_id=0).
    Возвращает список:
      [x1, y1, x2, y2, confidence, class_id=0]
    """
    results = model.predict(source=frame, conf=CONFIDENCE_THRESHOLD)
    detections = []
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        x1,y1,x2,y2 = box.xyxy[0].tolist()
        # Фильтруем класс 'person' (0)
        if cls_id == 0 and conf >= CONFIDENCE_THRESHOLD:
            detections.append([x1, y1, x2, y2, conf, 0])
    return detections
