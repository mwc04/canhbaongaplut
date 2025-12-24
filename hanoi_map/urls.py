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
    path('api/fixed-floodings/', views.get_fixed_floodings_api, name='fixed_floodings_api'),
    # path('api/trigger-flooding/', views.trigger_fixed_flooding_activation_api, name='trigger_flooding_api'),

     # Drainage Prediction APIs
    path('api/predict-drainage/', views.predict_drainage_time_api, name='predict_drainage'),
    path('api/predict-drainage-location/', views.predict_drainage_location_api, name='predict_drainage_location'),
    path('api/drainage-predictions/', views.get_drainage_predictions_api, name='get_drainage_predictions'),
    path('api/drainage-dashboard/', views.drainage_dashboard_api, name='drainage_dashboard'),
    path('api/auto-predict-drainage/', views.auto_predict_drainage_on_report, name='auto_predict_drainage'),

    
    
    # API REAL-TIME MỚI
    path('api/flood-data/', views.get_flood_data_api, name='flood_data_api'),
    path('api/statistics/', views.get_statistics_api, name='statistics_api'),
    path('api/recent-reports/', views.get_recent_reports_api, name='recent_reports_api'),
    
    # API phụ trợ
    path('api/test/', views.test_search_connection, name='test_api'),
    path('api/all-zones-status/', views.get_all_zones_status_api, name='all_zones_status_api'),
]