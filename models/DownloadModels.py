from ultralytics import YOLO
import os, shutil

# 1) Загружаем предобученную модель YOLOv8n (скачается автоматически)
model8 = YOLO("yolov8n.pt")
print(f'\nModel yolov8n.pt downloaded\n')
# 2) Экспортируем в формат OpenVINO IR
model8.export(format="openvino")
print(f'\nModel yolov8n.pt exported to openvino\n')

# 3) Загружаем предобученную модель YOLOv5n
model5 = YOLO("yolov5n.pt")
print(f'\nModel yolov5n.pt downloaded\n')
# 4) Экспортируем в OpenVINO IR
model5.export(format="openvino")
print(f'\nModel yolov5n.pt exported to openvino\n')

# 5) Переносим в models/:

