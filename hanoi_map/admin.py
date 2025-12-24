# hanoi_map/admin.py - PHIÊN BẢN ĐÃ SỬA LỖI HOÀN CHỈNH
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponse
import csv
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q

from .models import FloodZone, FloodReport, FloodPrediction, FixedFlooding, FloodHistory

# =============================================================================
# FLOOD ZONE ADMIN - SỬA LỖI TRƯỚC
# =============================================================================
@admin.register(FloodZone)
class FloodZoneAdmin(GISModelAdmin):
    """Admin configuration for FloodZone model"""
    list_display = [
        'name',
        'zone_type',
        'district',
        'max_depth_cm',
        'is_active',
        'last_flood_date',
        'report_count',
    ]
    list_filter = ['zone_type', 'district', 'is_active']
    search_fields = ['name', 'district', 'description']
    fieldsets = (
        ('📝 THÔNG TIN CƠ BẢN', {
            'fields': ('name', 'zone_type', 'district', 'ward', 'street')
        }),
        ('💧 ĐẶC ĐIỂM NGẬP', {
            'fields': ('max_depth_cm', 'avg_duration_hours', 'flood_cause')
        }),
        ('🗺️ VỊ TRÍ BẢN ĐỒ', {
            'fields': ('geometry',)
        }),
        ('⚡ TRẠNG THÁI', {
            'fields': ('is_active', 'last_flood_date')
        }),
    )
    
    # người dùng actions
    actions = ['activate_zones', 'deactivate_zones']
    
    def activate_zones(self, request, queryset):
        """Activate selected flood zones"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f"✅ Đã kích hoạt {updated} điểm ngập", 
            messages.SUCCESS
        )
    activate_zones.short_description = "✅ Kích hoạt điểm ngập"
    
    def deactivate_zones(self, request, queryset):
        """Deactivate selected flood zones"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f"⭕ Đã tắt {updated} điểm ngập", 
            messages.WARNING
        )
    deactivate_zones.short_description = "⭕ Tắt điểm ngập"

# =============================================================================
# FLOOD REPORT ADMIN
# =============================================================================
@admin.register(FloodReport)
class FloodReportAdmin(GISModelAdmin):
    """Admin configuration for FloodReport model"""
    list_display = [
        'id',
        'address_display',
        'water_depth',
        'district',
        'status',
        'created_at_display',
    ]
    list_filter = ['status', 'severity', 'district']
    search_fields = ['address', 'district', 'description']
    fieldsets = (
        ('📍 THÔNG TIN VỊ TRÍ', {
            'fields': ('location', 'address', 'district', 'ward', 'street')
        }),
        ('💧 THÔNG TIN NGẬP', {
            'fields': ('water_depth', 'severity', 'area_size', 'description')
        }),
        ('👤 THÔNG TIN NGƯỜI BÁO CÁO', {
            'fields': ('reporter_name', 'reporter_phone', 'reporter_email')
        }),
        ('✅ XỬ LÝ BÁO CÁO', {
            'fields': ('status', 'verified_by', 'verification_notes', 'flood_zone')
        }),
    )
    
    actions = ['mark_as_verified', 'mark_as_resolved', 'export_to_csv']
    
    def address_display(self, obj):
        """Display truncated address for list view"""
        if len(obj.address) > 50:
            return f"{obj.address[:50]}..."
        return obj.address
    address_display.short_description = 'ĐỊA CHỈ'
    address_display.admin_order_field = 'address'
    
    def created_at_display(self, obj):
        """Format datetime for display"""
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_at_display.short_description = 'THỜI GIAN'
    created_at_display.admin_order_field = 'created_at'
    
    def mark_as_verified(self, request, queryset):
        """Mark selected reports as verified"""
        updated = queryset.update(status='verified')
        self.message_user(
            request, 
            f"✅ Đã xác nhận {updated} báo cáo", 
            messages.SUCCESS
        )
    mark_as_verified.short_description = "✅ Xác nhận báo cáo đã chọn"
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected reports as resolved"""
        updated = queryset.update(status='resolved')
        self.message_user(
            request, 
            f"🔄 Đã đánh dấu {updated} báo cáo đã xử lý", 
            messages.INFO
        )
    mark_as_resolved.short_description = "🔄 Đánh dấu đã xử lý"
    
    def export_to_csv(self, request, queryset):
        """Export selected reports to CSV"""
        response = HttpResponse(
            content_type='text/csv',
            charset='utf-8-sig' 
        )
        response['Content-Disposition'] = 'attachment; filename="flood_reports.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 
            'ĐỊA CHỈ', 
            'QUẬN/HUYỆN', 
            'ĐỘ SÂU (cm)', 
            'TRẠNG THÁI',
            'THỜI GIAN BÁO CÁO'
        ])
        
        # Write data
        for report in queryset:
            writer.writerow([
                report.id,
                report.address[:100],
                report.district,
                report.water_depth,
                report.get_status_display(),
                report.created_at.strftime('%d/%m/%Y %H:%M:%S')
            ])
        
        return response
    export_to_csv.short_description = "📊 Xuất CSV"

# =============================================================================
# FIXED FLOODING ADMIN - PHẦN QUAN TRỌNG NHẤT ĐÃ SỬA
# =============================================================================
@admin.register(FixedFlooding)
class FixedFloodingAdmin(GISModelAdmin):
    """Admin configuration for FixedFlooding model"""
    
    # QUAN TRỌNG: Đặt list_display trước các methods
    list_display = [
        'name',
        'district',
        'flood_type_display',
        'rainfall_threshold_mm',
        'predicted_depth_cm',
        'severity_display',
        'active_status_display',  # Đổi tên thành active_status_display
        'monitored_status_display',  # Đổi tên thành monitored_status_display
        'activation_count',
        'last_activated_display',
    ]
    
    list_filter = ['flood_type', 'district', 'is_active', 'is_monitored', 'severity']
    search_fields = ['name', 'address', 'district', 'ward', 'description']
    list_per_page = 50
    readonly_fields = ['created_at', 'updated_at', 'last_activated', 'last_deactivated', 
                       'activation_count', 'flood_history']
    
    fieldsets = (
        ('📝 THÔNG TIN CƠ BẢN', {
            'fields': ('name', 'flood_type', 'address', 'district', 'ward', 'street')
        }),
        ('📍 VỊ TRÍ', {
            'fields': ('location', 'radius_meters')
        }),
        ('🌧️ THÔNG SỐ KÍCH HOẠT', {
            'fields': ('rainfall_threshold_mm', 'predicted_depth_cm', 'duration_hours', 'severity')
        }),
        ('⚡ TRẠNG THÁI', {
            'fields': ('is_active', 'is_monitored', 'last_activated', 'last_deactivated', 'activation_count')
        }),
        ('📊 LỊCH SỬ & THỐNG KÊ', {
            'fields': ('flood_history',)
        }),
        ('📋 THÔNG TIN BỔ SUNG', {
            'fields': ('description', 'recommendations', 'flood_zone', 'managed_by')
        }),
        ('📅 THỜI GIAN', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['activate_monitoring', 'deactivate_monitoring', 'test_activation', 'export_to_csv']
    
    # CÁCH 1: Dùng mark_safe (đơn giản)
    def flood_type_display(self, obj):
        """Display flood type"""
        if not obj:
            return ""
        
        type_config = {
            'rain': ('info', '🌧️'),
            'tide': ('primary', '🌊'),
            'river': ('success', '🌊'),
            'drainage': ('warning', '🚰'),
            'sewer': ('secondary', '🕳️'),
            'urban': ('dark', '🏙️'),
        }
        color, icon = type_config.get(obj.flood_type, ('secondary', '❓'))
        display_text = obj.get_flood_type_display() if hasattr(obj, 'get_flood_type_display') else obj.flood_type
        return mark_safe(f'<span class="badge bg-{color}">{icon}</span> {display_text}')
    flood_type_display.short_description = 'LOẠI NGẬP'
    
    def severity_display(self, obj):
        """Display severity"""
        if not obj:
            return ""
        
        severity_config = {
            'low': ('success', '🟢'),
            'medium': ('warning', '🟡'),
            'high': ('danger', '🔴'),
            'very_high': ('dark', '⚫'),
        }
        color, icon = severity_config.get(obj.severity, ('secondary', '⚪'))
        display_text = obj.get_severity_display() if hasattr(obj, 'get_severity_display') else obj.severity
        return mark_safe(f'<span class="badge bg-{color}">{icon}</span> {display_text}')
    severity_display.short_description = 'MỨC ĐỘ'
    
    def active_status_display(self, obj):
        """Display active status"""
        if not obj:
            return ""
        
        if obj.is_active:
            return mark_safe('<span class="badge bg-danger">⚡ ĐANG CẢNH BÁO</span>')
        else:
            return mark_safe('<span class="badge bg-success">✅ ĐANG THEO DÕI</span>')
    active_status_display.short_description = 'TRẠNG THÁI'
    
    def monitored_status_display(self, obj):
        """Display monitored status"""
        if not obj:
            return ""
        
        if obj.is_monitored:
            return mark_safe('<span class="badge bg-info">📡 ĐANG GIÁM SÁT</span>')
        else:
            return mark_safe('<span class="badge bg-secondary">⏸️ TẠM DỪNG</span>')
    monitored_status_display.short_description = 'GIÁM SÁT'
    
    # CÁCH 2: Dùng format_html (bảo mật hơn)
    """
    def active_status_display(self, obj):
        if not obj:
            return ""
        
        if obj.is_active:
            return format_html('<span class="badge bg-danger">{} ĐANG CẢNH BÁO</span>', '⚡')
        else:
            return format_html('<span class="badge bg-success">{} ĐANG THEO DÕI</span>', '✅')
    """
    
    def last_activated_display(self, obj):
        """Format last activated time"""
        if not obj or not obj.last_activated:
            return "Chưa kích hoạt"
        
        try:
            now = datetime.now()
            last_activated = obj.last_activated
            
            # Xử lý timezone
            if hasattr(last_activated, 'astimezone'):
                last_activated = last_activated.replace(tzinfo=None)
            
            diff = now - last_activated
            if diff.days > 0:
                return f"{diff.days} ngày trước"
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600} giờ trước"
            elif diff.seconds > 60:
                return f"{diff.seconds // 60} phút trước"
            else:
                return "Vừa xong"
        except Exception as e:
            print(f"⚠️ Lỗi format thời gian: {e}")
            return obj.last_activated.strftime('%d/%m %H:%M') if hasattr(obj.last_activated, 'strftime') else "Lỗi"
    last_activated_display.short_description = 'KÍCH HOẠT CUỐI'
    
    def activate_monitoring(self, request, queryset):
        """Enable monitoring for selected floodings"""
        updated = queryset.update(is_monitored=True)
        self.message_user(request, f"✅ Đã bật giám sát cho {updated} điểm ngập cố định", messages.SUCCESS)
    activate_monitoring.short_description = "✅ Bật giám sát"
    
    def deactivate_monitoring(self, request, queryset):
        """Disable monitoring for selected floodings"""
        updated = queryset.update(is_monitored=False)
        self.message_user(request, f"⭕ Đã tắt giám sát cho {updated} điểm ngập cố định", messages.WARNING)
    deactivate_monitoring.short_description = "⭕ Tắt giám sát"
    
    def test_activation(self, request, queryset):
        """Test activation of selected floodings"""
        from django.utils import timezone
        
        success_count = 0
        for flooding in queryset:
            try:
                flooding.is_active = True
                flooding.last_activated = timezone.now()
                flooding.activation_count += 1
                
                history_entry = {
                    'timestamp': timezone.now().isoformat(),
                    'rainfall_mm': flooding.rainfall_threshold_mm + 5,
                    'threshold_mm': flooding.rainfall_threshold_mm,
                    'predicted_depth_cm': flooding.predicted_depth_cm,
                    'source': 'manual_test',
                    'action': 'activated',
                    'duration_hours': flooding.duration_hours
                }
                
                flood_history = flooding.flood_history or []
                flood_history.append(history_entry)
                if len(flood_history) > 100:
                    flood_history = flood_history[-100:]
                
                flooding.flood_history = flood_history
                flooding.save()
                
                success_count += 1
            except Exception as e:
                print(f"❌ Lỗi test activation: {e}")
        
        self.message_user(request, f"⚡ Đã test kích hoạt {success_count}/{len(queryset)} điểm ngập cố định", messages.INFO)
    test_activation.short_description = "⚡ Test kích hoạt"
    
    def export_to_csv(self, request, queryset):
        """Export selected fixed floodings to CSV"""
        response = HttpResponse(
            content_type='text/csv',
            charset='utf-8-sig'
        )
        response['Content-Disposition'] = 'attachment; filename="fixed_floodings.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'TÊN', 'ĐỊA CHỈ', 'QUẬN/HUYỆN', 'LOẠI NGẬP', 'NGƯỠNG MƯA (mm/h)',
            'ĐỘ SÂU DỰ BÁO (cm)', 'TRẠNG THÁI', 'GIÁM SÁT', 'SỐ LẦN KÍCH HOẠT', 'KÍCH HOẠT CUỐI'
        ])
        
        for flooding in queryset:
            writer.writerow([
                flooding.id,
                flooding.name or "",
                flooding.address or "",
                flooding.district or "",
                flooding.get_flood_type_display() if hasattr(flooding, 'get_flood_type_display') else flooding.flood_type or "",
                flooding.rainfall_threshold_mm or 0,
                flooding.predicted_depth_cm or 0,
                'Đang cảnh báo' if flooding.is_active else 'Đang theo dõi',
                'Bật' if flooding.is_monitored else 'Tắt',
                flooding.activation_count or 0,
                flooding.last_activated.strftime('%d/%m/%Y %H:%M') if flooding.last_activated else ''
            ])
        
        return response
    export_to_csv.short_description = "📊 Xuất CSV"

    
# =============================================================================
# FLOOD HISTORY ADMIN
# =============================================================================
@admin.register(FloodHistory)
class FloodHistoryAdmin(GISModelAdmin):
    """Admin configuration for FloodHistory model"""
    list_display = [
        'district',
        'flood_type',
        'water_depth_cm',
        'history_severity',
        'history_source',
        'start_time_display',
        'duration_display',
        'impact_level_display',
    ]
    list_filter = ['source', 'flood_type', 'district', 'severity', 'impact_level', 'start_time']
    search_fields = ['address', 'district', 'description']
    list_per_page = 50
    readonly_fields = ['created_at', 'timestamp']
    fieldsets = (
        ('📍 THÔNG TIN VỊ TRÍ', {
            'fields': ('location', 'address', 'district')
        }),
        ('💧 THÔNG SỐ NGẬP', {
            'fields': ('flood_type', 'water_depth_cm', 'rainfall_mm', 'affected_area_sqm')
        }),
        ('⏰ THỜI GIAN', {
            'fields': ('start_time', 'end_time', 'duration_minutes', 'timestamp')
        }),
        ('📊 NGUỒN DỮ LIỆU', {
            'fields': ('source', 'source_id')
        }),
        ('🔗 LIÊN KẾT', {
            'fields': ('related_zone', 'related_report', 'related_prediction', 'related_fixed_flooding')
        }),
        ('📋 THÔNG TIN BỔ SUNG', {
            'fields': ('severity', 'impact_level', 'description')
        }),
        ('📅 THỜI GIAN TẠO', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['export_to_csv']
    
    def history_severity(self, obj):
        """Display severity"""
        if not obj:
            return ""
        
        severity_config = {
            'light': ('success', '🟢'),
            'medium': ('warning', '🟡'),
            'heavy': ('danger', '🔴'),
            'severe': ('dark', '⚫'),
        }
        color, icon = severity_config.get(obj.severity, ('secondary', '⚪'))
        return format_html(
            '<span class="badge bg-{}">{} {}</span>',
            color,
            icon,
            obj.get_severity_display() if hasattr(obj, 'get_severity_display') else obj.severity
        )
    history_severity.short_description = 'MỨC ĐỘ'
    
    def history_source(self, obj):
        """Display source"""
        if not obj:
            return ""
        
        source_config = {
            'report': ('info', '📢'),
            'prediction': ('warning', '🔮'),
            'sensor': ('success', '📡'),
            'fixed': ('danger', '⚡'),
            'manual': ('primary', '👤'),
        }
        color, icon = source_config.get(obj.source, ('secondary', '❓'))
        return format_html(
            '<span class="badge bg-{}">{} {}</span>',
            color,
            icon,
            obj.get_source_display() if hasattr(obj, 'get_source_display') else obj.source
        )
    history_source.short_description = 'NGUỒN'
    
    def start_time_display(self, obj):
        """Format start time"""
        if not obj or not obj.start_time:
            return ""
        return obj.start_time.strftime('%d/%m %H:%M')
    start_time_display.short_description = 'THỜI ĐIỂM'
    
    def duration_display(self, obj):
        """Format duration"""
        if not obj or not obj.duration_minutes:
            return "0m"
        
        if obj.duration_minutes >= 60:
            hours = obj.duration_minutes // 60
            minutes = obj.duration_minutes % 60
            return f"{hours}h{minutes}m"
        return f"{obj.duration_minutes}m"
    duration_display.short_description = 'THỜI GIAN'
    
    def impact_level_display(self, obj):
        """Display impact level"""
        if not obj:
            return ""
        
        impact_config = {
            'minor': ('success', '🟢'),
            'moderate': ('warning', '🟡'),
            'major': ('danger', '🔴'),
            'severe': ('dark', '⚫'),
        }
        color, icon = impact_config.get(obj.impact_level, ('secondary', '⚪'))
        return format_html(
            '<span class="badge bg-{}">{} {}</span>',
            color,
            icon,
            obj.get_impact_level_display() if hasattr(obj, 'get_impact_level_display') else obj.impact_level
        )
    impact_level_display.short_description = 'ẢNH HƯỞNG'
    
    def export_to_csv(self, request, queryset):
        """Export selected history records to CSV"""
        response = HttpResponse(
            content_type='text/csv',
            charset='utf-8-sig'
        )
        response['Content-Disposition'] = 'attachment; filename="flood_history.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 
            'QUẬN/HUYỆN',
            'ĐỊA CHỈ',
            'LOẠI NGẬP',
            'ĐỘ SÂU (cm)',
            'LƯỢNG MƯA (mm/h)',
            'THỜI GIAN BẮT ĐẦU',
            'THỜI GIAN KẾT THÚC',
            'THỜI LƯỢNG (phút)',
            'NGUỒN',
            'MỨC ĐỘ',
            'ẢNH HƯỞNG'
        ])
        
        for history in queryset:
            writer.writerow([
                history.id,
                history.district or "",
                history.address[:100] if history.address else "",
                history.flood_type or "",
                history.water_depth_cm or 0,
                history.rainfall_mm or 0,
                history.start_time.strftime('%d/%m/%Y %H:%M') if history.start_time else "",
                history.end_time.strftime('%d/%m/%Y %H:%M') if history.end_time else "",
                history.duration_minutes or 0,
                history.get_source_display() if hasattr(history, 'get_source_display') else history.source or "",
                history.get_severity_display() if hasattr(history, 'get_severity_display') else history.severity or "",
                history.get_impact_level_display() if hasattr(history, 'get_impact_level_display') else history.impact_level or ""
            ])
        
        return response
    export_to_csv.short_description = "📊 Xuất CSV"

# =============================================================================
# FLOOD PREDICTION ADMIN
# =============================================================================
@admin.register(FloodPrediction)
class FloodPredictionAdmin(admin.ModelAdmin):
    """Admin configuration for FloodPrediction model"""
    
    list_display = [
        'address',
        'district',
        'risk_level_display',
        'predicted_depth_cm',
        'rainfall_mm',
        'confidence_percentage',
        # 'warning_triggered_display',
        'prediction_time_display',
    ]
    
    list_filter = ['risk_level', 'district', 'warning_triggered', 'drainage_capacity']
    search_fields = ['address', 'district', 'description', 'recommendations']
    ordering = ['-prediction_time']
    readonly_fields = ['created_at', 'updated_at']
    
    # ========== CUSTOM METHODS ==========
    
    def risk_level_display(self, obj):
        """Color-coded risk level display"""
        if not obj:
            return ""
        
        colors = {
            'very_low': 'success',
            'low': 'info',
            'medium': 'warning',
            'high': 'danger',
            'very_high': 'dark',
        }
        color = colors.get(obj.risk_level, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_risk_level_display().upper() if hasattr(obj, 'get_risk_level_display') else obj.risk_level
        )
    risk_level_display.short_description = 'MỨC ĐỘ RỦI RO'
    
    def confidence_percentage(self, obj):
        """Display confidence as percentage"""
        if not obj or not obj.confidence:
            return "0%"
        return f"{obj.confidence:.1f}%"
    confidence_percentage.short_description = 'ĐỘ TIN CẬY'
    
    def warning_triggered_display(self, obj):
        """Display warning triggered status"""
        if not obj:
            return ""
        
        if obj.warning_triggered:
            return format_html('<span class="badge bg-danger">⚡ ĐÃ KÍCH HOẠT</span>')
        return format_html('<span class="badge bg-secondary">⏳ CHỜ</span>')
    warning_triggered_display.short_description = 'CẢNH BÁO'
    
    def prediction_time_display(self, obj):
        """Format prediction time"""
        if not obj or not obj.prediction_time:
            return ""
        return obj.prediction_time.strftime('%d/%m %H:%M')
    prediction_time_display.short_description = 'THỜI ĐIỂM DỰ BÁO'

# =============================================================================
# ADMIN SITE CONFIGURATION
# =============================================================================

# Custom admin site header
admin.site.site_header = "🌊 HỆ THỐNG GIÁM SÁT NGẬP LỤT HÀ NỘI"
admin.site.site_title = "Quản trị Ngập lụt Hà Nội"
admin.site.index_title = "📊 BẢNG ĐIỀU KHIỂN"