# hanoi_map/admin.py - PHIÊN BẢN ĐƠN GIẢN
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponse
import csv

from .models import FloodZone, FloodReport, WeatherForecast, FloodPrediction


# =============================================================================
# FLOOD REPORT ADMIN
# =============================================================================
@admin.register(FloodReport)
class FloodReportAdmin(GISModelAdmin):
    """Admin configuration for FloodReport model"""
    
    # List display configuration
    list_display = [
        'id',
        'address_display',
        'water_depth',
        'district',
        'status',
        'created_at_display',
    ]
    
    # Filter and search configuration
    list_filter = ['status', 'severity', 'district']
    search_fields = ['address', 'district', 'description']
    
    # Form field organization
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
    
    # Custom actions
    actions = ['mark_as_verified', 'mark_as_resolved', 'export_to_csv']
    
    # ========== CUSTOM METHODS ==========
    
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
    
    # ========== CUSTOM ACTIONS ==========
    
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
            charset='utf-8-sig'  # Support Vietnamese characters
        )
        response['Content-Disposition'] = 'attachment; filename="flood_reports.csv"'
        
        writer = csv.writer(response)
        # Write header
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
                report.get_status_display(),  # Get human-readable status
                report.created_at.strftime('%d/%m/%Y %H:%M:%S')
            ])
        
        return response
    export_to_csv.short_description = "📊 Xuất CSV"


# =============================================================================
# FLOOD ZONE ADMIN
# =============================================================================
@admin.register(FloodZone)
class FloodZoneAdmin(GISModelAdmin):
    """Admin configuration for FloodZone model"""
    
    # List display configuration
    list_display = [
        'name',
        'zone_type',
        'district',
        'max_depth_cm',
        'is_active',
        'last_flood_date',
        'report_count',
    ]
    
    # Filter and search configuration
    list_filter = ['zone_type', 'district', 'is_active']
    search_fields = ['name', 'district', 'description']
    
    # Form field organization
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
    
    # Custom actions
    actions = ['activate_zones', 'deactivate_zones']
    
    # ========== CUSTOM ACTIONS ==========
    
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
# WEATHER FORECAST ADMIN
# =============================================================================
@admin.register(WeatherForecast)
class WeatherForecastAdmin(admin.ModelAdmin):
    """Admin configuration for WeatherForecast model"""
    
    list_display = [
        'location_name',
        'current_temp',
        'current_rainfall',
        'current_description',
        'updated_at',
    ]
    
    list_filter = ['location_name']
    search_fields = ['location_name', 'current_description']
    
    fields = [
        'location_name',
        'current_temp',
        'current_rainfall',
        'current_description',
    ]
    
    # Add ordering
    ordering = ['location_name']
    
    def updated_at(self, obj):
        """Format updated time"""
        return obj.updated_at.strftime('%d/%m/%Y %H:%M')
    updated_at.short_description = 'CẬP NHẬT LÚC'


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
        'confidence_percentage',
        'created_at',
    ]
    
    list_filter = ['risk_level', 'district']
    search_fields = ['address', 'district', 'description']
    ordering = ['-created_at']
    
    # ========== CUSTOM METHODS ==========
    
    def risk_level_display(self, obj):
        """Color-coded risk level display"""
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
        }
        color = colors.get(obj.risk_level, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_risk_level_display().upper()
        )
    risk_level_display.short_description = 'MỨC ĐỘ RỦI RO'
    
    def confidence_percentage(self, obj):
        """Display confidence as percentage"""
        return f"{obj.confidence * 100:.1f}%"
    confidence_percentage.short_description = 'ĐỘ TIN CẬY'
    
    def created_at(self, obj):
        """Format creation time"""
        return obj.created_at.strftime('%d/%m %H:%M')
    created_at.short_description = 'DỰ BÁO LÚC'


# =============================================================================
# ADMIN SITE CONFIGURATION
# =============================================================================

# Custom admin site header
admin.site.site_header = "🌊 HỆ THỐNG GIÁM SÁT NGẬP LỤT HÀ NỘI"
admin.site.site_title = "Quản trị Ngập lụt Hà Nội"
admin.site.index_title = "📊 BẢNG ĐIỀU KHIỂN"