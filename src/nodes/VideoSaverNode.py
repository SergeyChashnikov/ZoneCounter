# src/nodes/VideoSaverNode.py
import cv2

class VideoSaverNode:
    def __init__(self, output_path: str, frame_size: tuple, fps: float):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(output_path, fourcc, fps, frame_size)

    def process(self, frame_element):
        frame = frame_element.frame
        self.writer.write(frame)
        return frame_element

    def release(self):
        if self.writer:
            self.writer.release()
