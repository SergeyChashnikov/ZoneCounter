from flask import Flask, request, jsonify
import cv2
import tempfile
from detection import load_yolov5, detect_people
from tracking import SimpleCentroidTracker
from zone_counter import ZoneCounter
from database import SessionLocal, engine
from models import Base, DetectionLog
from logger import setup_logger

logger = setup_logger()

app = Flask(__name__)

# Создаем таблицы в БД при старте
Base.metadata.create_all(bind=engine)

model = load_yolov5('yolov5s')
tracker = SimpleCentroidTracker()
zc = ZoneCounter()

@app.route('/')
def home():
    return "ZoneCounter REST API работает!"

@app.route('/detect', methods=['POST'])
def detect():
    """
    Принимает multipart/form-data с ключом 'file' (видео).
    Выполняет детекцию и трекинг, обновляет счетчик, сохраняет в БД.
    Возвращает JSON с результатами.
    """
    if 'file' not in request.files:
        return jsonify({"error":"No file in request"}),400
    file=request.files['file']
    if file.filename=='':
        return jsonify({"error":"Empty filename"}),400

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file.save(tmp.name)
        video_path=tmp.name

    cap=cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return jsonify({"error":"Cannot open video"}),400

    db=SessionLocal()
    while True:
        ret,frame=cap.read()
        if not ret:
            break
        detections=detect_people(frame,model)
        tracks=tracker.update(detections)
        zc.update(tracks)

        # Простейший пример сохранения в БД
        stats=zc.get_stats()
        for tid,info in stats['details'].items():
            log_entry=DetectionLog(track_id=tid,
                                   total_time=info['total_time'],
                                   is_inside=info['is_inside'])
            db.add(log_entry)
        db.commit()

    cap.release()
    db.close()
    stats=zc.get_stats()
    return jsonify({
        "message":"OK",
        "unique_count":stats['unique_count'],
        "details":stats['details']
    }),200

if __name__=="__main__":
    app.run(debug=True,port=5000)
