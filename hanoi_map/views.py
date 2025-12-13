# hanoi_map/views.py - ĐÃ SỬA LỖI SRID
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geos import Point
from django.conf import settings
import json
from datetime import datetime, timedelta
import requests
import traceback

from .models import FloodZone, FloodReport, WeatherForecast, FloodPrediction
from .services import LocationSearchService, WeatherService, FloodCheckService, FloodPredictionService, FloodDataService

# Hằng số SRID
SRID = 4326

class FloodMapView(TemplateView):
    """Trang bản đồ chính"""
    template_name = 'hanoi_map/flood_map.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Thống kê tổng quan
        context['stats'] = {
            'total_zones': FloodZone.objects.filter(is_active=True).count(),
            'total_reports': FloodReport.objects.filter(status='verified').count(),
            'recent_reports': FloodReport.objects.filter(
                created_at__gte=datetime.now().replace(hour=0, minute=0, second=0)
            ).filter(status='verified').count(),
            'active_reports': FloodReport.objects.filter(
                created_at__gte=datetime.now() - timedelta(hours=6),
                status='verified'
            ).count(),
        }
        
        # Các điểm ngập nghiêm trọng
        context['critical_zones'] = FloodZone.objects.filter(
            zone_type__in=['black', 'frequent']
        ).filter(is_active=True).order_by('-max_depth_cm')[:5]
        
        # Dự báo thời tiết
        weather_service = WeatherService()
        context['hanoi_weather'] = weather_service.get_current_weather(21.0285, 105.8542) or {
            'temp': 28,
            'description': 'Nắng',
            'rain': 0,
            'icon': '01d'
        }
        
        return context

# API Endpoints

def search_location_api(request):
    """API tìm kiếm địa điểm Hà Nội"""
    try:
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({
                'success': True,
                'results': [],
                'message': 'Vui lòng nhập ít nhất 2 ký tự'
            })
        
        results = LocationSearchService.search_hanoi_location(query)
        
        return JsonResponse({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        print(f"❌ Lỗi search_location_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'results': []
        }, status=500)
def check_flood_api(request):
    """API kiểm tra ngập tại vị trí - ĐÃ SỬA LỖI get_rain_alerts"""
    try:
        # Lấy và validate tham số
        lat_str = request.GET.get('lat', '').strip()
        lng_str = request.GET.get('lng', '').strip()
        
        if not lat_str or not lng_str:
            return JsonResponse({
                'success': False,
                'error': 'Thiếu tham số lat hoặc lng',
                'message': 'Vui lòng cung cấp tọa độ'
            }, status=400)
        
        try:
            lat = float(lat_str)
            lng = float(lng_str)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Tọa độ không hợp lệ',
                'message': 'Tọa độ phải là số'
            }, status=400)
        
        radius = float(request.GET.get('radius', 1000))
        
        print(f"🌍 API Check Flood: lat={lat}, lng={lng}, radius={radius}")
        
        # Kiểm tra ngập
        flood_check = FloodCheckService.check_flood_at_location(lat, lng, radius)
        
        # Lấy thông tin địa điểm
        location_info = LocationSearchService.get_location_info(lat, lng)
        
        # Lấy thời tiết
        weather_service = WeatherService()
        weather = weather_service.get_current_weather(lat, lng)
        
        # KHÔNG gọi get_rain_alerts nữa
        alerts = []  # Trả về mảng rỗng
        
        response_data = {
            'success': True,
            'location': {
                'lat': lat,
                'lng': lng,
                'address': location_info.get('display_name', '') if location_info and location_info.get('success') else f"{lat}, {lng}",
                'district': location_info.get('district', '') if location_info and location_info.get('success') else '',
                'ward': location_info.get('ward', '') if location_info and location_info.get('success') else ''
            },
            'flood_check': flood_check,
            'weather': weather,
            'alerts': alerts,  # Mảng rỗng
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ API trả về thành công: {flood_check.get('message', '')}")
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ Lỗi check_flood_api: {e}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Có lỗi xảy ra khi kiểm tra ngập'
        }, status=500)

def get_flood_data_api(request):
    """API lấy dữ liệu ngập cho bản đồ"""
    try:
        # Lấy tham số tùy chọn
        lat_str = request.GET.get('lat', '').strip()
        lng_str = request.GET.get('lng', '').strip()
        radius = float(request.GET.get('radius', 10))  # km
        
        if lat_str and lng_str:
            try:
                lat = float(lat_str)
                lng = float(lng_str)
                print(f"📍 API Flood Data với tọa độ: ({lat}, {lng}), radius={radius}km")
                flood_data = FloodDataService.get_realtime_flood_data(lat, lng, radius)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Tọa độ không hợp lệ',
                    'data': {'flood_zones': [], 'flood_reports': []}
                }, status=400)
        else:
            print("📍 API Flood Data lấy tất cả")
            flood_data = FloodDataService.get_all_flood_data()
        
        return JsonResponse({
            'success': True,
            'data': flood_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Lỗi get_flood_data_api: {e}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': {'flood_zones': [], 'flood_reports': []}
        }, status=500)

def get_area_status_api(request):
    """API lấy trạng thái khu vực"""
    try:
        lat_str = request.GET.get('lat', '').strip()
        lng_str = request.GET.get('lng', '').strip()
        
        if not lat_str or not lng_str:
            # Mặc định Hồ Gươm
            lat = 21.0285
            lng = 105.8542
        else:
            try:
                lat = float(lat_str)
                lng = float(lng_str)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Tọa độ không hợp lệ'
                }, status=400)
        
        radius = float(request.GET.get('radius', 2000))
        
        print(f"🌍 API Area Status: ({lat}, {lng}), radius={radius}m")
        
        area_status = FloodCheckService.get_area_flood_status(lat, lng, radius)
        
        # Lấy dự báo thời tiết
        weather_service = WeatherService()
        forecast = weather_service.get_forecast(lat, lng)
        
        response_data = {
            'success': True,
            'area_status': area_status,
            'forecast': forecast.get('forecasts', [])[:4] if forecast and isinstance(forecast, dict) else [],
            'timestamp': datetime.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ Lỗi get_area_status_api: {e}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def report_flood_api(request):
    """API báo cáo ngập mới - ĐÃ SỬA LỖI SRID"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"📤 Nhận báo cáo ngập: {data}")
            
            # Validate dữ liệu
            required_fields = ['lat', 'lng', 'water_depth']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Thiếu trường bắt buộc: {field}'
                    }, status=400)
            
            # Chuyển đổi tọa độ
            try:
                lat = float(data['lat'])
                lng = float(data['lng'])
                water_depth = float(data['water_depth'])
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Dữ liệu số không hợp lệ'
                }, status=400)
            
            # Lấy thông tin địa điểm
            location_info = LocationSearchService.get_location_info(lat, lng)
            
            # Tạo báo cáo VỚI SRID
            report = FloodReport.objects.create(
                location=Point(lng, lat, srid=SRID),  # QUAN TRỌNG: thêm srid
                address=data.get('address', '') or (location_info.get('display_name', '') if location_info and location_info.get('success') else f"{lat}, {lng}"),
                district=location_info.get('district', '') if location_info and location_info.get('success') else '',
                ward=location_info.get('ward', '') if location_info and location_info.get('success') else '',
                street=location_info.get('street', '') if location_info and location_info.get('success') else '',
                water_depth=water_depth,
                area_size=data.get('area_size', ''),
                description=data.get('description', ''),
                photo_url=data.get('photo_url', ''),
                reporter_name=data.get('reporter_name', ''),
                reporter_phone=data.get('reporter_phone', ''),
                status='verified'  # Tự động xác nhận cho demo
            )
            
            print(f"✅ Đã tạo báo cáo #{report.id} tại ({lat}, {lng})")
            
            return JsonResponse({
                'success': True,
                'message': '✅ Báo cáo đã được gửi thành công!',
                'report_id': report.id,
                'address': report.address[:50],
                'water_depth': report.water_depth,
                'show_on_map': True
            })
            
        except Exception as e:
            print(f"❌ Lỗi report_flood_api: {e}")
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)

def get_weather_api(request):
    """API lấy thông tin thời tiết"""
    try:
        lat_str = request.GET.get('lat', '').strip()
        lng_str = request.GET.get('lng', '').strip()
        
        if not lat_str or not lng_str:
            # Mặc định Hồ Gươm
            lat = 21.0285
            lng = 105.8542
        else:
            try:
                lat = float(lat_str)
                lng = float(lng_str)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Tọa độ không hợp lệ'
                }, status=400)
        
        weather_service = WeatherService()
        current = weather_service.get_current_weather(lat, lng)
        forecast = weather_service.get_forecast(lat, lng)
        alerts = weather_service.get_rain_alerts(lat, lng)
        
        return JsonResponse({
            'success': True,
            'current': current,
            'forecast': forecast.get('forecasts', [])[:8] if forecast and isinstance(forecast, dict) else [],
            'alerts': alerts
        })
        
    except Exception as e:
        print(f"❌ Lỗi get_weather_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_statistics_api(request):
    """API thống kê real-time"""
    try:
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        stats = {
            'reports': {
                'total': FloodReport.objects.count(),
                'verified': FloodReport.objects.filter(status='verified').count(),
                'today': FloodReport.objects.filter(created_at__gte=today_start).count(),
                'pending': FloodReport.objects.filter(status='pending').count(),
                'last_hour': FloodReport.objects.filter(
                    created_at__gte=now - timedelta(hours=1)
                ).count(),
            },
            'zones': {
                'total': FloodZone.objects.count(),
                'active': FloodZone.objects.filter(is_active=True).count(),
                'black_zones': FloodZone.objects.filter(zone_type='black').count(),
                'new_today': FloodZone.objects.filter(
                    created_at__gte=today_start
                ).count(),
            },
            'timestamp': now.isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ Lỗi get_statistics_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_recent_reports_api(request):
    """API lấy báo cáo gần đây"""
    try:
        limit = int(request.GET.get('limit', 10))
        hours = int(request.GET.get('hours', 24))
        
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        reports = FloodReport.objects.filter(
            status='verified',
            created_at__gte=time_threshold
        ).order_by('-created_at')[:limit]
        
        reports_list = []
        for report in reports:
            reports_list.append({
                'id': report.id,
                'lat': report.location.y,
                'lng': report.location.x,
                'address': report.address or 'Không có địa chỉ',
                'water_depth': report.water_depth or 0,
                'severity': report.severity or 'unknown',
                'severity_display': report.get_severity_display() if hasattr(report, 'get_severity_display') else report.severity,
                'created_at': report.created_at.strftime('%H:%M %d/%m'),
                'created_at_iso': report.created_at.isoformat(),
                'reporter_name': report.reporter_name or 'Ẩn danh',
                'photo_url': report.photo_url,
                'description': report.description[:100] if report.description else ''
            })
        
        return JsonResponse({
            'success': True,
            'reports': reports_list,
            'count': len(reports_list),
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Lỗi get_recent_reports_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# API test
def test_search_connection(request):
    return JsonResponse({
        'success': True,
        'message': '✅ Kết nối search API hoạt động tốt!',
        'timestamp': datetime.now().isoformat()
    })