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

    def update(self, timestamp):
        # Обновление времени последнего обнаружения
        self.timestamp_last = timestamp
