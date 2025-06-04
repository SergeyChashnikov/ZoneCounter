# nodes/TrackerInfoUpdateNode.py
# ──────────────────────────────────────────────────────────────
#  Версия с фиксацией входа/выхода в ROI-зоны и передачей
#  zone_now / bbox в TrackElement.update()
# ──────────────────────────────────────────────────────────────
import logging

from elements.FrameElement import FrameElement
from elements.TrackElement import TrackElement
from elements.VideoEndBreakElement import VideoEndBreakElement
from utils_local.utils import profile_time, intersects_central_point

logger = logging.getLogger("buffer_tracks")


class TrackerInfoUpdateNode:
    """Модуль обновления актуальных треков"""

    def __init__(self, config: dict) -> None:
        config_general = config["general"]

        self.size_buffer_analytics = (
            config_general["buffer_analytics"] * 60
        )  # число секунд в буфере аналитики
        # добавим мин времени жизни чтобы при расчете статистики были именно
        # люди за последие buffer_analytics минут:
        self.size_buffer_analytics += config_general["min_time_life_track"]
        self.buffer_tracks = {}  # Буфер актуальных треков

    @profile_time 
    def process(self, frame_element: FrameElement) -> FrameElement:
        # Выйти из обработки если это пришел VideoEndBreakElement а не FrameElement
        if isinstance(frame_element, VideoEndBreakElement):
            return frame_element
        assert isinstance(
            frame_element, FrameElement
        ), f"TrackerInfoUpdateNode | Неправильный формат входного элемента {type(frame_element)}"

        id_list = frame_element.id_list

        zones  = frame_element.zones_info      # {id: polygon}
        ts_now  = frame_element.timestamp

        for i, id in enumerate(id_list):
            
            # Обновление или создание нового трека
            if id not in self.buffer_tracks:
                # Создаем новый ключ
                self.buffer_tracks[id] = TrackElement(
                    id=id,
                    timestamp_first=frame_element.timestamp,
                )
            else:
                # Обновление времени последнего обнаружения
                self.buffer_tracks[id].update(frame_element.timestamp)

            # Поиск первого пересечения с полигонами зон
            if self.buffer_tracks[id].start_zone is None:
                self.buffer_tracks[id].start_zone = intersects_central_point(
                    tracked_xyxy=frame_element.tracked_xyxy[i],
                    polygons=frame_element.zones_info,
                )
                # Проверка того, что отработка функции дала наконец-то актуальный номер зоны:
                if self.buffer_tracks[id].start_zone is not None:
                    # Тогда сохраняем время такого момента:
                    self.buffer_tracks[id].timestamp_init_zone = frame_element.timestamp

            # -------------------------------------------------------------
            # НОВОЕ: определяем зону, где находится центр bbox
            bbox      = frame_element.tracked_xyxy[i]
            zone_now = intersects_central_point(bbox, zones)

            tr = self.buffer_tracks[id]

            # ------- ВХОД -------------------------------------------------
            if not tr.in_zone and zone_now is not None:
                tr.in_zone = True
                tr.zone_id = zone_now
                tr.t_enter = ts_now
                tr.t_exit  = None        # на всякий случай

            # ------- ВЫХОД -----------------------------------------------
            if tr.in_zone and zone_now is None:
                tr.in_zone = False
                tr.t_exit  = ts_now

                # <— сразу пишем в CSV и обнуляем
                if tr.t_enter is not None:
                    duration = tr.t_exit - tr.t_enter
                    with open("logs/zone_events.csv", "a", newline="") as f:
                        import csv
                        csv.writer(f).writerow(
                            [frame_element.source,
                            tr.id,
                            tr.zone_id,
                            f"{tr.t_enter:.3f}",
                            f"{tr.t_exit:.3f}",
                            f"{duration:.3f}"]
                        )
                        print(f"LOG  id={tr.id} zone={tr.zone_id}  {tr.t_enter:.2f}->{tr.t_exit:.2f}") # это для проверки закомментировать в нормальной работе
                # готов к следующему циклу
                tr.t_enter = None
                tr.t_exit  = None
                tr.zone_id = None

        # Удаление старых айдишников из словаря если их время жизни > size_buffer_analytics
        keys_to_remove = []
        for key, track_element in sorted(self.buffer_tracks.items()):  # Сортируем элементы по ключу
            if frame_element.timestamp - track_element.timestamp_first < self.size_buffer_analytics:
                break  # Прерываем цикл, если значение time_delta больше check
            else:
                keys_to_remove.append(key)  # Добавляем ключ для удаления

        for key in keys_to_remove:
            self.buffer_tracks.pop(key)  # Удаляем элемент из словаря
            logger.info(f"Removed tracker with key {key}")

        # Запись результатов обработки:
        frame_element.buffer_tracks = self.buffer_tracks

        return frame_element
