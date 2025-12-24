
// ============ LẤY VỊ TRÍ HIỆN TẠI ============
async function getCurrentLocation() {
    console.log('📍 Đang lấy vị trí hiện tại...');
    showNotification('📍 Đang lấy vị trí của bạn...', 'info');
    
    if (!navigator.geolocation) {
        showNotification('Trình duyệt của bạn không hỗ trợ lấy vị trí', 'error');
        return;
    }
    
    try {
        // Yêu cầu quyền truy cập vị trí
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,  // Sử dụng GPS nếu có
                timeout: 10000,           // Thời gian chờ tối đa 10 giây
                maximumAge: 0             // Không sử dụng vị trí cũ
            });
        });
        
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        const accuracy = position.coords.accuracy; // Độ chính xác (mét)
        
        console.log(`📍 Vị trí hiện tại: ${lat}, ${lng} (độ chính xác: ${accuracy}m)`);
        if (!HANOI_BOUNDS.contains([lat, lng])) {
            showNotification('📍 Vị trí của bạn không nằm trong Hà Nội', 'warning');
        }
        map.setView([lat, lng], 16);
        if (userLocationMarker) {
            map.removeLayer(userLocationMarker);
        }
        userLocationMarker = L.marker([lat, lng], {
            icon: L.divIcon({
                html: `
                    <div style="
                        width: 40px;
                        height: 40px;
                        background: linear-gradient(135deg, #3498db, #2980b9);
                        border-radius: 50%;
                        border: 3px solid white;
                        box-shadow: 0 3px 15px rgba(52, 152, 219, 0.6);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 16px;
                        position: relative;
                    ">
                        <i class="fas fa-location-arrow"></i>
                        ${accuracy < 50 ? `
                            <div style="
                                position: absolute;
                                top: -5px;
                                right: -5px;
                                width: 15px;
                                height: 15px;
                                background: #2ecc71;
                                border-radius: 50%;
                                border: 2px solid white;
                            "></div>
                        ` : ''}
                    </div>
                `,
                className: 'user-location-marker',
                iconSize: [40, 40],
                iconAnchor: [20, 40]
            })
        }).addTo(map);
        
        // Thêm popup thông tin
        const accuracyText = accuracy < 50 ? 'Cao' : (accuracy < 200 ? 'Trung bình' : 'Thấp');
        
        userLocationMarker.bindPopup(`
            <div style="min-width: 250px; padding: 10px;">
                <h6 style="color: #2c3e50; margin-bottom: 8px;">
                    <i class="fas fa-user-circle me-2"></i>Vị trí của bạn
                </h6>
                
                <div style="margin-bottom: 10px;">
                    <p style="margin: 5px 0;">
                        <i class="fas fa-crosshairs me-2" style="color: #3498db;"></i>
                        <strong>Tọa độ:</strong> ${lat.toFixed(6)}, ${lng.toFixed(6)}
                    </p>
                    
                    <p style="margin: 5px 0;">
                        <i class="fas fa-bullseye me-2" style="color: ${accuracy < 50 ? '#2ecc71' : accuracy < 200 ? '#f39c12' : '#e74c3c'}"></i>
                        <strong>Độ chính xác:</strong> ${Math.round(accuracy)} mét
                        <span class="badge ms-2" style="background-color: ${accuracy < 50 ? '#2ecc71' : accuracy < 200 ? '#f39c12' : '#e74c3c'}">
                            ${accuracyText}
                        </span>
                    </p>
                </div>
                
                <div class="d-grid gap-2">
                    <button class="btn btn-sm btn-primary" onclick="checkFloodAtLocation(${lat}, ${lng}, 'Vị trí của tôi')">
                        <i class="fas fa-search me-1"></i>Kiểm tra ngập tại đây
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="showReportAtLocation(${lat}, ${lng})">
                        <i class="fas fa-exclamation-triangle me-1"></i>Báo cáo ngập
                    </button>
                </div>
            </div>
        `).openPopup();
        
        // Kiểm tra ngập tại vị trí này
        await checkFloodAtLocation(lat, lng, 'Vị trí của tôi');
        
        // Hiển thị thông báo thành công
        showNotification(`✅ Đã lấy vị trí của bạn (độ chính xác: ${Math.round(accuracy)}m)`, 'success');
        
        // Cập nhật thời tiết tại vị trí hiện tại
        try {
            const response = await fetch(`/api/weather/?lat=${lat}&lng=${lng}`);
            const data = await response.json();
            
            if (data.success && data.current) {
                updateWeatherInfo(data.current);
            }
        } catch (weatherError) {
            console.error('❌ Lỗi cập nhật thời tiết:', weatherError);
        }
        
        // Lấy tên địa chỉ từ tọa độ
        getAddressFromCoordinates(lat, lng);
        
    } catch (error) {
        console.error('❌ Lỗi lấy vị trí:', error);
        
        let errorMessage = 'Không thể lấy vị trí của bạn. ';
        
        switch(error.code) {
            case error.PERMISSION_DENIED:
                errorMessage += 'Bạn đã từ chối quyền truy cập vị trí.';
                break;
            case error.POSITION_UNAVAILABLE:
                errorMessage += 'Thông tin vị trí không khả dụng.';
                break;
            case error.TIMEOUT:
                errorMessage += 'Hết thời gian chờ lấy vị trí.';
                break;
            default:
                errorMessage += error.message;
        }
        
        showNotification(errorMessage, 'error');
        
        // Fallback: Sử dụng vị trí mặc định (Hồ Gươm)
        useFallbackLocation();
    }
}

// ============ HÀM HỖ TRỢ ============

async function getAddressFromCoordinates(lat, lng) {
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&addressdetails=1`);
        const data = await response.json();
        
        if (data && data.display_name) {
            console.log('📍 Địa chỉ:', data.display_name);
            
            // Cập nhật địa chỉ trong popup
            if (userLocationMarker && userLocationMarker.getPopup()) {
                const popup = userLocationMarker.getPopup();
                const currentContent = popup.getContent();
                
                // Thêm địa chỉ vào popup
                const newContent = currentContent.replace(
                    '</div>',
                    `<p style="margin: 5px 0; font-size: 12px; color: #7f8c8d;">
                        <i class="fas fa-map-marker-alt me-2"></i>
                        ${data.display_name.substring(0, 80)}...
                    </p>
                    </div>`
                );
                
                popup.setContent(newContent);
            }
        }
    } catch (error) {
        console.error('❌ Lỗi lấy địa chỉ:', error);
    }
}

function useFallbackLocation() {
    console.log('📍 Sử dụng vị trí mặc định (Hồ Gươm)');
    const defaultLat = 21.0285;
    const defaultLng = 105.8542;
    
    map.setView([defaultLat, defaultLng], 14);
    
    userLocationMarker = L.marker([defaultLat, defaultLng], {
        icon: L.divIcon({
            html: `
                <div style="
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(135deg, #95a5a6, #7f8c8d);
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 3px 15px rgba(149, 165, 166, 0.6);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 16px;
                ">
                    <i class="fas fa-map-marker-alt"></i>
                </div>
            `,
            className: 'fallback-location-marker',
            iconSize: [40, 40],
            iconAnchor: [20, 40]
        })
    }).addTo(map);
    
    userLocationMarker.bindPopup(`
        <div style="min-width: 250px; padding: 10px;">
            <h6 style="color: #2c3e50; margin-bottom: 8px;">
                <i class="fas fa-info-circle me-2"></i>Vị trí mặc định
            </h6>
            <p style="margin: 5px 0;">Không thể lấy vị trí của bạn. Đang hiển thị Hồ Gươm, Hà Nội.</p>
            <p style="margin: 5px 0;"><strong>Tọa độ:</strong> ${defaultLat.toFixed(6)}, ${defaultLng.toFixed(6)}</p>
            <button class="btn btn-sm btn-primary mt-2 w-100" onclick="getCurrentLocation()">
                <i class="fas fa-redo me-1"></i>Thử lại
            </button>
        </div>
    `).openPopup();
    
    showNotification('⚠️ Đang sử dụng vị trí mặc định (Hồ Gươm)', 'warning');
}

function updateWeatherInfo(weather) {
    if (weather) {
        const tempElement = document.getElementById('current-temp');
        const rainElement = document.getElementById('current-rain');
        const descElement = document.getElementById('weather-desc');
        const iconElement = document.getElementById('weather-icon');
        
        if (tempElement) tempElement.textContent = `${Math.round(weather.temp || 25)}°C`;
        if (rainElement) rainElement.textContent = `${weather.rain || 0} mm`;
        if (descElement) descElement.textContent = weather.description || 'Nắng';
        
        if (iconElement) {
            const icons = {
                '01d': 'fa-sun', '01n': 'fa-moon',
                '02d': 'fa-cloud-sun', '02n': 'fa-cloud-moon',
                '03d': 'fa-cloud', '03n': 'fa-cloud',
                '04d': 'fa-cloud', '04n': 'fa-cloud',
                '09d': 'fa-cloud-rain', '09n': 'fa-cloud-rain',
                '10d': 'fa-cloud-showers-heavy', '10n': 'fa-cloud-showers-heavy',
                '11d': 'fa-bolt', '11n': 'fa-bolt',
                '13d': 'fa-snowflake', '13n': 'fa-snowflake',
                '50d': 'fa-smog', '50n': 'fa-smog'
            };
            
            const iconClass = icons[weather.icon || '01d'] || 'fa-cloud-sun';
            iconElement.innerHTML = `<i class="fas ${iconClass}"></i>`;
        }
    }
}

// ============ HÀM XÓA MARKER ============
function clearAllMarkers() {
    console.log('🗑️ Xóa tất cả marker');
    
    let markerCount = 0;
    
    if (currentSearchMarker) {
        map.removeLayer(currentSearchMarker);
        currentSearchMarker = null;
        markerCount++;
    }
    
    if (clickMarker) {
        map.removeLayer(clickMarker);
        clickMarker = null;
        markerCount++;
    }
    
    if (userLocationMarker) {
        map.removeLayer(userLocationMarker);
        userLocationMarker = null;
        markerCount++;
    }
    
    if (searchCircle) {
        map.removeLayer(searchCircle);
        searchCircle = null;
        markerCount++;
    }
    
    showNotification(`✅ Đã xóa ${markerCount} marker`, 'success');
}

// ============ KIỂM TRA QUYỀN VỊ TRÍ KHI KHỞI ĐỘNG ============
function checkLocationPermission() {
    if (navigator.permissions) {
        navigator.permissions.query({name: 'geolocation'})
            .then(function(result) {
                console.log('📍 Quyền vị trí:', result.state);
                
                // if (result.state === 'granted') {
                //     // Tự động lấy vị trí nếu đã được cấp quyền
                //     console.log('📍 Tự động lấy vị trí (đã có quyền)');
                //     setTimeout(() => getCurrentLocation(), 2000);
                // }
                
                // Theo dõi thay đổi quyền
                result.onchange = function() {
                    console.log('📍 Quyền vị trí thay đổi:', this.state);
                };
            });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(checkLocationPermission, 3000);
});