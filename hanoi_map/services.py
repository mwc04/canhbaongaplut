import requests
from django.conf import settings
from datetime import datetime, timedelta
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Count, Avg, Q, Max
from django.http import JsonResponse
import json
from django.utils import timezone
from datetime import timedelta
import traceback


from .models import FloodZone, FloodReport, FloodPrediction, FixedFlooding, FloodHistory
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
            print(f"❌ Lỗi tìm kiếm: {e}")
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
                'cnt': 8,  
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
                    messages.append(f'')
            
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
        """Lấy trạng thái ngập của khu vực - CHỈ TRONG BÁN KÍNH"""
        try:
            print(f"🌍 FloodCheckService.get_area_flood_status(radius={radius_m}m)")
            
            point = Point(float(lon), float(lat), srid=SRID)
            print(f"📍 Point with SRID {SRID}: {point}")
            
            # ============ 1. TÌM ĐIỂM NGẬP TRONG BÁN KÍNH ============
            zones_in_radius = []
            zones_count = 0
            avg_depth = 0
            
            try:
                zones_query = FloodZone.objects.annotate(
                    distance=Distance('geometry', point)
                ).filter(
                    distance__lt=radius_m,
                    is_active=True
                )
                zones_count = zones_query.count()
                
                # Tính độ sâu trung bình
                if zones_count > 0:
                    total_depth = 0
                    for zone in zones_query:
                        zones_in_radius.append({
                            'name': zone.name or 'Điểm ngập',
                            'type': zone.zone_type or 'unknown',
                            'type_display': zone.get_zone_type_display() if hasattr(zone, 'get_zone_type_display') else zone.zone_type,
                            'max_depth': zone.max_depth_cm or 0,
                            'district': zone.district or '',
                            'street': zone.street or '',
                            'is_active': zone.is_active,
                            'report_count': zone.report_count or 0
                        })
                        if zone.max_depth_cm:
                            total_depth += zone.max_depth_cm
                    
                    if zones_count > 0:
                        avg_depth = total_depth / zones_count
                
                print(f"📍 Tìm thấy {zones_count} điểm ngập trong bán kính {radius_m}m")
                
            except Exception as e:
                print(f"⚠️ Lỗi tìm điểm ngập: {e}")
                traceback.print_exc()
            
            # ============ 2. TÌM BÁO CÁO TRONG BÁN KÍNH ============
            reports_in_radius = []
            reports_count = 0
            recent_reports_count = 0
            
            try:
                # Báo cáo trong 24h
                time_threshold = datetime.now() - timedelta(hours=24)
                recent_time_threshold = datetime.now() - timedelta(hours=1)
                
                reports_query = FloodReport.objects.annotate(
                    distance=Distance('location', point)
                ).filter(
                    distance__lt=radius_m,
                    status='verified',
                    created_at__gte=time_threshold
                ).order_by('-created_at')
                
                reports_count = reports_query.count()
                
                # Báo cáo gần đây (1h)
                recent_reports_query = FloodReport.objects.annotate(
                    distance=Distance('location', point)
                ).filter(
                    distance__lt=radius_m,
                    status='verified',
                    created_at__gte=recent_time_threshold
                )
                recent_reports_count = recent_reports_query.count()
                
                # Lấy danh sách chi tiết
                for report in reports_query[:10]:  # Lấy 10 báo cáo mới nhất
                    reports_in_radius.append({
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
                
                print(f"📍 Tìm thấy {reports_count} báo cáo trong 24h (gần đây: {recent_reports_count})")
                
            except Exception as e:
                print(f"⚠️ Lỗi tìm báo cáo: {e}")
                traceback.print_exc()
            
            # ============ 3. TÍNH MỨC ĐỘ NGUY CƠ ============
            risk_level = 'low'
            risk_color = 'success'
            risk_text = 'THẤP'
            
            if zones_count > 3 or reports_count > 5:
                risk_level = 'high'
                risk_color = 'danger'
                risk_text = 'CAO'
            elif zones_count > 0 or reports_count > 0:
                risk_level = 'medium'
                risk_color = 'warning'
                risk_text = 'TRUNG BÌNH'
            else:
                risk_level = 'low'
                risk_color = 'success'
                risk_text = 'THẤP'
            
            # ============ 4. TẠO THỐNG KÊ ============
            stats = {
                'total_zones': zones_count,
                'total_reports': reports_count,
                'recent_reports': recent_reports_count,
                'max_depth': round(avg_depth, 1) if avg_depth > 0 else 0,
                'active_zones': zones_count,
                'search_radius': radius_m
            }
            
            # ============ 5. TẠO THÔNG BÁO ============
            messages = []
            if zones_count > 0:
                messages.append(f'Có {zones_count} điểm ngập')
            if reports_count > 0:
                messages.append(f'Có {reports_count} báo cáo trong 24h')
            
            if not messages:
                messages.append('Không có điểm ngập hoặc báo cáo nào trong khu vực này')
            
            result = {
                'success': True,
                'stats': stats,
                'risk_level': risk_level,
                'risk_color': risk_color,
                'risk_text': risk_text,
                'zones': zones_in_radius[:5],  # Chỉ lấy 5 điểm đầu
                'reports': reports_in_radius[:5],  # Chỉ lấy 5 báo cáo đầu
                'center': {'lat': lat, 'lng': lon},
                'radius': radius_m,
                'timestamp': datetime.now().isoformat(),
                'summary': ' | '.join(messages),
                'has_data': zones_count > 0 or reports_count > 0,
                'total_data_in_radius': zones_count + reports_count
            }
            
            print(f"📊 Kết quả kiểm tra khu vực: {result['summary']}")
            return result
            
        except Exception as e:
            print(f"❌ Lỗi get_area_flood_status: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'stats': {
                    'total_zones': 0,
                    'total_reports': 0,
                    'recent_reports': 0,
                    'max_depth': 0
                },
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
        

# Phần xử lý FixedFlood 

class FixedFloodingService:
    """Service xử lý FixedFlooding và tích hợp với weather API"""
    @staticmethod
    def check_and_activate_by_rainfall(lat, lng, rainfall_mm):
        """Kiểm tra và kích hoạt FixedFlooding dựa trên lượng mưa"""
        try:
            print(f"⚡ FixedFloodingService: Kiểm tra mưa={rainfall_mm}mm/h tại ({lat}, {lng})")
            point = Point(lng, lat, srid=SRID)
            activated_floodings = []
            floodings = FixedFlooding.objects.annotate(
                distance=Distance('location', point)
            ).filter(
                distance__lt=10000,  # 10km
                is_monitored=True
            )
            
            for flooding in floodings:
                try:
                    result = flooding.activate_flood_warning(rainfall_mm, "WeatherService")
                    if result is True:  
                        activated_floodings.append(flooding)
                        FloodZoneService.create_or_update_from_fixed_flooding(flooding, rainfall_mm)
                        FloodHistoryService.create_from_fixed_flooding(flooding, rainfall_mm) 
                        print(f"✅ Đã kích hoạt: {flooding.name}")
                except Exception as e:
                    print(f"❌ Lỗi kích hoạt FixedFlooding {flooding.id}: {e}")
                    traceback.print_exc()
            
            print(f"📊 Tổng: {len(activated_floodings)} FixedFlooding được kích hoạt")
            return activated_floodings
            
        except Exception as e:
            print(f"❌ Lỗi check_and_activate_by_rainfall: {e}")
            traceback.print_exc()
            return []
    @staticmethod
    def get_nearby_floodings(lat, lng, radius_m=5000, only_active=False):
        """Lấy FixedFlooding trong bán kính"""
        try:
            point = Point(lng, lat, srid=SRID)
            
            query = FixedFlooding.objects.annotate(
                distance=Distance('location', point)
            ).filter(
                distance__lt=radius_m
            ).order_by('distance')
            
            if only_active:
                query = query.filter(is_active=True)
                
            return query
            
        except Exception as e:
            print(f"❌ Lỗi get_nearby_floodings: {e}")
            return FixedFlooding.objects.none()
    @staticmethod
    def get_active_alerts(lat, lng):
        """Lấy cảnh báo từ FixedFlooding đang kích hoạt"""
        try:
            point = Point(lng, lat, srid=SRID)
            active_floodings = FixedFlooding.objects.annotate(
                distance=Distance('location', point)
            ).filter(
                distance__lt=5000,
                is_active=True
            ).order_by('-severity')
            
            alerts = []
            for flooding in active_floodings:
                # Tính khoảng cách
                distance_km = round(flooding.distance.m / 1000, 1) if hasattr(flooding, 'distance') else 0
                
                # Xác định mức độ cảnh báo
                if flooding.predicted_depth_cm >= 50:
                    alert_level = 'danger'
                    icon = 'fa-exclamation-triangle'
                    prefix = '🚨 CẢNH BÁO NGUY HIỂM: '
                elif flooding.predicted_depth_cm >= 30:
                    alert_level = 'warning'
                    icon = 'fa-exclamation-circle'
                    prefix = '⚠️ CẢNH BÁO: '
                else:
                    alert_level = 'info'
                    icon = 'fa-info-circle'
                    prefix = 'ℹ️ THÔNG BÁO: '
                
                alerts.append({
                    'level': alert_level,
                    'icon': icon,
                    'title': f"{prefix}{flooding.name}",
                    'message': f"Khu vực này đang có ngập dự báo {flooding.predicted_depth_cm}cm.",
                    'distance': distance_km,
                    'details': {
                        'location': flooding.address,
                        'predicted_depth': flooding.predicted_depth_cm,
                        'flood_type': flooding.get_flood_type_display() if hasattr(flooding, 'get_flood_type_display') else flooding.flood_type,
                        'recommendations': flooding.recommendations
                    },
                    'timestamp': datetime.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            print(f"❌ Lỗi get_active_alerts: {e}")
            return []
    
    @staticmethod
    def trigger_manual_activation(flooding_id, rainfall_mm):
        """Kích hoạt thủ công FixedFlooding (dùng để test)"""
        try:
            flooding = FixedFlooding.objects.get(id=flooding_id)
            
            # Kích hoạt cảnh báo
            result = flooding.activate_flood_warning(rainfall_mm, "ManualService")
            
            if result:
                # Tạo FloodZone và lịch sử
                zone = FloodZoneService.create_or_update_from_fixed_flooding(flooding, rainfall_mm)
                history = FloodHistoryService.create_from_fixed_flooding(flooding, rainfall_mm)
                
                return {
                    'success': True,
                    'flooding': flooding,
                    'zone_created': zone is not None,
                    'history_created': history is not None
                }
            else:
                return {
                    'success': False,
                    'message': f'Lượng mưa {rainfall_mm}mm/h chưa đạt ngưỡng {flooding.rainfall_threshold_mm}mm/h'
                }
                
        except FixedFlooding.DoesNotExist:
            return {'success': False, 'error': 'Không tìm thấy FixedFlooding'}
        except Exception as e:
            print(f"❌ Lỗi trigger_manual_activation: {e}")
            return {'success': False, 'error': str(e)}


class FloodZoneService:
    """Service xử lý FloodZone từ FixedFlooding"""
    
    @staticmethod
    def create_or_update_from_fixed_flooding(fixed_flooding, rainfall_mm):
        """Tạo hoặc cập nhật FloodZone từ FixedFlooding"""
        try:
            existing_zone = fixed_flooding.flood_zone
            
            if existing_zone:
                # Cập nhật FloodZone hiện có
                existing_zone.is_active = True
                existing_zone.max_depth_cm = max(existing_zone.max_depth_cm, fixed_flooding.predicted_depth_cm)
                existing_zone.last_reported_at = timezone.now()
                existing_zone.last_flood_date = timezone.now().date()
                existing_zone.flood_cause = f"Mưa lớn: {rainfall_mm}mm/h (Tự động từ FixedFlooding)"
                existing_zone.save()
                print(f"🔄 Đã cập nhật FloodZone #{existing_zone.id}")
                return existing_zone
                
            else:
                # Tạo FloodZone mới
                flood_polygon = fixed_flooding.get_flood_polygon()
                
                zone_name = f"[Tự động] {fixed_flooding.name}"
                
                new_zone = FloodZone.objects.create(
                    name=zone_name,
                    zone_type='rain',
                    geometry=flood_polygon,
                    district=fixed_flooding.district,
                    ward=fixed_flooding.ward or '',
                    street=fixed_flooding.address,
                    max_depth_cm=fixed_flooding.predicted_depth_cm,
                    avg_duration_hours=fixed_flooding.duration_hours,
                    flood_cause=f"Mưa lớn: {rainfall_mm}mm/h (Tự động kích hoạt)",
                    is_active=True,
                    last_reported_at=timezone.now(),
                    last_flood_date=timezone.now().date(),
                    description=f"Tự động tạo từ FixedFlooding '{fixed_flooding.name}'. Ngưỡng mưa: {fixed_flooding.rainfall_threshold_mm}mm/h. Lượng mưa: {rainfall_mm}mm/h",
                    solution=fixed_flooding.recommendations or "Di chuyển phương tiện đến nơi cao, tránh đi qua khu vực ngập."
                )
                
                # Liên kết FixedFlooding với FloodZone mới
                fixed_flooding.flood_zone = new_zone
                fixed_flooding.save(update_fields=['flood_zone'])
                
                print(f"✅ Đã tạo FloodZone #{new_zone.id}")
                return new_zone
                
        except Exception as e:
            print(f"❌ Lỗi create_or_update_from_fixed_flooding: {e}")
            traceback.print_exc()
            return None


class FloodHistoryService:
    """Service xử lý lịch sử ngập"""
    
    @staticmethod
    def create_from_fixed_flooding(fixed_flooding, rainfall_mm):
        """Ghi lịch sử ngập từ FixedFlooding"""
        try:
            flood_zone = fixed_flooding.flood_zone
            
            if not flood_zone:
                print(f"⚠️ FixedFlooding {fixed_flooding.id} không có FloodZone")
                return None

            history = FloodHistory.objects.create(
                location=fixed_flooding.location,
                address=fixed_flooding.address,
                district=fixed_flooding.district,
                flood_type=fixed_flooding.flood_type,
                rainfall_mm=rainfall_mm,
                water_depth_cm=fixed_flooding.predicted_depth_cm,
                duration_minutes=int(fixed_flooding.duration_hours * 60),
                start_time=timezone.now(),
                timestamp=timezone.now(),
                source='fixed',
                source_id=f"fixed_{fixed_flooding.id}",
                related_zone=flood_zone,
                description=f"Tự động kích hoạt từ FixedFlooding '{fixed_flooding.name}'. Mưa: {rainfall_mm}mm/h (Ngưỡng: {fixed_flooding.rainfall_threshold_mm}mm/h)",
                impact_level='major' if fixed_flooding.predicted_depth_cm > 30 else 'moderate'
            )
            
            print(f"📝 Đã ghi lịch sử #{history.id}")
            return history
            
        except Exception as e:
            print(f"❌ Lỗi create_from_fixed_flooding: {e}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def create_from_report(flood_report):
        """Ghi lịch sử từ báo cáo ngập"""
        try:
            history = FloodHistory.objects.create(
                location=flood_report.location,
                address=flood_report.address,
                district=flood_report.district,
                flood_type='user_report',
                rainfall_mm=None,
                water_depth_cm=flood_report.water_depth,
                duration_minutes=60,  # Mặc định 1 giờ
                start_time=flood_report.created_at,
                timestamp=timezone.now(),
                source='report',
                source_id=f"report_{flood_report.id}",
                related_zone=flood_report.flood_zone,
                related_report=flood_report,
                description=f"Báo cáo từ người dùng: {flood_report.description[:200] if flood_report.description else 'Không có mô tả'}",
                impact_level='major' if flood_report.water_depth > 50 else 'moderate' if flood_report.water_depth > 20 else 'minor'
            )
            
            return history
            
        except Exception as e:
            print(f"❌ Lỗi create_from_report: {e}")
            return None
# ============ DRAINAGE PREDICTION SERVICE ============

class DrainageTimeService:
    """
    Service dự đoán thời gian cạn nước
    """
    
    @staticmethod
    def predict_drainage_time(flood_report):
        """Dự đoán thời gian cạn nước cho một FloodReport - PHIÊN BẢN CHÍNH"""
        try:
            print(f"⏳ [PREDICT] Bắt đầu dự đoán cho FloodReport #{flood_report.id}")
            
            data = DrainageTimeService._collect_prediction_data(flood_report)
            drainage_hours = DrainageTimeService._calculate_drainage_hours(data)
            print(f"📊 [PREDICT] Thời gian cạn tính được: {drainage_hours} giờ")
            result = DrainageTimeService._create_prediction_result(
                flood_report, data, drainage_hours
            )
            prediction_saved = DrainageTimeService._save_prediction_to_db(flood_report, result)
            
            if prediction_saved:
                result['prediction_saved'] = True
                result['prediction_id'] = prediction_saved.id if hasattr(prediction_saved, 'id') else None
                print(f"✅ [PREDICT] ĐÃ LƯU THÀNH CÔNG vào database")
            else:
                result['prediction_saved'] = False
                print(f"⚠️ [PREDICT] KHÔNG THỂ LƯU vào database")
            
            result['success'] = True
            return result
            
        except Exception as e:
            print(f"❌ [PREDICT] Lỗi trong predict_drainage_time: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'estimated_drainage_time_hours': 0,
                'message': 'Không thể dự đoán thời gian cạn',
                'prediction_saved': False
            }
    
    @staticmethod
    def _collect_prediction_data(flood_report):
        """Thu thập dữ liệu cần thiết (private)"""
        from django.utils import timezone
        
        return {
            'water_depth_cm': flood_report.water_depth,
            'flood_type': getattr(flood_report, 'flood_type', 'rain'),
            'location': flood_report.location,
            'timestamp': flood_report.created_at or timezone.now(),
            'terrain': DrainageTimeService._get_terrain_info(
                flood_report.location.y if flood_report.location else None,
                flood_report.location.x if flood_report.location else None
            ),
            'weather': DrainageTimeService._get_weather_info(
                flood_report.location.y if flood_report.location else None,
                flood_report.location.x if flood_report.location else None
            ),
            'current_time': timezone.now()
        }
    
    @staticmethod
    def _get_terrain_info(lat, lng):
        """Lấy thông tin địa hình (private)"""
        # Giả lập dữ liệu
        return {
            'elevation': 3.5,
            'drainage_capacity': 'average',
            'distance_to_river': 350,
            'slope_percentage': 2.1,
            'soil_type': 'clay',
            'urban_density': 'high'
        }
    
    @staticmethod
    def _get_weather_info(lat, lng):
        """Lấy thông tin thời tiết (private)"""
        try:
            weather_service = WeatherService()
            current_weather = weather_service.get_current_weather(lat, lng)
            
            if current_weather:
                return {
                    'current_rainfall_mm': current_weather.get('rain', 0),
                    'rainfall_last_3h': current_weather.get('rain', 0) * 3,
                    'temperature': current_weather.get('temp', 28),
                    'humidity': current_weather.get('humidity', 75),
                    'wind_speed': current_weather.get('wind_speed', 2.5)
                }
        except Exception as e:
            print(f"⚠️ Không thể lấy thông tin thời tiết: {e}")
        return {
            'current_rainfall_mm': 8.5,
            'rainfall_last_3h': 25.3,
            'temperature': 29.2,
            'humidity': 82,
            'wind_speed': 12.5
        }
    
    @staticmethod
    def _calculate_drainage_hours(data):
        """Tính toán thời gian cạn nước (private)"""
        try:
            water_depth = float(data.get('water_depth_cm', 0))
            
            if water_depth <= 0:
                return 0.5
            
            terrain = data.get('terrain', {})
            weather = data.get('weather', {})
            
            # Tốc độ thoát nước cơ bản
            base_rates = {
                'very_poor': 0.5,
                'poor': 1.0,
                'average': 2.0,
                'good': 3.5,
                'excellent': 5.0
            }
            
            drainage_capacity = terrain.get('drainage_capacity', 'average')
            base_rate = base_rates.get(drainage_capacity, 1.5)
            current_rainfall = float(weather.get('current_rainfall_mm', 0))
            rain_factor = 1.0
            if current_rainfall > 30:
                rain_factor = 0.3
            elif current_rainfall > 20:
                rain_factor = 0.5
            elif current_rainfall > 10:
                rain_factor = 0.7
            elif current_rainfall > 5:
                rain_factor = 0.9
            
            elevation = float(terrain.get('elevation', 0))
            elevation_factor = 1.0 + (elevation / 50) * 0.1 if elevation > 0 else 1.0
            effective_rate = base_rate * elevation_factor * rain_factor
            effective_rate = max(effective_rate, 0.1)
            effective_rate = min(effective_rate, 10.0)
            drainage_hours = water_depth / effective_rate
            drainage_hours = round(drainage_hours, 1)
            drainage_hours = min(drainage_hours, 72)   # Tối đa 3 ngày
            drainage_hours = max(drainage_hours, 0.5)  # Tối thiểu 30 phút
            
            return drainage_hours
            
        except Exception as e:
            print(f"❌ Lỗi tính toán: {e}")
            return 6.0
    
    @staticmethod
    def _create_prediction_result(flood_report, data, drainage_hours):
        """Tạo kết quả dự đoán (private)"""
        completion_time = timezone.now() + timedelta(hours=drainage_hours)
        if drainage_hours <= 2:
            level = 'fast'
            level_text = 'Nhanh'
            icon = '⚡'
        elif drainage_hours <= 6:
            level = 'medium'
            level_text = 'Trung bình'
            icon = '⏱️'
        elif drainage_hours <= 12:
            level = 'slow'
            level_text = 'Chậm'
            icon = '🐌'
        else:
            level = 'very_slow'
            level_text = 'Rất chậm'
            icon = '🚧'
        if drainage_hours >= 24:
            message = f"{icon} Mực nước dự kiến sẽ rút sau khoảng {drainage_hours} giờ ({drainage_hours/24:.1f} ngày)"
        else:
            message = f"{icon} Mực nước dự kiến sẽ rút sau khoảng {drainage_hours} giờ"
        recommendations = [
            "Theo dõi tình hình thời tiết",
            "Hạn chế di chuyển qua khu vực ngập",
            "Kiểm tra phương tiện trước khi sử dụng"
        ]
        
        # Tạo factors_considered
        factors_considered = [
            f"Độ sâu nước: {data.get('water_depth_cm', 0)}cm",
            f"Khả năng thoát nước: {data['terrain'].get('drainage_capacity', 'Không xác định')}",
            f"Lượng mưa hiện tại: {data['weather'].get('current_rainfall_mm', 0)}mm/h"
        ]
        
        return {
            'flood_report_id': flood_report.id if hasattr(flood_report, 'id') else None,
            'water_depth_cm': data.get('water_depth_cm', 0),
            'estimated_drainage_time_hours': drainage_hours,
            'estimated_completion_time': completion_time,
            'completion_time_formatted': completion_time.strftime("%H:%M %d/%m/%Y"),
            'drainage_level': level,
            'drainage_level_text': level_text,
            'message': message,
            'recommendations': recommendations,
            'factors_considered': factors_considered,
            'calculation_time': timezone.now().isoformat()
        }
    
    @staticmethod
    def _save_prediction_to_db(flood_report, result):
        """Lưu dự đoán vào database (private) - PHIÊN BẢN ĐƠN GIẢN"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            from .models import FloodPrediction
            
            print(f"💾 [SAVE] Đang lưu dự đoán cho FloodReport #{flood_report.id}")
            
            # Tạo prediction đơn giản
            prediction = FloodPrediction.objects.create(
                location=flood_report.location,
                address=getattr(flood_report, 'address', 'Không xác định')[:200],
                district=getattr(flood_report, 'district', '')[:100],
                prediction_time=timezone.now(),
                predicted_depth_cm=getattr(flood_report, 'water_depth', 0),
                current_depth_cm=getattr(flood_report, 'water_depth', 0),
                estimated_drainage_time_hours=result.get('estimated_drainage_time_hours', 0),
                drainage_start_time=timezone.now(),
                last_depth_update=timezone.now(),
                risk_level='high' if result.get('estimated_drainage_time_hours', 0) > 24 else 'medium' if result.get('estimated_drainage_time_hours', 0) > 6 else 'low',
                is_active=True,
                confidence=70.0,
                rainfall_mm=0,
                flood_report=flood_report  # QUAN TRỌNG: Liên kết với flood_report
            )
            
            print(f"✅ [SAVE] ĐÃ LƯU THÀNH CÔNG FloodPrediction #{prediction.id}")
            print(f"   • ID: {prediction.id}")
            print(f"   • Address: {prediction.address}")
            print(f"   • Drainage hours: {prediction.estimated_drainage_time_hours}")
            print(f"   • FloodReport ID: {prediction.flood_report.id}")
            
            return prediction
            
        except Exception as e:
            print(f"❌ [SAVE] Lỗi lưu vào database: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_active_drainage_predictions(limit=20):
        """
        Lấy danh sách các dự đoán cạn nước đang hoạt động
        """
        try:
            from .models import FloodPrediction
            
            predictions = FloodPrediction.objects.filter(
                is_active=True
            ).order_by('-prediction_time')[:limit]
            
            results = []
            for pred in predictions:
                results.append({
                    'id': pred.id,
                    'address': pred.address or "Không xác định",
                    'district': pred.district or "",
                    'current_depth': pred.current_depth_cm or pred.predicted_depth_cm,
                    'estimated_hours': pred.estimated_drainage_time_hours or 0,
                    'risk_level': pred.risk_level or 'medium',
                    'report_id': pred.flood_report.id if pred.flood_report else None
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Lỗi get_active_drainage_predictions: {e}")
            return []
    
    @staticmethod
    def get_drainage_dashboard_data():
        """
        Lấy dữ liệu cho dashboard dự đoán cạn nước
        """
        try:
            # Lấy các predictions đang hoạt động
            active_predictions = DrainageTimeService.get_active_drainage_predictions(limit=50)
            
            # Thống kê
            total_active = len(active_predictions)
            
            # Phân loại theo thời gian còn lại
            fast_drainage = [p for p in active_predictions if p.get('estimated_hours', 0) <= 2]
            medium_drainage = [p for p in active_predictions if 2 < p.get('estimated_hours', 0) <= 6]
            slow_drainage = [p for p in active_predictions if p.get('estimated_hours', 0) > 6]
            
            # Phân loại theo quận
            districts = {}
            for pred in active_predictions:
                district = pred.get('district', 'Không xác định')
                if district not in districts:
                    districts[district] = 0
                districts[district] += 1
            
            dashboard_data = {
                'summary': {
                    'total_active_predictions': total_active,
                    'fast_drainage_count': len(fast_drainage),
                    'medium_drainage_count': len(medium_drainage),
                    'slow_drainage_count': len(slow_drainage),
                    'districts': districts
                },
                'soonest_completions': active_predictions[:5],  # Lấy 5 cái mới nhất
                'last_updated': timezone.now().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            print(f"❌ Lỗi get_drainage_dashboard_data: {e}")
            return {
                'summary': {
                    'total_active_predictions': 0,
                    'fast_drainage_count': 0,
                    'medium_drainage_count': 0,
                    'slow_drainage_count': 0,
                    'districts': {}
                },
                'soonest_completions': [],
                'last_updated': timezone.now().isoformat()
            }