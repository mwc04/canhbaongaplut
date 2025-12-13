# hanoi_map/services.py - PHIÊN BẢN ĐẦY ĐỦ VỚI API THỜI TIẾT
import requests
from django.conf import settings
from datetime import datetime, timedelta
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Count, Avg, Q, Max
import json
import traceback

from .models import FloodZone, FloodReport, WeatherForecast, FloodPrediction

# Hằng số SRID cho Hà Nội (WGS84)
SRID = 4326


class LocationSearchService:
    """Service tìm kiếm địa điểm tại Hà Nội"""
    
    @staticmethod
    def search_hanoi_location(query):
        """Tìm kiếm địa điểm trong Hà Nội"""
        try:
            if not query or len(query.strip()) < 2:
                return []
                
            encoded_query = requests.utils.quote(f"{query} Hà Nội")
            url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=10&countrycodes=vn&addressdetails=1"
            
            headers = {
                'User-Agent': 'HanoiFloodMonitor/1.0',
                'Accept-Language': 'vi'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                results = response.json()
                
                hanoi_results = []
                for result in results:
                    address = result.get('address', {})
                    city = address.get('city', '').lower()
                    state = address.get('state', '').lower()
                    county = address.get('county', '').lower()
                    
                    hanoi_keywords = ['hanoi', 'hà nội', 'hn', 'thành phố hà nội']
                    location_text = f"{city} {state} {county}".lower()
                    
                    if any(keyword in location_text for keyword in hanoi_keywords):
                        hanoi_results.append({
                            'display_name': result.get('display_name', ''),
                            'lat': float(result.get('lat', 0)),
                            'lon': float(result.get('lon', 0)),
                            'address': address,
                            'type': result.get('type', ''),
                            'importance': result.get('importance', 0)
                        })
                
                return hanoi_results
            
            return []
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    @staticmethod
    def get_location_info(lat, lon):
        """Lấy thông tin chi tiết về một vị trí"""
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
            
            headers = {
                'User-Agent': 'HanoiFloodMonitor/1.0',
                'Accept-Language': 'vi'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})
                
                district = (
                    address.get('city_district') or 
                    address.get('district') or 
                    address.get('subdistrict') or 
                    address.get('county') or 
                    ''
                )
                
                ward = (
                    address.get('suburb') or 
                    address.get('quarter') or 
                    address.get('neighbourhood') or 
                    address.get('town') or 
                    ''
                )
                
                return {
                    'success': True,
                    'display_name': data.get('display_name', ''),
                    'district': district,
                    'ward': ward,
                    'street': address.get('road', ''),
                    'full_address': address,
                    'coordinates': {'lat': lat, 'lon': lon}
                }
            
            return {'success': False, 'error': 'Không thể lấy thông tin địa chỉ'}
            
        except Exception as e:
            print(f"❌ Reverse geocode error: {e}")
            return {'success': False, 'error': str(e)}


class WeatherService:
    """Service lấy thời tiết từ OpenWeatherMap"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.use_fallback = not self.api_key
    
    def get_current_weather(self, lat, lon):
        """Lấy thời tiết hiện tại"""
        try:
            if self.use_fallback:
                return self.get_fallback_weather()
            
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'vi'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️ Weather API error: {response.status_code}")
                return self.get_fallback_weather()
                
            data = response.json()
            
            return {
                'success': True,
                'temp': round(data['main']['temp'], 1),
                'feels_like': round(data['main']['feels_like'], 1),
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'rain': data.get('rain', {}).get('1h', 0),
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': round(data['wind']['speed'], 1),
                'clouds': data['clouds']['all'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Weather API error: {e}")
            return self.get_fallback_weather()
    
    def get_forecast(self, lat, lon):
        """Lấy dự báo thời tiết"""
        try:
            if self.use_fallback:
                return self.get_fallback_forecast()
            
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': 8,  # 8 bản ghi = 24 giờ
                'lang': 'vi'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️ Forecast API error: {response.status_code}")
                return self.get_fallback_forecast()
                
            data = response.json()
            
            forecasts = []
            for item in data.get('list', [])[:8]:
                forecasts.append({
                    'datetime': item.get('dt_txt', ''),
                    'temp': round(item['main']['temp'], 1),
                    'feels_like': round(item['main']['feels_like'], 1),
                    'humidity': item['main']['humidity'],
                    'rain': item.get('rain', {}).get('3h', 0),
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon'],
                    'wind_speed': round(item['wind']['speed'], 1),
                    'clouds': item['clouds']['all']
                })
            
            return {
                'success': True,
                'city': data.get('city', {}).get('name', 'Hà Nội'),
                'forecasts': forecasts,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Forecast API error: {e}")
            return self.get_fallback_forecast()
    
    def get_rain_alerts(self, lat, lon):
        """Lấy cảnh báo mưa"""
        try:
            # OpenWeatherMap không có API cảnh báo miễn phí
            # Nên trả về dữ liệu mẫu hoặc tích hợp với API khác
            current = self.get_current_weather(lat, lon)
            
            alerts = []
            if current.get('rain', 0) > 10:
                alerts.append({
                    'level': 'high',
                    'message': 'Mưa lớn: Lượng mưa > 10mm/h. Cẩn thận ngập lụt!',
                    'icon': 'fa-exclamation-triangle',
                    'time': datetime.now().strftime('%H:%M')
                })
            elif current.get('rain', 0) > 5:
                alerts.append({
                    'level': 'medium',
                    'message': 'Mưa vừa: Có thể gây ngập cục bộ',
                    'icon': 'fa-cloud-rain',
                    'time': datetime.now().strftime('%H:%M')
                })
            
            return alerts
            
        except Exception as e:
            print(f"❌ Rain alerts error: {e}")
            return []
    
    def get_fallback_weather(self):
        """Dữ liệu thời tiết mặc định"""
        now = datetime.now()
        hour = now.hour
        month = now.month
        
        if 4 <= month <= 9:
            if 5 <= hour < 18:
                description = "Nắng"
                icon = "01d"
                temp = 28 + (hour - 12) * 0.5
            else:
                description = "Trời quang"
                icon = "01n"
                temp = 25
        else:
            if 6 <= hour < 17:
                description = "Nhiều mây"
                icon = "03d"
                temp = 20
            else:
                description = "Lạnh"
                icon = "13n"
                temp = 15
        
        return {
            'success': True,
            'temp': round(temp, 1),
            'feels_like': round(temp + 2, 1),
            'humidity': 75,
            'pressure': 1013,
            'rain': 0,
            'description': description,
            'icon': icon,
            'wind_speed': 2.5,
            'clouds': 20,
            'timestamp': now.isoformat(),
            'is_fallback': True
        }
    
    def get_fallback_forecast(self):
        """Dữ liệu dự báo mặc định cho demo"""
        now = datetime.now()
        forecasts = []
        
        # Tạo 8 bản ghi dự báo (24 giờ)
        for i in range(8):
            hour_offset = i * 3
            forecast_time = now + timedelta(hours=hour_offset)
            
            hour = forecast_time.hour
            is_day = 6 <= hour < 18
            
            if hour_offset < 12:
                if hour_offset < 6:
                    temp = 26 + (hour_offset * 0.5)
                    rain = 0.5 if hour_offset == 3 else 0
                else:
                    temp = 28 - ((hour_offset - 6) * 0.3)
                    rain = 1.2 if hour_offset == 9 else 0.8
            else:
                temp = 25
                rain = 0
            
            forecasts.append({
                'datetime': forecast_time.strftime('%Y-%m-%d %H:%M:%S'),
                'temp': round(temp, 1),
                'feels_like': round(temp + 1, 1),
                'humidity': 70 + (i * 2),
                'rain': round(rain, 1),
                'description': 'Mưa nhẹ' if rain > 0 else ('Nắng' if is_day else 'Trời quang'),
                'icon': '10d' if rain > 0 else ('01d' if is_day else '01n'),
                'wind_speed': round(2.5 + (i * 0.3), 1),
                'clouds': 40 + (i * 5)
            })
        
        return {
            'success': True,
            'city': 'Hà Nội',
            'forecasts': forecasts,
            'timestamp': now.isoformat(),
            'is_fallback': True
        }


class FloodDataService:
    """Service cung cấp dữ liệu ngập cho bản đồ"""
    
    @staticmethod
    def get_all_flood_data():
        """Lấy TẤT CẢ dữ liệu ngập từ database"""
        try:
            print("📍 FloodDataService.get_all_flood_data() - Lấy TẤT CẢ dữ liệu")
            
            data = {
                'flood_zones': [],
                'flood_reports': [],
                'stats': {},
                'last_updated': datetime.now().isoformat(),
                'success': True
            }
            
            # ============ 1. LẤY TẤT CẢ ĐIỂM NGẬP ============
            zones = FloodZone.objects.filter(is_active=True)
            print(f"✅ Tìm thấy {zones.count()} điểm ngập hoạt động")
            
            for zone in zones:
                try:
                    geometry = None
                    if zone.geometry:
                        try:
                            geometry = json.loads(zone.geometry.geojson)
                        except:
                            center = zone.geometry.centroid
                            geometry = {
                                'type': 'Point',
                                'coordinates': [center.x, center.y]
                            }
                    else:
                        geometry = {'type': 'Point', 'coordinates': [0, 0]}
                    
                    data['flood_zones'].append({
                        'type': 'Feature',
                        'geometry': geometry,
                        'properties': {
                            'id': f"zone_{zone.id}",
                            'name': zone.name or 'Điểm ngập',
                            'zone_type': zone.zone_type or 'unknown',
                            'zone_type_display': zone.get_zone_type_display() if hasattr(zone, 'get_zone_type_display') else zone.zone_type,
                            'district': zone.district or '',
                            'ward': zone.ward or '',
                            'street': zone.street or '',
                            'max_depth': zone.max_depth_cm or 0,
                            'report_count': zone.report_count or 0,
                            'last_reported': zone.last_reported_at.strftime('%H:%M %d/%m') if zone.last_reported_at else 'Chưa có',
                            'description': (zone.description or '')[:100],
                            'is_active': zone.is_active,
                            'flood_cause': zone.flood_cause or 'Không xác định'
                        }
                    })
                except Exception as e:
                    print(f"⚠️ Lỗi xử lý zone {zone.id}: {e}")
            
            # ============ 2. LẤY TẤT CẢ BÁO CÁO ============
            reports = FloodReport.objects.filter(status='verified').order_by('-created_at')
            print(f"✅ Tìm thấy {reports.count()} báo cáo đã xác nhận")
            
            for report in reports:
                try:
                    data['flood_reports'].append({
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [report.location.x, report.location.y]
                        },
                        'properties': {
                            'id': f"report_{report.id}",
                            'address': report.address or 'Không có địa chỉ',
                            'water_depth': report.water_depth or 0,
                            'severity': report.severity or 'unknown',
                            'severity_display': report.get_severity_display() if hasattr(report, 'get_severity_display') else report.severity,
                            'created_at': report.created_at.strftime('%H:%M %d/%m'),
                            'created_at_iso': report.created_at.isoformat(),
                            'reporter_name': report.reporter_name or 'Ẩn danh',
                            'reporter_phone': report.reporter_phone or '',
                            'photo_url': report.photo_url if report.photo_url else None,
                            'description': (report.description or '')[:100],
                            'district': report.district or '',
                            'ward': report.ward or '',
                            'status': report.status
                        }
                    })
                except Exception as e:
                    print(f"⚠️ Lỗi xử lý report {report.id}: {e}")
            
            # ============ 3. THỐNG KÊ ============
            data['stats'] = {
                'total_zones': zones.count(),
                'total_reports': reports.count(),
                'active_zones': zones.count(),
                'total_verified_reports': reports.count(),
                'last_update': datetime.now().strftime('%H:%M %d/%m/%Y')
            }
            
            print(f"📊 Thống kê: {data['stats']}")
            return data
            
        except Exception as e:
            print(f"❌ Lỗi get_all_flood_data: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'flood_zones': [],
                'flood_reports': [],
                'stats': {},
                'last_updated': datetime.now().isoformat()
            }


class FloodCheckService:
    """Service kiểm tra ngập lụt - ĐÃ SỬA LỖI SRID"""
    
    @staticmethod
    def check_flood_at_location(lat, lon, radius_m=1000):
        """Kiểm tra ngập tại vị trí - SỬA LỖI SRID"""
        try:
            print(f"🔍 FloodCheckService.check_flood_at_location({lat}, {lon})")
            
            # Tạo point VỚI SRID
            point = Point(float(lon), float(lat), srid=SRID)
            print(f"📍 Point created with SRID {SRID}: {point}")
            
            response = {
                'success': True,
                'has_flood': False,
                'has_risk': False,
                'sources': [],
                'details': {},
                'nearby_data': [],
                'all_data': [],
                'risk_level': 'low',
                'severity': 'none',
                'message': '✅ Đang kiểm tra ngập lụt...',
                'timestamp': datetime.now().isoformat(),
                'database_stats': {
                    'total_zones': 0,
                    'total_reports': 0
                }
            }
            
            # ============ 1. THỐNG KÊ DATABASE ============
            try:
                total_zones = FloodZone.objects.filter(is_active=True).count()
                total_reports = FloodReport.objects.filter(status='verified').count()
                
                response['database_stats'] = {
                    'total_zones': total_zones,
                    'total_reports': total_reports
                }
                
                print(f"📊 Database stats: {total_zones} zones, {total_reports} reports")
                
            except Exception as e:
                print(f"⚠️ Lỗi thống kê database: {e}")
                traceback.print_exc()
            
            # ============ 2. TÌM ĐIỂM NGẬP TRONG BÁN KÍNH ============
            nearby_zones = []
            try:
                flood_zones = FloodZone.objects.annotate(
                    distance=Distance('geometry', point)
                ).filter(
                    distance__lt=radius_m,
                    is_active=True
                ).order_by('distance')
                
                zone_count = flood_zones.count()
                print(f"📍 Tìm thấy {zone_count} điểm ngập trong {radius_m}m")
                
                if flood_zones.exists():
                    response['has_flood'] = True
                    response['sources'].append('known_zone')
                    
                    for zone in flood_zones[:5]:
                        try:
                            zone_data = {
                                'type': 'zone',
                                'name': zone.name or 'Điểm ngập',
                                'zone_type': zone.zone_type or 'unknown',
                                'type_display': zone.get_zone_type_display() if hasattr(zone, 'get_zone_type_display') else zone.zone_type,
                                'max_depth': zone.max_depth_cm or 0,
                                'distance': round(zone.distance.m, 1) if hasattr(zone, 'distance') else 0,
                                'last_reported': zone.last_reported_at.strftime('%H:%M %d/%m') if zone.last_reported_at else 'Chưa có',
                                'report_count': zone.report_count or 0,
                                'cause': zone.flood_cause or 'Không xác định',
                                'district': zone.district or '',
                                'street': zone.street or ''
                            }
                            nearby_zones.append(zone_data)
                        except Exception as zone_detail_err:
                            print(f"⚠️ Lỗi chi tiết zone: {zone_detail_err}")
                    
                    if nearby_zones:
                        response['details']['zone'] = nearby_zones[0]
                        zone = flood_zones.first()
                        response['severity'] = 'high' if zone.max_depth_cm and zone.max_depth_cm > 30 else 'medium'
                        
            except Exception as e:
                print(f"⚠️ Lỗi tìm điểm ngập: {e}")
                traceback.print_exc()
            
            # ============ 3. TÌM BÁO CÁO TRONG BÁN KÍNH ============
            nearby_reports = []
            try:
                time_threshold = datetime.now() - timedelta(hours=24)
                recent_reports = FloodReport.objects.annotate(
                    distance=Distance('location', point)
                ).filter(
                    distance__lt=radius_m,
                    status='verified',
                    created_at__gte=time_threshold
                ).order_by('-created_at')
                
                report_count = recent_reports.count()
                print(f"📍 Tìm thấy {report_count} báo cáo trong 24h")
                
                if recent_reports.exists():
                    response['has_flood'] = True
                    response['sources'].append('user_report')
                    
                    for report in recent_reports[:5]:
                        try:
                            report_data = {
                                'type': 'report',
                                'id': report.id,
                                'depth': report.water_depth or 0,
                                'severity': report.severity or 'unknown',
                                'severity_display': report.get_severity_display() if hasattr(report, 'get_severity_display') else report.severity,
                                'time': report.created_at.strftime('%H:%M %d/%m'),
                                'address': report.address[:100] if report.address else 'Không có địa chỉ',
                                'distance': round(report.distance.m, 1) if hasattr(report, 'distance') else 0,
                                'reporter': report.reporter_name or 'Ẩn danh',
                                'description': report.description[:200] if report.description else '',
                                'district': report.district or '',
                                'ward': report.ward or ''
                            }
                            nearby_reports.append(report_data)
                        except Exception as report_detail_err:
                            print(f"⚠️ Lỗi chi tiết report: {report_detail_err}")
                    
                    if nearby_reports:
                        response['details']['report'] = nearby_reports[0]
                        report = recent_reports.first()
                        water_depth = report.water_depth or 0
                        if water_depth > 50:
                            response['severity'] = 'severe'
                        elif water_depth > 30:
                            response['severity'] = 'heavy'
                        elif water_depth > 15:
                            response['severity'] = 'medium'
                        else:
                            response['severity'] = 'light'
                            
            except Exception as e:
                print(f"⚠️ Lỗi tìm báo cáo: {e}")
                traceback.print_exc()
            
            # ============ 4. GỘP DỮ LIỆU GẦN ĐÓ ============
            response['nearby_data'] = nearby_zones + nearby_reports
            
            # ============ 5. TẠO THÔNG BÁO THÔNG MINH ============
            messages = []
            
            if response['has_flood']:
                if response['severity'] in ['severe', 'heavy']:
                    response['risk_level'] = 'high'
                    messages.append('🚨 KHU VỰC NÀY ĐANG CÓ NGẬP LỤT NGHIÊM TRỌNG')
                elif response['severity'] == 'medium':
                    response['risk_level'] = 'medium'
                    messages.append('⚠️ Khu vực này đang có ngập lụt')
                else:
                    response['risk_level'] = 'low'
                    messages.append('ℹ️ Khu vực này có ngập nhẹ')
            else:
                if nearby_zones or nearby_reports:
                    response['has_risk'] = True
                    response['risk_level'] = 'medium'
                    
                    if nearby_zones:
                        messages.append(f'📍 Có {len(nearby_zones)} điểm ngập trong khu vực')
                    if nearby_reports:
                        messages.append(f'📢 Có {len(nearby_reports)} báo cáo trong 24h')
                else:
                    messages.append(f'✅ Database có {total_zones} điểm ngập và {total_reports} báo cáo')
            
            response['message'] = ' | '.join(messages) if messages else 'Đã kiểm tra xong'
            
            print(f"📊 Kết quả: {response}")
            return response
            
        except Exception as e:
            print(f"❌ Lỗi check_flood_at_location: {e}")
            traceback.print_exc()
            
            return {
                'success': False,
                'has_flood': False,
                'has_risk': False,
                'error': str(e),
                'message': '❌ Lỗi kiểm tra ngập lụt',
                'timestamp': datetime.now().isoformat(),
                'database_stats': {
                    'total_zones': 0,
                    'total_reports': 0
                }
            }
    
    @staticmethod
    def get_area_flood_status(lat, lon, radius_m=2000):
        """Lấy trạng thái ngập của khu vực - SỬA LỖI SRID"""
        try:
            print(f"🌍 FloodCheckService.get_area_flood_status(radius={radius_m}m)")
            
            point = Point(float(lon), float(lat), srid=SRID)
            print(f"📍 Point with SRID {SRID}: {point}")
            
            total_zones = FloodZone.objects.filter(is_active=True).count()
            total_reports = FloodReport.objects.filter(status='verified').count()
            
            print(f"📍 Tổng trong DB: {total_zones} điểm ngập, {total_reports} báo cáo")
            
            stats = {
                'total_zones': total_zones,
                'total_reports': total_reports,
                'recent_reports': FloodReport.objects.filter(
                    created_at__gte=datetime.now() - timedelta(hours=1),
                    status='verified'
                ).count(),
                'active_zones': total_zones,
                'total_verified_reports': total_reports,
                'search_radius': radius_m
            }
            
            zones_list = []
            reports_list = []
            
            try:
                some_zones = FloodZone.objects.filter(is_active=True)[:10]
                for zone in some_zones:
                    zones_list.append({
                        'name': zone.name or 'Điểm ngập',
                        'type': zone.zone_type or 'unknown',
                        'type_display': zone.get_zone_type_display() if hasattr(zone, 'get_zone_type_display') else zone.zone_type,
                        'max_depth': zone.max_depth_cm or 0,
                        'district': zone.district or '',
                        'street': zone.street or '',
                        'is_active': zone.is_active,
                        'report_count': zone.report_count or 0
                    })
            except Exception as zone_err:
                print(f"⚠️ Lỗi lấy zones list: {zone_err}")
            
            try:
                some_reports = FloodReport.objects.filter(status='verified').order_by('-created_at')[:10]
                for report in some_reports:
                    reports_list.append({
                        'id': report.id,
                        'address': report.address[:80] + '...' if report.address and len(report.address) > 80 else (report.address or ''),
                        'water_depth': report.water_depth or 0,
                        'severity': report.severity or 'unknown',
                        'severity_display': report.get_severity_display() if hasattr(report, 'get_severity_display') else report.severity,
                        'created_at': report.created_at.strftime('%H:%M %d/%m'),
                        'district': report.district or '',
                        'ward': report.ward or '',
                        'reporter': report.reporter_name or 'Ẩn danh'
                    })
            except Exception as report_err:
                print(f"⚠️ Lỗi lấy reports list: {report_err}")
            
            messages = []
            if total_zones > 0:
                messages.append(f'Có {total_zones} điểm ngập')
            if total_reports > 0:
                messages.append(f'Có {total_reports} báo cáo')
            
            if not messages:
                messages.append('Không có dữ liệu ngập')
            
            result = {
                'success': True,
                'stats': stats,
                'risk_level': 'low',
                'risk_score': 0,
                'zones': zones_list,
                'reports': reports_list,
                'center': {'lat': lat, 'lng': lon},
                'radius': radius_m,
                'timestamp': datetime.now().isoformat(),
                'summary': ' | '.join(messages),
                'has_data': total_zones > 0 or total_reports > 0,
                'total_data_in_db': total_zones + total_reports
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Lỗi get_area_flood_status: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'stats': {},
                'risk_level': 'unknown',
                'timestamp': datetime.now().isoformat()
            }


class FloodPredictionService:
    """Service dự đoán ngập"""
    
    @staticmethod
    def get_all_predictions():
        """Lấy tất cả dự đoán"""
        try:
            predictions = FloodPrediction.objects.all().order_by('-created_at')[:50]
            return predictions
        except Exception as e:
            print(f"❌ Lỗi get_all_predictions: {e}")
            return []