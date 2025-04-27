# src/nodes/ZoneCountingNode.py
import cv2
import time

class ZoneCountingNode:
    def __init__(self, zones_config):
        # zones_config: список словарей с определением зон (id, name, polygon coords)
        self.zones = []
        for zone in zones_config:
            zone_id = zone["id"]
            if zone.get("shape") == "rectangle":
                x1,y1,x2,y2 = zone["coords"]
                # конвертируем в список точек многоугольника (четыре угла)
                poly = [(x1,y1), (x2,y1), (x2,y2), (x1,y2)]
            else:
                poly = zone["points"]
            poly_cnt = np.array(poly, dtype=np.int32)
            self.zones.append({"id": zone_id, "name": zone.get("name", zone_id), "points": poly_cnt})
        # Словарь, хранящий текущие ID треков в каждой зоне
        self.current_ids_in_zone = {zone["id"]: set() for zone in self.zones}
        # Хранение суммарного времени по трекам (track_id -> {zone_id: total_time})
        self.track_time_stats = {}

    def process(self, frame_element):
        current_time = time.time()
        # Обнулить счетчики перед новым вычислением
        zone_counts = {zone["id"]: 0 for zone in self.zones}
        # Проверяем каждый активный трек
        for track in frame_element.tracks:
            x1, y1, x2, y2 = track.bbox
            # вычисляем центр bbox
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            track_id = track.id
            # пометим, что трек не в какой-либо зоне до проверки
            currently_in_zone = None
            for zone in self.zones:
                zone_id = zone["id"]
                # Проверка попадания точки (cx,cy) внутрь контура зоны
                # Используем cv2.pointPolygonTest: >0 = внутри, 0 = на границе, <0 = вне
                if cv2.pointPolygonTest(zone["points"], (cx, cy), False) >= 0:
                    currently_in_zone = zone_id
                    zone_counts[zone_id] += 1
                    # Если этот track_id еще не помечен как находящийся в zone_id:
                    if track_id not in self.current_ids_in_zone[zone_id]:
                        # событие входа
                        self.current_ids_in_zone[zone_id].add(track_id)
                        track.in_zone = zone_id
                        track.zone_entry_time[zone_id] = current_time
                        # инициализируем запись во времени, если не было
                        if track_id not in self.track_time_stats:
                            self.track_time_stats[track_id] = {}
                        if zone_id not in self.track_time_stats[track_id]:
                            self.track_time_stats[track_id][zone_id] = 0.0
                    break  # предположим, один трек может быть не более чем в одной зоне одновременно
            # Если трек не попал ни в одну зону, но раньше был в какой-то – зафиксируем выход
            if currently_in_zone is None:
                if track.in_zone:
                    zone_id = track.in_zone
                    if track_id in self.current_ids_in_zone[zone_id]:
                        self.current_ids_in_zone[zone_id].remove(track_id)
                    # зафиксируем время выхода и накопим время пребывания
                    entry_time = track.zone_entry_time.get(zone_id, current_time)
                    duration = current_time - entry_time
                    # суммируем общее время в зоне
                    if track_id not in self.track_time_stats:
                        self.track_time_stats[track_id] = {}
                    prev_total = self.track_time_stats[track_id].get(zone_id, 0.0)
                    self.track_time_stats[track_id][zone_id] = prev_total + duration
                    # обнуляем отметки в треке
                    track.in_zone = None
                    track.zone_entry_time.pop(zone_id, None)
        # Обработка треков, которые исчезли (если они находились в зонах, считаем что вышли в момент исчезновения)
        if hasattr(frame_element, "disappeared_ids"):
            for track_id in frame_element.disappeared_ids:
                # Проверяем все зоны, в которых мог числиться этот трек
                for zone_id, ids_set in self.current_ids_in_zone.items():
                    if track_id in ids_set:
                        ids_set.remove(track_id)
                        # фиксируем выход
                        exit_time = current_time
                        # Для вычисления времени найдем TrackElement (в идеале надо хранить track по id)
                        # Здесь упрощенно: не имея track, пытаемся воспользоваться сохраненными временами
                        entry_time = None
                        # Мы не храним явно track_element для исчезнувших, 
                        # но могли бы хранить в самом трекере или в self.track_time_stats последние entry_time.
                        # Предположим, что при входе мы сохраняли время входа track.zone_entry_time.
                        # Можно расширить хранение: например, сохранить last_entry_time[track_id][zone_id].
                        # В MVP ограничимся нулевой длительностью.
                        if track_id in self.track_time_stats and zone_id in self.track_time_stats[track_id]:
                            prev_total = self.track_time_stats[track_id][zone_id]
                        else:
                            prev_total = 0.0
                        # Обновляем суммарное время (без точного учета entry_time, т.к. он не сохранён глобально)
                        self.track_time_stats.setdefault(track_id, {})
                        self.track_time_stats[track_id].setdefault(zone_id, prev_total)
                        # Здесь можно улучшить, если сохранять entry_time при входе глобально
        # Записываем результаты в frame_element
        frame_element.zone_counts = zone_counts
        frame_element.zone_stats = self.track_time_stats
        return frame_element
