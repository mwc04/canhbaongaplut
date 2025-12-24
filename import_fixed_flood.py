import os
import django
from django.utils import timezone
import random
from datetime import timedelta
from django.contrib.gis.geos import Point  

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hanoi_flood.settings')
django.setup()

from hanoi_map.models import FixedFlooding
from django.contrib.auth.models import User

def clear_old_data():
    """Xóa dữ liệu cũ trong bảng FixedFlooding"""
    print("🗑️  Đang xóa dữ liệu cũ trong bảng FixedFlooding...")
    FixedFlooding.objects.all().delete()
    print("✅ Đã xóa dữ liệu cũ")

def create_all_flood_zones():
    """
    Tạo dữ liệu vùng ngập THỰC TẾ với 58 điểm ngập đầy đủ
    """
    print("\n📍 ĐANG TẠO DỮ LIỆU 58 ĐIỂM NGẬP THỰC TẾ TẠI HÀ NỘI")
    print("=" * 80)
    
    # Lấy user admin đầu tiên để gán vào managed_by
    admin_user = User.objects.filter(is_superuser=True).first()
    
    # DANH SÁCH ĐẦY ĐỦ 58 ĐIỂM NGẬP CỐ ĐỊNH HÀ NỘI - ĐÃ SỬA LỖI TỌA ĐỘ
    fixed_floodings = [
        {
            'name': 'Ngã 3 Xuân Đỉnh - Tân Xuân',
            'flood_type': 'rain',
            'district': 'Bắc Từ Liêm', 
            'ward': 'Xuân Đỉnh',
            'street': 'Phạm Văn Đồng, ngã 3 Xuân Đỉnh - Tân Xuân',
            'address': 'Phạm Văn Đồng, ngã 3 Xuân Đỉnh - Tân Xuân, Hà Nội',
            'location': Point(105.7925, 21.0875, srid=4326),
            'radius_meters': 150,
            'rainfall_threshold_mm': 40.0,
            'predicted_depth_cm': 50.0,
            'duration_hours': 3.5,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(3, 15),
            'description': 'Điểm ngập đen khi có mưa lớn, khu vực trũng thấp, giao thông ùn tắc nghiêm trọng',
            'recommendations': 'Nâng cao mặt đường, cải tạo hệ thống thoát nước',
            'managed_by': admin_user
        },
        {
            'name': 'UBND phường Mai Dịch đến Bệnh viện 19/8',
            'flood_type': 'urban',
            'district': 'Cầu Giấy', 
            'ward': 'Mai Dịch',
            'street': 'Đường Trần Bình, đoạn từ UBND phường đến Bệnh viện 19/8',
            'address': 'Đường Trần Bình, đoạn từ UBND phường Mai Dịch đến Bệnh viện 19/8, Hà Nội',
            'location': Point(105.7775, 21.0475, srid=4326),
            'radius_meters': 200,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(5, 20),
            'description': 'Ngập thường xuyên do hệ thống thoát nước quá tải, ảnh hưởng đến bệnh viện',
            'recommendations': 'Mở rộng cống thoát nước, lắp đặt bơm chống ngập',
            'managed_by': admin_user
        },
        {
            'name': 'Trước và đối diện Công ty Cầu 7',
            'flood_type': 'rain',
            'district': 'Bắc Từ Liêm', 
            'ward': 'Xuân Đỉnh',
            'street': 'Phạm Văn Đồng, khu vực trước và đối diện Công ty Cầu 7',
            'address': 'Phạm Văn Đồng, khu vực trước và đối diện Công ty Cầu 7, Xuân Đỉnh, Hà Nội',
            'location': Point(105.7875, 21.0825, srid=4326),
            'radius_meters': 100,
            'rainfall_threshold_mm': 45.0,
            'predicted_depth_cm': 55.0,
            'duration_hours': 4.0,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(2, 10),
            'description': 'Khu vực trũng, thoát nước kém, ngập sâu khi mưa lớn',
            'recommendations': 'Đào hồ điều hòa, nạo vét cống rãnh',
            'managed_by': admin_user
        },
        {
            'name': 'Khu đô thị RESCO',
            'flood_type': 'drainage',
            'district': 'Bắc Từ Liêm', 
            'ward': 'Cổ Nhuế 1',
            'street': 'Khu đô thị RESCO, đường Phạm Văn Đồng',
            'address': 'Khu đô thị RESCO, đường Phạm Văn Đồng, Cổ Nhuế 1, Hà Nội',
            'location': Point(105.7525, 21.0525, srid=4326),
            'radius_meters': 180,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(4, 12),
            'description': 'Hệ thống thoát nước chưa đồng bộ với quy hoạch đô thị',
            'recommendations': 'Hoàn thiện hệ thống thoát nước khu đô thị',
            'managed_by': admin_user
        },
        {
            'name': 'Cổng chợ - Doanh trại quân đội',
            'flood_type': 'urban',
            'district': 'Thanh Xuân', 
            'ward': 'Thanh Xuân Bắc',
            'street': 'Phan Văn Trường, đoạn cổng chợ đến doanh trại quân đội',
            'address': 'Phan Văn Trường, đoạn cổng chợ đến doanh trại quân đội, Thanh Xuân Bắc, Hà Nội',
            'location': Point(105.8125, 20.9975, srid=4326),
            'radius_meters': 120,
            'rainfall_threshold_mm': 50.0,
            'predicted_depth_cm': 60.0,
            'duration_hours': 5.0,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(3, 15),
            'description': 'Điểm ngập đen, khu vực thấp trũng, ảnh hưởng đến chợ và doanh trại',
            'recommendations': 'Cải tạo thoát nước, nâng cao mặt đường',
            'managed_by': admin_user
        },
        {
            'name': 'Số 91-97 Hoa Bằng',
            'flood_type': 'sewer',
            'district': 'Cầu Giấy', 
            'ward': 'Quan Hoa',
            'street': 'Hoa Bằng, từ số 91 đến 97',
            'address': 'Hoa Bằng, từ số 91 đến 97, Quan Hoa, Cầu Giấy, Hà Nội',
            'location': Point(105.7975, 21.0425, srid=4326),
            'radius_meters': 80,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 30.0,
            'duration_hours': 1.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(6, 25),
            'description': 'Hệ thống cống thoát nước nhỏ, dễ tắc nghẽn do rác thải',
            'recommendations': 'Nạo vét cống thường xuyên, tuyên truyền không xả rác',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã ba Lê Trọng Tấn - Đại lộ Thăng Long',
            'flood_type': 'rain',
            'district': 'Thanh Xuân', 
            'ward': 'Thanh Xuân Nam',
            'street': 'Đại lộ Thăng Long, ngã ba giao Lê Trọng Tấn',
            'address': 'Đại lộ Thăng Long, ngã ba giao Lê Trọng Tấn, Thanh Xuân Nam, Hà Nội',
            'location': Point(105.8075, 20.9925, srid=4326),
            'radius_meters': 150,
            'rainfall_threshold_mm': 40.0,
            'predicted_depth_cm': 50.0,
            'duration_hours': 3.0,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(2, 8),
            'description': 'Giao lộ trũng, nước tập trung từ nhiều hướng',
            'recommendations': 'Lắp đặt hệ thống thoát nước nhanh',
            'managed_by': admin_user
        },
        {
            'name': 'Đường vào Miếu Đầm',
            'flood_type': 'rain',
            'district': 'Nam Từ Liêm', 
            'ward': 'Mỹ Đình 1',
            'street': 'Đỗ Đức Dục, đường vào Miếu Đầm',
            'address': 'Đỗ Đức Dục, đường vào Miếu Đầm, Mỹ Đình 1, Nam Từ Liêm, Hà Nội',
            'location': Point(105.7725, 21.0225, srid=4326),
            'radius_meters': 100,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 4.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(3, 10),
            'description': 'Ngập theo mùa, khu vực gần sông, đất trũng',
            'recommendations': 'Đắp đê bao, xây dựng trạm bơm',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã ba Phan Đình Giót - Lê Trọng Tấn',
            'flood_type': 'urban',
            'district': 'Hà Đông', 
            'ward': 'Yết Kiêu',
            'street': 'Quang Trung, từ ngã ba Phan Đình Giót đến ngã tư Lê Trọng Tấn',
            'address': 'Quang Trung, từ ngã ba Phan Đình Giót đến ngã tư Lê Trọng Tấn, Yết Kiêu, Hà Đông, Hà Nội',
            'location': Point(105.7675, 20.9725, srid=4326),
            'radius_meters': 200,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 45.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(5, 18),
            'description': 'Ngập thường xuyên do mật độ xây dựng cao, mặt đường thấp',
            'recommendations': 'Quy hoạch lại thoát nước đô thị',
            'managed_by': admin_user
        },
        {
            'name': 'Trước Chi cục Thuế và tòa nhà HUD3',
            'flood_type': 'drainage',
            'district': 'Hà Đông', 
            'ward': 'Văn Quán',
            'street': 'Tô Hiệu, trước Chi cục Thuế và tòa nhà HUD3',
            'address': 'Tô Hiệu, trước Chi cục Thuế và tòa nhà HUD3, Văn Quán, Hà Đông, Hà Nội',
            'location': Point(105.7625, 20.9775, srid=4326),
            'radius_meters': 90,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(4, 15),
            'description': 'Hệ thống thoát nước cục bộ không đáp ứng được lượng mưa lớn',
            'recommendations': 'Cải tạo hệ thống cống thoát nước',
            'managed_by': admin_user
        },
        {
            'name': 'Đình Phùng Khoang',
            'flood_type': 'rain',
            'district': 'Nam Từ Liêm', 
            'ward': 'Phùng Khoang',
            'street': 'Phố Phùng Khoang, khu vực đình Phùng Khoang',
            'address': 'Phố Phùng Khoang, khu vực đình Phùng Khoang, Phùng Khoang, Nam Từ Liêm, Hà Nội',
            'location': Point(105.7825, 21.0025, srid=4326),
            'radius_meters': 120,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 3.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(2, 7),
            'description': 'Khu vực truyền thống, thoát nước tự nhiên kém hiệu quả',
            'recommendations': 'Bảo tồn di tích, cải tạo thoát nước hiện đại',
            'managed_by': admin_user
        },
        {
            'name': 'Ngõ 42, 58 Triều Khúc',
            'flood_type': 'sewer',
            'district': 'Thanh Xuân', 
            'ward': 'Triều Khúc',
            'street': 'Ngõ 42 và 58 Triều Khúc',
            'address': 'Ngõ 42 và 58 Triều Khúc, Triều Khúc, Thanh Xuân, Hà Nội',
            'location': Point(105.8225, 20.9875, srid=4326),
            'radius_meters': 60,
            'rainfall_threshold_mm': 20.0,
            'predicted_depth_cm': 25.0,
            'duration_hours': 1.0,
            'severity': 'low',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(8, 30),
            'description': 'Ngõ nhỏ, hệ thống thoát nước hạn chế, dễ ngập cục bộ',
            'recommendations': 'Mở rộng ngõ, lắp đặt cống thoát nước',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã ba Nguyễn Trãi - Nguyễn Xiển đến ngõ 214',
            'flood_type': 'rain',
            'district': 'Thanh Xuân', 
            'ward': 'Nhân Chính',
            'street': 'Nguyễn Xiển, từ ngã ba Nguyễn Trãi đến ngõ 214',
            'address': 'Nguyễn Xiển, từ ngã ba Nguyễn Trãi đến ngõ 214, Nhân Chính, Thanh Xuân, Hà Nội',
            'location': Point(105.8175, 20.9925, srid=4326),
            'radius_meters': 180,
            'rainfall_threshold_mm': 45.0,
            'predicted_depth_cm': 55.0,
            'duration_hours': 4.0,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(3, 12),
            'description': 'Điểm ngập đen, khu vực giao thông quan trọng, trũng thấp',
            'recommendations': 'Thiết kế lại mặt đường có độ dốc thoát nước',
            'managed_by': admin_user
        },
        {
            'name': 'Trường ĐH KHXH&NV - Làn xe buýt',
            'flood_type': 'urban',
            'district': 'Thanh Xuân', 
            'ward': 'Thanh Xuân Trung',
            'street': 'Nguyễn Trãi, trước trường ĐH KHXH&NV (bên chẵn làn xe buýt)',
            'address': 'Nguyễn Trãi, trước trường ĐH KHXH&NV, Thanh Xuân Trung, Thanh Xuân, Hà Nội',
            'location': Point(105.8125, 20.9975, srid=4326),
            'radius_meters': 100,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(5, 20),
            'description': 'Ngập thường xuyên do mặt đường thấp, ảnh hưởng đến giao thông công cộng',
            'recommendations': 'Nâng cao làn đường, cải thiện thoát nước',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã ba Vũ Trọng Phụng - Quan Nhân',
            'flood_type': 'drainage',
            'district': 'Thanh Xuân', 
            'ward': 'Thanh Xuân Bắc',
            'street': 'Ngã ba Vũ Trọng Phụng - Quan Nhân',
            'address': 'Ngã ba Vũ Trọng Phụng - Quan Nhân, Thanh Xuân Bắc, Thanh Xuân, Hà Nội',
            'location': Point(105.8075, 20.9975, srid=4326),
            'radius_meters': 80,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 30.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(6, 22),
            'description': 'Hệ thống thoát nước tại ngã ba không đủ công suất',
            'recommendations': 'Lắp đặt cống lớn hơn tại giao lộ',
            'managed_by': admin_user
        },
        {
            'name': 'Số 49 đến 93 Bùi Xương Trạch',
            'flood_type': 'sewer',
            'district': 'Thanh Trì', 
            'ward': 'Tân Triều',
            'street': 'Bùi Xương Trạch, từ số 49 đến 93',
            'address': 'Bùi Xương Trạch, từ số 49 đến 93, Tân Triều, Thanh Trì, Hà Nội',
            'location': Point(105.8325, 20.9775, srid=4326),
            'radius_meters': 70,
            'rainfall_threshold_mm': 20.0,
            'predicted_depth_cm': 25.0,
            'duration_hours': 1.5,
            'severity': 'low',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(7, 25),
            'description': 'Khu dân cư đông đúc, cống nhỏ, thường xuyên tắc nghẽn',
            'recommendations': 'Thay thế cống lớn, vệ sinh định kỳ',
            'managed_by': admin_user
        },
        {
            'name': 'Số 12 đến ngõ 95 Cự Lộc',
            'flood_type': 'rain',
            'district': 'Thanh Xuân', 
            'ward': 'Khương Đình',
            'street': 'Phố Cự Lộc, từ số 12 đến ngõ 95',
            'address': 'Phố Cự Lộc, từ số 12 đến ngõ 95, Khương Đình, Thanh Xuân, Hà Nội',
            'location': Point(105.8225, 20.9925, srid=4326),
            'radius_meters': 150,
            'rainfall_threshold_mm': 40.0,
            'predicted_depth_cm': 50.0,
            'duration_hours': 3.5,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(4, 15),
            'description': 'Điểm ngập đen, khu vực trũng, đường dốc tập trung nước',
            'recommendations': 'Xây dựng hồ điều hòa tại khu vực',
            'managed_by': admin_user
        },
        {
            'name': 'Đường Vương Thừa Vũ',
            'flood_type': 'urban',
            'district': 'Thanh Xuân', 
            'ward': 'Thanh Xuân Nam',
            'street': 'Vương Thừa Vũ (đoạn thường xuyên ngập)',
            'address': 'Vương Thừa Vũ, Thanh Xuân Nam, Thanh Xuân, Hà Nội',
            'location': Point(105.8175, 20.9875, srid=4326),
            'radius_meters': 200,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 3.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(5, 18),
            'description': 'Ngập thường xuyên, mặt đường xuống cấp, thoát nước kém',
            'recommendations': 'Sửa chữa mặt đường, nâng cấp hệ thống thoát nước',
            'managed_by': admin_user
        },
        {
            'name': 'Đoạn Bệnh viện Phổi Hà Nội',
            'flood_type': 'urban',
            'district': 'Đống Đa', 
            'ward': 'Trung Liệt',
            'street': 'Trường Chinh, đoạn trước Bệnh viện Phổi Hà Nội',
            'address': 'Trường Chinh, đoạn trước Bệnh viện Phổi Hà Nội, Trung Liệt, Đống Đa, Hà Nội',
            'location': Point(105.8275, 21.0125, srid=4326),
            'radius_meters': 120,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 45.0,
            'duration_hours': 3.0,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(2, 10),
            'description': 'Khu vực nhạy cảm, ảnh hưởng đến bệnh viện, nguy cơ cao',
            'recommendations': 'Ưu tiên xử lý ngập, lắp đặt hệ thống bơm khẩn cấp',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã tư Tây Sơn - Thái Hà',
            'flood_type': 'rain',
            'district': 'Đống Đa', 
            'ward': 'Trung Liệt',
            'street': 'Ngã tư Tây Sơn - Thái Hà',
            'address': 'Ngã tư Tây Sơn - Thái Hà, Trung Liệt, Đống Đa, Hà Nội',
            'location': Point(105.8305, 21.0145, srid=4326),
            'radius_meters': 150,
            'rainfall_threshold_mm': 45.0,
            'predicted_depth_cm': 55.0,
            'duration_hours': 4.0,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(3, 12),
            'description': 'Giao lộ lớn, điểm ngập đen, giao thông phức tạp',
            'recommendations': 'Thiết kế lại giao lộ với hệ thống thoát nước tối ưu',
            'managed_by': admin_user
        },
        {
            'name': 'Nhà B7 Phạm Ngọc Thạch',
            'flood_type': 'urban',
            'district': 'Đống Đa', 
            'ward': 'Trung Tự',
            'street': 'Phạm Ngọc Thạch, khu vực nhà B7',
            'address': 'Phạm Ngọc Thạch, khu vực nhà B7, Trung Tự, Đống Đa, Hà Nội',
            'location': Point(105.8345, 21.0205, srid=4326),
            'radius_meters': 80,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 30.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(8, 20),
            'description': 'Khu tập thể cũ, hệ thống thoát nước lạc hậu',
            'recommendations': 'Cải tạo hệ thống thoát nước khu tập thể',
            'managed_by': admin_user
        },
        {
            'name': 'Số 209 Đội Cấn - Chùa Bát Tháp',
            'flood_type': 'rain',
            'district': 'Ba Đình', 
            'ward': 'Đội Cấn',
            'street': 'Đội Cấn, số 209 khu vực Chùa Bát Tháp',
            'address': 'Đội Cấn, số 209 khu vực Chùa Bát Tháp, Đội Cấn, Ba Đình, Hà Nội',
            'location': Point(105.8275, 21.0375, srid=4326),
            'radius_meters': 100,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 3.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(3, 10),
            'description': 'Khu vực di tích, ngập theo mùa do địa hình',
            'recommendations': 'Bảo vệ di tích, xây dựng hệ thống thoát nước phù hợp',
            'managed_by': admin_user
        },
        {
            'name': 'Trường Chu Văn An - Dốc La Pho',
            'flood_type': 'urban',
            'district': 'Ba Đình', 
            'ward': 'Thụy Khuê',
            'street': 'Thụy Khuê, đoạn trường Chu Văn An đến Dốc La Pho',
            'address': 'Thụy Khuê, đoạn trường Chu Văn An đến Dốc La Pho, Thụy Khuê, Ba Đình, Hà Nội',
            'location': Point(105.8375, 21.0475, srid=4326),
            'radius_meters': 150,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(5, 15),
            'description': 'Khu vực trường học, ngập ảnh hưởng đến học sinh',
            'recommendations': 'Ưu tiên xử lý ngập trước cổng trường',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã năm Bà Triệu',
            'flood_type': 'rain',
            'district': 'Hai Bà Trưng', 
            'ward': 'Ngô Thì Nhậm',
            'street': 'Ngã năm Bà Triệu (giao nhiều tuyến phố)',
            'address': 'Ngã năm Bà Triệu, Ngô Thì Nhậm, Hai Bà Trưng, Hà Nội',
            'location': Point(105.8545, 21.0205, srid=4326),
            'radius_meters': 180,
            'rainfall_threshold_mm': 40.0,
            'predicted_depth_cm': 50.0,
            'duration_hours': 3.5,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(4, 14),
            'description': 'Giao lộ phức tạp, điểm ngập đen quan trọng',
            'recommendations': 'Thiết kế lại nút giao với hệ thống thoát nước hiện đại',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã tư Liên Trì - Nguyễn Gia Thiều',
            'flood_type': 'urban',
            'district': 'Hai Bà Trưng', 
            'ward': 'Nguyễn Du',
            'street': 'Ngã tư Liên Trì - Nguyễn Gia Thiều',
            'address': 'Ngã tư Liên Trì - Nguyễn Gia Thiều, Nguyễn Du, Hai Bà Trưng, Hà Nội',
            'location': Point(105.8575, 21.0175, srid=4326),
            'radius_meters': 120,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(6, 18),
            'description': 'Khu dân cư đông đúc, hệ thống thoát nước quá tải',
            'recommendations': 'Nâng cấp hệ thống thoát nước khu vực',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã tư Phan Bội Châu - Lý Thường Kiệt',
            'flood_type': 'rain',
            'district': 'Hoàn Kiếm', 
            'ward': 'Trần Hưng Đạo',
            'street': 'Ngã tư Phan Bội Châu - Lý Thường Kiệt',
            'address': 'Ngã tư Phan Bội Châu - Lý Thường Kiệt, Trần Hưng Đạo, Hoàn Kiếm, Hà Nội',
            'location': Point(105.8605, 21.0245, srid=4326),
            'radius_meters': 130,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 3.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(5, 16),
            'description': 'Khu vực trung tâm, ngập ảnh hưởng đến thương mại',
            'recommendations': 'Cải tạo thoát nước khu trung tâm',
            'managed_by': admin_user
        },
        {
            'name': 'Trước cổng trường Lý Thường Kiệt',
            'flood_type': 'urban',
            'district': 'Hai Bà Trưng', 
            'ward': 'Bùi Thị Xuân',
            'street': 'Nguyễn Khuyến, khu vực trước cổng trường Lý Thường Kiệt',
            'address': 'Nguyễn Khuyến, khu vực trước cổng trường Lý Thường Kiệt, Bùi Thị Xuân, Hai Bà Trưng, Hà Nội',
            'location': Point(105.8525, 21.0145, srid=4326),
            'radius_meters': 90,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 30.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(7, 22),
            'description': 'Trước cổng trường, ảnh hưởng đến phụ huynh đưa đón',
            'recommendations': 'Xây dựng vỉa hè cao, hệ thống thoát nước riêng',
            'managed_by': admin_user
        },
        {
            'name': 'Cổng Công ty Môi trường đô thị',
            'flood_type': 'sewer',
            'district': 'Ba Đình', 
            'ward': 'Điện Biên',
            'street': 'Cao Bá Quát, khu vực cổng Công ty Môi trường đô thị',
            'address': 'Cao Bá Quát, khu vực cổng Công ty Môi trường đô thị, Điện Biên, Ba Đình, Hà Nội',
            'location': Point(105.8405, 21.0345, srid=4326),
            'radius_meters': 70,
            'rainfall_threshold_mm': 20.0,
            'predicted_depth_cm': 25.0,
            'duration_hours': 1.5,
            'severity': 'low',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(10, 30),
            'description': 'Điểm ngập trước cổng công ty môi trường - nghịch lý',
            'recommendations': 'Cần xử lý ngay điểm ngập tại chính công ty môi trường',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã tư Điện Biên Phủ - Nguyễn Tri Phương',
            'flood_type': 'rain',
            'district': 'Ba Đình', 
            'ward': 'Điện Biên',
            'street': 'Ngã tư Điện Biên Phủ - Nguyễn Tri Phương',
            'address': 'Ngã tư Điện Biên Phủ - Nguyễn Tri Phương, Điện Biên, Ba Đình, Hà Nội',
            'location': Point(105.8425, 21.0375, srid=4326),
            'radius_meters': 160,
            'rainfall_threshold_mm': 45.0,
            'predicted_depth_cm': 55.0,
            'duration_hours': 4.0,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(3, 13),
            'description': 'Giao lộ quan trọng, điểm ngập đen lịch sử',
            'recommendations': 'Thiết kế lại nút giao với thoát nước ưu tiên',
            'managed_by': admin_user
        },
        {
            'name': 'Khu phố cổ Hà Nội',
            'flood_type': 'urban',
            'district': 'Hoàn Kiếm', 
            'ward': 'Hàng Bồ',
            'street': 'Phùng Hưng - Bát Đàn - Đường Thành - Nhà Hỏa',
            'address': 'Khu phố cổ Hà Nội, các phố Phùng Hưng, Bát Đàn, Đường Thành, Nhà Hỏa, Hoàn Kiếm, Hà Nội',
            'location': Point(105.8505, 21.0405, srid=4326),
            'radius_meters': 250,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 3.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(8, 25),
            'description': 'Khu phố cổ, đường hẹp, thoát nước khó khăn',
            'recommendations': 'Bảo tồn kiến trúc kết hợp cải tạo thoát nước',
            'managed_by': admin_user
        },
        {
            'name': 'Khách sạn Thủy Tiên',
            'flood_type': 'rain',
            'district': 'Hoàn Kiếm', 
            'ward': 'Tràng Tiền',
            'street': 'Phố Tông Đản, trước khách sạn Thủy Tiên',
            'address': 'Phố Tông Đản, trước khách sạn Thủy Tiên, Tràng Tiền, Hoàn Kiếm, Hà Nội',
            'location': Point(105.8625, 21.0305, srid=4326),
            'radius_meters': 100,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(6, 18),
            'description': 'Khu vực khách sạn, ảnh hưởng đến du khách',
            'recommendations': 'Xử lý ngập cục bộ trước khách sạn',
            'managed_by': admin_user
        },
        {
            'name': 'Bến xe phía Nam',
            'flood_type': 'urban',
            'district': 'Hoàng Mai', 
            'ward': 'Giáp Bát',
            'street': 'Bến xe phía Nam - đường Giải Phóng',
            'address': 'Bến xe phía Nam, đường Giải Phóng, Giáp Bát, Hoàng Mai, Hà Nội',
            'location': Point(105.8445, 20.9845, srid=4326),
            'radius_meters': 200,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 45.0,
            'duration_hours': 3.5,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(2, 9),
            'description': 'Bến xe lớn, ngập ảnh hưởng đến giao thông liên tỉnh',
            'recommendations': 'Ưu tiên xử lý, lắp đặt hệ thống bơm công suất lớn',
            'managed_by': admin_user
        },
        {
            'name': 'Ngõ 74 đến cống hóa mương Tân Mai',
            'flood_type': 'sewer',
            'district': 'Hoàng Mai', 
            'ward': 'Tân Mai',
            'street': 'Nguyễn Chính, từ ngõ 74 đến cống hóa mương Tân Mai',
            'address': 'Nguyễn Chính, từ ngõ 74 đến cống hóa mương Tân Mai, Tân Mai, Hoàng Mai, Hà Nội',
            'location': Point(105.8505, 20.9905, srid=4326),
            'radius_meters': 150,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 30.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(9, 28),
            'description': 'Khu vực cống hóa chưa hoàn thiện, thường xuyên ngập',
            'recommendations': 'Hoàn thiện công trình cống hóa mương',
            'managed_by': admin_user
        },
        {
            'name': 'Cao Bá Quát (đoạn trung tâm)',
            'flood_type': 'urban',
            'district': 'Ba Đình', 
            'ward': 'Điện Biên',
            'street': 'Cao Bá Quát, đoạn từ số 50 đến 100',
            'address': 'Cao Bá Quát, đoạn từ số 50 đến 100, Điện Biên, Ba Đình, Hà Nội',
            'location': Point(105.8385, 21.0325, srid=4326),
            'radius_meters': 180,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(7, 20),
            'description': 'Đường chính, ngập thường xuyên do mặt đường thấp',
            'recommendations': 'Nâng cấp mặt đường, cải tạo thoát nước',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã 4 Phan Bội Châu - Lý Thường Kiệt',
            'flood_type': 'rain',
            'district': 'Hoàn Kiếm', 
            'ward': 'Hàng Bài',
            'street': 'Ngã 4 Phan Bội Châu - Lý Thường Kiệt',
            'address': 'Ngã 4 Phan Bội Châu - Lý Thường Kiệt, Hàng Bài, Hoàn Kiếm, Hà Nội',
            'location': Point(105.8585, 21.0225, srid=4326),
            'radius_meters': 140,
            'rainfall_threshold_mm': 40.0,
            'predicted_depth_cm': 50.0,
            'duration_hours': 3.5,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(4, 15),
            'description': 'Giao lộ trung tâm, điểm ngập đen quan trọng',
            'recommendations': 'Thiết kế lại giao lộ với thoát nước tối ưu',
            'managed_by': admin_user
        },
        {
            'name': 'Phố Tôn Đản (đoạn chính)',
            'flood_type': 'rain',
            'district': 'Hoàn Kiếm', 
            'ward': 'Tràng Tiền',
            'street': 'Phố Tôn Đản, đoạn từ Hàng Khay đến Lý Thái Tổ',
            'address': 'Phố Tôn Đản, đoạn từ Hàng Khay đến Lý Thái Tổ, Tràng Tiền, Hoàn Kiếm, Hà Nội',
            'location': Point(105.8605, 21.0275, srid=4326),
            'radius_meters': 160,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 3.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(5, 17),
            'description': 'Phố trung tâm, ngập ảnh hưởng đến thương mại',
            'recommendations': 'Cải tạo thoát nước khu phố cổ',
            'managed_by': admin_user
        },
        {
            'name': 'Ngõ 99 Hoa Bằng',
            'flood_type': 'sewer',
            'district': 'Cầu Giấy', 
            'ward': 'Quan Hoa',
            'street': 'Ngõ 99 Hoa Bằng',
            'address': 'Ngõ 99 Hoa Bằng, Quan Hoa, Cầu Giấy, Hà Nội',
            'location': Point(105.8005, 21.0405, srid=4326),
            'radius_meters': 60,
            'rainfall_threshold_mm': 20.0,
            'predicted_depth_cm': 25.0,
            'duration_hours': 1.5,
            'severity': 'low',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(12, 35),
            'description': 'Ngõ nhỏ, hệ thống thoát nước hạn chế',
            'recommendations': 'Mở rộng ngõ, lắp đặt cống mới',
            'managed_by': admin_user
        },
        {
            'name': 'Ngã ba Mỹ Đình - Thiên Hiền',
            'flood_type': 'rain',
            'district': 'Nam Từ Liêm', 
            'ward': 'Mỹ Đình 2',
            'street': 'Ngã ba Mỹ Đình - Thiên Hiền',
            'address': 'Ngã ba Mỹ Đình - Thiên Hiền, Mỹ Đình 2, Nam Từ Liêm, Hà Nội',
            'location': Point(105.7705, 21.0175, srid=4326),
            'radius_meters': 120,
            'rainfall_threshold_mm': 40.0,
            'predicted_depth_cm': 50.0,
            'duration_hours': 3.5,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(3, 11),
            'description': 'Điểm ngập đen, khu vực đang phát triển',
            'recommendations': 'Quy hoạch thoát nước đồng bộ với phát triển đô thị',
            'managed_by': admin_user
        },
        {
            'name': 'Yên Duyên - Vành đai 3',
            'flood_type': 'rain',
            'district': 'Thanh Trì', 
            'ward': 'Yên Duyên',
            'street': 'Đường Vành đai 3 đoạn qua Yên Duyên',
            'address': 'Đường Vành đai 3 đoạn qua Yên Duyên, Thanh Trì, Hà Nội',
            'location': Point(105.8475, 20.9625, srid=4326),
            'radius_meters': 200,
            'rainfall_threshold_mm': 45.0,
            'predicted_depth_cm': 55.0,
            'duration_hours': 4.0,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(2, 8),
            'description': 'Đường vành đai, ngập ảnh hưởng đến giao thông liên vùng',
            'recommendations': 'Xây dựng hệ thống thoát nước dọc đường vành đai',
            'managed_by': admin_user
        },
        {
            'name': 'Hoàng Mai (ngõ 169 đến UBND)',
            'flood_type': 'urban',
            'district': 'Hoàng Mai', 
            'ward': 'Hoàng Văn Thụ',
            'street': 'Đường Hoàng Mai, từ ngõ 169 đến đường vào UBND phường',
            'address': 'Đường Hoàng Mai, từ ngõ 169 đến đường vào UBND phường, Hoàng Văn Thụ, Hoàng Mai, Hà Nội',
            'location': Point(105.8605, 20.9805, srid=4326),
            'radius_meters': 180,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(8, 22),
            'description': 'Khu vực hành chính, ngập ảnh hưởng đến UBND',
            'recommendations': 'Ưu tiên xử lý ngập trước trụ sở hành chính',
            'managed_by': admin_user
        },
        {
            'name': 'Đường 2,5 Đền Lừ',
            'flood_type': 'rain',
            'district': 'Hoàng Mai', 
            'ward': 'Đền Lừ',
            'street': 'Đường 2,5 Đền Lừ, cạnh hồ Đền Lừ',
            'address': 'Đường 2,5 Đền Lừ, cạnh hồ Đền Lừ, Đền Lừ, Hoàng Mai, Hà Nội',
            'location': Point(105.8675, 20.9775, srid=4326),
            'radius_meters': 140,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 3.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(4, 12),
            'description': 'Khu vực gần hồ, ngập theo mùa mưa',
            'recommendations': 'Nạo vét hồ, xây dựng đê bao',
            'managed_by': admin_user
        },
        {
            'name': 'Ngõ 165 Thái Hà',
            'flood_type': 'sewer',
            'district': 'Đống Đa', 
            'ward': 'Trung Liệt',
            'street': 'Ngõ 165 Thái Hà',
            'address': 'Ngõ 165 Thái Hà, Trung Liệt, Đống Đa, Hà Nội',
            'location': Point(105.8245, 21.0105, srid=4326),
            'radius_meters': 70,
            'rainfall_threshold_mm': 20.0,
            'predicted_depth_cm': 25.0,
            'duration_hours': 1.5,
            'severity': 'low',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(15, 40),
            'description': 'Ngõ trong khu dân cư cũ, cống nhỏ',
            'recommendations': 'Cải tạo hệ thống thoát nước ngõ nhỏ',
            'managed_by': admin_user
        },
        {
            'name': 'Chợ xanh Thành Công',
            'flood_type': 'rain',
            'district': 'Ba Đình', 
            'ward': 'Thành Công',
            'street': 'Khu vực chợ xanh Thành Công',
            'address': 'Khu vực chợ xanh Thành Công, Thành Công, Ba Đình, Hà Nội',
            'location': Point(105.8155, 21.0305, srid=4326),
            'radius_meters': 120,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 30.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(10, 25),
            'description': 'Khu vực chợ, ngập ảnh hưởng đến buôn bán',
            'recommendations': 'Xây dựng hệ thống thoát nước khu chợ',
            'managed_by': admin_user
        },
        {
            'name': 'Gầm cầu chui xe lửa phố Thiên Đức',
            'flood_type': 'rain',
            'district': 'Long Biên', 
            'ward': 'Thượng Thanh',
            'street': 'Gầm cầu chui xe lửa phố Thiên Đức',
            'address': 'Gầm cầu chui xe lửa phố Thiên Đức, Thượng Thanh, Long Biên, Hà Nội',
            'location': Point(105.9025, 21.0625, srid=4326),
            'radius_meters': 100,
            'rainfall_threshold_mm': 20.0,
            'predicted_depth_cm': 60.0,
            'duration_hours': 6.0,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(1, 5),
            'description': 'Gầm cầu chui, ngập sâu nguy hiểm, nhiều tai nạn',
            'recommendations': 'Lắp đặt cảnh báo, hệ thống bơm khẩn cấp',
            'managed_by': admin_user
        },
        {
            'name': 'Đường Tố Hữu (Lương Thế Vinh - Trung Văn)',
            'flood_type': 'urban',
            'district': 'Nam Từ Liêm', 
            'ward': 'Trung Văn',
            'street': 'Đường Tố Hữu, từ Lương Thế Vinh đến Trung Văn',
            'address': 'Đường Tố Hữu, từ Lương Thế Vinh đến Trung Văn, Trung Văn, Nam Từ Liêm, Hà Nội',
            'location': Point(105.7605, 21.0075, srid=4326),
            'radius_meters': 220,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(6, 18),
            'description': 'Trục đường chính, ngập ảnh hưởng đến giao thông',
            'recommendations': 'Cải tạo thoát nước dọc trục đường',
            'managed_by': admin_user
        },
        {
            'name': 'Khu vực Quan Nhân',
            'flood_type': 'rain',
            'district': 'Thanh Xuân', 
            'ward': 'Thanh Xuân Bắc',
            'street': 'Khu vực Quan Nhân, các ngõ nhỏ',
            'address': 'Khu vực Quan Nhân, các ngõ nhỏ, Thanh Xuân Bắc, Thanh Xuân, Hà Nội',
            'location': Point(105.8105, 20.9945, srid=4326),
            'radius_meters': 250,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 30.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(12, 30),
            'description': 'Khu dân cư với nhiều ngõ nhỏ, thoát nước kém',
            'recommendations': 'Quy hoạch lại hệ thống thoát nước toàn khu vực',
            'managed_by': admin_user
        },
        {
            'name': 'Hầm chui số 5 ĐLTL',
            'flood_type': 'rain',
            'district': 'Nam Từ Liêm', 
            'ward': 'Tây Mỗ',
            'street': 'Hầm chui số 5 Đại lộ Thăng Long',
            'address': 'Hầm chui số 5 Đại lộ Thăng Long, Tây Mỗ, Nam Từ Liêm, Hà Nội',
            'location': Point(105.7425, 21.0275, srid=4326),
            'radius_meters': 150,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 70.0,
            'duration_hours': 8.0,
            'severity': 'very_high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(1, 4),
            'description': 'Hầm chui đường cao tốc, ngập sâu cực kỳ nguy hiểm',
            'recommendations': 'Lắp đặt hệ thống bơm tự động, cảnh báo sớm',
            'managed_by': admin_user
        },
        {
            'name': 'Hầm chui số 3 ĐLTL',
            'flood_type': 'rain',
            'district': 'Nam Từ Liêm', 
            'ward': 'Đại Mỗ',
            'street': 'Hầm chui số 3 Đại lộ Thăng Long',
            'address': 'Hầm chui số 3 Đại lộ Thăng Long, Đại Mỗ, Nam Từ Liêm, Hà Nội',
            'location': Point(105.7375, 21.0225, srid=4326),
            'radius_meters': 150,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 65.0,
            'duration_hours': 7.0,
            'severity': 'very_high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(1, 4),
            'description': 'Hầm chui nguy hiểm, nhiều xe bị chết máy',
            'recommendations': 'Xây dựng hệ thống chống ngập chuyên dụng cho hầm',
            'managed_by': admin_user
        },
        {
            'name': 'Hầm chui Km9+656 ĐLTL',
            'flood_type': 'rain',
            'district': 'Hoài Đức', 
            'ward': 'An Khánh',
            'street': 'Hầm chui Km9+656 Đại lộ Thăng Long',
            'address': 'Hầm chui Km9+656 Đại lộ Thăng Long, An Khánh, Hoài Đức, Hà Nội',
            'location': Point(105.7225, 21.0325, srid=4326),
            'radius_meters': 140,
            'rainfall_threshold_mm': 20.0,
            'predicted_depth_cm': 60.0,
            'duration_hours': 6.5,
            'severity': 'very_high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(1, 3),
            'description': 'Hầm chui vùng ngoại thành, thiếu hệ thống thoát nước',
            'recommendations': 'Lắp đặt hệ thống bơm và cảnh báo',
            'managed_by': admin_user
        },
        {
            'name': 'Hầm chui số 6 ĐLTL',
            'flood_type': 'rain',
            'district': 'Hoài Đức', 
            'ward': 'Đông Xuân',
            'street': 'Hầm chui số 6 Đại lộ Thăng Long',
            'address': 'Hầm chui số 6 Đại lộ Thăng Long, Đông Xuân, Hoài Đức, Hà Nội',
            'location': Point(105.7175, 21.0275, srid=4326),
            'radius_meters': 130,
            'rainfall_threshold_mm': 20.0,
            'predicted_depth_cm': 55.0,
            'duration_hours': 6.0,
            'severity': 'very_high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(1, 3),
            'description': 'Hầm chui đường cao tốc, ngập thường xuyên',
            'recommendations': 'Cải tạo hệ thống thoát nước hầm chui',
            'managed_by': admin_user
        },
        {
            'name': 'Khu Tổng cục V - Bộ Công An',
            'flood_type': 'urban',
            'district': 'Nam Từ Liêm', 
            'ward': 'Mỹ Đình 1',
            'street': 'Khu vực Tổng cục V - Bộ Công An',
            'address': 'Khu vực Tổng cục V - Bộ Công An, Mỹ Đình 1, Nam Từ Liêm, Hà Nội',
            'location': Point(105.7725, 21.0205, srid=4326),
            'radius_meters': 160,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 45.0,
            'duration_hours': 3.0,
            'severity': 'very_high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(2, 7),
            'description': 'Khu vực cơ quan nhà nước quan trọng',
            'recommendations': 'Ưu tiên xử lý ngập, đảm bảo an ninh',
            'managed_by': admin_user
        },
        {
            'name': 'Triều Khúc (đối diện trường GTVT)',
            'flood_type': 'urban',
            'district': 'Thanh Xuân', 
            'ward': 'Triều Khúc',
            'street': 'Triều Khúc, đối diện trường Giao thông Vận tải',
            'address': 'Triều Khúc, đối diện trường Giao thông Vận tải, Triều Khúc, Thanh Xuân, Hà Nội',
            'location': Point(105.8205, 20.9845, srid=4326),
            'radius_meters': 120,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(7, 20),
            'description': 'Khu vực trường học, ngập ảnh hưởng đến sinh viên',
            'recommendations': 'Xử lý ngập trước cổng trường đại học',
            'managed_by': admin_user
        },
        {
            'name': 'Ngọc Hồi (số 611-673)',
            'flood_type': 'sewer',
            'district': 'Thanh Trì', 
            'ward': 'Ngọc Hồi',
            'street': 'Ngọc Hồi, từ số 611 đến 673',
            'address': 'Ngọc Hồi, từ số 611 đến 673, Ngọc Hồi, Thanh Trì, Hà Nội',
            'location': Point(105.8375, 20.9575, srid=4326),
            'radius_meters': 200,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 30.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(10, 25),
            'description': 'Khu vực ngoại thành, hệ thống thoát nước đơn giản',
            'recommendations': 'Xây dựng hệ thống thoát nước tập trung',
            'managed_by': admin_user
        },
        {
            'name': 'Triều Khúc (ngõ 97 đến Ao Đình)',
            'flood_type': 'rain',
            'district': 'Thanh Xuân', 
            'ward': 'Triều Khúc',
            'street': 'Triều Khúc, từ ngõ 97 đến Ao Đình',
            'address': 'Triều Khúc, từ ngõ 97 đến Ao Đình, Triều Khúc, Thanh Xuân, Hà Nội',
            'location': Point(105.8185, 20.9865, srid=4326),
            'radius_meters': 150,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 3.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(5, 15),
            'description': 'Khu vực gần ao, ngập theo mùa mưa',
            'recommendations': 'Nạo vét ao, xây dựng hệ thống thoát nước',
            'managed_by': admin_user
        },
        {
            'name': 'Chợ Hà Đông',
            'flood_type': 'rain',
            'district': 'Hà Đông', 
            'ward': 'Hà Cầu',
            'street': 'Khu vực chợ Hà Đông, giao Lê Lợi - Trần Hưng Đạo',
            'address': 'Khu vực chợ Hà Đông, giao Lê Lợi - Trần Hưng Đạo, Hà Cầu, Hà Đông, Hà Nội',
            'location': Point(105.7775, 20.9675, srid=4326),
            'radius_meters': 180,
            'rainfall_threshold_mm': 40.0,
            'predicted_depth_cm': 50.0,
            'duration_hours': 4.0,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(4, 14),
            'description': 'Khu chợ lớn, ngập ảnh hưởng đến kinh tế',
            'recommendations': 'Cải tạo thoát nước khu chợ trung tâm',
            'managed_by': admin_user
        },
        {
            'name': 'Trước trường THPT Nguyễn Huệ',
            'flood_type': 'urban',
            'district': 'Hà Đông', 
            'ward': 'Nguyễn Trãi',
            'street': 'Quang Trung, trước trường THPT Nguyễn Huệ',
            'address': 'Quang Trung, trước trường THPT Nguyễn Huệ, Nguyễn Trãi, Hà Đông, Hà Nội',
            'location': Point(105.7745, 20.9705, srid=4326),
            'radius_meters': 100,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(8, 22),
            'description': 'Trước cổng trường THPT, ảnh hưởng đến học sinh',
            'recommendations': 'Xử lý ngập trước cổng trường',
            'managed_by': admin_user
        },
        {
            'name': 'Đối diện nhà ga La Khê',
            'flood_type': 'rain',
            'district': 'Hà Đông', 
            'ward': 'La Khê',
            'street': 'Quang Trung, đối diện nhà ga La Khê',
            'address': 'Quang Trung, đối diện nhà ga La Khê, La Khê, Hà Đông, Hà Nội',
            'location': Point(105.7705, 20.9725, srid=4326),
            'radius_meters': 110,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 40.0,
            'duration_hours': 3.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(6, 18),
            'description': 'Khu vực nhà ga, ngập ảnh hưởng đến hành khách',
            'recommendations': 'Cải tạo thoát nước khu vực ga tàu',
            'managed_by': admin_user
        },
        {
            'name': 'Tổ dân phố 1+4 Yên Nghĩa',
            'flood_type': 'urban',
            'district': 'Hà Đông', 
            'ward': 'Yên Nghĩa',
            'street': 'Tổ dân phố số 1 và 4, phường Yên Nghĩa',
            'address': 'Tổ dân phố số 1 và 4, phường Yên Nghĩa, Hà Đông, Hà Nội',
            'location': Point(105.7645, 20.9645, srid=4326),
            'radius_meters': 130,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 30.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(9, 24),
            'description': 'Khu dân cư, hệ thống thoát nước cũ',
            'recommendations': 'Cải tạo hệ thống thoát nước khu dân cư',
            'managed_by': admin_user
        },
        {
            'name': 'Phố Xốm (đối diện Hải Phát)',
            'flood_type': 'rain',
            'district': 'Hà Đông', 
            'ward': 'Phú Lãm',
            'street': 'Phố Xốm, đoạn đối diện tòa nhà Hải Phát',
            'address': 'Phố Xốm, đoạn đối diện tòa nhà Hải Phát, Phú Lãm, Hà Đông, Hà Nội',
            'location': Point(105.7605, 20.9625, srid=4326),
            'radius_meters': 90,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(7, 20),
            'description': 'Khu vực thương mại, ngập ảnh hưởng đến tòa nhà văn phòng',
            'recommendations': 'Xử lý ngập trước tòa nhà cao tầng',
            'managed_by': admin_user
        },
        {
            'name': 'Yên Nghĩa (Bến xe đến ngã ba Ba La)',
            'flood_type': 'rain',
            'district': 'Hà Đông', 
            'ward': 'Yên Nghĩa',
            'street': 'Yên Nghĩa, từ Bến xe đến ngã ba Ba La',
            'address': 'Yên Nghĩa, từ Bến xe đến ngã ba Ba La, Yên Nghĩa, Hà Đông, Hà Nội',
            'location': Point(105.7625, 20.9605, srid=4326),
            'radius_meters': 200,
            'rainfall_threshold_mm': 45.0,
            'predicted_depth_cm': 55.0,
            'duration_hours': 4.5,
            'severity': 'high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(3, 11),
            'description': 'Điểm ngập đen, khu vực bến xe, giao thông quan trọng',
            'recommendations': 'Cải tạo thoát nước toàn tuyến đường',
            'managed_by': admin_user
        },
        {
            'name': 'Đường Quyết Thắng',
            'flood_type': 'urban',
            'district': 'Hà Đông', 
            'ward': 'Kiến Hưng',
            'street': 'Đường Quyết Thắng',
            'address': 'Đường Quyết Thắng, Kiến Hưng, Hà Đông, Hà Nội',
            'location': Point(105.7575, 20.9575, srid=4326),
            'radius_meters': 170,
            'rainfall_threshold_mm': 30.0,
            'predicted_depth_cm': 35.0,
            'duration_hours': 2.5,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(8, 22),
            'description': 'Đường chính khu đô thị mới, thoát nước chưa hoàn thiện',
            'recommendations': 'Hoàn thiện hệ thống thoát nước đô thị mới',
            'managed_by': admin_user
        },
        {
            'name': 'Khu TT18 Phú La',
            'flood_type': 'rain',
            'district': 'Hà Đông', 
            'ward': 'Phú La',
            'street': 'Khu TT18, phường Phú La',
            'address': 'Khu TT18, phường Phú La, Hà Đông, Hà Nội',
            'location': Point(105.7525, 20.9545, srid=4326),
            'radius_meters': 140,
            'rainfall_threshold_mm': 25.0,
            'predicted_depth_cm': 30.0,
            'duration_hours': 2.0,
            'severity': 'medium',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(10, 26),
            'description': 'Khu tái định cư, hệ thống thoát nước còn hạn chế',
            'recommendations': 'Nâng cấp hệ thống thoát nước khu tái định cư',
            'managed_by': admin_user
        },
        {
            'name': 'Võ Chí Công (Tòa nhà UDIC)',
            'flood_type': 'urban',
            'district': 'Tây Hồ', 
            'ward': 'Xuân La',
            'street': 'Võ Chí Công, trước tòa nhà UDIC',
            'address': 'Võ Chí Công, trước tòa nhà UDIC, Xuân La, Tây Hồ, Hà Nội',
            'location': Point(105.8075, 21.0825, srid=4326),
            'radius_meters': 110,
            'rainfall_threshold_mm': 35.0,
            'predicted_depth_cm': 45.0,
            'duration_hours': 3.0,
            'severity': 'very_high',
            'is_active': False,
            'is_monitored': True,
            'activation_count': random.randint(2, 8),
            'description': 'Khu vực tòa nhà cao tầng, ngập ảnh hưởng đến hoạt động văn phòng',
            'recommendations': 'Xử lý ngập trước tòa nhà trung tâm',
            'managed_by': admin_user
        }
    ]

    return fixed_floodings

def import_all_fixed_floodings():
    """Import tất cả dữ liệu điểm ngập cố định vào database"""
    created_count = 0
    updated_count = 0
    errors = []
    
    print("🚀 BẮT ĐẦU IMPORT DỮ LIỆU ĐIỂM NGẬP CỐ ĐỊNH")
    print("=" * 60)
    
    # Lấy danh sách tất cả các điểm ngập
    fixed_floodings = create_all_flood_zones()
    
    for i, flooding_data in enumerate(fixed_floodings, 1):
        try:
            # Kiểm tra xem đã tồn tại chưa
            existing = FixedFlooding.objects.filter(
                name=flooding_data['name'],
                district=flooding_data['district']
            ).first()
            
            if existing:
                # Cập nhật nếu đã tồn tại
                for key, value in flooding_data.items():
                    if hasattr(existing, key):  # Chỉ cập nhật các trường tồn tại
                        setattr(existing, key, value)
                existing.updated_at = timezone.now()
                
                # Thêm thời gian kích hoạt cuối nếu có số lần kích hoạt
                if existing.activation_count > 0 and not existing.last_activated:
                    existing.last_activated = timezone.now() - timedelta(days=random.randint(1, 30))
                
                existing.save()
                updated_count += 1
                print(f"✅ [{i:2d}/{len(fixed_floodings)}] Đã cập nhật: {flooding_data['name']}")
            else:
                # Tạo mới - chỉ lấy các trường hợp lệ
                valid_fields = {k: v for k, v in flooding_data.items() 
                               if hasattr(FixedFlooding, k)}
                
                flooding = FixedFlooding.objects.create(**valid_fields)
                
                # Thêm thời gian kích hoạt cuối nếu có số lần kích hoạt
                if flooding.activation_count > 0:
                    flooding.last_activated = timezone.now() - timedelta(days=random.randint(1, 30))
                    flooding.save()
                
                created_count += 1
                print(f"✅ [{i:2d}/{len(fixed_floodings)}] Đã tạo mới: {flooding_data['name']}")
                
        except Exception as e:
            errors.append((flooding_data['name'], str(e)))
            print(f"❌ [{i:2d}/{len(fixed_floodings)}] Lỗi khi import {flooding_data['name']}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"🎯 TỔNG KẾT IMPORT:")
    print(f"   - Đã tạo mới: {created_count} điểm ngập")
    print(f"   - Đã cập nhật: {updated_count} điểm ngập")
    print(f"   - Tổng cộng: {created_count + updated_count} / {len(fixed_floodings)}")
    
    if errors:
        print(f"   - Lỗi: {len(errors)} điểm")
        print("\n📋 CHI TIẾT LỖI:")
        for name, error in errors[:5]:
            print(f"     • {name}: {error}")
        if len(errors) > 5:
            print(f"     ... và {len(errors) - 5} lỗi khác")
    
    return created_count, updated_count, errors

def show_detailed_statistics():
    """Hiển thị thống kê chi tiết dữ liệu"""
    fixed_floodings = create_all_flood_zones()
    print(f"📊 TỔNG SỐ ĐIỂM NGẬP CỐ ĐỊNH: {len(fixed_floodings)}")
    
    # Phân tích theo quận
    from collections import Counter
    district_counter = Counter([zone['district'] for zone in fixed_floodings])
    print("\n📍 PHÂN BỐ THEO QUẬN/HUYỆN:")
    for district, count in district_counter.most_common():
        percentage = (count / len(fixed_floodings)) * 100
        print(f"   {district:<15}: {count:2d} điểm ({percentage:.1f}%)")
    
    # Phân tích theo loại ngập
    type_counter = Counter([zone['flood_type'] for zone in fixed_floodings])
    print("\n🌧️ PHÂN BỐ THEO LOẠI NGẬP:")
    type_names = {
        'rain': 'Mưa',
        'urban': 'Đô thị',
        'drainage': 'Thoát nước',
        'sewer': 'Cống',
        'tide': 'Triều',
        'river': 'Sông'
    }
    for flood_type, count in type_counter.most_common():
        name = type_names.get(flood_type, flood_type)
        percentage = (count / len(fixed_floodings)) * 100
        print(f"   {name:<10}: {count:2d} điểm ({percentage:.1f}%)")
    
    # Phân tích theo mức độ nghiêm trọng
    severity_counter = Counter([zone['severity'] for zone in fixed_floodings])
    print("\n⚠️ PHÂN BỐ THEO MỨC ĐỘ NGHIÊM TRỌNG:")
    severity_names = {
        'low': 'Thấp',
        'medium': 'Trung bình',
        'high': 'Cao',
        'very_high': 'Rất cao'
    }
    for severity, count in severity_counter.most_common():
        name = severity_names.get(severity, severity)
        percentage = (count / len(fixed_floodings)) * 100
        print(f"   {name:<12}: {count:2d} điểm ({percentage:.1f}%)")
    
    # Thống kê ngưỡng mưa
    rainfall_thresholds = [zone['rainfall_threshold_mm'] for zone in fixed_floodings]
    avg_rainfall = sum(rainfall_thresholds) / len(rainfall_thresholds)
    max_rainfall = max(rainfall_thresholds)
    min_rainfall = min(rainfall_thresholds)
    
    print("\n📈 THỐNG KÊ NGƯỠNG MƯA:")
    print(f"   - Trung bình: {avg_rainfall:.1f} mm/h")
    print(f"   - Cao nhất:  {max_rainfall:.1f} mm/h")
    print(f"   - Thấp nhất: {min_rainfall:.1f} mm/h")
    
    # Thống kê độ sâu dự báo
    predicted_depths = [zone['predicted_depth_cm'] for zone in fixed_floodings]
    avg_depth = sum(predicted_depths) / len(predicted_depths)
    max_depth = max(predicted_depths)
    min_depth = min(predicted_depths)
    
    print("\n📏 THỐNG KÊ ĐỘ SÂU DỰ BÁO:")
    print(f"   - Trung bình: {avg_depth:.1f} cm")
    print(f"   - Cao nhất:  {max_depth:.1f} cm")
    print(f"   - Thấp nhất: {min_depth:.1f} cm")
    
    # Tổng số lần kích hoạt ước tính
    total_activations = sum([zone.get('activation_count', 0) for zone in fixed_floodings])
    print(f"\n🔢 TỔNG SỐ LẦN KÍCH HOẠT ƯỚC TÍNH: {total_activations}")

def main():
    """Hàm chạy chính"""
    print("=" * 80)
    print("🔄 SCRIPT IMPORT DỮ LIỆU ĐIỂM NGẬP CỐ ĐỊNH HÀ NỘI")
    print("=" * 80)
    show_detailed_statistics()
    response = input("\n⚠️  Bạn có muốn xóa dữ liệu cũ trước khi import? (y/n): ")
    if response.lower() == 'y':
        clear_old_data()
    response = input("\n🚀 Bạn có muốn import dữ liệu mới? (y/n): ")
    if response.lower() == 'y':
        created, updated, errors = import_all_fixed_floodings()
        print("\n✅ IMPORT HOÀN TẤT!")
    else:
        print("\n⏸️  Đã hủy import.")

if __name__ == "__main__":
    main()