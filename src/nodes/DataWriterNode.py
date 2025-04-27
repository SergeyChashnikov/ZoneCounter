# src/nodes/DataWriterNode.py
from influxdb_client import InfluxDBClient, Point, WritePrecision

INFLUX_URL    = "http://localhost:8086"
INFLUX_ORG    = "PeopleCounterOrg"
INFLUX_BUCKET = "people_counter"
INFLUX_TOKEN  = "ваш-сохранённый-token"

class DataWriterNode:
    def __init__(self, influx_url: str, influx_org: str, influx_bucket: str, influx_token: str):
        self.client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
        self.write_api = self.client.write_api(write_options=None)  # можно включить batching по необходимости
        self.bucket = influx_bucket
        self.org = influx_org

    def process(self, frame_element):
        # Формируем точки для записи
        points = []
        # Текущие счетчики людей по зонам
        for zone_id, count in frame_element.zone_counts.items():
            point = Point("people_count") \
                    .tag("zone", zone_id) \
                    .field("count", count) \
                    .time(frame_element.timestamp, WritePrecision.S) 
            points.append(point)
        # FPS (можно записывать раз в несколько кадров для экономии ресурсов, но здесь – каждый кадр)
        point_fps = Point("performance").field("fps", frame_element.fps).time(frame_element.timestamp, WritePrecision.S)
        points.append(point_fps)
        # Запись батчем
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
        except Exception as e:
            print(f"[DataWriterNode] Error writing to InfluxDB: {e}")
        return frame_element
