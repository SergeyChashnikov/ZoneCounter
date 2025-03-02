from sqlalchemy import Column, Integer, Float, Boolean, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class DetectionLog(Base):
    """
    Модель для хранения информации о детекциях/треках.
    """
    __tablename__ = "detection_logs"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, index=True)
    total_time = Column(Float, default=0.0)
    is_inside = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class VideoLog(Base):
    """
    Логи о файлах видео, которые анализировали (опционально).
    """
    __tablename__ = "video_logs"

    id = Column(Integer, primary_key=True, index=True)
    filepath = Column(String, index=True)
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)
