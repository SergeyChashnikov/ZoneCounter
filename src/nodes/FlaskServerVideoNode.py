# src/nodes/FlaskServerVideoNode.py
from flask import Flask, Response

class FlaskServerVideoNode:
    def __init__(self, host="0.0.0.0", port=5000):
        self.app = Flask(__name__)
        self.latest_frame = None   # сюда основной процесс будет помещать последний кадр (bytes JPEG)
        self.current_stats = {}    # сюда – текущие статистики (например, zone_counts, fps)
        # Определяем маршруты
        @self.app.route('/')
        def index():
            # Формируем простую HTML-страницу с видео и статистикой
            stats_html = ""
            if self.current_stats:
                stats_html += "<h3>Current Statistics:</h3><ul>"
                # например, self.current_stats = {"zone1":2, "zone2":1, "fps": 15.0}
                for key, val in self.current_stats.items():
                    stats_html += f"<li>{key}: {val}</li>"
                stats_html += "</ul>"
            else:
                stats_html = "<p>No stats available.</p>"
            return f"<html><body><h2>PeopleCounter Stream</h2>" \
                   f"<img src='/video' style='max-width:100%; height:auto;'/><br/>{stats_html}</body></html>"

        @self.app.route('/video')
        def video_feed():
            # Возврат потока кадров
            def generate():
                while True:
                    if self.latest_frame is not None:
                        # формируем HTTP-часть с boundary
                        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + self.latest_frame + b"\r\n")
            return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

        # Запускаем Flask в отдельном потоке
        import threading
        thread = threading.Thread(target=self.app.run, kwargs={"host": host, "port": port}, daemon=True)
        thread.start()

    def process(self, frame_element):
        # Кодирование кадра в JPEG и обновление latest_frame
        import cv2
        ret, jpeg = cv2.imencode('.jpg', frame_element.frame)
        if ret:
            self.latest_frame = jpeg.tobytes()
        # Обновляем текущую статистику для отображения
        stats = {}
        for zone_id, count in frame_element.zone_counts.items():
            stats[f"Zone {zone_id}"] = count
        stats["FPS"] = round(frame_element.fps, 2)
        self.current_stats = stats
        return frame_element
