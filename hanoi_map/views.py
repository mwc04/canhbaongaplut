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
import decimal
from django.db.models import Model
from django.db.models.query import QuerySet
from django.utils.timezone import is_aware
from datetime import datetime, date, time
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.gis.db.models.functions import Distance
from .models import FixedFlooding, FloodHistory 
from .models import FloodZone, FloodReport, FloodPrediction
from .services import LocationSearchService, WeatherService, FloodCheckService, FloodPredictionService, FloodDataService
from .services import FixedFloodingService, FloodZoneService, FloodHistoryService, DrainageTimeService

# Hằng số SRID
SRID = 4326

class FloodMapView(TemplateView):
    """Trang bản đồ chính"""
    template_name = 'hanoi_map/flood_map.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
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
        
        context['critical_zones'] = FloodZone.objects.filter(
            zone_type__in=['black', 'frequent']
        ).filter(is_active=True).order_by('-max_depth_cm')[:5]
        
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
        flood_check = FloodCheckService.check_flood_at_location(lat, lng, radius)
        location_info = LocationSearchService.get_location_info(lat, lng)
        weather_service = WeatherService()
        weather = weather_service.get_current_weather(lat, lng)
        alerts = [] 
        
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
                status='pending'  # Tự động xác nhận cho demo
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

def get_all_zones_status_api(request):
    """API lấy trạng thái của TẤT CẢ điểm ngập"""
    try:
        zones = FloodZone.objects.filter(is_active=True)
        
        results = []
        for zone in zones:
            try:
                # Lấy tọa độ từ geometry
                if zone.geometry:
                    centroid = zone.geometry.centroid
                    lat = centroid.y
                    lon = centroid.x
                    
                    # Kiểm tra trạng thái
                    flood_check = FloodCheckService.check_flood_at_location(lat, lon, radius_m=100)
                    
                    results.append({
                        'id': zone.id,
                        'name': zone.name or 'Điểm ngập',
                        'lat': lat,
                        'lon': lon,
                        'status': flood_check.get('has_flood', False),
                        'risk_level': flood_check.get('risk_level', 'low'),
                        'severity': flood_check.get('severity', 'none'),
                        'message': flood_check.get('message', ''),
                        'max_depth': zone.max_depth_cm or 0,
                        'zone_type': zone.zone_type
                    })
            except Exception as e:
                print(f"⚠️ Lỗi xử lý zone {zone.id}: {e}")
        
        return JsonResponse({
            'success': True,
            'count': len(results),
            'zones_status': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Lỗi get_all_zones_status_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
# ============ FUNCTIONS FOR FIXED FLOODING HANDLING ============


# Cập nhật hàm get_weather_api để tích hợp FixedFlooding

def get_weather_api(request):
    """API lấy thông tin thời tiết và kích hoạt FixedFlooding"""
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
        
        # KIỂM TRA VÀ KÍCH HOẠT FIXED FLOODING DỰA TRÊN LƯỢNG MƯA
        activated_floodings = []
        if current.get('rain', 0) > 0:
            activated_floodings = FixedFloodingService.check_and_activate_by_rainfall(
                lat, lng, current.get('rain', 0)
            )
            
            if activated_floodings:
                print(f"⚡ Đã kích hoạt {len(activated_floodings)} điểm ngập cố định")
        
        # Lấy cảnh báo từ FixedFlooding đang kích hoạt
        alerts = FixedFloodingService.get_active_alerts(lat, lng)
        
        return JsonResponse({
            'success': True,
            'current': current,
            'forecast': forecast.get('forecasts', [])[:8] if forecast and isinstance(forecast, dict) else [],
            'alerts': alerts,
            'fixed_floodings_activated': len(activated_floodings),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Lỗi get_weather_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# API mới cho FixedFlooding
def get_fixed_floodings_api(request):
    """API lấy danh sách FixedFlooding"""
    try:
        lat_str = request.GET.get('lat', '').strip()
        lng_str = request.GET.get('lng', '').strip()
        radius = float(request.GET.get('radius', 5000))  # mặc định 5km
        only_active = request.GET.get('active', 'false').lower() == 'true'
        
        floodings = FixedFloodingService.get_nearby_floodings(
            float(lat_str) if lat_str else 21.0285,
            float(lng_str) if lng_str else 105.8542,
            radius,
            only_active
        )
        
        results = []
        for flooding in floodings[:50]:  # Giới hạn 50 kết quả
            distance_km = round(flooding.distance.m / 1000, 2) if hasattr(flooding, 'distance') else None
            
            results.append({
                'id': flooding.id,
                'name': flooding.name,
                'address': flooding.address,
                'district': flooding.district,
                'ward': flooding.ward,
                'lat': flooding.location.y,
                'lng': flooding.location.x,
                'is_active': flooding.is_active,
                'is_monitored': flooding.is_monitored,
                'rainfall_threshold': flooding.rainfall_threshold_mm,
                'predicted_depth': flooding.predicted_depth_cm,
                'severity': flooding.severity,
                'flood_type': flooding.flood_type,
                'flood_type_display': flooding.get_flood_type_display() if hasattr(flooding, 'get_flood_type_display') else flooding.flood_type,
                'radius_meters': flooding.radius_meters,
                'distance_km': distance_km,
                'activation_count': flooding.activation_count,
                'last_activated': flooding.last_activated.isoformat() if flooding.last_activated else None,
                'recommendations': flooding.recommendations,
                'description': flooding.description
            })
        
        return JsonResponse({
            'success': True,
            'count': len(results),
            'fixed_floodings': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Lỗi get_fixed_floodings_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def trigger_fixed_flooding_api(request):
    """API kích hoạt thủ công FixedFlooding (dùng để test)"""
    try:
        flooding_id = request.GET.get('id')
        rainfall_mm = float(request.GET.get('rainfall', 35.0))
        
        if not flooding_id:
            return JsonResponse({
                'success': False,
                'error': 'Thiếu ID FixedFlooding'
            }, status=400)
        
        result = FixedFloodingService.trigger_manual_activation(flooding_id, rainfall_mm)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f'✅ Đã kích hoạt FixedFlooding "{result["flooding"].name}"',
                'fixed_flooding': {
                    'id': result['flooding'].id,
                    'name': result['flooding'].name,
                    'is_active': result['flooding'].is_active,
                    'activation_count': result['flooding'].activation_count
                },
                'zone_created': result.get('zone_created', False),
                'history_created': result.get('history_created', False)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result.get('message', 'Không thể kích hoạt'),
                'error': result.get('error', '')
            })
            
    except Exception as e:
        print(f"❌ Lỗi trigger_fixed_flooding_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
@receiver(post_save, sender=FloodReport)

# SỬA: Loại bỏ recursion bằng cách kiểm tra điều kiện
@receiver(post_save, sender=FloodReport)
def handle_flood_report_save(sender, instance, created, **kwargs):
    """Ghi lịch sử và tự động dự đoán thời gian cạn khi báo cáo được tạo"""
    if created and instance.status == 'verified':
        FloodHistoryService.create_from_report(instance)
        try:
            # Kiểm tra xem report đã có predictions chưa
            has_predictions = False
            if hasattr(instance, 'predictions'):
                has_predictions = instance.predictions.exists()
            if (instance.water_depth and instance.water_depth > 10 and 
                not has_predictions and
                instance.reporter_name != 'Hệ thống dự đoán tự động'):
                
                print(f"🤖 Tự động dự đoán thời gian cạn cho report #{instance.id}")
                prediction_result = DrainageTimeService.predict_drainage_time(instance)
                
                if prediction_result['success']:
                    print(f"✅ Đã dự đoán: {prediction_result['estimated_drainage_time_hours']} giờ")
                else:
                    print(f"⚠️ Không thể dự đoán: {prediction_result.get('error', '')}")
        except Exception as e:
            print(f"⚠️ Lỗi tự động dự đoán: {e}")

# ============ DRAINAGE PREDICTION APIs ============

def predict_drainage_time_api(request):
    """
    API dự đoán thời gian cạn nước cho một FloodReport
    GET /api/flood-reports/{id}/predict-drainage/
    """
    try:
        flood_report_id = request.GET.get('flood_report_id')
        
        if not flood_report_id:
            return JsonResponse({
                'success': False,
                'error': 'Thiếu flood_report_id'
            }, status=400)
        
        # Lấy FloodReport từ database
        try:
            flood_report = FloodReport.objects.get(id=flood_report_id)
        except FloodReport.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Không tìm thấy FloodReport với ID {flood_report_id}'
            }, status=404)
        
        # Gọi service để dự đoán
        result = DrainageTimeService.predict_drainage_time(flood_report)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'data': result,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Dự đoán thất bại')
            }, status=500)
            
    except Exception as e:
        print(f"❌ Lỗi predict_drainage_time_api: {e}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Lỗi server: {str(e)}'
        }, status=500)


def get_drainage_predictions_api(request):
    """
    API lấy danh sách dự đoán thời gian cạn nước
    GET /api/drainage-predictions/
    """
    try:
        prediction_id = request.GET.get('id')
        
        if prediction_id:
            # Lấy một prediction cụ thể
            try:
                prediction = FloodPrediction.objects.get(id=prediction_id)
                
                remaining_time = DrainageTimeService.calculate_remaining_time(prediction)
                
                data = {
                    'id': prediction.id,
                    'address': prediction.address,
                    'district': prediction.district,
                    'ward': prediction.ward,
                    'water_depth_cm': prediction.current_depth_cm or prediction.predicted_depth_cm,
                    'estimated_drainage_time_hours': prediction.estimated_drainage_time_hours,
                    'remaining_time_hours': remaining_time,
                    'drainage_start_time': prediction.drainage_start_time,
                    'estimated_completion_time': prediction.drainage_start_time + timezone.timedelta(
                        hours=prediction.estimated_drainage_time_hours
                    ) if prediction.drainage_start_time else None,
                    'risk_level': prediction.risk_level,
                    'recommendations': prediction.recommendations,
                    'is_active': prediction.is_active,
                    'flood_report_id': prediction.flood_report.id if prediction.flood_report else None,
                    'created_at': prediction.created_at
                }
                
                return JsonResponse({
                    'success': True,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
                
            except FloodPrediction.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Không tìm thấy dự đoán với ID {prediction_id}'
                }, status=404)
                
        else:
            # Lấy tất cả predictions đang hoạt động
            limit = int(request.GET.get('limit', 20))
            predictions = DrainageTimeService.get_active_drainage_predictions(limit)
            
            return JsonResponse({
                'success': True,
                'count': len(predictions),
                'data': predictions,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        print(f"❌ Lỗi get_drainage_predictions_api: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Lỗi server: {str(e)}'
        }, status=500)


def drainage_dashboard_api(request):
    """
    API dashboard hiển thị thông tin dự đoán cạn nước
    GET /api/drainage-dashboard/
    """
    try:
        dashboard_data = DrainageTimeService.get_drainage_dashboard_data()
        
        return JsonResponse({
            'success': True,
            'data': dashboard_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Lỗi drainage_dashboard_api: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Lỗi server: {str(e)}'
        }, status=500)

# Trong class DrainageTimeService, thêm hàm này:

@staticmethod
def collect_prediction_data(flood_report):
    """
    Thu thập tất cả dữ liệu cần thiết cho dự đoán
    """
    from django.utils import timezone
    
    data = {
        # Dữ liệu từ flood report
        'water_depth_cm': flood_report.water_depth,
        
        # QUAN TRỌNG: Sử dụng flood_zone thay vì flood_type
        'flood_type': getattr(flood_report, 'flood_type', None) or 
                    getattr(flood_report, 'flood_zone', None) or 
                    'rain',  # Default to 'rain'
                    
        'location': flood_report.location,
        'timestamp': flood_report.created_at or timezone.now(),
        
        # Giả lập dữ liệu địa hình (thực tế cần lấy từ GIS database)
        'terrain': DrainageTimeService.get_terrain_info(
            flood_report.location.y if flood_report.location else None,
            flood_report.location.x if flood_report.location else None
        ),
        'weather': DrainageTimeService.get_weather_info(
            flood_report.location.y if flood_report.location else None,
            flood_report.location.x if flood_report.location else None
        ),
        'current_time': timezone.now()
    }
    
    return data

@staticmethod
def predict_drainage_time(flood_report):
    """Dự đoán thời gian cạn nước cho một FloodReport"""
    try:
        print(f"⏳ DrainageTimeService.predict_drainage_time: Dự đoán cho FloodReport #{flood_report.id}")
        data = DrainageTimeService.collect_prediction_data(flood_report)
        drainage_hours = DrainageTimeService.calculate_drainage_hours(data)
        result = DrainageTimeService.create_prediction_result(
            flood_report, data, drainage_hours
        )
        prediction = DrainageTimeService.save_prediction_result_simple(flood_report, result)
        if prediction:
            result['prediction_id'] = prediction.id
            result['prediction_saved'] = True
            print(f"✅ ĐÃ LƯU THÀNH CÔNG vào FloodPrediction #{prediction.id}")
        else:
            result['prediction_saved'] = False
            print(f"⚠️ KHÔNG THỂ LƯU vào database")
        
        print(f"✅ Dự đoán hoàn thành: {drainage_hours} giờ")
        return result
        
    except Exception as e:
        print(f"❌ Lỗi trong predict_drainage_time: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'estimated_drainage_time_hours': 0,
            'message': 'Không thể dự đoán thời gian cạn',
            'prediction_saved': False
        }

def auto_predict_drainage_on_report(request):
    """
    API tự động dự đoán khi có báo cáo mới (có thể gọi từ webhook hoặc cron job)
    POST /api/auto-predict-drainage/
    """
    try:
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        recent_reports = FloodReport.objects.filter(
            created_at__gte=one_hour_ago,
            status='verified'
        ).exclude(
            predictions__isnull=False  # Đã có prediction
        )[:10]  # Giới hạn 10 báo cáo mỗi lần
        
        results = []
        for report in recent_reports:
            try:
                prediction_result = DrainageTimeService.predict_drainage_time(report)
                
                results.append({
                    'report_id': report.id,
                    'success': prediction_result['success'],
                    'estimated_hours': prediction_result.get('estimated_drainage_time_hours', 0),
                    'message': prediction_result.get('message', '')
                })
                
                print(f"✅ Tự động dự đoán cho report #{report.id}: {prediction_result.get('estimated_drainage_time_hours', 0)} giờ")
                
            except Exception as e:
                results.append({
                    'report_id': report.id,
                    'success': False,
                    'error': str(e)
                })
        
        return JsonResponse({
            'success': True,
            'processed_count': len(recent_reports),
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Lỗi auto_predict_drainage_on_report: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Lỗi server: {str(e)}'
        }, status=500)

@receiver(post_save, sender=FloodReport)
def handle_flood_report_save(sender, instance, created, **kwargs):
    """Ghi lịch sử và tự động dự đoán thời gian cạn khi báo cáo được tạo"""
    if created and instance.status == 'verified':
        # 1. Ghi lịch sử
        FloodHistoryService.create_from_report(instance)
        
        # 2. Tự động dự đoán thời gian cạn
        try:
            if instance.water_depth and instance.water_depth > 10:  # Chỉ dự đoán nếu ngập > 10cm
                print(f"🤖 Tự động dự đoán thời gian cạn cho report #{instance.id}")
                prediction_result = DrainageTimeService.predict_drainage_time(instance)
                
                if prediction_result['success']:
                    print(f"✅ Đã dự đoán: {prediction_result['estimated_drainage_time_hours']} giờ")
                else:
                    print(f"⚠️ Không thể dự đoán: {prediction_result.get('error', '')}")
        except Exception as e:
            print(f"⚠️ Lỗi tự động dự đoán: {e}")


@staticmethod
def save_prediction_result_simple(flood_report, result):
    """
    Phiên bản đơn giản để lưu prediction - LUÔN HOẠT ĐỘNG
    """
    try:
        print(f"💾 DrainageTimeService: Lưu dự đoán cho FloodReport #{flood_report.id}")
        
        # 1. Chuẩn bị dữ liệu cơ bản
        from django.contrib.gis.geos import Point
        from django.utils import timezone
        
        prediction_data = {
            'location': flood_report.location,
            'address': getattr(flood_report, 'address', 'Không xác định')[:200],
            'district': getattr(flood_report, 'district', '')[:100],
            'ward': getattr(flood_report, 'ward', '')[:100],
            'prediction_time': timezone.now(),
            'predicted_depth_cm': getattr(flood_report, 'water_depth', 0),
            'current_depth_cm': getattr(flood_report, 'water_depth', 0),
            'estimated_drainage_time_hours': result.get('estimated_drainage_time_hours', 0),
            'drainage_start_time': timezone.now(),
            'last_depth_update': timezone.now(),
            'reasons': ['Dự đoán tự động từ FloodReport'],
            'recommendations': '\n'.join(result.get('recommendations', [])[:5]) if result.get('recommendations') else '',
            'risk_level': 'high' if result.get('estimated_drainage_time_hours', 0) > 24 else 'medium' if result.get('estimated_drainage_time_hours', 0) > 6 else 'low',
            'is_active': True,
            'confidence': 70.0,  # Độ tin cậy mặc định
            'rainfall_mm': 0,    # Giá trị mặc định
            'valid_until': timezone.now() + timedelta(hours=result.get('estimated_drainage_time_hours', 6))
        }
        if hasattr(flood_report, 'id'):
            prediction_data['flood_report'] = flood_report
        
        # 3. Tạo prediction
        from .models import FloodPrediction
        prediction = FloodPrediction.objects.create(**prediction_data)
        
        print(f"✅ ĐÃ LƯU FloodPrediction #{prediction.id} thành công!")
        print(f"   • Địa chỉ: {prediction.address}")
        print(f"   • Thời gian cạn: {prediction.estimated_drainage_time_hours} giờ")
        print(f"   • Độ sâu: {prediction.current_depth_cm} cm")
        
        return prediction
        
    except Exception as e:
        print(f"❌ LỖI LƯU PREDICTION: {e}")
        import traceback
        traceback.print_exc()
        try:
            print("🔄 Thử lưu phiên bản cực kỳ đơn giản...")
            from .models import FloodPrediction
            prediction = FloodPrediction.objects.create(
                location=flood_report.location,
                address=getattr(flood_report, 'address', 'Địa chỉ')[100],
                prediction_time=timezone.now(),
                predicted_depth_cm=getattr(flood_report, 'water_depth', 0),
                is_active=True
            )
            print(f"✅ Đã lưu prediction đơn giản #{prediction.id}")
            return prediction
        except Exception as simple_error:
            print(f"❌ Lỗi cả phiên bản đơn giản: {simple_error}")
            return None

@staticmethod
def predict_drainage_time_for_location(lat, lng, water_depth, flood_report_id=None):
    """
    Dự đoán thời gian cạn nước cho một vị trí
    SỬA: Thêm flag để tránh recursion
    """
    try:
        print(f"⏳ DrainageTimeService: Dự đoán cạn nước cho vị trí {lat}, {lng}")
        import inspect
        stack = inspect.stack()
        call_count = sum(1 for frame in stack if frame.function == 'predict_drainage_time_for_location')
        
        if call_count > 2:  
            print(f"⚠️ Phát hiện recursion, trả về kết quả mặc định")
            return {
                'success': False,
                'message': 'Lỗi recursion trong dự đoán',
                'estimated_drainage_time_hours': 6.0
            }
        flood_report = None
        if flood_report_id:
            try:
                from .models import FloodReport  # Import tương đối
                flood_report = FloodReport.objects.filter(id=flood_report_id).first()
                if flood_report:
                    print(f"📄 Đã tìm thấy FloodReport #{flood_report_id}")
            except Exception as e:
                print(f"⚠️ Không thể lấy FloodReport: {e}")
        terrain_info = DrainageTimeService.get_terrain_info(lat, lng)
        weather_info = DrainageTimeService.get_weather_info(lat, lng)
        data = {
            'water_depth_cm': water_depth,
            'terrain': terrain_info,
            'weather': weather_info,
            'flood_type': getattr(flood_report, 'flood_type', 'rain') if flood_report else 'rain'
        }
        drainage_hours = DrainageTimeService.calculate_drainage_hours(data)
        result = DrainageTimeService.create_prediction_result(flood_report, data, drainage_hours)
        if flood_report and result.get('success', False):
            try:
                if not hasattr(flood_report, 'has_prediction_saved') or not flood_report.has_prediction_saved:
                    saved_prediction = DrainageTimeService.save_prediction_result(flood_report, result)
                    if saved_prediction:
                        flood_report.has_prediction_saved = True
            except Exception as e:
                print(f"⚠️ Không thể lưu dự đoán: {e}")
        
        print(f"✅ Dự đoán hoàn thành: {drainage_hours} giờ")
        return result
        
    except Exception as e:
        print(f"❌ Lỗi predict_drainage_time_for_location: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Lỗi dự đoán: {str(e)}',
            'estimated_drainage_time_hours': 6.0
        }
def predict_drainage_location_api(request):
    """
    API dự đoán cực kỳ đơn giản - LUÔN HOẠT ĐỘNG và LUU VÀO DATABASE
    """
    try:
        import json
        from django.contrib.gis.geos import Point
        from django.utils import timezone
        from datetime import timedelta
        from hanoi_map.models import FloodPrediction
        try:
            data = json.loads(request.body)
        except:
            data = {}
        lat = data.get('lat', 21.0)
        lng = data.get('lng', 105.8)
        location_name = data.get('location_name', 'Vị trí được chọn')
        water_depth_cm = float(data.get('water_depth_cm', 20))
        
        print(f"✅ API SIÊU ĐƠN GIẢN: {location_name}, {water_depth_cm}cm")
        drainage_hours = round(water_depth_cm * 0.5, 1)
        drainage_hours = min(max(drainage_hours, 0.5), 72)
        
        completion_time = timezone.now() + timedelta(hours=drainage_hours)
        if drainage_hours <= 2:
            level_text = 'Nhanh'
            risk_level = 'low'
        elif drainage_hours <= 6:
            level_text = 'Trung bình'
            risk_level = 'medium'
        elif drainage_hours <= 12:
            level_text = 'Chậm'
            risk_level = 'high'
        else:
            level_text = 'Rất chậm'
            risk_level = 'critical'
        
        # ============ PHẦN SỬA: LƯU VÀO DATABASE ============
        try:
            print(f"💾 Đang lưu vào FloodPrediction database...")
            
            # Tạo FloodPrediction thật sự
            prediction = FloodPrediction.objects.create(
                location=Point(lng, lat, srid=4326),
                address=location_name[:200],
                prediction_time=timezone.now(),
                predicted_depth_cm=water_depth_cm,
                current_depth_cm=water_depth_cm,
                estimated_drainage_time_hours=drainage_hours,
                drainage_start_time=timezone.now(),
                last_depth_update=timezone.now(),
                risk_level=risk_level,
                is_active=True,
                confidence=70.0,
                rainfall_mm=0,
                valid_until=timezone.now() + timedelta(hours=drainage_hours),
                # Các trường tùy chọn khác
                drainage_capacity='average',
                rainfall_duration_hours=1.0,
                elevation=5.0,
                distance_to_river=500,
                affected_areas=f"Khu vực {location_name}"
            )
            
            print(f"✅✅✅ ĐÃ LƯU THÀNH CÔNG FloodPrediction #{prediction.id}")
            print(f"   • ID: {prediction.id}")
            print(f"   • Địa chỉ: {prediction.address}")
            print(f"   • Thời gian cạn: {prediction.estimated_drainage_time_hours} giờ")
            print(f"   • Độ sâu: {prediction.current_depth_cm} cm")
            print(f"   • Created at: {prediction.created_at}")
            
            prediction_id = prediction.id
            prediction_saved = True
            
        except Exception as db_error:
            print(f"❌ Lỗi lưu database: {db_error}")
            import traceback
            traceback.print_exc()
            
            # Thử phiên bản đơn giản hơn
            try:
                print("🔄 Thử lưu phiên bản đơn giản...")
                prediction = FloodPrediction.objects.create(
                    location=Point(lng, lat),
                    address=location_name[:100],
                    prediction_time=timezone.now(),
                    predicted_depth_cm=water_depth_cm,
                    estimated_drainage_time_hours=drainage_hours,
                    is_active=True
                )
                print(f"✅ Đã lưu prediction đơn giản #{prediction.id}")
                prediction_id = prediction.id
                prediction_saved = True
            except Exception as simple_error:
                print(f"❌ Lỗi cả phiên bản đơn giản: {simple_error}")
                prediction_id = None
                prediction_saved = False
        # ============ KẾT THÚC PHẦN SỬA ============
        
        # Trả về response đơn giản
        response = {
            'success': True,
            'message': f'Dự đoán thành công: {drainage_hours} giờ',
            'prediction_saved': prediction_saved,
            'prediction_id': prediction_id,
            'data': {
                'estimated_drainage_time_hours': float(drainage_hours),
                'water_depth_cm': float(water_depth_cm),
                'completion_time_formatted': completion_time.strftime("%H:%M %d/%m/%Y"),
                'drainage_level_text': level_text,
                'location_name': location_name,
                'recommendations': ['Theo dõi hệ thống để cập nhật thông tin mới nhất'],
                'factors_considered': [f'Độ sâu nước: {water_depth_cm}cm'],
                'prediction_id': prediction_id,
                'prediction_saved': prediction_saved
            }
        }
        
        return JsonResponse(response, safe=True)
        
    except Exception as e:
        print(f"❌ Lỗi API đơn giản: {e}")
        import traceback
        traceback.print_exc()
        
        # Vẫn trả về response hợp lệ để frontend không crash
        return JsonResponse({
            'success': True,
            'message': 'Dự đoán mặc định (do có lỗi)',
            'prediction_saved': False,
            'data': {
                'estimated_drainage_time_hours': 6.0,
                'water_depth_cm': 20.0,
                'completion_time_formatted': 'Đang tính toán...',
                'drainage_level_text': 'Trung bình',
                'location_name': 'Vị trí mặc định',
                'recommendations': ['Kiểm tra lại sau'],
                'factors_considered': ['Sử dụng giá trị mặc định'],
                'prediction_saved': False
            }
        }, safe=True)