# src/nodes/DetectionNode.py
import cv2
import numpy as np
from openvino.runtime import Core

class DetectionNode:
    def __init__(self, model_path: str, conf_threshold: float = 0.3, nms_threshold: float = 0.4):
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        # Инициализация OpenVINO
        core = Core()
        self.model = core.compile_model(model_path, "CPU")  # компиляция модели для CPU
        # Получаем информацию о входах/выходах модели
        self.input_layer = self.model.input(0)
        self.output_layer = self.model.output(0)
        # Размер входного тензора (например, 640x640 для YOLO)
        self.input_shape = self.input_layer.shape  # [N,C,H,W]

        # Определяем индекс класса "person" (для COCO, предположим 0)
        self.person_class_id = 0

    def process(self, frame_element):
        frame = frame_element.frame
        # Подготовка кадра: масштабирование до размера модели и нормализация
        img = cv2.resize(frame, (self.input_shape[3], self.input_shape[2]))
        # Преобразование к формату [1,C,H,W]
        tensor = np.expand_dims(np.transpose(img, (2, 0, 1)), axis=0).astype(np.float32)
        # Выполняем инференс
        results = self.model([tensor])[self.output_layer]
        # Преобразуем выход модели в удобный вид
        detections = []
        # Предположим, что results имеет форму (1, N, 6) или (N,6): [x1,y1,x2,y2, conf, class_id]
        if results is None:
            frame_element.detections = []
            return frame_element
        output_data = results.squeeze()  # убираем размер batch
        # Если одна детекция, приводим к списку, иначе итерируем
        if output_data.ndim == 1:
            output_data = np.expand_dims(output_data, axis=0)
        for det in output_data:
            x1, y1, x2, y2, conf, cls = det.tolist()
            if conf < self.conf_threshold:
                continue
            cls = int(cls)
            if cls != self.person_class_id:
                continue  # игнорируем не-людей
            # Координаты могут быть уже в масштабе оригинала или относительные – 
            # если относительные, домножаем на размеры кадра:
            # (для простоты считаем, что уже абсолютные пиксели)
            detections.append([int(x1), int(y1), int(x2), int(y2), conf])
        # Применяем NMS, чтобы убрать пересекающиеся окна одной персоны
        bboxes = [d[:4] for d in detections]
        scores = [d[4] for d in detections]
        indices = cv2.dnn.NMSBoxes(bboxes, scores, self.conf_threshold, self.nms_threshold)
        final_dets = []
        if len(indices) > 0:
            for idx in indices:
                i = idx[0] if isinstance(idx, (tuple, list, np.ndarray)) else idx
                x1, y1, x2, y2, conf = detections[i]
                final_dets.append((x1, y1, x2, y2, conf))
        else:
            # если нет пересечений или одна детекция
            final_dets = [tuple(det) for det in detections]
        frame_element.detections = final_dets
        return frame_element
