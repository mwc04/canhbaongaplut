# create_sample_data.py
import os
import django
import json
from datetime import datetime, timedelta
from django.contrib.gis.geos import LineString, Point, Polygon

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hanoi_flood.settings')
django.setup()

from hanoi_map.models import *
from django.db.models import Count, Q

def clear_old_data():
    """Xóa dữ liệu cũ"""
    print("🗑️  Đang xóa dữ liệu cũ...")
    RoadSegment.objects.all().delete()
    FloodZone.objects.all().delete()
    RainfallStation.objects.all().delete()
    FloodReport.objects.all().delete()
    WeatherForecast.objects.all().delete()
    FloodPrediction.objects.all().delete()
    print("✅ Đã xóa dữ liệu cũ")

def create_flood_zones():
    """Tạo vùng ngập mẫu"""
    print("\n📍 Đang tạo vùng ngập...")
    
    zones = [
        {
            'name': 'Khu vực Cầu Giấy - Thường xuyên ngập',
            'zone_type': 'frequent',
            'geometry': Polygon((
                (105.780, 21.024), (105.795, 21.024),
                (105.795, 21.036), (105.780, 21.036),
                (105.780, 21.024)
            )),
            'priority': 5,
            'description': 'Khu vực trũng, thường xuyên ngập khi mưa lớn'
        },
        {
            'name': 'Khu vực Hoàn Kiếm - Trung tâm',
            'zone_type': 'critical',
            'geometry': Polygon((
                (105.848, 21.018), (105.862, 21.018),
                (105.862, 21.032), (105.848, 21.032),
                (105.848, 21.018)
            )),
            'priority': 5,
            'description': 'Khu vực trung tâm thành phố, trọng điểm'
        },
        {
            'name': 'Khu vực Hai Bà Trưng',
            'zone_type': 'seasonal',
            'geometry': Polygon((
                (105.840, 21.008), (105.855, 21.008),
                (105.855, 21.020), (105.840, 21.020),
                (105.840, 21.008)
            )),
            'priority': 4,
            'description': 'Ngập theo mùa mưa'
        }
    ]
    
    for zone_data in zones:
        FloodZone.objects.create(**zone_data)
        print(f"  ✅ {zone_data['name']}")

def create_road_segments():
    """Tạo đoạn đường mẫu với trạng thái khác nhau"""
    print("\n🛣️  Đang tạo đoạn đường...")
    
    # Lấy vùng ngập
    zone_cg = FloodZone.objects.filter(name__contains="Cầu Giấy").first()
    zone_hk = FloodZone.objects.filter(name__contains="Hoàn Kiếm").first()
    zone_hbt = FloodZone.objects.filter(name__contains="Hai Bà Trưng").first()
    
    roads = [
        # Cầu Giấy - ĐANG NGẬP
        {
            'road_id': 'HN_CG_001',
            'name': 'Đường Trần Duy Hưng',
            'district': 'Cầu Giấy',
            'ward': 'Trung Hòa',
            'geometry': LineString([
                (105.785, 21.026), (105.788, 21.027),
                (105.791, 21.027), (105.795, 21.026)
            ]),
            'elevation': 8.2,
            'slope': 0.5,
            'drainage_capacity': 80,
            'flood_count': 15,
            'last_flood_date': datetime.now().date(),
            'warning_threshold': 25,
            'flood_threshold': 40,
            'current_rainfall': 65.5,
            'current_status': 'flooded',
            'water_depth': 35,
            'is_critical': True,
            'traffic_level': 5,
            'flood_zone': zone_cg,
            'notes': 'Thường xuyên ngập sâu khi mưa lớn'
        },
        {
            'road_id': 'HN_CG_002',
            'name': 'Đường Xuân Thủy',
            'district': 'Cầu Giấy',
            'ward': 'Dịch Vọng',
            'geometry': LineString([
                (105.788, 21.030), (105.791, 21.031),
                (105.794, 21.032)
            ]),
            'elevation': 9.1,
            'slope': 0.8,
            'drainage_capacity': 120,
            'flood_count': 8,
            'warning_threshold': 30,
            'flood_threshold': 45,
            'current_rainfall': 42.3,
            'current_status': 'warning',
            'water_depth': 0,
            'is_critical': True,
            'traffic_level': 4,
            'flood_zone': zone_cg
        },
        
        # Hoàn Kiếm - CẢNH BÁO
        {
            'road_id': 'HN_HK_001',
            'name': 'Phố Lý Thái Tổ',
            'district': 'Hoàn Kiếm',
            'ward': 'Tràng Tiền',
            'geometry': LineString([
                (105.853, 21.024), (105.855, 21.025),
                (105.858, 21.026)
            ]),
            'elevation': 12.5,
            'slope': 1.2,
            'drainage_capacity': 150,
            'flood_count': 3,
            'warning_threshold': 35,
            'flood_threshold': 55,
            'current_rainfall': 38.7,
            'current_status': 'warning',
            'water_depth': 0,
            'is_critical': True,
            'traffic_level': 5,
            'flood_zone': zone_hk,
            'notes': 'Đường trung tâm, ngập nhẹ khi mưa lớn'
        },
        
        # Ba Đình - BÌNH THƯỜNG
        {
            'road_id': 'HN_BD_001',
            'name': 'Đường Nguyễn Chí Thanh',
            'district': 'Ba Đình',
            'ward': 'Ngọc Hà',
            'geometry': LineString([
                (105.815, 21.032), (105.818, 21.033),
                (105.822, 21.034)
            ]),
            'elevation': 14.2,
            'slope': 1.5,
            'drainage_capacity': 200,
            'flood_count': 2,
            'warning_threshold': 40,
            'flood_threshold': 60,
            'current_rainfall': 18.5,
            'current_status': 'normal',
            'water_depth': 0,
            'is_critical': True,
            'traffic_level': 4
        },
        
        # Hai Bà Trưng - ĐANG NGẬP
        {
            'road_id': 'HN_HBT_001',
            'name': 'Đường Bạch Mai',
            'district': 'Hai Bà Trưng',
            'ward': 'Bạch Mai',
            'geometry': LineString([
                (105.843, 21.012), (105.847, 21.013),
                (105.851, 21.014)
            ]),
            'elevation': 7.8,
            'slope': 0.3,
            'drainage_capacity': 70,
            'flood_count': 10,
            'warning_threshold': 20,
            'flood_threshold': 35,
            'current_rainfall': 58.2,
            'current_status': 'flooded',
            'water_depth': 28,
            'is_critical': True,
            'traffic_level': 5,
            'flood_zone': zone_hbt,
            'notes': 'Ngập thường xuyên, thoát nước kém'
        },
        
        # Đống Đa - BÌNH THƯỜNG
        {
            'road_id': 'HN_DD_001',
            'name': 'Đường Tây Sơn',
            'district': 'Đống Đa',
            'ward': 'Trung Liệt',
            'geometry': LineString([
                (105.820, 21.016), (105.825, 21.017),
                (105.830, 21.018)
            ]),
            'elevation': 13.5,
            'slope': 1.0,
            'drainage_capacity': 180,
            'flood_count': 1,
            'warning_threshold': 38,
            'flood_threshold': 58,
            'current_rainfall': 15.3,
            'current_status': 'normal',
            'water_depth': 0,
            'is_critical': False,
            'traffic_level': 3
        }
    ]
    
    for road_data in roads:
        road = RoadSegment.objects.create(**road_data)
        # SỬA DÒNG NÀY - THÊM status_icon thủ công
        status_icon_map = {'normal': '🟢', 'warning': '🟡', 'flooded': '🔴'}
        icon = status_icon_map.get(road.current_status, '⚪')
        status_text = road.get_current_status_display()
        print(f"  {icon} {road.name} - {road.district} ({status_text})")

def create_rainfall_stations():
    """Tạo trạm đo mưa"""
    print("\n🌧️  Đang tạo trạm đo mưa...")
    
    stations = [
        {
            'station_id': 'ST_CG_01',
            'name': 'Trạm Cầu Giấy',
            'location': Point(105.789, 21.030),
            'elevation': 8.5,
            'current_rainfall': 65.5,
            'rainfall_1h': 55.2,
            'rainfall_24h': 145.7,
            'last_update': datetime.now(),
            'is_active': True
        },
        {
            'station_id': 'ST_HK_01',
            'name': 'Trạm Hoàn Kiếm',
            'location': Point(105.856, 21.025),
            'elevation': 11.8,
            'current_rainfall': 38.7,
            'rainfall_1h': 32.1,
            'rainfall_24h': 88.4,
            'last_update': datetime.now(),
            'is_active': True
        },
        {
            'station_id': 'ST_HBT_01',
            'name': 'Trạm Hai Bà Trưng',
            'location': Point(105.848, 21.014),
            'elevation': 7.9,
            'current_rainfall': 58.2,
            'rainfall_1h': 49.8,
            'rainfall_24h': 132.6,
            'last_update': datetime.now(),
            'is_active': True
        }
    ]
    
    for station_data in stations:
        station = RainfallStation.objects.create(**station_data)
        print(f"  📡 {station.name}: {station.current_rainfall}mm/h")

def create_flood_reports():
    """Tạo báo cáo ngập từ người dân"""
    print("\n📝 Đang tạo báo cáo ngập...")
    
    # Lấy các đường gần đó
    road_tdh = RoadSegment.objects.filter(name__contains="Trần Duy Hưng").first()
    road_bm = RoadSegment.objects.filter(name__contains="Bạch Mai").first()
    road_ltt = RoadSegment.objects.filter(name__contains="Lý Thái Tổ").first()
    
    reports = [
        {
            'location': Point(105.788, 21.027),
            'address': 'Số 25 Trần Duy Hưng, phường Trung Hòa, Cầu Giấy',
            'water_depth_cm': 40,
            'flood_area_m2': 600,
            'description': 'Ngập sâu khoảng 40cm, ô tô không thể đi qua, xe máy rất khó khăn',
            'reporter_name': 'Nguyễn Văn An',
            'reporter_phone': '0987123456',
            'status': 'verified',
            'nearest_road': road_tdh
        },
        {
            'location': Point(105.791, 21.031),
            'address': 'Ngã tư Trần Duy Hưng - Xuân Thủy, Cầu Giấy',
            'water_depth_cm': 25,
            'flood_area_m2': 400,
            'description': 'Ngập khoảng 25cm, xe máy vẫn đi được nhưng chậm',
            'reporter_name': 'Trần Thị Bình',
            'reporter_phone': '0918765432',
            'status': 'pending',
            'nearest_road': road_tdh
        },
        {
            'location': Point(105.850, 21.014),
            'address': 'Đoạn giữa đường Bạch Mai, gần Bệnh viện Bạch Mai',
            'water_depth_cm': 35,
            'flood_area_m2': 800,
            'description': 'Ngập khá sâu, giao thông ùn tắc nghiêm trọng',
            'reporter_name': 'Lê Minh Châu',
            'reporter_phone': '0903123789',
            'status': 'verified',
            'nearest_road': road_bm
        },
        {
            'location': Point(105.855, 21.025),
            'address': 'Đoạn phố Lý Thái Tổ gần Bờ Hồ',
            'water_depth_cm': 15,
            'flood_area_m2': 200,
            'description': 'Ngập nhẹ, nước tràn lên vỉa hè',
            'reporter_name': 'Phạm Quốc Đạt',
            'reporter_phone': '0978456123',
            'status': 'resolved',
            'nearest_road': road_ltt
        }
    ]
    
    for report_data in reports:
        report = FloodReport.objects.create(**report_data)
        status_icon_map = {'pending': '⏳', 'verified': '✅', 'resolved': '🏁', 'false_alarm': '❌'}
        icon = status_icon_map.get(report.status, '📋')
        print(f"  {icon} {report.address[:40]}... ({report.water_depth_cm}cm)")

def create_weather_forecasts():
    """Tạo dự báo thời tiết mẫu"""
    print("\n⛈️  Đang tạo dự báo thời tiết...")
    
    location = Point(105.8542, 21.0285)
    now = datetime.now()
    
    for i in range(8):  # 24 giờ (8 bản ghi x 3h)
        forecast_time = now + timedelta(hours=i*3)
        
        WeatherForecast.objects.create(
            location=location,
            forecast_date=forecast_time.date(),
            forecast_hour=forecast_time.hour,
            temperature=28 + (i % 3) - 1,  # 27-30°C
            humidity=75 + (i % 4) * 5,     # 75-90%
            rainfall_mm=5 + (i % 2) * 10,  # 5-15mm
            wind_speed=2.5 + (i % 3) * 0.5,
            description=['Mưa rào', 'Mưa nhẹ', 'Ít mây'][i % 3],
            source='openweathermap'
        )
    
    print(f"  ✅ Đã tạo 8 bản ghi dự báo")
def main():
    """Hàm chính"""
    print("=" * 60)
    print("🚀 BẮT ĐẦU TẠO DỮ LIỆU MẪU CHO HỆ THỐNG NGẬP LỤT HÀ NỘI")
    print("=" * 60)
    
    # Xóa dữ liệu cũ
    clear_old_data()
    
    # Tạo dữ liệu mới
    create_flood_zones()
    create_road_segments()
    create_rainfall_stations()
    create_flood_reports()
    create_weather_forecasts()
    
    # Thống kê
    print("\n" + "=" * 60)
    print("📊 THỐNG KÊ DỮ LIỆU ĐÃ TẠO:")
    print("=" * 60)
    
    try:
        print(f"• 🗺️  Vùng ngập: {FloodZone.objects.count()}")
        print(f"• 🛣️  Đoạn đường: {RoadSegment.objects.count()}")
        
        # Sửa phần thống kê để tránh lỗi
        flooded_count = RoadSegment.objects.filter(current_status='flooded').count()
        warning_count = RoadSegment.objects.filter(current_status='warning').count()
        normal_count = RoadSegment.objects.filter(current_status='normal').count()
        
        print(f"  - 🔴 Đang ngập: {flooded_count}")
        print(f"  - 🟡 Cảnh báo: {warning_count}")
        print(f"  - 🟢 Bình thường: {normal_count}")
        
        print(f"• 📡 Trạm đo mưa: {RainfallStation.objects.count()}")
        print(f"• 📝 Báo cáo ngập: {FloodReport.objects.count()}")
        print(f"• ⛈️  Dự báo thời tiết: {WeatherForecast.objects.count()}")
        
    except Exception as e:
        print(f"⚠️  Lỗi khi thống kê: {e}")
        print("Vẫn tiếp tục...")
    
    print("\n" + "=" * 60)
    print("✅ HOÀN THÀNH TẠO DỮ LIỆU MẪU!")
    print("=" * 60)
    
    # Hiển thị URL
    print("\n🌐 TRUY CẬP ỨNG DỤNG:")
    print("• 👤 User: http://localhost:8000/")
    print("• 👑 Admin: http://localhost:8000/admin/")