# src/nodes/VideoReaderNode.py
import cv2
from elements.FrameElement import FrameElement

class VideoReaderNode:
    def __init__(self, source: str):
        self.source = source
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {source}")
        self.frame_id = 0

    def read_frame(self) -> FrameElement:
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None  # источник исчерпан
        self.frame_id += 1
        # Создаем FrameElement с текущим временем (для реального времени можно использовать time.time())
        fe = FrameElement(frame=frame, frame_id=self.frame_id)
        return fe

    def release(self):
        if self.cap:
            self.cap.release()
