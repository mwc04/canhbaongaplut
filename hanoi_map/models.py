from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, Polygon
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.gis.db.models.functions import Distance
from django.contrib.auth.models import User
import json, traceback


# FLOOD ZONE MODEL

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
    district = models.CharField(max_length=100, verbose_name="Phường")
    ward = models.CharField(max_length=100, verbose_name="Xã", blank=True)
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


# FLOOD REPORT MODEL

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
    
    location = models.PointField(srid=4326, verbose_name="Vị trí báo cáo")
    address = models.TextField(verbose_name="Địa chỉ chi tiết")
    district = models.CharField(max_length=100, verbose_name="Phường")
    ward = models.CharField(max_length=100, verbose_name="Xã", blank=True)
    street = models.CharField(max_length=200, verbose_name="Tên đường", blank=True)
    water_depth = models.FloatField(verbose_name="Độ sâu nước (cm)")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name="Mức độ")
    area_size = models.CharField(max_length=50, verbose_name="Diện tích ngập", 
                                help_text="VD: 10m, cả mặt đường, 1 làn đường...")
    description = models.TextField(verbose_name="Mô tả tình hình", blank=True)
    photo_url = models.URLField(verbose_name="Link ảnh", blank=True)
    video_url = models.URLField(verbose_name="Link video", blank=True)
    reporter_name = models.CharField(max_length=100, verbose_name="Tên người báo", blank=True)
    reporter_phone = models.CharField(max_length=20, verbose_name="Số điện thoại", blank=True)
    reporter_email = models.EmailField(verbose_name="Email", blank=True)
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='pending')
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, 
                                   null=True, blank=True, verbose_name="Xác nhận bởi")
    verification_notes = models.TextField(verbose_name="Ghi chú xác nhận", blank=True)
    verified_at = models.DateTimeField(verbose_name="Thời điểm xác nhận", null=True, blank=True)
    flood_zone = models.ForeignKey(FloodZone, on_delete=models.SET_NULL, 
                                  null=True, blank=True, verbose_name="Thuộc điểm ngập",
                                  related_name='reports')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    source = models.CharField(
        max_length=50,
        verbose_name="Nguồn báo cáo",
        choices=[
            ('user', 'Người dân'),
            ('fixed_flooding_auto', 'FixedFlooding tự động'),
            ('fixed_flooding_admin', 'FixedFlooding từ admin'),
            ('prediction', 'Dự đoán'),
            ('sensor', 'Cảm biến'),
            ('manual', 'Thủ công'),
        ],
        default='user'
    )
    
    confidence_score = models.FloatField(
        verbose_name="Độ tin cậy",
        default=1.0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Độ tin cậy của báo cáo (0-1)"
    )
    
    estimated_duration_hours = models.FloatField(
        verbose_name="Thời gian ngập ước tính (giờ)",
        default=2.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(72)]
    )
    
    is_active = models.BooleanField(
        verbose_name="Đang hoạt động",
        default=True,
        help_text="Cảnh báo này còn hiệu lực không"
    )
    
    def save(self, *args, **kwargs):
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
            existing_zones = FloodZone.objects.annotate(
                distance=Distance('geometry', instance.location)
            ).filter(distance__lt=50)  # 50m
            
            if existing_zones.exists():
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
                from django.contrib.gis.geos import Polygon
                if instance.water_depth > 70:
                    zone_type = 'black'
                elif instance.water_depth > 40:
                    zone_type = 'frequent'
                elif instance.water_depth > 20:
                    zone_type = 'seasonal'
                else:
                    zone_type = 'rain'
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


# FIXED FLOODING MODEL

class FixedFlooding(models.Model):
    """Điểm ngập cố định - tự động kích hoạt khi lượng mưa vượt ngưỡng"""
    FLOOD_TYPE_CHOICES = [
        ('rain', 'Ngập do mưa'),
        ('tide', 'Ngập do triều'),
        ('river', 'Ngập do sông'),
        ('drainage', 'Ngập do thoát nước'),
        ('sewer', 'Ngập do cống'),
        ('urban', 'Ngập đô thị'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('very_high', 'Rất cao'),
    ]
    
    # Thông tin cơ bản
    name = models.CharField(
        max_length=200, 
        verbose_name="Tên điểm ngập",
        help_text="Tên điểm ngập cố định"
    )
    flood_type = models.CharField(
        max_length=20, 
        choices=FLOOD_TYPE_CHOICES, 
        default='rain', 
        verbose_name="Loại ngập"
    )
    
    # Vị trí
    location = models.PointField(
        srid=4326, 
        verbose_name="Vị trí trung tâm",
        help_text="Điểm trung tâm khu vực ngập"
    )
    address = models.CharField(
        max_length=300, 
        verbose_name="Địa chỉ"
    )
    district = models.CharField(
        max_length=100, 
        verbose_name="Quận/Huyện"
    )
    ward = models.CharField(
        max_length=100, 
        verbose_name="Phường/Xã", 
        blank=True
    )
    street = models.CharField(
        max_length=200, 
        verbose_name="Đường", 
        blank=True
    )
    
    # Thông số kỹ thuật
    radius_meters = models.FloatField(
        verbose_name="Bán kính ảnh hưởng (m)",
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text="Bán kính khu vực ngập từ điểm trung tâm (1-1000m)"
    )
    rainfall_threshold_mm = models.FloatField(
        verbose_name="Ngưỡng mưa kích hoạt (mm/h)",
        validators=[MinValueValidator(0.1), MaxValueValidator(500)],
        help_text="Lượng mưa tối thiểu để kích hoạt cảnh báo ngập"
    )
    predicted_depth_cm = models.FloatField(
        verbose_name="Độ sâu dự đoán (cm)",
        default=30.0,
        validators=[MinValueValidator(1), MaxValueValidator(300)],
        help_text="Độ sâu nước dự đoán khi vượt ngưỡng"
    )
    duration_hours = models.FloatField(
        verbose_name="Thời gian ngập dự kiến (giờ)",
        default=2.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(72)],
        help_text="Thời gian ngập dự kiến sau khi mưa"
    )
    
    # Thông tin hiển thị
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='medium',
        verbose_name="Mức độ nghiêm trọng"
    )
    description = models.TextField(
        verbose_name="Mô tả", 
        blank=True,
        help_text="Mô tả chi tiết về điểm ngập"
    )
    recommendations = models.TextField(
        verbose_name="Khuyến nghị",
        blank=True,
        help_text="Khuyến nghị cho người dân khi khu vực này ngập"
    )
    
    # Trạng thái
    is_active = models.BooleanField(
        verbose_name="Đang cảnh báo",
        default=False,
        help_text="Đang trong trạng thái cảnh báo ngập"
    )
    is_monitored = models.BooleanField(
        verbose_name="Được giám sát",
        default=True,
        help_text="Điểm ngập có được hệ thống giám sát tự động"
    )
    
    # Thống kê
    flood_history = models.JSONField(
        verbose_name="Lịch sử ngập",
        default=list,
        help_text="Danh sách các lần ngập đã xảy ra"
    )
    activation_count = models.IntegerField(
        verbose_name="Số lần kích hoạt",
        default=0
    )
    last_activated = models.DateTimeField(
        verbose_name="Kích hoạt lần cuối",
        null=True,
        blank=True
    )
    last_deactivated = models.DateTimeField(
        verbose_name="Tắt cảnh báo lần cuối",
        null=True,
        blank=True
    )
    
    # Liên kết
    flood_zone = models.ForeignKey(
        FloodZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Vùng ngập liên quan",
        related_name='fixed_floodings'
    )
    managed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Quản lý bởi",
        related_name='managed_floodings'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        status = "⚡" if self.is_active else "✅"
        return f"{status} {self.name} - {self.district}"
    
    def save(self, *args, **kwargs):
        """Tự động tính toán severity dựa trên predicted_depth_cm"""
        if self.predicted_depth_cm < 20:
            self.severity = 'low'
        elif self.predicted_depth_cm < 40:
            self.severity = 'medium'
        elif self.predicted_depth_cm < 70:
            self.severity = 'high'
        else:
            self.severity = 'very_high'
        super().save(*args, **kwargs)
    
    def activate_flood_warning(self, rainfall_mm, source="FloodPrediction"):
        """Kích hoạt cảnh báo ngập khi lượng mưa vượt ngưỡng"""
        if rainfall_mm >= self.rainfall_threshold_mm and not self.is_active:
            self.is_active = True
            self.last_activated = timezone.now()
            self.activation_count += 1
            
            # Thêm vào lịch sử
            history_entry = {
                'timestamp': timezone.now().isoformat(),
                'rainfall_mm': rainfall_mm,
                'threshold_mm': self.rainfall_threshold_mm,
                'predicted_depth_cm': self.predicted_depth_cm,
                'source': source,
                'action': 'activated',
                'duration_hours': self.duration_hours
            }
            
            self.flood_history.append(history_entry)
            
            # Giới hạn lịch sử 100 bản ghi
            if len(self.flood_history) > 100:
                self.flood_history = self.flood_history[-100:]
            
            self.save(update_fields=['is_active', 'last_activated', 'activation_count', 'flood_history'])
            return True
            
        elif rainfall_mm < self.rainfall_threshold_mm and self.is_active:
            # Tắt cảnh báo khi mưa giảm
            self.is_active = False
            self.last_deactivated = timezone.now()
            
            # Cập nhật lịch sử
            if self.flood_history:
                self.flood_history[-1]['deactivated_at'] = timezone.now().isoformat()
                self.flood_history[-1]['action'] = 'deactivated'
            
            self.save(update_fields=['is_active', 'last_deactivated', 'flood_history'])
            return False
        
        return None
    
    def get_flood_polygon(self):
        """Tạo Polygon từ điểm trung tâm và bán kính"""
        radius_degrees = self.radius_meters / 111320.0  # 1 độ ≈ 111,320m
        return self.location.buffer(radius_degrees).envelope
    
    def get_nearby_reports(self, hours=24):
        """Lấy báo cáo ngập gần đây trong khu vực"""
        from django.contrib.gis.db.models.functions import Distance
        
        flood_polygon = self.get_flood_polygon()
        time_threshold = timezone.now() - timezone.timedelta(hours=hours)
        
        return FloodReport.objects.filter(
            location__within=flood_polygon,
            created_at__gte=time_threshold,
            status='verified'
        ).annotate(
            distance=Distance('location', self.location)
        ).order_by('created_at')
    
    class Meta:
        verbose_name = "Điểm ngập cố định"
        verbose_name_plural = "Điểm ngập cố định"
        ordering = ['-is_active', 'severity', 'district']
        indexes = [
            models.Index(fields=['is_active', 'district']),
            models.Index(fields=['rainfall_threshold_mm']),
            models.Index(fields=['severity']),
        ]


# PRE_SAVE SIGNAL FOR FIXED FLOODING

@receiver(pre_save, sender=FixedFlooding)
def fixed_flooding_pre_save(sender, instance, **kwargs):
    """
    Lưu trạng thái cũ trước khi lưu
    """
    if instance.pk:
        try:
            old_instance = FixedFlooding.objects.get(pk=instance.pk)
            instance._pre_is_active = old_instance.is_active
            instance._pre_is_monitored = old_instance.is_monitored
        except FixedFlooding.DoesNotExist:
            instance._pre_is_active = None
            instance._pre_is_monitored = None
    else:
        instance._pre_is_active = None
        instance._pre_is_monitored = None


# HELPER FUNCTIONS FOR FIXED FLOODING

def _create_flood_report_from_fixed_flooding(fixed_flooding):
    """Hàm helper tạo FloodReport từ FixedFlooding"""
    from django.utils import timezone
    from django.contrib.gis.db.models.functions import Distance
    
    try:
        print(f"📝 Bắt đầu tạo FloodReport từ FixedFlooding #{fixed_flooding.id}")
        time_threshold = timezone.now() - timezone.timedelta(hours=1)
        recent_report = FloodReport.objects.filter(
            location__distance_lte=(fixed_flooding.location, fixed_flooding.radius_meters),
            created_at__gte=time_threshold,
            status='verified'
        ).exists()
        
        if not recent_report:
            # Tạo mô tả chi tiết
            flood_type_display = fixed_flooding.get_flood_type_display()
            severity_display = fixed_flooding.get_severity_display()
            
            description = f"""
📍 **Điểm ngập cố định đã được kích hoạt:**
• Tên điểm: {fixed_flooding.name}
• Địa chỉ: {fixed_flooding.address}
• Quận/Huyện: {fixed_flooding.district}
• Ngưỡng mưa: {fixed_flooding.rainfall_threshold_mm} mm/h
• Độ sâu dự báo: {fixed_flooding.predicted_depth_cm} cm
• Thời gian ngập dự kiến: {fixed_flooding.duration_hours} giờ
• Loại ngập: {flood_type_display}
• Mức độ: {severity_display}

💡 **Khuyến nghị từ hệ thống:**
{fixed_flooding.recommendations or 'Di chuyển phương tiện đến nơi cao, tránh đi qua khu vực ngập.'}

⚠️ **Đây là cảnh báo tự động từ hệ thống FixedFlooding.**
"""
            
            report = FloodReport.objects.create(
                location=fixed_flooding.location,
                address=fixed_flooding.address,
                district=fixed_flooding.district,
                ward=fixed_flooding.ward or '',
                street=fixed_flooding.street or '',
                water_depth=fixed_flooding.predicted_depth_cm,
                severity=fixed_flooding.severity,
                area_size=f"Khu vực bán kính {fixed_flooding.radius_meters}m",
                description=description.strip(),
                source='fixed_flooding_admin',
                status='verified',
                verified_at=timezone.now(),
                confidence_score=0.95,
                estimated_duration_hours=fixed_flooding.duration_hours,
                is_active=True,
                reporter_name="Hệ thống FixedFlooding"
            )
            
            print(f"✅ Đã tạo FloodReport #{report.id} từ FixedFlooding #{fixed_flooding.id}")
            try:
                from .services import FloodZoneService
                FloodZoneService.create_or_update_from_fixed_flooding(
                    fixed_flooding, 
                    fixed_flooding.rainfall_threshold_mm
                )
            except Exception as e:
                print(f"⚠️ Lỗi tạo FloodZone: {e}")
                traceback.print_exc()
            try:
                from .services import FloodHistoryService
                FloodHistoryService.create_from_fixed_flooding(
                    fixed_flooding,
                    fixed_flooding.rainfall_threshold_mm
                )
            except Exception as e:
                print(f"⚠️ Lỗi tạo lịch sử: {e}")
                traceback.print_exc()
            
            return report
        else:
            print(f"ℹ️ Đã có FloodReport gần đây cho FixedFlooding #{fixed_flooding.id}, bỏ qua...")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi tạo FloodReport từ FixedFlooding: {e}")
        traceback.print_exc()
        return None

def _deactivate_flood_reports(fixed_flooding):
    """Hàm helper cập nhật FloodReport khi FixedFlooding bị tắt"""
    from django.utils import timezone
    
    try:
        time_threshold = timezone.now() - timezone.timedelta(hours=6)
        recent_reports = FloodReport.objects.filter(
            location__distance_lte=(fixed_flooding.location, fixed_flooding.radius_meters),
            created_at__gte=time_threshold,
            status='verified',
            is_active=True
        )
        
        for report in recent_reports:
            report.description += f"\n\n🔄 **CẬP NHẬT LÚC {timezone.now().strftime('%H:%M %d/%m/%Y')}:**\n• Điểm ngập {fixed_flooding.name} đã tắt cảnh báo."
            report.is_active = False
            report.save(update_fields=['description', 'is_active'])
            print(f"✅ Đã cập nhật FloodReport #{report.id}")
            
    except Exception as e:
        print(f"⚠️ Lỗi cập nhật FloodReport: {e}")
        traceback.print_exc()


# POST_SAVE SIGNAL FOR FIXED FLOODING

@receiver(post_save, sender=FixedFlooding)
def handle_fixed_flooding_activation(sender, instance, created, **kwargs):
    """
    Tạo FloodReport khi FixedFlooding được kích hoạt từ admin hoặc tự động
    """
    from django.utils import timezone
    
    try:
        print(f"🔔 Signal FixedFlooding được gọi:")
        print(f"   - ID: {instance.id}")
        print(f"   - Created: {created}")
        print(f"   - is_active mới: {instance.is_active}")
        print(f"   - is_active cũ: {getattr(instance, '_pre_is_active', 'N/A')}")
        if created and instance.is_active:
            print(f"⚡ FixedFlooding #{instance.id} tạo mới với is_active=True, tạo FloodReport...")
            _create_flood_report_from_fixed_flooding(instance)
        elif hasattr(instance, '_pre_is_active') and instance.is_active and not instance._pre_is_active:
            print(f"⚡ FixedFlooding #{instance.id} được kích hoạt từ admin (False -> True), tạo FloodReport...")
            _create_flood_report_from_fixed_flooding(instance)
        elif hasattr(instance, '_pre_is_active') and not instance.is_active and instance._pre_is_active:
            print(f"⭕ FixedFlooding #{instance.id} bị tắt (True -> False), cập nhật trạng thái...")
            _deactivate_flood_reports(instance)
            
    except Exception as e:
        print(f"❌ Lỗi signal FixedFlooding: {e}")
        traceback.print_exc()

# FLOOD PREDICTION MODEL
class FloodPrediction(models.Model):
    """Dự đoán ngập dựa trên thời tiết và địa hình"""
    RISK_LEVEL_CHOICES = [
        ('very_low', 'Rất thấp'),
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('very_high', 'Rất cao'),
    ]
    
    DRAINAGE_CHOICES = [
        ('good', 'Tốt'),
        ('average', 'Trung bình'), 
        ('poor', 'Kém'),
        ('very_poor', 'Rất kém'),
    ]
    
    # Vị trí
    location = models.PointField(
        srid=4326, 
        verbose_name="Vị trí dự đoán"
    )
    address = models.CharField(
        max_length=300, 
        verbose_name="Địa chỉ"
    )
    district = models.CharField(
        max_length=100, 
        verbose_name="Quận"
    )
    ward = models.CharField(
        max_length=100, 
        verbose_name="Phường", 
        blank=True
    )
    
    # Thông số dự đoán
    prediction_time = models.DateTimeField(
        verbose_name="Thời điểm dự đoán", 
        default=timezone.now
    )
    valid_until = models.DateTimeField(
        verbose_name="Có hiệu lực đến",
        help_text="Thời gian dự đoán còn hiệu lực"
    )
    risk_level = models.CharField(
        max_length=20, 
        choices=RISK_LEVEL_CHOICES, 
        verbose_name="Mức độ nguy cơ"
    )
    predicted_depth_cm = models.FloatField(
        verbose_name="Độ sâu dự đoán (cm)", 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(500)]
    )
    confidence = models.FloatField(
        verbose_name="Độ tin cậy (%)", 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=70.0
    )
    
    # Nguyên nhân
    rainfall_mm = models.FloatField(
        verbose_name="Lượng mưa (mm/h)",
        validators=[MinValueValidator(0)]
    )
    rainfall_duration_hours = models.FloatField(
        verbose_name="Thời gian mưa (giờ)",
        default=1.0,
        validators=[MinValueValidator(0.1)]
    )
    elevation = models.FloatField(
        verbose_name="Độ cao (m)", 
        help_text="So với mực nước biển"
    )
    distance_to_river = models.FloatField(
        verbose_name="Khoảng cách đến sông (m)", 
        default=1000
    )
    drainage_capacity = models.CharField(
        max_length=20, 
        choices=DRAINAGE_CHOICES,
        default='average',
        verbose_name="Khả năng thoát nước"
    )
    
    # Thông tin bổ sung
    reasons = models.JSONField(
        verbose_name="Nguyên nhân dự đoán", 
        default=list,
        help_text="Danh sách nguyên nhân gây ngập"
    )
    recommendations = models.TextField(
        verbose_name="Khuyến nghị", 
        blank=True
    )
    affected_areas = models.TextField(
        verbose_name="Khu vực ảnh hưởng",
        blank=True,
        help_text="Mô tả chi tiết khu vực bị ảnh hưởng"
    )
    
    # Liên kết
    fixed_flooding = models.ForeignKey(
        FixedFlooding,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Điểm ngập cố định liên quan",
        related_name='predictions'
    )
    flood_zone = models.ForeignKey(
        FloodZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Vùng ngập liên quan",
        related_name='predictions'
    )
    
    # Trạng thái
    warning_triggered = models.BooleanField(
        verbose_name="Đã kích hoạt cảnh báo",
        default=False
    )
    is_active = models.BooleanField(
        verbose_name="Còn hiệu lực",
        default=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    estimated_drainage_time_hours = models.FloatField(
        verbose_name="Thời gian cạn dự kiến (giờ)",
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Dự đoán thời gian để nước rút hết",
        null=True,  # Cho phép null nếu chưa tính
        blank=True
    )
    
    drainage_start_time = models.DateTimeField(
        verbose_name="Thời điểm bắt đầu rút nước",
        null=True,
        blank=True
    )
    
    current_depth_cm = models.FloatField(
        verbose_name="Độ sâu hiện tại (cm)",
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    last_depth_update = models.DateTimeField(
        verbose_name="Cập nhật độ sâu lần cuối",
        null=True,
        blank=True
    )
    
    # Liên kết với FloodReport
    flood_report = models.ForeignKey(
        'FloodReport',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Báo cáo ngập liên quan",
        related_name='predictions'
    )
    
    def __str__(self):
        return f"Dự đoán {self.address} - {self.get_risk_level_display()}"
    
    def save(self, *args, **kwargs):
        """Tự động tính toán valid_until và risk_level"""
        # Mặc định valid trong 3 giờ
        if not self.valid_until:
            self.valid_until = self.prediction_time + timezone.timedelta(hours=3)
        
        # Tính risk_level dựa trên các yếu tố
        if not self.risk_level or kwargs.get('force_recalculate', False):
            self.risk_level = self.calculate_risk_level()
        
        super().save(*args, **kwargs)
    
    def calculate_risk_level(self):
        """Tính toán mức độ rủi ro dựa trên các yếu tố"""
        score = 0
        
        # Điểm cho lượng mưa
        if self.rainfall_mm >= 50:
            score += 30
        elif self.rainfall_mm >= 30:
            score += 20
        elif self.rainfall_mm >= 20:
            score += 10
        
        # Điểm cho thời gian mưa
        if self.rainfall_duration_hours >= 3:
            score += 20
        elif self.rainfall_duration_hours >= 1:
            score += 10
        
        # Điểm cho khả năng thoát nước
        drainage_scores = {
            'very_poor': 25,
            'poor': 15,
            'average': 5,
            'good': 0
        }
        score += drainage_scores.get(self.drainage_capacity, 0)
        
        # Điểm cho khoảng cách đến sông
        if self.distance_to_river < 100:
            score += 15
        elif self.distance_to_river < 500:
            score += 10
        
        # Xác định risk_level
        if score >= 60:
            return 'very_high'
        elif score >= 45:
            return 'high'
        elif score >= 30:
            return 'medium'
        elif score >= 15:
            return 'low'
        else:
            return 'very_low'
    
    def check_and_activate_fixed_flooding(self):
        """Kiểm tra và kích hoạt FixedFlooding nếu lượng mưa vượt ngưỡng"""
        activated_floodings = []
        
        if self.rainfall_mm > 0:
            # Tìm các FixedFlooding trong bán kính 2km
            nearby_floodings = FixedFlooding.objects.annotate(
                distance=Distance('location', self.location)
            ).filter(
                distance__lt=2000,  # 2km
                is_monitored=True
            )
            
            for flooding in nearby_floodings:
                result = flooding.activate_flood_warning(
                    self.rainfall_mm, 
                    f"FloodPrediction #{self.id}"
                )
                
                if result is True:
                    activated_floodings.append(flooding)
                    self.fixed_flooding = flooding
                    self.warning_triggered = True
        
        if activated_floodings:
            self.save(update_fields=['fixed_flooding', 'warning_triggered'])
        
        return activated_floodings
    
    def create_flood_zone_from_prediction(self):
        """Tạo FloodZone mới từ dự đoán nếu cần"""
        if self.risk_level in ['high', 'very_high'] and self.predicted_depth_cm >= 20:
            try:
                # Tạo polygon buffer 50m
                buffer_distance = 0.00045  # ~50m
                bbox = self.location.buffer(buffer_distance).envelope
                
                zone_name = f"Dự đoán ngập {self.district}"
                if self.ward:
                    zone_name += f" - {self.ward}"
                
                zone = FloodZone.objects.create(
                    name=zone_name,
                    zone_type='rain',
                    geometry=bbox,
                    district=self.district,
                    ward=self.ward or '',
                    max_depth_cm=self.predicted_depth_cm,
                    flood_cause=f"Dự đoán: Mưa {self.rainfall_mm}mm/h",
                    is_active=True,
                    last_reported_at=timezone.now(),
                    last_flood_date=timezone.now().date(),
                    description=f"Tạo từ dự đoán #{self.id}. Nguyên nhân: {', '.join(self.reasons[:3]) if self.reasons else 'Không xác định'}",
                    report_count=0
                )
                
                self.flood_zone = zone
                self.save(update_fields=['flood_zone'])
                return zone
                
            except Exception as e:
                print(f"❌ Lỗi tạo FloodZone từ dự đoán: {e}")
        
        return None
    
    class Meta:
        verbose_name = "Dự đoán ngập"
        verbose_name_plural = "Dự đoán ngập"
        ordering = ['-prediction_time']
        indexes = [
            models.Index(fields=['risk_level', 'prediction_time']),
            models.Index(fields=['district', 'warning_triggered']),
            models.Index(fields=['is_active', 'valid_until']),
        ]

@receiver(post_save, sender=FloodPrediction)
def handle_flood_prediction_save(sender, instance, created, **kwargs):
    """Xử lý khi FloodPrediction được lưu"""
    if created:
        instance.check_and_activate_fixed_flooding()
        if instance.risk_level in ['high', 'very_high']:
            instance.create_flood_zone_from_prediction()


# FLOOD HISTORY MODEL

class FloodHistory(models.Model):
    """Lưu lịch sử ngập chi tiết"""
    SOURCE_CHOICES = [
        ('report', 'Báo cáo'),
        ('prediction', 'Dự đoán'),
        ('sensor', 'Cảm biến'),
        ('fixed', 'Điểm cố định'),
        ('manual', 'Thủ công'),
    ]
    
    # Thông tin cơ bản
    location = models.PointField(
        srid=4326,
        verbose_name="Vị trí"
    )
    address = models.CharField(
        max_length=300,
        verbose_name="Địa chỉ",
        blank=True
    )
    district = models.CharField(
        max_length=100,
        verbose_name="Quận"
    )
    
    # Thông số ngập
    flood_type = models.CharField(
        max_length=50,
        verbose_name="Loại ngập"
    )
    rainfall_mm = models.FloatField(
        verbose_name="Lượng mưa (mm/h)",
        null=True,
        blank=True
    )
    water_depth_cm = models.FloatField(
        verbose_name="Độ sâu nước (cm)"
    )
    duration_minutes = models.IntegerField(
        verbose_name="Thời gian ngập (phút)"
    )
    affected_area_sqm = models.FloatField(
        verbose_name="Diện tích ảnh hưởng (m²)",
        null=True,
        blank=True
    )
    
    # Thời gian
    start_time = models.DateTimeField(
        verbose_name="Thời điểm bắt đầu"
    )
    end_time = models.DateTimeField(
        verbose_name="Thời điểm kết thúc",
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(
        verbose_name="Thời điểm ghi nhận",
        default=timezone.now
    )
    
    # Nguồn dữ liệu
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        verbose_name="Nguồn dữ liệu"
    )
    source_id = models.CharField(
        max_length=100,
        verbose_name="ID nguồn",
        blank=True,
        help_text="ID của bản ghi gốc (report ID, prediction ID, etc.)"
    )
    
    # Liên kết
    related_zone = models.ForeignKey(
        FloodZone,
        on_delete=models.CASCADE,
        verbose_name="Vùng ngập liên quan",
        related_name='histories'
    )
    related_report = models.ForeignKey(
        FloodReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Báo cáo liên quan",
        related_name='histories'
    )
    related_prediction = models.ForeignKey(
        FloodPrediction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Dự đoán liên quan"
    )
    related_fixed_flooding = models.ForeignKey(
        FixedFlooding,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Điểm cố định liên quan"
    )
    
    # Thông tin bổ sung
    severity = models.CharField(
        max_length=20,
        choices=FloodReport.SEVERITY_CHOICES,
        verbose_name="Mức độ"
    )
    description = models.TextField(
        verbose_name="Mô tả",
        blank=True
    )
    impact_level = models.CharField(
        max_length=20,
        choices=[
            ('minor', 'Nhẹ'),
            ('moderate', 'Trung bình'),
            ('major', 'Nặng'),
            ('severe', 'Nghiêm trọng'),
        ],
        default='minor',
        verbose_name="Mức độ ảnh hưởng"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Lịch sử ngập {self.district} - {self.start_time.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        """Tự động tính toán duration_minutes nếu có end_time"""
        if self.start_time and self.end_time and self.end_time > self.start_time:
            duration = (self.end_time - self.start_time).total_seconds() / 60
            self.duration_minutes = int(duration)
        
        # Tự động tính severity
        if self.water_depth_cm < 20:
            self.severity = 'light'
        elif self.water_depth_cm < 40:
            self.severity = 'medium'
        elif self.water_depth_cm < 70:
            self.severity = 'heavy'
        else:
            self.severity = 'severe'
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Lịch sử ngập"
        verbose_name_plural = "Lịch sử ngập"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'location']),
            models.Index(fields=['district', 'start_time']),
            models.Index(fields=['source', 'severity']),
        ]

@receiver(post_save, sender=FloodReport)
def handle_flood_report_save(sender, instance, created, **kwargs):
    """Ghi lịch sử khi báo cáo được tạo"""
    if created and instance.status == 'verified':
        from .services import FloodHistoryService
        FloodHistoryService.create_from_report(instance)