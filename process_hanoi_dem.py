# process_dem_hanoi.py
"""
Script xử lý DEM Hà Nội từ QGIS và import vào Django WebGIS
Tác giả: [Tên của bạn]
Ngày tạo: [Ngày hiện tại]
"""

import os
import sys
import json
import logging
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape, mapping
from django.contrib.gis.geos import Polygon, GEOSGeometry
import matplotlib.pyplot as plt
from pathlib import Path

# =========================================================
# CẤU HÌNH LOGGING
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dem_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =========================================================
# HÀM CHÍNH - XỬ LÝ DEM HÀ NỘI
# =========================================================
def process_hanoi_dem(input_tif: str, output_dir: str) -> dict:
    """
    Xử lý file DEM Hà Nội từ QGIS
    
    Args:
        input_tif: Đường dẫn file DEM (.tif)
        output_dir: Thư mục lưu kết quả
    
    Returns:
        Dict chứa kết quả phân tích
    """
    logger.info("=" * 60)
    logger.info("🔄 BẮT ĐẦU XỬ LÝ DEM HÀ NỘI")
    logger.info(f"📁 File đầu vào: {input_tif}")
    logger.info(f"📂 Thư mục đầu ra: {output_dir}")
    logger.info("=" * 60)
    
    # Kiểm tra file tồn tại
    if not os.path.exists(input_tif):
        logger.error(f"❌ File không tồn tại: {input_tif}")
        raise FileNotFoundError(f"Không tìm thấy file: {input_tif}")
    
    # Tạo thư mục output
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        with rasterio.open(input_tif) as src:
            # Đọc dữ liệu DEM
            dem_array = src.read(1)
            nodata = src.nodata
            crs = src.crs.to_string() if src.crs else "Không xác định"
            
            logger.info("📊 THÔNG TIN DEM:")
            logger.info(f"  • Hệ tọa độ: {crs}")
            logger.info(f"  • Kích thước: {dem_array.shape} (hàng x cột)")
            logger.info(f"  • Độ phân giải: {src.res[0]}m x {src.res[1]}m")
            logger.info(f"  • NoData value: {nodata}")
            logger.info(f"  • Bounding box: {src.bounds}")
            
            # 1. TÍNH TOÁN THỐNG KÊ
            logger.info("\n📈 ĐANG TÍNH TOÁN THỐNG KÊ...")
            stats = calculate_dem_statistics(dem_array, nodata)
            
            # 2. PHÂN TÍCH ĐỘ DỐC
            logger.info("📐 ĐANG PHÂN TÍCH ĐỘ DỐC...")
            slope_analysis = calculate_slope_analysis(dem_array, src.transform, nodata)
            
            # 3. PHÂN TÍCH NGUY CƠ NGẬP
            logger.info("⚠️  ĐANG PHÂN TÍCH NGUY CƠ NGẬP...")
            flood_risk = analyze_flood_risk_hanoi(dem_array, stats['mean'], nodata)
            
            # 4. XÁC ĐỊNH VÙNG THẤP TRŨNG
            logger.info("📍 ĐANG XÁC ĐỊNH VÙNG THẤP TRŨNG...")
            depression_zones = identify_depression_zones(dem_array, src.transform, nodata)
            
            # 5. TẠO BOUNDING BOX
            bbox = get_bounding_box_hanoi(src)
            
            # 6. LƯU KẾT QUẢ
            logger.info("💾 ĐANG LƯU KẾT QUẢ...")
            save_dem_analysis_results(
                output_dir=output_dir,
                stats=stats,
                slope_analysis=slope_analysis,
                flood_risk=flood_risk,
                depression_zones=depression_zones,
                bbox=bbox,
                crs=crs
            )
            
            # 7. TẠO HÌNH ẢNH TRỰC QUAN
            logger.info("🖼️  ĐANG TẠO HÌNH ẢNH TRỰC QUAN...")
            create_visualizations(dem_array, output_dir, stats)
            
            # 8. TẠO GEOJSON CHO WEBGIS
            logger.info("🗺️  ĐANG TẠO DỮ LIỆU CHO WEBGIS...")
            create_webgis_data(dem_array, src.transform, output_dir, flood_risk)
            
            # Tổng hợp kết quả
            results = {
                'file_info': {
                    'path': input_tif,
                    'crs': crs,
                    'shape': dem_array.shape,
                    'resolution': src.res
                },
                'statistics': stats,
                'slope_analysis': slope_analysis,
                'flood_risk': flood_risk,
                'depression_zones_count': len(depression_zones),
                'bounding_box': bbox,
                'output_dir': output_dir
            }
            
            logger.info("=" * 60)
            logger.info("✅ XỬ LÝ DEM HOÀN TẤT!")
            logger.info("=" * 60)
            
            return results
            
    except Exception as e:
        logger.error(f"❌ LỖI KHI XỬ LÝ DEM: {str(e)}")
        raise

# =========================================================
# HÀM PHỤ TRỢ - TÍNH TOÁN THỐNG KÊ
# =========================================================
def calculate_dem_statistics(dem_array: np.ndarray, nodata: float) -> dict:
    """
    Tính toán các thống kê từ dữ liệu DEM
    
    Args:
        dem_array: Mảng dữ liệu DEM
        nodata: Giá trị NoData
    
    Returns:
        Dict chứa các thống kê
    """
    # Tạo mask loại bỏ NoData
    if nodata is not None:
        mask = dem_array != nodata
        valid_data = dem_array[mask]
    else:
        valid_data = dem_array.flatten()
    
    if len(valid_data) == 0:
        return {
            'error': 'Không có dữ liệu hợp lệ',
            'valid_cells': 0
        }
    
    # Tính các thống kê cơ bản
    stats = {
        'min': float(np.min(valid_data)),
        'max': float(np.max(valid_data)),
        'mean': float(np.mean(valid_data)),
        'median': float(np.median(valid_data)),
        'std': float(np.std(valid_data)),
        'percentile_25': float(np.percentile(valid_data, 25)),
        'percentile_75': float(np.percentile(valid_data, 75)),
        'valid_cells': int(len(valid_data)),
        'total_cells': int(dem_array.size),
        'valid_percentage': round(len(valid_data) / dem_array.size * 100, 2)
    }
    
    # Phân loại độ cao
    elevation_classes = classify_elevation(valid_data)
    stats['elevation_classes'] = elevation_classes
    
    logger.info(f"  • Độ cao min: {stats['min']:.2f}m")
    logger.info(f"  • Độ cao max: {stats['max']:.2f}m")
    logger.info(f"  • Độ cao TB: {stats['mean']:.2f}m")
    logger.info(f"  • Ô hợp lệ: {stats['valid_cells']:,} ({stats['valid_percentage']}%)")
    
    return stats

def classify_elevation(elevation_data: np.ndarray) -> dict:
    """
    Phân loại độ cao thành các mức
    """
    bins = [0, 5, 10, 15, 20, 30, 50, 100, float('inf')]
    labels = ['<5m', '5-10m', '10-15m', '15-20m', '20-30m', '30-50m', '50-100m', '>100m']
    
    counts, _ = np.histogram(elevation_data, bins=bins)
    percentages = (counts / len(elevation_data) * 100).round(2)
    
    return {
        label: {
            'count': int(count),
            'percentage': float(percent)
        }
        for label, count, percent in zip(labels, counts, percentages)
    }

# =========================================================
# HÀM PHỤ TRỢ - PHÂN TÍCH ĐỘ DỐC
# =========================================================
def calculate_slope_analysis(dem_array: np.ndarray, transform, nodata: float) -> dict:
    """
    Tính toán độ dốc từ DEM
    """
    # Tạo mask
    if nodata is not None:
        mask = dem_array != nodata
    else:
        mask = np.ones_like(dem_array, dtype=bool)
    
    # Tính độ dốc đơn giản (phương pháp Horn)
    dx, dy = np.gradient(dem_array)
    slope = np.sqrt(dx**2 + dy**2)
    
    # Chuyển từ radians sang degrees
    slope_degrees = np.arctan(slope) * (180 / np.pi)
    slope_degrees[~mask] = np.nan
    
    # Phân loại độ dốc
    slope_classes = {
        'flat': np.sum(slope_degrees < 2),
        'gentle': np.sum((slope_degrees >= 2) & (slope_degrees < 5)),
        'moderate': np.sum((slope_degrees >= 5) & (slope_degrees < 15)),
        'steep': np.sum((slope_degrees >= 15) & (slope_degrees < 30)),
        'very_steep': np.sum(slope_degrees >= 30)
    }
    
    total_valid = np.sum(mask)
    slope_percentages = {
        k: round(v / total_valid * 100, 2) if total_valid > 0 else 0
        for k, v in slope_classes.items()
    }
    
    analysis = {
        'max_slope': float(np.nanmax(slope_degrees)),
        'mean_slope': float(np.nanmean(slope_degrees)),
        'slope_classes': slope_classes,
        'slope_percentages': slope_percentages
    }
    
    logger.info(f"  • Độ dốc TB: {analysis['mean_slope']:.2f}°")
    logger.info(f"  • Độ dốc max: {analysis['max_slope']:.2f}°")
    logger.info(f"  • Diện tích bằng phẳng (<2°): {slope_percentages['flat']}%")
    
    return analysis

# =========================================================
# HÀM PHỤ TRỢ - PHÂN TÍCH NGUY CƠ NGẬP
# =========================================================
def analyze_flood_risk_hanoi(dem_array: np.ndarray, mean_elevation: float, nodata: float) -> dict:
    """
    Phân tích nguy cơ ngập lụt cho Hà Nội
    """
    # Tạo mask
    if nodata is not None:
        mask = dem_array != nodata
        valid_dem = np.where(mask, dem_array, np.nan)
    else:
        valid_dem = dem_array
        mask = np.ones_like(dem_array, dtype=bool)
    
    total_valid = np.sum(mask)
    
    # Phân tích theo mức độ cao tuyệt đối
    risk_levels = {
        'very_high': valid_dem < 5,      # Dưới 5m - Rất cao
        'high': valid_dem < 10,          # 5-10m - Cao
        'medium': valid_dem < 15,        # 10-15m - Trung bình
        'low': valid_dem < mean_elevation, # 15-trung bình - Thấp
        'very_low': valid_dem >= mean_elevation # Trên trung bình - Rất thấp
    }
    
    risk_counts = {}
    risk_percentages = {}
    
    for level_name, level_mask in risk_levels.items():
        count = np.nansum(level_mask)
        risk_counts[level_name] = int(count)
        risk_percentages[level_name] = round(count / total_valid * 100, 2)
    
    # Phân tích vùng đặc biệt nguy hiểm
    critical_areas = {
        'below_sea_level': np.nansum(valid_dem < 0),
        'below_2m': np.nansum(valid_dem < 2),
        'below_5m': np.nansum(valid_dem < 5),
        'depressions': np.nansum(valid_dem < (mean_elevation - 5))
    }
    
    analysis = {
        'risk_counts': risk_counts,
        'risk_percentages': risk_percentages,
        'critical_areas': critical_areas,
        'risk_thresholds': {
            'very_high': 5,
            'high': 10,
            'medium': 15,
            'low': mean_elevation
        }
    }
    
    logger.info(f"  • Nguy cơ rất cao (<5m): {risk_percentages['very_high']}%")
    logger.info(f"  • Nguy cơ cao (5-10m): {risk_percentages['high']}%")
    logger.info(f"  • Dưới 2m (rất nguy hiểm): {critical_areas['below_2m']:,} ô")
    
    return analysis

# =========================================================
# HÀM PHỤ TRỢ - XÁC ĐỊNH VÙNG THẤP TRŨNG
# =========================================================
def identify_depression_zones(dem_array: np.ndarray, transform, nodata: float, 
                             threshold: float = 5) -> list:
    """
    Xác định các vùng thấp trũng (depression)
    
    Args:
        threshold: Ngưỡng thấp hơn trung bình (m)
    """
    if nodata is not None:
        mask = dem_array != nodata
        valid_dem = np.where(mask, dem_array, np.nan)
    else:
        valid_dem = dem_array
        mask = np.ones_like(dem_array, dtype=bool)
    
    mean_elevation = np.nanmean(valid_dem)
    depression_mask = valid_dem < (mean_elevation - threshold)
    
    # Chuyển mask thành polygon
    depression_polygons = []
    try:
        for geom, value in shapes(depression_mask.astype('uint8'), 
                                 transform=transform):
            if value == 1:
                # Chuyển sang hệ tọa độ WGS84 (EPSG:4326) nếu cần
                polygon = shape(geom)
                if not polygon.is_empty:
                    depression_polygons.append({
                        'geometry': mapping(polygon),
                        'area_sq_m': polygon.area * (transform[0] * transform[4]),  # Tính diện tích
                        'type': 'depression'
                    })
    except Exception as e:
        logger.warning(f"⚠️ Không thể tạo polygon từ depression: {e}")
    
    logger.info(f"  • Tìm thấy {len(depression_polygons)} vùng thấp trũng")
    return depression_polygons

# =========================================================
# HÀM PHỤ TRỢ - BOUNDING BOX
# =========================================================
def get_bounding_box_hanoi(src) -> dict:
    """
    Lấy thông tin bounding box
    """
    bounds = src.bounds
    
    return {
        'west': bounds.left,
        'east': bounds.right,
        'south': bounds.bottom,
        'north': bounds.top,
        'width_km': (bounds.right - bounds.left) / 1000,  # Chuyển sang km
        'height_km': (bounds.top - bounds.bottom) / 1000,
        'center': {
            'lon': (bounds.left + bounds.right) / 2,
            'lat': (bounds.bottom + bounds.top) / 2
        }
    }

# =========================================================
# HÀM PHỤ TRỢ - LƯU KẾT QUẢ
# =========================================================
def save_dem_analysis_results(output_dir: str, **kwargs) -> None:
    """
    Lưu tất cả kết quả phân tích ra file
    """
    # Lưu thống kê
    with open(os.path.join(output_dir, 'dem_statistics.json'), 'w', encoding='utf-8') as f:
        json.dump(kwargs.get('stats', {}), f, indent=2, ensure_ascii=False)
    
    # Lưu phân tích độ dốc
    with open(os.path.join(output_dir, 'slope_analysis.json'), 'w', encoding='utf-8') as f:
        json.dump(kwargs.get('slope_analysis', {}), f, indent=2, ensure_ascii=False)
    
    # Lưu phân tích nguy cơ ngập
    with open(os.path.join(output_dir, 'flood_risk_analysis.json'), 'w', encoding='utf-8') as f:
        json.dump(kwargs.get('flood_risk', {}), f, indent=2, ensure_ascii=False)
    
    # Lưu thông tin bounding box
    with open(os.path.join(output_dir, 'bounding_box.json'), 'w', encoding='utf-8') as f:
        json.dump(kwargs.get('bbox', {}), f, indent=2, ensure_ascii=False)
    
    # Lưu vùng thấp trũng
    if kwargs.get('depression_zones'):
        with open(os.path.join(output_dir, 'depression_zones.json'), 'w', encoding='utf-8') as f:
            json.dump(kwargs['depression_zones'], f, indent=2, ensure_ascii=False)
    
    # Lưu tổng hợp
    summary = {
        'timestamp': str(datetime.now()),
        'crs': kwargs.get('crs', 'Unknown'),
        'summary': {
            'min_elevation': kwargs.get('stats', {}).get('min', 0),
            'max_elevation': kwargs.get('stats', {}).get('max', 0),
            'mean_elevation': kwargs.get('stats', {}).get('mean', 0),
            'high_risk_percentage': kwargs.get('flood_risk', {}).get('risk_percentages', {}).get('very_high', 0)
        }
    }
    
    with open(os.path.join(output_dir, 'analysis_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Đã lưu kết quả vào: {output_dir}")

# =========================================================
# HÀM PHỤ TRỢ - TẠO HÌNH ẢNH
# =========================================================
def create_visualizations(dem_array: np.ndarray, output_dir: str, stats: dict) -> None:
    """
    Tạo hình ảnh trực quan từ DEM
    """
    try:
        plt.figure(figsize=(15, 10))
        
        # 1. Histogram độ cao
        plt.subplot(2, 2, 1)
        plt.hist(dem_array[dem_array > -9999].flatten(), bins=50, edgecolor='black')
        plt.title('Phân bố độ cao Hà Nội')
        plt.xlabel('Độ cao (m)')
        plt.ylabel('Số lượng')
        plt.grid(True, alpha=0.3)
        
        # 2. Heatmap đơn giản
        plt.subplot(2, 2, 2)
        plt.imshow(dem_array, cmap='terrain', aspect='auto')
        plt.colorbar(label='Độ cao (m)')
        plt.title('Bản đồ độ cao')
        
        # 3. Box plot
        plt.subplot(2, 2, 3)
        plt.boxplot(dem_array[dem_array > -9999].flatten())
        plt.title('Thống kê độ cao')
        plt.ylabel('Meters')
        
        # 4. Thông tin thống kê
        plt.subplot(2, 2, 4)
        plt.axis('off')
        info_text = f"""THỐNG KÊ DEM HÀ NỘI
        ----------------------
        Min: {stats.get('min', 0):.1f}m
        Max: {stats.get('max', 0):.1f}m
        Mean: {stats.get('mean', 0):.1f}m
        Std: {stats.get('std', 0):.1f}m
        Valid cells: {stats.get('valid_cells', 0):,}
        """
        plt.text(0.1, 0.5, info_text, fontsize=10, 
                verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'dem_visualization.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"🖼️  Đã tạo hình ảnh: {output_path}")
        
    except Exception as e:
        logger.warning(f"⚠️ Không thể tạo hình ảnh: {e}")

# =========================================================
# HÀM PHỤ TRỢ - TẠO DỮ LIỆU WEBGIS
# =========================================================
def create_webgis_data(dem_array: np.ndarray, transform, output_dir: str, 
                      flood_risk: dict) -> None:
    """
    Tạo dữ liệu GeoJSON cho WebGIS
    """
    try:
        # Tạo Grid cells với thông tin độ cao
        grid_size = 100  # Mỗi grid 100x100 pixels
        height, width = dem_array.shape
        
        features = []
        for i in range(0, height, grid_size):
            for j in range(0, width, grid_size):
                # Lấy subset của DEM
                subset = dem_array[i:i+grid_size, j:j+grid_size]
                valid_subset = subset[subset > -9999]
                
                if len(valid_subset) == 0:
                    continue
                
                # Tính toán thông tin
                avg_elevation = np.mean(valid_subset)
                
                # Xác định nguy cơ
                risk_level = 'very_low'
                if avg_elevation < 5:
                    risk_level = 'very_high'
                elif avg_elevation < 10:
                    risk_level = 'high'
                elif avg_elevation < 15:
                    risk_level = 'medium'
                elif avg_elevation < 20:
                    risk_level = 'low'
                
                # Tạo polygon cho grid cell
                x1, y1 = transform * (j, i)
                x2, y2 = transform * (j + grid_size, i + grid_size)
                
                geometry = {
                    "type": "Polygon",
                    "coordinates": [[
                        [x1, y1], [x2, y1],
                        [x2, y2], [x1, y2],
                        [x1, y1]
                    ]]
                }
                
                feature = {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "id": f"grid_{i}_{j}",
                        "avg_elevation": round(avg_elevation, 2),
                        "risk_level": risk_level,
                        "cell_count": int(len(valid_subset))
                    }
                }
                
                features.append(feature)
        
        # Tạo GeoJSON
        geojson = {
            "type": "FeatureCollection",
            "name": "DEM_Hanoi_Grid",
            "crs": {
                "type": "name",
                "properties": {"name": "EPSG:4326"}
            },
            "features": features[:1000]  # Giới hạn số lượng features
        }
        
        output_path = os.path.join(output_dir, 'dem_grid.geojson')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
        
        logger.info(f"🗺️  Đã tạo {len(features)} grid cells: {output_path}")
        
    except Exception as e:
        logger.error(f"❌ Lỗi tạo WebGIS data: {e}")

# =========================================================
# HÀM IMPORT VÀO DJANGO
# =========================================================
def import_dem_to_django(dem_path: str, analysis_results: dict) -> bool:
    """
    Import kết quả phân tích DEM vào Django database
    
    Returns:
        bool: True nếu thành công
    """
    logger.info("🗄️  BẮT ĐẦU IMPORT VÀO DJANGO DATABASE")
    
    try:
        # Setup Django
        import django
        import sys
        
        # Thêm project path vào sys.path
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_path not in sys.path:
            sys.path.append(project_path)
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hanoi_flood.settings")
        django.setup()
        
        from hanoi_map.models import DigitalElevationModel, FloodRiskFromDEM
        from datetime import datetime
        
        # Lấy thông tin từ kết quả phân tích
        stats = analysis_results.get('statistics', {})
        bbox_info = analysis_results.get('bounding_box', {})
        flood_risk = analysis_results.get('flood_risk', {})
        
        # Tạo bounding box geometry
        try:
            bbox_polygon = Polygon.from_bbox([
                bbox_info.get('west', 105.0),
                bbox_info.get('south', 20.5),
                bbox_info.get('east', 106.5),
                bbox_info.get('north', 21.5)
            ])
            bbox_polygon.srid = 4326
        except Exception as e:
            logger.error(f"❌ Lỗi tạo bounding box: {e}")
            bbox_polygon = None
        
        # 1. Tạo bản ghi DEM
        dem_obj = DigitalElevationModel.objects.create(
            name=f"DEM Hà Nội - {datetime.now().strftime('%Y%m%d')}",
            description="Mô hình số độ cao Hà Nội xử lý từ QGIS",
            source="QGIS Processing",
            resolution=0.0001,  # Cần điều chỉnh theo thực tế
            coordinate_system="EPSG:4326",
            bounding_box=bbox_polygon,
            min_elevation=stats.get('min', 0),
            max_elevation=stats.get('max', 0),
            mean_elevation=stats.get('mean', 0),
            dem_file=os.path.basename(dem_path)  # Chỉ lưu tên file
        )
        
        logger.info(f"✅ Đã tạo DEM record: {dem_obj.name}")
        
        # 2. Tạo bản ghi Flood Risk Analysis
        flood_risk_obj = FloodRiskFromDEM.objects.create(
            dem=dem_obj,
            name="Phân tích nguy cơ ngập từ DEM",
            risk_level=_determine_overall_risk(flood_risk),
            high_risk_area_km2=_calculate_risk_area(flood_risk, 'very_high'),
            medium_risk_area_km2=_calculate_risk_area(flood_risk, 'high'),
            low_risk_area_km2=_calculate_risk_area(flood_risk, 'medium'),
            elevation_analysis=stats,
            slope_analysis=analysis_results.get('slope_analysis', {}),
            drainage_analysis={},  # Cần bổ sung sau
            dem_based_risk=flood_risk
        )
        
        logger.info(f"✅ Đã tạo Flood Risk Analysis: {flood_risk_obj.name}")
        
        # 3. Cập nhật các FloodZone hiện có với thông tin độ cao
        _update_flood_zones_with_elevation(dem_obj, stats)
        
        logger.info("=" * 60)
        logger.info("🎉 IMPORT VÀO DJANGO THÀNH CÔNG!")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LỖI IMPORT VÀO DJANGO: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def _determine_overall_risk(flood_risk: dict) -> str:
    """Xác định mức độ nguy cơ tổng thể"""
    percentages = flood_risk.get('risk_percentages', {})
    
    if percentages.get('very_high', 0) > 10:
        return 'very_high'
    elif percentages.get('very_high', 0) + percentages.get('high', 0) > 20:
        return 'high'
    elif percentages.get('medium', 0) > 30:
        return 'medium'
    else:
        return 'low'

def _calculate_risk_area(flood_risk: dict, risk_level: str) -> float:
    """Tính diện tích nguy cơ (km²) - ước tính"""
    percentages = flood_risk.get('risk_percentages', {})
    
    # Giả sử diện tích Hà Nội ~ 3,359 km²
    hanoi_area = 3359
    return round(percentages.get(risk_level, 0) / 100 * hanoi_area, 2)

def _update_flood_zones_with_elevation(dem_obj, stats: dict):
    """Cập nhật FloodZone với thông tin độ cao"""
    try:
        from hanoi_map.models import FloodZone
        
        flood_zones = FloodZone.objects.all()
        updated_count = 0
        
        for zone in flood_zones:
            # Cập nhật elevation information vào description
            if not zone.description:
                zone.description = ""
            
            elevation_info = f"\n\n=== THÔNG TIN ĐỘ CAO ===\n"
            elevation_info += f"• Độ cao khu vực: {stats.get('mean', 0):.1f}m\n"
            elevation_info += f"• So với trung bình: "
            
            # Thêm phân tích đơn giản
            if stats.get('mean', 0) < 10:
                elevation_info += "THẤP - Nguy cơ ngập cao\n"
            elif stats.get('mean', 0) < 15:
                elevation_info += "TRUNG BÌNH - Nguy cơ ngập trung bình\n"
            else:
                elevation_info += "CAO - Nguy cơ ngập thấp\n"
            
            zone.description += elevation_info
            zone.save()
            updated_count += 1
        
        logger.info(f"✅ Đã cập nhật {updated_count} FloodZone với thông tin độ cao")
        
    except Exception as e:
        logger.warning(f"⚠️ Không thể cập nhật FloodZone: {e}")

# =========================================================
# HÀM CHÍNH - ĐIỂM KHỞI ĐẦU
# =========================================================
if __name__ == "__main__":
    # =====================================================
    # CẤU HÌNH ĐƯỜNG DẪN
    # =====================================================
    DEM_PATH = "data/dem_hanoi.tif"  # Thay bằng đường dẫn thực tế
    OUTPUT_DIR = "processed_output/dem_analysis"
    
    # Import datetime cho logging
    from datetime import datetime
    
    print("=" * 70)
    print("🚀 CHƯƠNG TRÌNH XỬ LÝ DEM HÀ NỘI CHO WEBGIS")
    print("=" * 70)
    print(f"Thời gian bắt đầu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"File DEM: {DEM_PATH}")
    print(f"Thư mục kết quả: {OUTPUT_DIR}")
    print("=" * 70)
    
    try:
        # 1. Xử lý DEM
        print("\n1️⃣  ĐANG XỬ LÝ DEM...")
        results = process_hanoi_dem(DEM_PATH, OUTPUT_DIR)
        
        # 2. Import vào Django
        print("\n2️⃣  ĐANG IMPORT VÀO DJANGO...")
        import_success = import_dem_to_django(DEM_PATH, results)
        
        if import_success:
            print("\n" + "=" * 70)
            print("🎊 HOÀN TẤT XỬ LÝ DEM!")
            print("=" * 70)
            
            # Hiển thị thông tin tổng hợp
            stats = results.get('statistics', {})
            flood_risk = results.get('flood_risk', {})
            
            print("\n📈 KẾT QUẢ CHÍNH:")
            print(f"  • Độ cao trung bình: {stats.get('mean', 0):.1f}m")
            print(f"  • Vùng nguy cơ cao (<5m): {flood_risk.get('risk_percentages', {}).get('very_high', 0)}%")
            print(f"  • Vùng thấp trũng: {results.get('depression_zones_count', 0)} vùng")
            print(f"  • Diện tích phân tích: {results.get('bounding_box', {}).get('width_km', 0):.1f}km x "
                  f"{results.get('bounding_box', {}).get('height_km', 0):.1f}km")
            
            print("\n📍 TRUY CẬP WEBGIS:")
            print("  • DEM Visualization: http://localhost:8000/dem/")
            print("  • Flood Risk Map: http://localhost:8000/map/")
            print("  • Admin Panel: http://localhost:8000/admin/")
            
            print("\n📁 CÁC FILE ĐÃ TẠO:")
            for file in os.listdir(OUTPUT_DIR):
                if file.endswith(('.json', '.png', '.geojson')):
                    print(f"  • {file}")
            
        else:
            print("\n❌ CÓ LỖI KHI IMPORT VÀO DJANGO!")
            print("Vui lòng kiểm tra file log: dem_processing.log")
        
    except FileNotFoundError:
        print(f"\n❌ KHÔNG TÌM THẤY FILE DEM: {DEM_PATH}")
        print("Vui lòng kiểm tra đường dẫn file DEM.")
        
    except Exception as e:
        print(f"\n❌ LỖI KHÔNG XÁC ĐỊNH: {str(e)}")
        print("Chi tiết lỗi đã được ghi vào file log.")
    
    finally:
        print("\n" + "=" * 70)
        print(f"Thời gian kết thúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)