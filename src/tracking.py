import time
import numpy as np
from logger import setup_logger

logger = setup_logger()

class SimpleCentroidTracker:
    def __init__(self, max_distance=50):
        self.next_id = 0
        self.tracks = {}
        self.max_distance = max_distance
        logger.info(f"Инициализация SimpleCentroidTracker: max_distance={max_distance}")

    def update(self, detections):
        updated_tracks = []
        new_tracks = {}

        centroids = []
        for x1,y1,x2,y2,conf,cls_id in detections:
            cx = (x1+x2)/2
            cy = (y1+y2)/2
            centroids.append((cx,cy))

        unmatched = set(range(len(detections)))

        for track_id, info in self.tracks.items():
            prev_centroid = info['centroid']
            min_dist = float('inf')
            best_idx = -1
            for i in unmatched:
                dist = np.linalg.norm(np.array(prev_centroid)-np.array(centroids[i]))
                if dist<min_dist:
                    min_dist = dist
                    best_idx=i
            if best_idx>=0 and min_dist<=self.max_distance:
                x1,y1,x2,y2,conf,cls_id = detections[best_idx]
                new_tracks[track_id] = {
                    'centroid': centroids[best_idx],
                    'bbox':[x1,y1,x2,y2],
                    'last_seen': time.time()
                }
                updated_tracks.append({
                    'track_id': track_id,
                    'bbox':[x1,y1,x2,y2],
                    'centroid':centroids[best_idx]
                })
                unmatched.remove(best_idx)

        # новые треки
        for i in unmatched:
            x1,y1,x2,y2,conf,cls_id = detections[i]
            new_tracks[self.next_id] = {
                'centroid': centroids[i],
                'bbox':[x1,y1,x2,y2],
                'last_seen': time.time()
            }
            updated_tracks.append({
                'track_id':self.next_id,
                'bbox':[x1,y1,x2,y2],
                'centroid':centroids[i]
            })
            self.next_id+=1

        self.tracks=new_tracks
        return updated_tracks
