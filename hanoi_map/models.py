from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, Polygon
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.gis.db.models.functions import Distance
import json

class FloodZone(models.Model):
    """Vùng ngập lụt thực tế tại Hà Nội"""
    ZONE_TYPE_CHOICES = [
        ('black', 'Điểm đen ngập lụt'),
        ('frequent', 'Thường xuyên ngập'),
        ('seasonal', 'Ngập theo mùa'),
        ('rain', 'Ngập khi mưa lớn'),
        ('tide', 'Ngập triều cường'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Tên điểm ngập")
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPE_CHOICES, verbose_name="Loại ngập")
    geometry = models.PolygonField(srid=4326, verbose_name="Khu vực ngập")
    
    district = models.CharField(max_length=100, verbose_name="Quận")
    ward = models.CharField(max_length=100, verbose_name="Phường", blank=True)
    street = models.CharField(max_length=200, verbose_name="Tên đường/phố", blank=True)
    
    max_depth_cm = models.FloatField(verbose_name="Độ sâu tối đa (cm)", default=50)
    avg_duration_hours = models.FloatField(verbose_name="Thời gian ngập trung bình (giờ)", default=3)
    flood_cause = models.CharField(max_length=100, verbose_name="Nguyên nhân ngập", 
                                  default="Hệ thống thoát nước quá tải")
    
    is_active = models.BooleanField(verbose_name="Đang có nguy cơ", default=True)
    last_flood_date = models.DateField(verbose_name="Ngày ngập gần nhất", null=True, blank=True)
    last_reported_at = models.DateTimeField(verbose_name="Báo cáo gần nhất", null=True, blank=True)
    
    report_count = models.IntegerField(verbose_name="Số báo cáo", default=0)
    
    description = models.TextField(verbose_name="Mô tả chi tiết", blank=True)
    solution = models.TextField(verbose_name="Biện pháp xử lý", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.district}"
    
    class Meta:
        verbose_name = "Điểm ngập"
        verbose_name_plural = "Các điểm ngập"
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['district']),
        ]

class FloodReport(models.Model):
    """Báo cáo ngập từ người dân"""
    REPORT_STATUS = [
        ('pending', '⏳ Chờ xác nhận'),
        ('verified', '✅ Đã xác nhận'),
        ('false', '❌ Sai thông tin'),
        ('resolved', '🏁 Đã xử lý'),
    ]
    
    SEVERITY_CHOICES = [
        ('light', 'Nhẹ (dưới 20cm)'),
        ('medium', 'Trung bình (20-40cm)'),
        ('heavy', 'Nặng (40-70cm)'),
        ('severe', 'Rất nặng (trên 70cm)'),
    ]
    
    # Thông tin vị trí
    location = models.PointField(srid=4326, verbose_name="Vị trí báo cáo")
    address = models.TextField(verbose_name="Địa chỉ chi tiết")
    district = models.CharField(max_length=100, verbose_name="Quận/Huyện")
    ward = models.CharField(max_length=100, verbose_name="Phường/Xã", blank=True)
    street = models.CharField(max_length=200, verbose_name="Tên đường", blank=True)
    
    # Thông tin ngập
    water_depth = models.FloatField(verbose_name="Độ sâu nước (cm)")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name="Mức độ")
    area_size = models.CharField(max_length=50, verbose_name="Diện tích ngập", 
                                help_text="VD: 10m, cả mặt đường, 1 làn đường...")
    description = models.TextField(verbose_name="Mô tả tình hình", blank=True)
    
    # Hình ảnh
    photo_url = models.URLField(verbose_name="Link ảnh", blank=True)
    video_url = models.URLField(verbose_name="Link video", blank=True)
    
    # Người báo cáo
    reporter_name = models.CharField(max_length=100, verbose_name="Tên người báo", blank=True)
    reporter_phone = models.CharField(max_length=20, verbose_name="Số điện thoại", blank=True)
    reporter_email = models.EmailField(verbose_name="Email", blank=True)
    
    # Trạng thái xử lý
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='pending')
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, 
                                   null=True, blank=True, verbose_name="Xác nhận bởi")
    verification_notes = models.TextField(verbose_name="Ghi chú xác nhận", blank=True)
    verified_at = models.DateTimeField(verbose_name="Thời điểm xác nhận", null=True, blank=True)
    
    # Liên kết với điểm ngập
    flood_zone = models.ForeignKey(FloodZone, on_delete=models.SET_NULL, 
                                  null=True, blank=True, verbose_name="Thuộc điểm ngập",
                                  related_name='reports')
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Tự động xác định mức độ dựa trên độ sâu
        if self.water_depth < 20:
            self.severity = 'light'
        elif self.water_depth < 40:
            self.severity = 'medium'
        elif self.water_depth < 70:
            self.severity = 'heavy'
        else:
            self.severity = 'severe'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Báo cáo #{self.id} - {self.address[:50]}"
    
    class Meta:
        verbose_name = "Báo cáo ngập"
        verbose_name_plural = "Báo cáo ngập"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['district', 'severity']),
        ]

@receiver(post_save, sender=FloodReport)
def update_flood_zones_on_report_save(sender, instance, created, **kwargs):
    """Tự động tạo hoặc cập nhật FloodZone khi có báo cáo mới"""
    if instance.status == 'verified' and instance.location:
        try:
            # Tìm điểm ngập trong vòng 50m
            existing_zones = FloodZone.objects.annotate(
                distance=Distance('geometry', instance.location)
            ).filter(distance__lt=50)  # 50m
            
            if existing_zones.exists():
                # Cập nhật điểm ngập đã tồn tại
                zone = existing_zones.first()
                zone.max_depth_cm = max(zone.max_depth_cm, instance.water_depth)
                zone.last_reported_at = instance.created_at
                zone.last_flood_date = instance.created_at.date()
                zone.report_count = FloodReport.objects.filter(
                    flood_zone=zone, 
                    status='verified'
                ).count()
                zone.save()
                instance.flood_zone = zone
                instance.save()
            else:
                # Tạo điểm ngập mới
                from django.contrib.gis.geos import Polygon
                
                # Xác định loại điểm ngập
                if instance.water_depth > 70:
                    zone_type = 'black'
                elif instance.water_depth > 40:
                    zone_type = 'frequent'
                elif instance.water_depth > 20:
                    zone_type = 'seasonal'
                else:
                    zone_type = 'rain'
                
                # Tạo polygon từ điểm (buffer khoảng 20m)
                buffer_distance = 0.00018  # ~20m
                bbox = instance.location.buffer(buffer_distance).envelope
                
                zone_name = f"Điểm ngập {instance.district}"
                if instance.street:
                    zone_name += f" - {instance.street}"
                elif instance.ward:
                    zone_name += f" - {instance.ward}"
                
                zone = FloodZone.objects.create(
                    name=zone_name,
                    zone_type=zone_type,
                    geometry=bbox,
                    district=instance.district,
                    ward=instance.ward or '',
                    street=instance.street or '',
                    max_depth_cm=instance.water_depth,
                    last_reported_at=instance.created_at,
                    last_flood_date=instance.created_at.date(),
                    report_count=1,
                    description=f"Tạo từ báo cáo #{instance.id}: {instance.description[:100] if instance.description else 'Không có mô tả'}",
                    is_active=True
                )
                instance.flood_zone = zone
                instance.save()
                
        except Exception as e:
            print(f"❌ Lỗi tạo/cập nhật điểm ngập: {e}")



class WeatherForecast(models.Model):
    """Dự báo thời tiết cho các khu vực Hà Nội"""
    location = models.PointField(srid=4326, verbose_name="Vị trí")
    location_name = models.CharField(max_length=200, verbose_name="Tên khu vực", default="Hà Nội")
    
    # Dữ liệu hiện tại
    current_temp = models.FloatField(verbose_name="Nhiệt độ hiện tại (°C)")
    current_humidity = models.FloatField(verbose_name="Độ ẩm hiện tại (%)")
    current_rainfall = models.FloatField(verbose_name="Lượng mưa hiện tại (mm/h)", default=0)
    current_description = models.CharField(max_length=100, verbose_name="Mô tả")
    current_icon = models.CharField(max_length=10, verbose_name="Icon thời tiết")
    
    # Dự báo 3 giờ tiếp theo
    forecast_3h = models.JSONField(verbose_name="Dự báo 3h", default=dict)
    
    # Dự báo 24 giờ
    forecast_24h = models.JSONField(verbose_name="Dự báo 24h", default=dict)
    
    # Cảnh báo
    alerts = models.JSONField(verbose_name="Cảnh báo", default=list, blank=True)
    
    # Metadata - SỬA LẠI
    updated_at = models.DateTimeField(auto_now=True)
    valid_until = models.DateTimeField(verbose_name="Hiệu lực đến")
    
    class Meta:
        verbose_name = "Dự báo thời tiết"
        verbose_name_plural = "Dự báo thời tiết"
    
    def __str__(self):
        return f"Dự báo {self.location_name} - {self.updated_at.strftime('%H:%M')}"

class FloodPrediction(models.Model):
    """Dự đoán ngập dựa trên thời tiết và địa hình"""
    RISK_LEVEL_CHOICES = [
        ('very_low', 'Rất thấp'),
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('very_high', 'Rất cao'),
    ]
    location = models.PointField(srid=4326, verbose_name="Vị trí")
    address = models.CharField(max_length=300, verbose_name="Địa chỉ")
    district = models.CharField(max_length=100, verbose_name="Quận")
    prediction_time = models.DateTimeField(
        verbose_name="Thời điểm dự đoán", 
        default=timezone.now  
    )
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, verbose_name="Mức độ nguy cơ")
    predicted_depth_cm = models.FloatField(verbose_name="Độ sâu dự đoán (cm)", default=0)
    confidence = models.FloatField(
        verbose_name="Độ tin cậy (%)", 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Yếu tố ảnh hưởng
    rainfall_mm = models.FloatField(verbose_name="Lượng mưa (mm/h)")
    elevation = models.FloatField(verbose_name="Độ cao (m)", help_text="So với mực nước biển")
    distance_to_river = models.FloatField(verbose_name="Khoảng cách đến sông (m)", default=1000)
    drainage_capacity = models.CharField(
        max_length=50, 
        verbose_name="Khả năng thoát nước", 
        choices=[('good', 'Tốt'), ('average', 'Trung bình'), ('poor', 'Kém')]
    )
    
    # Giải thích
    reasons = models.JSONField(verbose_name="Nguyên nhân dự đoán", default=list)
    recommendations = models.TextField(verbose_name="Khuyến nghị", blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Dự đoán ngập"
        verbose_name_plural = "Dự đoán ngập"
        ordering = ['-prediction_time']
    
    def __str__(self):
        return f"Dự đoán {self.address} - {self.get_risk_level_display()}"