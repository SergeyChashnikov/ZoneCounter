# src/nodes/TrackingNode.py
import numpy as np
from bytetracker import BYTETracker
from elements.TrackElement import TrackElement

class TrackingNode:
    def __init__(self, track_thresh: float = 0.5, track_buffer: int = 30, match_thresh: float = 0.8, frame_rate: int = 30):
        # Инициализация параметров ByteTrack
        args = {
            "track_thresh": track_thresh,       # порог детекции для начала трека
            "track_buffer": track_buffer,       # сколько кадров трек хранится без обновления
            "match_thresh": match_thresh,       # порог схожести для matching
            "mot20": False                     # если True, адаптирует параметры под MOT20Challenge
        }
        self.tracker = BYTETracker(args, frame_rate=frame_rate)

        # Будем хранить предыдущие активные ID, чтобы отслеживать исчезновения
        self.prev_track_ids = set()

    def process(self, frame_element):
        detections = frame_element.detections  # список (x1, y1, x2, y2, conf)
        # Формируем np.array для трекера: [x, y, w, h, score]
        dets_for_tracker = np.array([
            [x1, y1, x2 - x1, y2 - y1, conf] for (x1, y1, x2, y2, conf) in detections
        ], dtype=np.float32)
        # Обновляем трекер
        online_targets = self.tracker.update(dets_for_tracker, frame_id=frame_element.frame_id)
        current_tracks = []
        current_ids = set()
        for target in online_targets:
            tid = target.track_id
            tlwh = target.tlwh  # формат (x, y, w, h) последнего состояния трека
            tscore = target.score if hasattr(target, "score") else 1.0
            x, y, w, h = tlwh
            x1, y1, x2, y2 = int(x), int(y), int(x + w), int(y + h)
            # Создаем/обновляем TrackElement
            track_elem = TrackElement(track_id=tid, bbox=(x1, y1, x2, y2), score=tscore)
            current_tracks.append(track_elem)
            current_ids.add(tid)
        frame_element.tracks = current_tracks

        # Определим треки, которые исчезли на этом кадре (были в prev, нет в current)
        disappeared_ids = self.prev_track_ids - current_ids
        # Для простоты, можем обработать исчезнувшие в следующем узле (ZoneCountingNode),
        # где хранятся зоны. Здесь просто обновим prev_track_ids.
        self.prev_track_ids = current_ids.copy()
        frame_element.disappeared_ids = disappeared_ids  # передадим в следующий узел
        return frame_element
