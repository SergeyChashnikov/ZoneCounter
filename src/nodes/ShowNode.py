# src/nodes/ShowNode.py
import cv2

class ShowNode:
    def __init__(self):
        # Настройки отображения можно вынести, например, цвета, толщину линий, шрифт
        self.color_person = (0, 255, 0)   # зеленый
        self.color_zone = (255, 0, 0)     # синий
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def process(self, frame_element):
        frame = frame_element.frame
        # Рисуем зоны
        if hasattr(frame_element, "zone_counts"):
            for zone in frame_element.zone_counts.keys():
                # Найдем соответствующий полигон зоны (зоны хранятся, например, в ZoneCountingNode или глобально)
                # Предположим, для простоты, что ShowNode знает координаты зон через глобальную переменную или singleton
                pass
        # (На практике, лучше передать в ShowNode при инициализации список зон, аналогично ZoneCountingNode)
        # Здесь предполагается, что ShowNode был инициализирован ссылкой на список зон:
        for zone in getattr(self, "zones", []):
            pts = zone["points"]
            # рисуем контур
            cv2.polylines(frame, [pts], isClosed=True, color=self.color_zone, thickness=2)
            # пишем имя зоны
            label = zone["name"]
            # разместим текст у первого угла полигона
            x_text, y_text = pts[0][0], pts[0][1] - 10
            cv2.putText(frame, label, (x_text, y_text), self.font, 0.6, self.color_zone, 2)
            # выводим счетчик, если известен
            zone_id = zone["id"]
            count = frame_element.zone_counts.get(zone_id, 0)
            count_text = f"Count: {count}"
            cv2.putText(frame, count_text, (x_text, y_text+20), self.font, 0.6, self.color_zone, 2)

        # Рисуем детекции/треки
        for track in frame_element.tracks:
            x1, y1, x2, y2 = track.bbox
            tid = track.id
            cv2.rectangle(frame, (x1, y1), (x2, y2), self.color_person, 2)
            cv2.putText(frame, f"ID {tid}", (x1, y1-5), self.font, 0.5, self.color_person, 2)
        # Обновляем кадр в FrameElement
        frame_element.frame = frame
        return frame_element
