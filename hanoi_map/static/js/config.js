// ============ REFRESH TOÀN BỘ DỮ LIỆU (PHIÊN BẢN RÚT GỌN) ============
async function refreshAllData() {
    console.log('🔄 Đang refresh toàn bộ dữ liệu hệ thống...');
    showLoadingOnMap();
    const refreshBtn = document.querySelector('button[onclick="refreshAllData()"]');
    const originalText = refreshBtn.innerHTML;
    refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Đang cập nhật...';
    refreshBtn.disabled = true;
    
    try {
        console.log('📊 1/4: Đang refresh dữ liệu điểm ngập...');
        await loadFloodZones();
        
        console.log('📊 2/4: Đang refresh thống kê...');
        await updateControlPanelStats();
        
        console.log('🌤️ 3/4: Đang refresh thời tiết...');
        try {
            const center = map.getCenter();
            const response = await fetch(`/api/weather/?lat=${center.lat}&lng=${center.lng}`);
            const data = await response.json();
            if (data.success) {
                displayWeatherInfo(data.current, data.alerts || []);
            }
        } catch (weatherError) {
            console.warn('⚠️ Lỗi refresh thời tiết:', weatherError.message);
        }
        
        console.log('📋 4/4: Đang refresh báo cáo gần đây...');
        try {
            const response = await fetch('/api/recent-reports/');
            const data = await response.json();
            if (data.success) {
                window.recentReportsData = data.reports || [];
            }
        } catch (reportsError) {
            console.warn('⚠️ Lỗi refresh báo cáo:', reportsError.message);
        }
        
        showNotification('✅ Đã refresh toàn bộ dữ liệu thành công', 'success');
        
    } catch (error) {
        console.error('❌ Lỗi refreshAllData:', error);
        showNotification('⚠️ Có lỗi xảy ra khi refresh dữ liệu', 'warning');
    } finally {
        // Ẩn loading
        hideLoadingOnMap();
        refreshBtn.innerHTML = originalText;
        refreshBtn.disabled = false;
        console.log('✅ RefreshAllData hoàn tất!');
    }
}