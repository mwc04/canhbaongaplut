# hanoi_map/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Trang chính
    path('', views.FloodMapView.as_view(), name='flood_map'),
    
    # API chính
    path('api/search/', views.search_location_api, name='search_api'),
    path('api/check-flood/', views.check_flood_api, name='check_flood_api'),
    path('api/area-status/', views.get_area_status_api, name='area_status_api'),
    path('api/report-flood/', views.report_flood_api, name='report_flood_api'),
    path('api/weather/', views.get_weather_api, name='weather_api'),
    
    # API REAL-TIME MỚI
    path('api/flood-data/', views.get_flood_data_api, name='flood_data_api'),
    path('api/statistics/', views.get_statistics_api, name='statistics_api'),
    path('api/recent-reports/', views.get_recent_reports_api, name='recent_reports_api'),
    
    # API phụ trợ
    path('api/test/', views.test_search_connection, name='test_api'),
]