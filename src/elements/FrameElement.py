# src/elements/FrameElement.py
import numpy as np
import time

class FrameElement:
    def __init__(self, frame: np.ndarray, frame_id: int = 0, timestamp: float = None):
        self.frame: np.ndarray = frame         # Изображение кадра (BGR, OpenCV)
        self.frame_id: int = frame_id          # Номер кадра в потоке
        self.timestamp: float = timestamp if timestamp is not None else time.time()
        self.detections: list = []            # Детекции людей: список кортежей (x1,y1,x2,y2, conf)
        self.tracks: list = []                # Отслеживаемые объекты: список TrackElement
        self.zone_counts: dict = {}           # Счетчики людей по зонам (id зоны -> количество)
        self.fps: float = 0.0                 # Текущая оценка FPS обработки (кадр/с)
