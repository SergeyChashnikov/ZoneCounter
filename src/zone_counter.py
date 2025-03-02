import time
from collections import defaultdict
from config import ZONE_COORDS
from logger import setup_logger

logger = setup_logger()

class ZoneCounter:
    def __init__(self, zone_coords=ZONE_COORDS):
        self.zone_coords = zone_coords
        self.track_data = defaultdict(lambda: {'is_inside':False, 'enter_time':None, 'total_time':0.0})
        self.unique_tracks = set()
        logger.info(f"Инициализация ZoneCounter с зоной: {zone_coords}")

    def update(self, tracks):
        xA,yA,xB,yB = self.zone_coords
        now = time.time()

        for t in tracks:
            tid = t['track_id']
            cx, cy = t['centroid']
            inside = (cx>=xA and cx<=xB and cy>=yA and cy<=yB)

            if inside and not self.track_data[tid]['is_inside']:
                # вход
                self.track_data[tid]['is_inside']=True
                self.track_data[tid]['enter_time']=now
                self.unique_tracks.add(tid)
                logger.debug(f"Track {tid} вошел в зону.")
            elif not inside and self.track_data[tid]['is_inside']:
                # выход
                delta = now - self.track_data[tid]['enter_time']
                self.track_data[tid]['total_time']+=delta
                self.track_data[tid]['is_inside']=False
                self.track_data[tid]['enter_time']=None
                logger.debug(f"Track {tid} вышел из зоны. Время внутри={delta:.2f}")

    def get_stats(self):
        details={}
        for tid,info in self.track_data.items():
            details[tid]={'total_time':info['total_time'], 'is_inside':info['is_inside']}
        return {'unique_count': len(self.unique_tracks), 'details': details}
