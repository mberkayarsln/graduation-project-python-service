import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    
    OFFICE_LOCATION = (41.1097, 29.0204)
    
    NUM_EMPLOYEES = 500
    NUM_CLUSTERS = 25
    MAX_DISTANCE_FROM_CENTER = 2500
    
    EMPLOYEES_PER_STOP = 2
    MIN_STOPS_PER_CLUSTER = 1
    MAX_STOPS_PER_CLUSTER = 15
    MAX_WALK_DISTANCE = 500
    SNAP_STOPS_TO_ROADS = True
    ROAD_SNAP_MAX_DISTANCE = 500
    
    USE_TRAFFIC = False
    TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY')
    
    @staticmethod
    def get_departure_time():
        tomorrow_8am = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        if datetime.now().hour >= 8:
            tomorrow_8am += timedelta(days=1)
        return tomorrow_8am
    
    CLUSTER_COLORS = [
        '#ef4444',  
        '#3b82f6',  
        '#10b981',  
        '#f59e0b',  
        '#8b5cf6',  
        '#ec4899',  
        '#14b8a6',  
        '#06b6d4',  
        '#84cc16',  
        '#f97316'   
    ]
    
    OUTPUT_DIR = "maps"
    MAP_EMPLOYEES = f"{OUTPUT_DIR}/employees.html"
    MAP_CLUSTERS = f"{OUTPUT_DIR}/clusters.html"
    MAP_ROUTES = f"{OUTPUT_DIR}/optimized_routes.html"
    MAP_CLUSTER_DETAIL = f"{OUTPUT_DIR}/cluster_0_detail.html"
