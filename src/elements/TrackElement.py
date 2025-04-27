# src/elements/TrackElement.py
import time

class TrackElement:
    def __init__(self, track_id: int, bbox: tuple, score: float):
        """
        bbox: кортеж (x1, y1, x2, y2) текущего расположения объекта
        """
        self.id = track_id
        self.bbox = bbox  # текущие координаты bounding box
        self.score = score  # уверенность детекции, с которой этот объект был обнаружен
        self.last_seen = time.time()
        self.in_zone: str = None             # ID зоны, в которой объект сейчас находится (или None)
        self.zone_entry_time: dict = {}      # {zone_id: entry_timestamp} время входа в каждую зону (если внутри)
        self.time_in_zone: dict = {}         # {zone_id: total_time_seconds} суммарно проведённое время в зоне
