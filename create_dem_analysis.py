import rasterio
import numpy as np
from django.contrib.gis.geos import Polygon

def analyze_dem_for_flood_risk(dem_path):
    """Phân tích DEM để xác định vùng có nguy cơ ngập"""
    with rasterio.open(dem_path) as src:
        dem = src.read(1)
        transform = src.transform
        
        # Phân tích độ cao
        min_elevation = np.min(dem)
        max_elevation = np.max(dem)
        mean_elevation = np.mean(dem)
        
        # Xác định vùng thấp (nguy cơ ngập cao)
        low_areas = dem < (mean_elevation - 5)  # Thấp hơn trung bình 5m
        very_low_areas = dem < (mean_elevation - 10)  # Thấp hơn trung bình 10m
        
        return {
            'min_elevation': min_elevation,
            'max_elevation': max_elevation,
            'mean_elevation': mean_elevation,
            'low_area_percentage': np.sum(low_areas) / dem.size * 100,
            'very_low_area_percentage': np.sum(very_low_areas) / dem.size * 100,
            'shape': dem.shape
        }