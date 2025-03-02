import torch
import cv2
import numpy as np
from config import CONFIDENCE_THRESHOLD, DEVICE
from logger import setup_logger

logger = setup_logger()

def load_yolov5(model_name='yolov5s'):
    """
    Загружает модель YOLOv5 через torch.hub
    """
    logger.info(f"Загрузка модели YOLOv5: {model_name}")
    model = torch.hub.load('ultralytics/yolov5', model_name, pretrained=True)
    model.conf = CONFIDENCE_THRESHOLD
    model.to(DEVICE)
    logger.info("Модель YOLOv5 загружена.")
    return model

def detect_people(frame, model):
    """
    Детекция людей (class_id=0).
    """
    results = model(frame)
    det_tensor = results.xyxy[0].cpu().numpy()
    detections = []
    for x1,y1,x2,y2,conf,cls_id in det_tensor:
        if conf >= CONFIDENCE_THRESHOLD and int(cls_id) == 0:
            detections.append([float(x1),float(y1),float(x2),float(y2),float(conf),0])
    return detections
