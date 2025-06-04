class TrackElement:
    # Класс, содержаций информацию о конкретном треке человека
    def __init__(
        self,
        id: int,
        timestamp_first: float,
        start_zone: int | None = None,
    ) -> None:
        self.id = id  # Номер этого трека
        self.timestamp_first = timestamp_first  # Таймстемп инициализации (в сек)
        self.timestamp_last = timestamp_first  # Таймстемп последнего обнаружения (в сек)
        self.start_zone = start_zone  # Номер зоны, в которую зашел
        self.timestamp_init_zone = timestamp_first  # Таймстемп инициализации номера зоны (в сек)
        # ps: если зона не будет определена, то значение останется равным первому появлению

        # ───────────  ДОБАВЛЯЕМ  ───────────
        self.zone_id  = None       # в какой зоне был зафиксирован
        self.t_enter  = None       # время входа
        self.t_exit   = None       # время выхода
        # ────────────────────────────────────

    def update(self, timestamp, zone_now: int | None = None):
        # Обновление времени последнего обнаружения
        self.timestamp_last = timestamp

        # ───── маленькая вставка ─────
        if zone_now is not None and self.t_enter is None:
            # первое пересечение ROI
            self.zone_id = zone_now
            self.t_enter = timestamp
        elif zone_now is None and self.t_enter is not None and self.t_exit is None:
            # первый выход
            self.t_exit = timestamp
        # ─────────────────────────────
