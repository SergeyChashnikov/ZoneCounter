from collections import deque
import numpy as np
import csv, os

from elements.FrameElement import FrameElement
from elements.VideoEndBreakElement import VideoEndBreakElement
from utils_local.utils import profile_time


class CalcStatisticsNode:
    """Модуль для расчета загруженности/нарушения зон (вычисление статистик)"""

    def __init__(self, config: dict) -> None:
        config_general = config["general"]

        self.time_buffer_analytics = config_general[
            "buffer_analytics"
        ]  # размер времени буфера в минутах
        self.min_time_life_track = config_general[
            "min_time_life_track"
        ]  # минимальное время жизни трека в сек
        self.count_persons_buffer_frames = config_general["count_persons_buffer_frames"]
        self.persons_buffer = deque(maxlen=self.count_persons_buffer_frames)  # создали буфер значений

        # ────── НАСТРОЙКИ ЛОГИРОВАНИЯ ─────────────────────────
        self.log_enabled = config_general.get("log_zone_events", True)
        self.log_path    = config_general.get("zone_log_file", "logs/zone_events.csv")
        if self.log_enabled:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            # заголовок, если файл ещё пустой
            if not os.path.isfile(self.log_path) or os.path.getsize(self.log_path) == 0:
                with open(self.log_path, "w", newline="") as f:
                    csv.writer(f).writerow(
                        ["camera", "id", "zone", "t_in", "t_out", "duration"]
                    )
        # ───────────────────────────────────────────────────────

    @profile_time 
    def process(self, frame_element: FrameElement) -> FrameElement:
        # Выйти из обработки если это пришел VideoEndBreakElement а не FrameElement
        if isinstance(frame_element, VideoEndBreakElement):
            return frame_element
        assert isinstance(
            frame_element, FrameElement
        ), f"CalcStatisticsNode | Неправильный формат входного элемента {type(frame_element)}"

        buffer_tracks = frame_element.buffer_tracks
        self.persons_buffer.append(len(frame_element.id_list))

        info_dictionary = {}
        info_dictionary["persons_amount"] = round(np.mean(self.persons_buffer))
        zones_activity = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
        }  # всего 5 зон (занулим стартовое значение)

        # Посчитаем чило людей которые давно живут и имеют значения входа в зону
        for _, track_element in buffer_tracks.items():
            if (
                track_element.timestamp_last - track_element.timestamp_init_zone
                > self.min_time_life_track
                and track_element.start_zone is not None
            ):
                key = track_element.start_zone
                zones_activity[key] += 1

        # Переведем значения в размерность людей/мин согласно известному размеру буфера
        for key in zones_activity:
            zones_activity[key] /= self.time_buffer_analytics

        info_dictionary['zones_activity'] = zones_activity

        # Запись результатов обработки:
        frame_element.info = info_dictionary

        '''
        # ----------- (2) запись события вход-выход ------------
        if self.log_enabled:
            for tr in frame_element.buffer_tracks.values():
                if tr.t_enter is not None and tr.t_exit is not None:
                    duration = tr.t_exit - tr.t_enter
                    with open(self.log_path, "a", newline="") as f:
                        csv.writer(f).writerow(
                            [frame_element.source,
                            tr.id,
                            tr.zone_id,
                            f"{tr.t_enter:.3f}",
                            f"{tr.t_exit:.3f}",
                            f"{duration:.3f}"]
                        )

                    # ─── «обнуляем» для следующего цикла ───
                    tr.t_enter = None
                    tr.t_exit  = None
                    tr.zone_id = None #
        '''


        return frame_element
