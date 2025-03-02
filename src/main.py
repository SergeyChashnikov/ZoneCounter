import argparse
import cv2
from detection import load_yolov5, detect_people
from tracking import SimpleCentroidTracker
from zone_counter import ZoneCounter
from logger import setup_logger
from config import ZONE_COORDS
from database import SessionLocal, engine
from models import Base, DetectionLog

logger = setup_logger()

def main():
    parser = argparse.ArgumentParser(description="ZoneCounter CLI")
    parser.add_argument('--input', type=str, required=True, help="Путь к видеофайлу или '0' для камеры")
    parser.add_argument('--display', action='store_true', help="Показывать окно с видео?")
    args=parser.parse_args()

    # Создаем таблицы в БД, если не созданы
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    logger.info("Загрузка YOLOv5...")
    model = load_yolov5('yolov5s')
    tracker = SimpleCentroidTracker()
    zc = ZoneCounter(zone_coords=ZONE_COORDS)

    source = 0 if args.input=='0' else args.input
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error(f"Не удалось открыть источник: {args.input}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.info("Конец потока или ошибка чтения.")
            break

        detections = detect_people(frame, model)
        tracks = tracker.update(detections)
        zc.update(tracks)

        # Сохраняем информацию о треках в БД (простейший вариант)
        stats = zc.get_stats()
        for tid, info in stats['details'].items():
            # Для демонстрации - записываем total_time, is_inside
            log_entry = DetectionLog(track_id=tid,
                                     total_time=info['total_time'],
                                     is_inside=info['is_inside'])
            db.add(log_entry)
        db.commit()

        # Визуализация зоны
        xA,yA,xB,yB = ZONE_COORDS
        cv2.rectangle(frame,(xA,yA),(xB,yB),(255,0,0),2)

        # Отрисовка
        for d in detections:
            x1,y1,x2,y2,conf,cls_id=d
            cv2.rectangle(frame,(int(x1),int(y1)),(int(x2),int(y2)),(0,255,0),2)
        for tr in tracks:
            tid=tr['track_id']
            bbox=tr['bbox']
            cv2.putText(frame, f"ID:{tid}", (int(bbox[0]), int(bbox[1])-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255),2)

        if args.display:
            cv2.imshow("ZoneCounter", frame)
            if cv2.waitKey(1)&0xFF==ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    db.close()

    final_stats = zc.get_stats()
    logger.info(f"Уникальных посетителей: {final_stats['unique_count']}")

if __name__=="__main__":
    main()
