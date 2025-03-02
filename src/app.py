from flask import Flask, render_template, request, redirect, url_for
import os
import cv2
import tempfile

from detection import load_yolov5, detect_people
from tracking import SimpleCentroidTracker
from zone_counter import ZoneCounter
from database import SessionLocal, engine
from models import Base, DetectionLog, VideoLog
from logger import setup_logger

logger=setup_logger()

app=Flask(__name__)
Base.metadata.create_all(bind=engine)

model = load_yolov5('yolov5s')
tracker=SimpleCentroidTracker()
zc=ZoneCounter()

@app.route("/")
def index():
    # Отобразим простую страницу с формой загрузки видео
    return render_template("index.html")

@app.route("/upload",methods=["POST"])
def upload():
    """
    Принимает видеофайл из формы (HTML), сохраняет, обрабатывает, 
    и возвращает результаты
    """
    file=request.files.get("video_file",None)
    if not file or file.filename=="":
        return "Файл не выбран",400

    with tempfile.NamedTemporaryFile(delete=False,suffix=".mp4") as tmp:
        file.save(tmp.name)
        video_path=tmp.name

    # Записываем информацию о видео в БД
    db=SessionLocal()
    video_log=VideoLog(filepath=video_path)
    db.add(video_log)
    db.commit()

    cap=cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return "Не удалось открыть видео",400

    while True:
        ret,frame=cap.read()
        if not ret:
            break
        detections=detect_people(frame,model)
        tracks=tracker.update(detections)
        zc.update(tracks)

        # Сохраняем логи треков
        stats=zc.get_stats()
        for tid,info in stats['details'].items():
            log_entry=DetectionLog(track_id=tid,
                                   total_time=info['total_time'],
                                   is_inside=info['is_inside'])
            db.add(log_entry)
        db.commit()

    cap.release()
    db.close()

    final_stats=zc.get_stats()
    return render_template("results.html", 
                           unique_count=final_stats['unique_count'],
                           details=final_stats['details'])

if __name__=="__main__":
    app.run(debug=True, port=5001)
