import random
import cv2
import numpy as np

from utils_local.utils import profile_time, FPS_Counter
from elements.VideoEndBreakElement import VideoEndBreakElement
from elements.FrameElement import FrameElement


class ShowNode:
    """Модуль отвечающий, за визуализацию результатов"""

    def __init__(self, config) -> None:
        data_colors = config["general"]["colors_of_zones"]
        self.colors_zones = {key: tuple(value) for key, value in data_colors.items()}
        self.buffer_analytics_sec = (
            config["general"]["buffer_analytics"] * 1 + config["general"]["min_time_life_track"]
        )  # столько по времени буфер набирается и информацию о статистеке выводить рано

        config_show_node = config["show_node"]
        self.scale = config_show_node["scale"]
        self.fps_counter_N_frames_stat = config_show_node["fps_counter_N_frames_stat"]
        self.default_fps_counter = FPS_Counter(self.fps_counter_N_frames_stat)
        self.draw_fps_info = config_show_node["draw_fps_info"]
        self.show_roi = config_show_node["show_roi"]
        self.overlay_transparent_mask = config_show_node["overlay_transparent_mask"]
        self.imshow = config_show_node["imshow"]
        self.show_only_yolo_detections = config_show_node["show_only_yolo_detections"]
        self.show_track_id_different_colors = config_show_node["show_track_id_different_colors"]
        self.show_info_statistics = config_show_node["show_info_statistics"]

        self.show_number_of_zone = True  # отображение номеров зон

        # Параметры для шрифтов:
        self.fontFace = 1
        self.fontScale = 2.0
        self.thickness = 2

        # Параметры для полигонов и bboxes:
        self.thickness_lines = 3

        # Параметры для экрана статистики:
        self.width_window = 700  # ширина экрана в пикселях

    @profile_time
    def process(self, frame_element: FrameElement, fps_counter=None) -> FrameElement:
        # Выйти из обработки если это пришел VideoEndBreakElement а не FrameElement
        if isinstance(frame_element, VideoEndBreakElement):
            return frame_element
        assert isinstance(
            frame_element, FrameElement
        ), f"ShowNode | Неправильный формат входного элемента {type(frame_element)}"

        frame_result = frame_element.frame.copy()

        # Отображение лишь результатов детекции:
        if self.show_only_yolo_detections:
            for box, class_name in zip(frame_element.detected_xyxy, frame_element.detected_cls):
                x1, y1, x2, y2 = box
                # Отрисовка прямоугольника
                cv2.rectangle(frame_result, (x1, y1), (x2, y2), (0, 0, 0), 2)
                # Добавление подписи с именем класса
                cv2.putText(
                    frame_result,
                    class_name,
                    (x1, y1 - 10),
                    fontFace=self.fontFace,
                    fontScale=self.fontScale,
                    thickness=self.thickness,
                    color=(0, 0, 255),
                )

        else:
            # Отображение результатов трекинга:
            for box, class_name, id in zip(
                frame_element.tracked_xyxy, frame_element.tracked_cls, frame_element.id_list
            ):
                x1, y1, x2, y2 = box
                # Отрисовка прямоугольника
                if self.show_track_id_different_colors:
                    # Отображаем каждый трек своим цветом
                    random.seed(int(id))
                    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                else:
                    # Отображаем каждый трек согласно цвету пересечения с зоной
                    try:
                        start_zone = frame_element.buffer_tracks[int(id)].start_zone
                        if start_zone is not None:
                            color = self.colors_zones[int(start_zone)]
                        else:  # бокс черным цветом если еще нет информации о первой зоне
                            color = (0, 0, 0)
                    except KeyError:  # На случай если человек еще в кадре а трек уже удален
                        color = (0, 0, 0)

                cv2.rectangle(frame_result, (x1, y1), (x2, y2), color, self.thickness_lines)
                # Добавление подписи с именем класса
                cv2.putText(
                    frame_result,
                    f"{id}",
                    (x1, y1 - 10),
                    fontFace=self.fontFace,
                    fontScale=self.fontScale,
                    thickness=self.thickness,
                    color=(0, 0, 255),
                )

        # Построение полигонов зон
        if self.show_roi:
            for zone_id, points in frame_element.zones_info.items():
                color = self.colors_zones[int(zone_id)]
                points = np.array(points, np.int32)
                points = points.reshape((-1, 1, 2))
                cv2.polylines(
                    frame_result,
                    [points],
                    isClosed=True,
                    color=color,
                    thickness=self.thickness_lines,
                )

                if self.overlay_transparent_mask:
                    frame_result = self._overlay_transparent_mask(
                        frame_result, points, mask_color=color, alpha=0.3
                    )

                # Отображение номера зоны в залитой окружности
                if self.show_number_of_zone:
                    moments = cv2.moments(points)  # Найти центр области
                    if moments["m00"] != 0:
                        cx = int(moments["m10"] / moments["m00"])
                        cy = int(moments["m01"] / moments["m00"])

                        (label_width, label_height), _ = cv2.getTextSize(
                            str(zone_id),
                            fontFace=self.fontFace,
                            fontScale=self.fontScale * 1.3,
                            thickness=self.thickness,
                        )
                        # Определение размеров круга
                        circle_radius = max(label_width, label_height) // 2
                        # Рисование круга
                        cv2.circle(
                            frame_result,
                            (cx, cy),
                            circle_radius + 6,  # Добавляем небольшой отступ для текста
                            (200, 200, 200),
                            -1
                        )
                        # Нанесение подписи zone_id в центре области
                        cv2.putText(
                            frame_result,
                            str(zone_id),
                            (cx + 2 - label_width // 2, cy + 2 + label_height // 2),
                            fontFace=self.fontFace,
                            fontScale=self.fontScale * 1.3,
                            thickness=self.thickness,
                            color=(0, 0, 0),
                        )

        # Подсчет fps и отрисовка
        if self.draw_fps_info:
            fps_counter = fps_counter if fps_counter is not None else self.default_fps_counter
            fps_real = fps_counter.calc_FPS()

            text = f"FPS: {fps_real:.1f}"
            (label_width, label_height), _ = cv2.getTextSize(
                text,
                fontFace=self.fontFace,
                fontScale=self.fontScale,
                thickness=self.thickness,
            )
            cv2.rectangle(
                frame_result, (0, 0), (10 + label_width, 35 + label_height), (0, 0, 0), -1
            )
            cv2.putText(
                img=frame_result,
                text=text,
                org=(10, 40),
                fontFace=self.fontFace,
                fontScale=self.fontScale,
                thickness=self.thickness,
                color=(255, 255, 255),
            )

        # Обработка отдельного окна с выводом статистики
        if self.show_info_statistics:
            black_image = np.zeros((frame_result.shape[0], self.width_window, 3), dtype=np.uint8)
            data_info = frame_element.info

            # Текст для количества людей
            text_persons = f"Persons amount: {data_info['persons_amount']}"
            # Начальная координата для текста
            y = 55
            # Выводим текст для количества людей
            cv2.putText(
                img=black_image,
                text=text_persons,
                org=(20, y),
                fontFace=self.fontFace,
                fontScale=self.fontScale*1.5,
                thickness=self.thickness,
                color=(255, 255, 255),
            )
            # Увеличиваем y на высоту строки текста
            y += cv2.getTextSize(text_persons, self.fontFace, self.fontScale*1.5, self.thickness)[0][1] + 25
            # Текст для заголовка
            text_info = "Zone congestion:"
            # Выводим заголовок
            cv2.putText(
                img=black_image,
                text=text_info,
                org=(20, y),
                fontFace=self.fontFace,
                fontScale=self.fontScale*1.5,
                thickness=self.thickness,
                color=(255, 255, 255),
            )
            # Увеличиваем y на высоту строки текста
            y += cv2.getTextSize(text_info, self.fontFace, self.fontScale*1.5, self.thickness)[0][1] + 25
            
            # Проверим, что буфер уже наполнился и можно выводить статистику:
            if frame_element.timestamp >= self.buffer_analytics_sec:
                # Выводим информацию по зонам
                for key, value in data_info['zones_activity'].items():
                    text_person = f"  zone {key}: {value:.1f} persons/sec"
                    cv2.putText(
                        img=black_image,
                        text=text_person,
                        org=(20, y),
                        fontFace=self.fontFace,
                        fontScale=self.fontScale * 1.5,
                        thickness=self.thickness,
                        color=(255, 255, 255),
                    )
                    # Увеличиваем y на высоту строки текста
                    y += (
                        cv2.getTextSize(
                            text_person, self.fontFace, self.fontScale * 1.5, self.thickness
                        )[0][1] + 25
                    )
            else:
                text_to_show = f"   wait {round(self.buffer_analytics_sec - frame_element.timestamp)} sec"
                cv2.putText(
                    img=black_image,
                    text=text_to_show,
                    org=(20, y),
                    fontFace=self.fontFace,
                    fontScale=self.fontScale * 1.5,
                    thickness=self.thickness,
                    color=(255, 255, 255),
                )
            frame_result = np.hstack((frame_result, black_image))

        frame_element.frame_result = frame_result
        frame_show = cv2.resize(frame_result.copy(), (-1, -1), fx=self.scale, fy=self.scale)

        if self.imshow:
            cv2.imshow(frame_element.source, frame_show)
            cv2.waitKey(1)

        return frame_element

    def _overlay_transparent_mask(self, img, points, mask_color=(0, 255, 255), alpha=0.3):
        binary_mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
        binary_mask = cv2.fillPoly(binary_mask, pts=[points], color=1)
        colored_mask = (binary_mask[:, :, np.newaxis] * mask_color).astype(np.uint8)
        return cv2.addWeighted(img, 1, colored_mask, alpha, 0)
