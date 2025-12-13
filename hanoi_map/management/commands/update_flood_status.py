from django.core.management.base import BaseCommand
from django.utils import timezone
from hanoi_map.models import RoadSegment
import requests
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Cập nhật trạng thái ngập lụt tự động từ API mưa'
    
    def handle(self, *args, **options):
        self.stdout.write("🔄 Đang cập nhật trạng thái ngập lụt...")
        
        # 1. Lấy dữ liệu mưa từ API (Open-Meteo - miễn phí)
        try:
            # API Open-Meteo cho Hà Nội
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': 21.0285,
                'longitude': 105.8542,
                'hourly': 'rain',
                'timezone': 'Asia/Ho_Chi_Minh',
                'forecast_days': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # Lấy lượng mưa hiện tại (mm/giờ)
            hourly_rain = data.get('hourly', {}).get('rain', [0])
            current_rainfall = hourly_rain[0] if hourly_rain else 0
            
            # Nếu API không có dữ liệu, dùng dữ liệu mẫu
            if current_rainfall is None:
                current_rainfall = random.uniform(0, 60)  # 0-60mm/giờ
                self.stdout.write(f"⚠️ Sử dụng dữ liệu mẫu: {current_rainfall:.1f} mm/giờ")
            else:
                self.stdout.write(f"✅ Dữ liệu mưa thực tế: {current_rainfall} mm/giờ")
                
        except Exception as e:
            self.stdout.write(f"❌ Lỗi khi lấy dữ liệu mưa: {e}")
            current_rainfall = random.uniform(0, 60)  # Dùng dữ liệu mẫu
        
        # 2. Cập nhật tất cả đoạn đường
        roads = RoadSegment.objects.all()
        updated_count = 0
        flooded_count = 0
        warning_count = 0
        
        for road in roads:
            # Thêm biến động nhẹ cho mỗi đoạn đường
            road_rainfall = current_rainfall * random.uniform(0.8, 1.2)
            
            # Cập nhật thông tin
            new_status = road.update_flood_info(road_rainfall)
            
            if new_status == 'flooded':
                flooded_count += 1
            elif new_status == 'warning':
                warning_count += 1
            
            updated_count += 1
        
        # 3. Ghi log
        self.stdout.write(self.style.SUCCESS(
            f"✅ Đã cập nhật {updated_count} đoạn đường: "
            f"{flooded_count} đang ngập, {warning_count} cảnh báo"
        ))
        
        # 4. Tạo báo cáo ngập tự động nếu có đường ngập
        if flooded_count > 0:
            from hanoi_map.models import FloodReport
            from django.contrib.gis.geos import Point
            
            # Lấy một đoạn đường đang ngập
            flooded_road = RoadSegment.objects.filter(current_status='flooded').first()
            if flooded_road:
                # Lấy điểm giữa của đoạn đường
                center = flooded_road.geometry.interpolate_normalized(0.5)
                
                FloodReport.objects.create(
                    location=Point(center.x, center.y),
                    address=f"Tự động: {flooded_road.name}, {flooded_road.district}",
                    water_depth=flooded_road.water_depth,
                    description=f"Ngập do mưa {current_rainfall:.1f}mm/giờ. Tự động báo cáo.",
                    status='verified'
                )
                self.stdout.write(f"📝 Đã tạo báo cáo tự động cho {flooded_road.name}")