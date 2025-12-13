// static/js/main.js - TÁI CẤU TRÚC HOÀN TOÀN
let map;
let floodZonesLayer = null;
let searchCircle = null;
let clickMarker = null;
let userLocationMarker = null;
let currentSearchMarker = null;
let searchResultsDropdown = null;
let floodCheckInterval = null;
let weatherUpdateInterval = null;

// ============ GIỚI HẠN BẢN ĐỒ CHỈ HÀ NỘI ============
const HANOI_BOUNDS = L.latLngBounds(
    [20.85, 105.60],  // Tây Nam Hà Nội
    [21.25, 106.00]   // Đông Bắc Hà Nội
);

// ============ KHỞI TẠO BẢN ĐỒ ============
function initMap() {
    console.log('🚀 Khởi tạo bản đồ Hà Nội...');
    
    // Tạo bản đồ với giới hạn
    map = L.map('map', {
        center: [21.0285, 105.8542],
        zoom: 12,
        minZoom: 10,
        maxZoom: 18,
        maxBounds: HANOI_BOUNDS,
        maxBoundsViscosity: 1.0
    });
    
    // Tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors | HÀ NỘI',
        maxZoom: 19,
        bounds: HANOI_BOUNDS
    }).addTo(map);
    
    // Ngăn kéo ra ngoài Hà Nội
    map.on('drag', function() {
        map.panInsideBounds(HANOI_BOUNDS, { animate: false });
    });
    
    // Vẽ khung Hà Nội
    L.rectangle(HANOI_BOUNDS, {
        color: "#3498db",
        weight: 2,
        opacity: 0.2,
        fillOpacity: 0.05,
        dashArray: '5, 5',
        interactive: false
    }).addTo(map);
    
    // Load dữ liệu điểm ngập
    loadFloodZones();
    
    // Setup events
    setupMapClickHandler();
    initSearchDropdown();
    setupAutoUpdate();
    updateCurrentTime();
    setupWeatherAutoUpdate();
    
    console.log('✅ Bản đồ Hà Nội đã được khởi tạo');
}

// ============ TÌM KIẾM ĐỊA ĐIỂM ============
function initSearchDropdown() {
    const searchInput = document.getElementById('search-location');
    if (!searchInput) return;
    
    searchResultsDropdown = document.createElement('div');
    searchResultsDropdown.id = 'search-results-dropdown';
    searchResultsDropdown.className = 'search-results-dropdown';
    searchResultsDropdown.style.display = 'none';
    
    const searchContainer = searchInput.parentNode;
    searchContainer.style.position = 'relative';
    searchContainer.appendChild(searchResultsDropdown);
}

async function searchLocation() {
    const searchInput = document.getElementById('search-location');
    if (!searchInput) return;
    
    const query = searchInput.value.trim();
    
    if (query.length < 2) {
        showNotification('Vui lòng nhập ít nhất 2 ký tự', 'warning');
        return;
    }
    
    console.log(`🔍 Tìm kiếm: "${query}"`);
    
    // Hiển thị loading
    searchResultsDropdown.innerHTML = `
        <div style="padding: 20px; text-align: center; color: #7f8c8d;">
            <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span>Đang tìm kiếm "${query}"...</span>
        </div>
    `;
    searchResultsDropdown.style.display = 'block';
    
    try {
        const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.success) {
            if (data.results && data.results.length > 0) {
                displaySearchResults(data.results);
            } else {
                searchResultsDropdown.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: #7f8c8d;">
                        <i class="fas fa-search me-2"></i>
                        Không tìm thấy kết quả cho "${query}"
                    </div>
                `;
            }
        } else {
            searchResultsDropdown.innerHTML = `
                <div style="padding: 15px; text-align: center; color: #e74c3c;">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Lỗi: ${data.error || 'Không xác định'}
                </div>
            `;
        }
    } catch (error) {
        console.error('❌ Lỗi tìm kiếm:', error);
        searchResultsDropdown.innerHTML = `
            <div style="padding: 15px; text-align: center; color: #e74c3c;">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Không thể kết nối đến dịch vụ tìm kiếm
            </div>
        `;
    }
}

function displaySearchResults(results) {
    let html = '';
    
    results.slice(0, 10).forEach((result, index) => {
        const displayName = decodeUnicode(result.display_name || '');
        const address = result.address || {};
        
        html += `
            <div class="search-result-item" 
                 onclick="selectSearchResult(${result.lat}, ${result.lon}, '${escapeString(displayName)}')"
                 style="padding: 12px 15px; cursor: pointer; border-bottom: 1px solid #f0f0f0;"
                 onmouseover="this.style.backgroundColor='#f8f9fa'"
                 onmouseout="this.style.backgroundColor='white'">
                <div style="font-weight: 600; color: #2c3e50; margin-bottom: 4px; font-size: 14px;">
                    <i class="fas fa-map-marker-alt me-2" style="color: #3498db; width: 16px;"></i>
                    ${truncateString(displayName, 60)}
                </div>
                <div style="font-size: 0.85rem; color: #7f8c8d; line-height: 1.4; margin-bottom: 4px;">
                    ${address.road || address.district || address.city || ''}
                </div>
                <div style="font-size: 0.75rem; color: #95a5a6;">
                    <i class="fas fa-crosshairs me-1"></i>
                    ${result.lat.toFixed(4)}, ${result.lon.toFixed(4)}
                </div>
            </div>
        `;
    });
    
    html += `
        <div style="padding: 10px 15px; border-top: 1px solid #f0f0f0; background: #f8f9fa; font-size: 0.8rem; color: #6c757d;">
            <i class="fas fa-info-circle me-1"></i>
            Tìm thấy ${results.length} kết quả • Click để kiểm tra ngập
        </div>
    `;
    
    searchResultsDropdown.innerHTML = html;
    searchResultsDropdown.style.display = 'block';
}

async function selectSearchResult(lat, lon, name) {
    console.log(`📍 Chọn: ${name} (${lat}, ${lon})`);
    
    // Ẩn dropdown
    if (searchResultsDropdown) {
        searchResultsDropdown.style.display = 'none';
    }
    
    // Kiểm tra có trong Hà Nội không
    if (!HANOI_BOUNDS.contains([lat, lon])) {
        showNotification('Địa điểm này không nằm trong khu vực Hà Nội', 'warning');
        return;
    }
    
    // Cập nhật search input
    const decodedName = decodeUnicode(name);
    const searchInput = document.getElementById('search-location');
    if (searchInput) {
        searchInput.value = decodedName;
    }
    
    // Di chuyển bản đồ
    map.setView([lat, lon], 16);
    
    // Xóa marker cũ
    if (currentSearchMarker) {
        map.removeLayer(currentSearchMarker);
    }
    
    // Tạo marker mới
    currentSearchMarker = L.marker([lat, lon], {
        icon: L.divIcon({
            html: `
                <div style="
                    width: 42px;
                    height: 42px;
                    background: #3498db;
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 2px 10px rgba(52, 152, 219, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 18px;
                ">
                    <i class="fas fa-map-marker-alt"></i>
                </div>
            `,
            className: 'search-marker',
            iconSize: [42, 42],
            iconAnchor: [21, 42]
        })
    }).addTo(map);
    
    // Kiểm tra ngập tại vị trí này
    await checkFloodAtLocation(lat, lon, decodedName);
}
function createLocationPopup(data, lat, lon, locationName) {
    const floodCheck = data.flood_check || {};
    const weather = data.weather || {};
    const location = data.location || {};
    
    let html = `
        <div class="location-popup-container" style="
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            width: 320px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
            overflow: hidden;
            position: relative;
            margin-right: 5px;
        ">
            <!-- Header với nút đóng -->
            <div style="
                background: linear-gradient(135deg, #3498db, #2980b9);
                padding: 15px;
                color: white;
                position: relative;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 10px; max-width: 85%;">
                        <div style="
                            width: 36px;
                            height: 36px;
                            background: rgba(255, 255, 255, 0.2);
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 16px;
                            flex-shrink: 0;
                        ">
                            <i class="fas fa-map-marker-alt"></i>
                        </div>
                        <div style="overflow: hidden;">
                            <h3 style="
                                margin: 0;
                                font-size: 15px;
                                font-weight: 600;
                                color: white;
                                white-space: nowrap;
                                overflow: hidden;
                                text-overflow: ellipsis;
                            ">
                                ${escapeHtml(locationName || location.address || 'Vị trí đã chọn')}
                            </h3>
                            <p style="
                                margin: 3px 0 0 0;
                                font-size: 11px;
                                opacity: 0.9;
                                white-space: nowrap;
                                overflow: hidden;
                                text-overflow: ellipsis;
                            ">
                                <i class="fas fa-crosshairs me-1"></i>
                                ${lat.toFixed(6)}, ${lon.toFixed(6)}
                            </p>
                        </div>
                    </div>

                </div>
            </div>
            
            <!-- Nội dung chính -->
            <div style="padding: 15px;">
                <!-- Trạng thái ngập -->
                <div class="flood-status-card" style="
                    background: ${floodCheck.has_flood ? '#fff5f5' : '#f0fff4'};
                    border: 1px solid ${floodCheck.has_flood ? '#fed7d7' : '#c6f6d5'};
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 15px;
                ">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="
                            width: 32px;
                            height: 32px;
                            background: ${floodCheck.has_flood ? '#feb2b2' : '#9ae6b4'};
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            margin-right: 10px;
                            color: ${floodCheck.has_flood ? '#c53030' : '#276749'};
                            font-size: 14px;
                            flex-shrink: 0;
                        ">
                            <i class="fas ${floodCheck.has_flood ? 'fa-water' : 'fa-check-circle'}"></i>
                        </div>
                        <div style="flex: 1;">
                            <h4 style="
                                margin: 0;
                                color: ${floodCheck.has_flood ? '#c53030' : '#276749'};
                                font-size: 14px;
                                font-weight: 700;
                                line-height: 1.3;
                            ">
                                ${floodCheck.has_flood ? '⚠️ CÓ NGẬP LỤT' : '✅ KHÔNG CÓ NGẬP'}
                            </h4>
                            <p style="
                                margin: 3px 0 0 0;
                                color: ${floodCheck.has_flood ? '#9b2c2c' : '#22543d'};
                                font-size: 12px;
                                line-height: 1.3;
                            ">
                                ${escapeHtml(floodCheck.message || 'Trạng thái bình thường')}
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Thông tin thời tiết -->
                <div class="weather-card" style="
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 15px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <h4 style="margin: 0; color: #2d3748; font-size: 14px; font-weight: 600;">
                            <i class="fas fa-cloud-sun me-2" style="color: #4299e1;"></i>Thời tiết
                        </h4>
                        <span style="font-size: 11px; color: #718096;">
                            ${new Date().toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'})}
                        </span>
                    </div>
                    
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="
                            width: 50px;
                            height: 50px;
                            background: linear-gradient(135deg, #4299e1, #63b3ed);
                            border-radius: 10px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-size: 20px;
                            flex-shrink: 0;
                        ">
                            <i class="fas fa-temperature-low"></i>
                        </div>
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                <span style="font-size: 24px; font-weight: 700; color: #2d3748;">
                                    ${Math.round(weather.temp || 25)}°
                                    <span style="font-size: 12px; color: #718096;">C</span>
                                </span>
                                <span style="
                                    font-size: 12px;
                                    color: #4a5568;
                                    background: #edf2f7;
                                    padding: 3px 8px;
                                    border-radius: 20px;
                                    text-transform: capitalize;
                                    max-width: 120px;
                                    overflow: hidden;
                                    text-overflow: ellipsis;
                                    white-space: nowrap;
                                ">
                                    ${escapeHtml(weather.description || 'Nắng')}
                                </span>
                            </div>
                            <div style="display: flex; gap: 12px; font-size: 11px; color: #718096;">
                                <span><i class="fas fa-tint me-1" style="color: #4299e1;"></i> ${weather.humidity || 60}%</span>
                                <span><i class="fas fa-wind me-1" style="color: #9f7aea;"></i> ${weather.wind_speed || 0} m/s</span>
                                <span><i class="fas fa-cloud-rain me-1" style="color: #4fd1c7;"></i> ${weather.rain || 0}mm</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Nút hành động -->
                <div class="action-buttons" style="display: flex; gap: 8px;">
                    <button onclick="checkFloodAtLocation(${lat}, ${lon}, '${escapeString(locationName)}')" 
                            style="
                                flex: 1;
                                background: linear-gradient(135deg, #4299e1, #3182ce);
                                color: white;
                                border: none;
                                padding: 10px 15px;
                                border-radius: 6px;
                                font-size: 13px;
                                font-weight: 600;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                gap: 6px;
                                transition: all 0.3s;
                            "
                            onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(66, 153, 225, 0.3)'"
                            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        <i class="fas fa-sync-alt"></i>
                        <span>Kiểm tra lại</span>
                    </button>
                    
                    <button onclick="showReportAtLocation(${lat}, ${lon})" 
                            style="
                                flex: 1;
                                background: linear-gradient(135deg, #f56565, #e53e3e);
                                color: white;
                                border: none;
                                padding: 10px 15px;
                                border-radius: 6px;
                                font-size: 13px;
                                font-weight: 600;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                gap: 6px;
                                transition: all 0.3s;
                            "
                            onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(245, 101, 101, 0.3)'"
                            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>Báo cáo</span>
                    </button>
                </div>
                
                <!-- Footer -->
                <div style="
                    margin-top: 12px;
                    padding-top: 10px;
                    border-top: 1px solid #e2e8f0;
                    text-align: center;
                ">
                    <p style="margin: 0; font-size: 10px; color: #a0aec0;">
                        <i class="fas fa-info-circle me-1"></i>
                        ${new Date().toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'})}
                    </p>
                </div>
            </div>
        </div>
    `;
    
    return html;
}

// Thêm CSS tùy chỉnh để popup sát lề phải
function addPopupStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Tùy chỉnh popup để sát lề phải */
        .leaflet-popup {
            margin-left: -10px !important;
        }
        
        .leaflet-popup-content-wrapper {
            border-radius: 12px !important;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2) !important;
            padding: 0 !important;
            overflow: hidden !important;
            max-width: 320px !important;
            min-width: 320px !important;
        }
        
        .leaflet-popup-content {
            margin: 0 !important;
            padding: 0 !important;
            min-height: auto !important;
            width: 320px !important;
        }
        
        /* Điều chỉnh vị trí popup tip */
        .leaflet-popup-tip-container {
            margin-left: -10px !important;
        }
        
        .leaflet-popup-tip {
            background: white !important;
            box-shadow: 0 3px 14px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Nút đóng mặc định của Leaflet */
        .leaflet-popup-close-button {
            position: absolute !important;
            top: 8px !important;
            right: 8px !important;
            width: 26px !important;
            height: 26px !important;
            background: rgba(255, 255, 255, 0.9) !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 14px !important;
            color: #718096 !important;
            z-index: 1001 !important;
            transition: all 0.3s !important;
            border: none !important;
            outline: none !important;
        }
        
        .leaflet-popup-close-button:hover {
            background: white !important;
            color: #e53e3e !important;
            transform: scale(1.1) !important;
        }
        
        /* Đảm bảo popup không bị che bởi các phần tử khác */
        .leaflet-container .leaflet-popup {
            z-index: 1000 !important;
        }
        
        .leaflet-popup-pane {
            z-index: 1000 !important;
        }
        
        /* Responsive cho mobile */
        @media (max-width: 768px) {
            .leaflet-popup-content-wrapper {
                max-width: 280px !important;
                min-width: 280px !important;
            }
            
            .leaflet-popup-content {
                width: 280px !important;
            }
            
            .location-popup-container {
                width: 280px !important;
            }
        }
        
        @media (max-width: 480px) {
            .leaflet-popup-content-wrapper {
                max-width: 250px !important;
                min-width: 250px !important;
            }
            
            .leaflet-popup-content {
                width: 250px !important;
            }
            
            .location-popup-container {
                width: 250px !important;
            }
        }
        
        /* Animation */
        @keyframes slideInFromRight {
            from { 
                opacity: 0;
                transform: translateX(20px);
            }
            to { 
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .leaflet-popup {
            animation: slideInFromRight 0.3s ease-out !important;
        }
        
        /* Tránh đè lên thanh điều khiển bản đồ */
        .leaflet-top,
        .leaflet-bottom {
            z-index: 999 !important;
        }
        
        /* Đảm bảo popup không bị che bởi search panel */
        .search-panel {
            z-index: 990 !important;
        }
        
        .control-panel {
            z-index: 990 !important;
        }
    `;
    
    // Kiểm tra xem style đã tồn tại chưa
    if (!document.getElementById('leaflet-popup-styles')) {
        style.id = 'leaflet-popup-styles';
        document.head.appendChild(style);
    }
}

// Hàm điều chỉnh vị trí popup để sát lề phải
function adjustPopupPosition() {
    if (map && currentSearchMarker) {
        // Lấy kích thước bản đồ
        const mapWidth = map.getSize().x;
        const mapHeight = map.getSize().y;
        
        // Tính toán vị trí popup
        const latlng = currentSearchMarker.getLatLng();
        const point = map.latLngToContainerPoint(latlng);
        
        // Điều chỉnh popup sang phải
        const offsetX = -160; // Dịch sang trái để popup hiển thị bên phải marker
        const offsetY = -150; // Dịch lên trên một chút
        
        // Tạo popup với offset
        const popup = L.popup({
            offset: L.point(offsetX, offsetY),
            closeButton: true,
            autoClose: false,
            closeOnEscapeKey: true,
            className: 'custom-popup'
        });
        
        return popup;
    }
    return null;
}

// Cập nhật hàm checkFloodAtLocation để sử dụng popup sát lề phải
async function checkFloodAtLocation(lat, lon, locationName = '') {
    showLoadingOnMap();
    
    try {
        const response = await fetch(`/api/check-flood/?lat=${lat}&lng=${lon}`);
        const data = await response.json();
        
        if (data.success) {
            displayFloodCheckResults(data, lat, lon, locationName);
            
            // Thêm popup cho marker với vị trí sát lề phải
            if (currentSearchMarker) {
                // Xóa popup cũ nếu có
                if (currentSearchMarker.getPopup()) {
                    currentSearchMarker.unbindPopup();
                }
                
                const popupContent = createLocationPopup(data, lat, lon, locationName);
                
                // Tạo popup mới với offset
                const popup = L.popup({
                    offset: L.point(-160, -150), // Dịch sang trái và lên trên
                    closeButton: true,
                    autoClose: false,
                    closeOnEscapeKey: true,
                    className: 'custom-popup',
                    maxWidth: 320
                })
                .setLatLng([lat, lon])
                .setContent(popupContent);
                
                // Mở popup gần marker
                popup.openOn(map);
                
                // Cũng gắn popup vào marker để quản lý
                currentSearchMarker.bindPopup(popup);
            }
            
            // Hiển thị thời tiết nếu có dữ liệu
            if (data.weather) {
                displayWeatherInfo(data.weather, data.alerts || []);
            }
            
            // Cập nhật thống kê
            updateStatsPanel(data);
            
        } else {
            showNotification('Lỗi kiểm tra ngập: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('❌ Lỗi kiểm tra ngập:', error);
        showNotification('Không thể kiểm tra ngập', 'error');
    } finally {
        hideLoadingOnMap();
    }
}

// Gọi hàm addPopupStyles khi khởi tạo
document.addEventListener('DOMContentLoaded', function() {
    addPopupStyles();
});

// // Thêm CSS cho Leaflet popup để không bị đè
// function addPopupStyles() {
//     const style = document.createElement('style');
//     style.textContent = `
//         /* Tùy chỉnh popup của Leaflet */
//         .leaflet-popup-content-wrapper {
//             border-radius: 12px !important;
//             box-shadow: 0 6px 25px rgba(0, 0, 0, 0.15) !important;
//             padding: 0 !important;
//             overflow: hidden;
//         }
        
//         .leaflet-popup-content {
//             margin: 0 !important;
//             padding: 0 !important;
//             min-height: auto !important;
//         }
        
//         .leaflet-popup-tip-container {
//             margin-top: -1px;
//         }
        
//         .leaflet-popup-tip {
//             background: white !important;
//             box-shadow: 0 3px 14px rgba(0, 0, 0, 0.1) !important;
//         }
        
//         .leaflet-popup-close-button {
//             position: absolute !important;
//             top: 10px !important;
//             right: 10px !important;
//             width: 30px !important;
//             height: 30px !important;
//             background: rgba(255, 255, 255, 0.9) !important;
//             border-radius: 50% !important;
//             display: flex !important;
//             align-items: center !important;
//             justify-content: center !important;
//             font-size: 16px !important;
//             color: #718096 !important;
//             z-index: 1001 !important;
//             transition: all 0.3s !important;
//         }
        
//         .leaflet-popup-close-button:hover {
//             background: white !important;
//             color: #e53e3e !important;
//             transform: scale(1.1) !important;
//         }
        
//         /* Tùy chỉnh cho mobile */
//         @media (max-width: 768px) {
//             .location-popup-container {
//                 min-width: 280px !important;
//                 max-width: 90vw !important;
//             }
            
//             .leaflet-popup-content-wrapper {
//                 max-width: 90vw !important;
//             }
//         }
        
//         /* Animation */
//         @keyframes fadeIn {
//             from { opacity: 0; transform: translateY(10px); }
//             to { opacity: 1; transform: translateY(0); }
//         }
        
//         .leaflet-popup {
//             animation: fadeIn 0.3s ease-out !important;
//         }
//     `;
//     document.head.appendChild(style);
// }

document.addEventListener('DOMContentLoaded', function() {
    addPopupStyles();
});

// ============ KIỂM TRA NGẬP TẠI VỊ TRÍ ============
async function checkFloodAtLocation(lat, lon, locationName = '') {
    showLoadingOnMap();
    
    try {
        const response = await fetch(`/api/check-flood/?lat=${lat}&lng=${lon}`);
        const data = await response.json();
        
        if (data.success) {
            displayFloodCheckResults(data, lat, lon, locationName);
            
            // Thêm popup cho marker
            if (currentSearchMarker) {
                const popupContent = createLocationPopup(data, lat, lon, locationName);
                currentSearchMarker.bindPopup(popupContent).openPopup();
            }
            
            // Hiển thị thời tiết nếu có dữ liệu
            if (data.weather) {
                displayWeatherInfo(data.weather, data.alerts || []);
            }
            
            // Cập nhật thống kê
            updateStatsPanel(data);
            
        } else {
            showNotification('Lỗi kiểm tra ngập: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('❌ Lỗi kiểm tra ngập:', error);
        showNotification('Không thể kiểm tra ngập', 'error');
    } finally {
        hideLoadingOnMap();
    }
}


function displayFloodCheckResults(data, lat, lon, locationName) {
    console.log('📊 Hiển thị kết quả kiểm tra ngập');
    
    let panel = document.getElementById('flood-check-panel');
    
    // Nếu panel chưa tồn tại, tạo mới
    if (!panel) {
        panel = createPanel('flood-check-panel', 'Kiểm tra ngập');
    }
    
    const floodCheck = data.flood_check;
    const location = data.location || {};
    
    let html = `
        <div class="flood-check-results position-relative">
            <button type="button" class="btn-close position-absolute top-0 end-0 m-2" 
                    onclick="closeFloodCheckPanel()" aria-label="Close" style="z-index: 1001;">
            </button>
            
            <h5 class="mb-1">
                <i class="fas fa-map-marker-alt me-2" style="color: #3498db;"></i>
                ${escapeHtml(locationName || location.address || 'Vị trí đã chọn')}
            </h5>
            
            <p class="text-muted mb-2">
                <i class="fas fa-layer-group me-1"></i>
                ${escapeHtml(location.district || '')}
                ${location.ward ? ' • ' + escapeHtml(location.ward) : ''}
            </p>
            
            <div class="coordinate-info mb-3">
                <small class="text-muted">
                    <i class="fas fa-crosshairs me-1"></i>
                    ${lat.toFixed(6)}, ${lon.toFixed(6)}
                </small>
            </div>
            
            <div class="flood-status mt-3">
    `;
    
    if (floodCheck.has_flood) {
        html += `
            <div class="alert alert-danger">
                <h6 class="alert-heading">
                    <i class="fas fa-water me-2"></i>⚠️ CÓ NGẬP LỤT
                </h6>
                <p class="mb-2">${escapeHtml(floodCheck.message)}</p>
        `;
        
        if (floodCheck.source === 'known_zone' && floodCheck.zone) {
            html += `
                <p class="mb-1"><strong>Điểm ngập:</strong> ${escapeHtml(floodCheck.zone.name)}</p>
                <p class="mb-1"><strong>Loại ngập:</strong> ${escapeHtml(floodCheck.zone.type)}</p>
                <p class="mb-1"><strong>Độ sâu tối đa:</strong> ${floodCheck.zone.max_depth} cm</p>
                <p class="mb-0"><strong>Nguyên nhân:</strong> ${escapeHtml(floodCheck.zone.cause)}</p>
            `;
        }
        
        if (floodCheck.source === 'user_report' && floodCheck.report) {
            const reportTime = new Date(floodCheck.report.time).toLocaleString('vi-VN');
            html += `
                <p class="mb-1"><strong>Độ sâu:</strong> ${floodCheck.report.depth} cm</p>
                <p class="mb-1"><strong>Thời gian báo cáo:</strong> ${escapeHtml(reportTime)}</p>
                <p class="mb-0"><strong>Địa chỉ:</strong> ${escapeHtml(floodCheck.report.address)}</p>
            `;
        }
        
        html += `</div>`;
    }
    
    else if (floodCheck.has_risk) {
        html += `
            <div class="alert alert-warning">
                <h6 class="alert-heading">
                    <i class="fas fa-exclamation-triangle me-2"></i>⚠️ CÓ NGUY CƠ NGẬP
                </h6>
                <p class="mb-2">${escapeHtml(floodCheck.message)}</p>
        `;
        
        if (floodCheck.prediction) {
            html += `
                <p class="mb-1"><strong>Mức độ nguy cơ:</strong> ${escapeHtml(floodCheck.prediction.risk)}</p>
                <p class="mb-0"><strong>Độ tin cậy:</strong> ${floodCheck.prediction.confidence}%</p>
            `;
        }
        
        html += `</div>`;
    }
    
    else {
        html += `
            <div class="alert alert-success">
                <h6 class="alert-heading">
                    <i class="fas fa-check-circle me-2"></i>✅ KHÔNG CÓ NGẬP
                </h6>
                <p class="mb-0">${escapeHtml(floodCheck.message)}</p>
            </div>
        `;
    }
    
    html += `
            </div>
            
            <!-- Thông tin thời tiết -->
            <div class="weather-info mt-4">
                <h6 class="mb-2">
                    <i class="fas fa-cloud-sun me-2" style="color: #3498db;"></i>
                    Thời tiết hiện tại
                </h6>
    `;
    
    if (data.weather) {
        const weather = data.weather;
        html += `
            <div class="row align-items-center">
                <div class="col-4 text-center">
                    <img src="https://openweathermap.org/img/wn/${weather.icon || '01d'}@2x.png" 
                         alt="${weather.description || 'Nắng'}" width="50" height="50">
                </div>
                <div class="col-8">
                    <h4 class="mb-1">${Math.round(weather.temp || 25)}°C</h4>
                    <p class="text-capitalize mb-1">${weather.description || 'Nắng'}</p>
                    <div class="row">
                        <div class="col-6">
                            <small><i class="fas fa-tint me-1" style="color: #3498db;"></i> ${weather.humidity || 60}%</small>
                        </div>
                        <div class="col-6">
                            <small><i class="fas fa-wind me-1" style="color: #9b59b6;"></i> ${weather.wind_speed || 1.5} m/s</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        if (weather.rain > 0) {
            html += `
                <div class="alert alert-info mt-2 py-2" style="font-size: 0.85rem;">
                    <i class="fas fa-cloud-rain me-2"></i>
                    <strong>Lượng mưa:</strong> ${weather.rain} mm/h
                </div>
            `;
        }
    } else {
        html += `<p class="text-muted">Không có dữ liệu thời tiết</p>`;
    }
    
    html += `
            </div>
            
            <div class="d-grid gap-2 mt-4">
                <button
                    id="report-flood-btn"
                    class="btn btn-danger btn-sm"
                    onclick="showReportAtLocation(${lat}, ${lon})">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    Báo cáo ngập tại đây
                </button>
                
                <button
                    id="check-area-btn"
                    class="btn btn-outline-primary btn-sm"
                    onclick="checkAreaStatus(${lat}, ${lon})">
                    <i class="fas fa-expand me-1"></i>
                    Xem trạng thái khu vực
                </button>
            </div>
        </div>
    `;
    
    panel.innerHTML = html;
    panel.style.position = 'fixed';
    panel.style.top = '80px';
    panel.style.right = '0px';
    panel.style.left = 'auto';
    panel.style.display = 'block';
    
    console.log('✅ Panel kiểm tra ngập đã hiển thị');
}

// ============ KIỂM TRA TRẠNG THÁI KHU VỰC ============
async function checkAreaStatus(lat, lon) {
    console.log('🔍 Kiểm tra trạng thái khu vực tại:', lat, lon);
    
    let radius = 1000; // Mặc định 1000m
    
    const radiusSlider = document.getElementById('radius-slider');
    if (radiusSlider) {
        radius = radiusSlider.value;
    }
    
    showLoadingOnMap();
    
    try {
        console.log(`📡 Gọi API: /api/area-status/?lat=${lat}&lng=${lon}&radius=${radius}`);
        
        const response = await fetch(`/api/area-status/?lat=${lat}&lng=${lon}&radius=${radius}`);
        
        if (!response.ok) {
            let errorMessage = `HTTP error! status: ${response.status}`;
            
            // Thử lấy thông tin lỗi chi tiết từ response
            try {
                const errorData = await response.json();
                if (errorData && errorData.error) {
                    errorMessage = errorData.error;
                } else if (errorData && errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch (parseError) {
                console.warn('Không thể parse error response:', parseError);
            }
            
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        console.log('📦 Dữ liệu trả về:', data);
        
        if (data.success) {
            displayAreaStatusResults(data, lat, lon, radius);
            
            // Vẽ vòng tròn khu vực
            if (searchCircle) {
                map.removeLayer(searchCircle);
            }
            
            searchCircle = L.circle([lat, lon], {
                color: '#3498db',
                fillColor: '#2980b9',
                fillOpacity: 0.15,
                weight: 2,
                radius: parseInt(radius)
            }).addTo(map);
            
            // Di chuyển bản đồ để hiển thị vòng tròn
            map.fitBounds(searchCircle.getBounds());
            
        } else {
            console.error('❌ API trả về lỗi:', data);
            showNotification('Lỗi: ' + (data.error || 'Không xác định'), 'error');
        }
    } catch (error) {
        console.error('❌ Lỗi kiểm tra khu vực:', error);
        
        // Hiển thị thông báo lỗi chi tiết hơn
        let userMessage = 'Không thể kiểm tra trạng thái khu vực. ';
        
        if (error.message.includes('500')) {
            userMessage += 'Server đang gặp sự cố. Vui lòng thử lại sau.';
        } else if (error.message.includes('404')) {
            userMessage += 'Endpoint API không tồn tại.';
        } else if (error.message.includes('NetworkError')) {
            userMessage += 'Không thể kết nối đến server.';
        } else {
            userMessage += 'Lỗi: ' + error.message;
        }
        
        showNotification(userMessage, 'error');
        
        // Log chi tiết để debug
        console.error('Chi tiết lỗi:', {
            lat: lat,
            lon: lon,
            radius: radius,
            error: error.message,
            stack: error.stack
        });
    } finally {
        hideLoadingOnMap();
    }
}

function displayAreaStatusResults(data, lat, lon, radius) {
    console.log('📋 Hiển thị kết quả khu vực:', data);
    
    let panel = document.getElementById('area-status-panel');
    
    // Nếu panel chưa tồn tại, tạo mới
    if (!panel) {
        panel = createPanel('area-status-panel', 'Trạng thái khu vực');
    }
    
    const areaStatus = data.area_status || {};
    const stats = areaStatus.stats || {};
    const forecast = data.forecast || [];
    
    // Xác định mức độ rủi ro
    let riskLevel = 'low';
    let riskColor = 'success';
    let riskText = 'THẤP';
    
    if ((stats.total_zones || 0) > 3 || (stats.total_reports || 0) > 5) {
        riskLevel = 'high';
        riskColor = 'danger';
        riskText = 'CAO';
    } else if ((stats.total_zones || 0) > 0 || (stats.total_reports || 0) > 0) {
        riskLevel = 'medium';
        riskColor = 'warning';
        riskText = 'TRUNG BÌNH';
    }
    
    // Tạo HTML cho panel
    let html = `
        <div class="area-status-results position-relative">
            <button type="button" class="btn-close position-absolute top-0 end-0 m-2" 
                    onclick="closePanel('area-status-panel')" aria-label="Close" style="z-index: 1001;">
            </button>
            
            <h5 class="mb-2">
                <i class="fas fa-expand me-2" style="color: #3498db;"></i>Trạng thái khu vực
            </h5>
            
            <div class="location-info mb-3" style="background: #f8f9fa; padding: 10px; border-radius: 8px;">
                <div class="d-flex align-items-center mb-1">
                    <i class="fas fa-crosshairs me-2" style="color: #6c757d;"></i>
                    <small style="color: #6c757d;">${lat.toFixed(4)}, ${lon.toFixed(4)} • Bán kính: ${radius}m</small>
                </div>
            </div>
            
            <!-- Mức độ nguy cơ -->
            <div class="alert alert-${riskColor} mb-3">
                <div class="d-flex justify-content-between align-items-center">
                    <strong>Mức độ nguy cơ:</strong>
                    <span class="badge bg-${riskColor} px-3 py-2">${riskText}</span>
                </div>
            </div>
            
            <!-- Thống kê 4 ô -->
            <div class="stats-grid mb-4">
                <div class="row g-2 text-center">
                    <div class="col-6">
                        <div class="stat-box" style="background: #e3f2fd; border-radius: 10px; padding: 15px;">
                            <div class="stat-value" style="font-size: 2rem; font-weight: bold; color: #1976d2;">${stats.total_zones || 0}</div>
                            <div class="stat-label" style="font-size: 0.9rem; color: #5a6268; margin-top: 5px;">Điểm ngập</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="stat-box" style="background: #f3e5f5; border-radius: 10px; padding: 15px;">
                            <div class="stat-value" style="font-size: 2rem; font-weight: bold; color: #7b1fa2;">${stats.total_reports || 0}</div>
                            <div class="stat-label" style="font-size: 0.9rem; color: #5a6268; margin-top: 5px;">Báo cáo</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="stat-box" style="background: #e8f5e9; border-radius: 10px; padding: 15px;">
                            <div class="stat-value" style="font-size: 2rem; font-weight: bold; color: #388e3c;">${stats.recent_reports || 0}</div>
                            <div class="stat-label" style="font-size: 0.9rem; color: #5a6268; margin-top: 5px;">Báo cáo gần đây</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="stat-box" style="background: #fff3e0; border-radius: 10px; padding: 15px;">
                            <div class="stat-value" style="font-size: 2rem; font-weight: bold; color: #f57c00;">${stats.max_depth ? stats.max_depth.toFixed(1) : 0}<small style="font-size: 1rem;">cm</small></div>
                            <div class="stat-label" style="font-size: 0.9rem; color: #5a6268; margin-top: 5px;">Độ sâu TB</div>
                        </div>
                    </div>
                </div>
            </div>
    `;
    
    // Dự báo thời tiết (nếu có)
    if (forecast.length > 0) {
        html += `
            <div class="weather-forecast mb-4">
                <h6 class="mb-2" style="color: #2c3e50; font-weight: 600;">
                    <i class="fas fa-cloud-sun me-2" style="color: #3498db;"></i>Dự báo 12h tiếp:
                </h6>
                <div class="row g-2">
        `;
        
        // Hiển thị 4 khung giờ
        forecast.slice(0, 4).forEach((forecastData, index) => {
            const timeSlots = ['10:00', '13:00', '16:00', '19:00'];
            const temp = forecastData.temp ? Math.round(forecastData.temp) : 20;
            const rain = forecastData.rain || 0;
            
            html += `
                <div class="col-3">
                    <div class="forecast-item text-center" style="
                        background: ${rain > 0 ? '#e3f2fd' : '#f8f9fa'};
                        border: 1px solid #dee2e6;
                        border-radius: 8px;
                        padding: 10px 5px;
                    ">
                        <div style="font-size: 0.8rem; color: #6c757d; font-weight: 500; margin-bottom: 8px;">
                            ${timeSlots[index] || '--:--'}
                        </div>
                        <div style="font-size: 1.2rem; font-weight: bold; color: #2c3e50; margin-bottom: 5px;">
                            ${temp}°
                        </div>
                        ${rain > 0 ? `
                            <div style="font-size: 0.75rem; color: #3498db; font-weight: 500;">
                                ${rain.toFixed(1)}mm
                            </div>
                        ` : `
                            <div style="font-size: 0.75rem; color: #95a5a6;">
                                -
                            </div>
                        `}
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    // Nút hành động
    html += `
            <div class="action-buttons mt-4">
                <button class="btn btn-primary w-100 mb-2" onclick="checkAreaStatus(${lat}, ${lon})">
                    <i class="fas fa-sync-alt me-2"></i>Cập nhật
                </button>
                <button class="btn btn-outline-danger w-100" onclick="showReportAtLocation(${lat}, ${lon})">
                    <i class="fas fa-exclamation-triangle me-2"></i>Báo cáo ngập
                </button>
            </div>
        </div>
    `;
    
    // Cập nhật panel
    panel.innerHTML = html;
    
    // Hiển thị panel
    panel.style.display = 'block';
    
    console.log('✅ Panel trạng thái khu vực đã hiển thị');
}

// ============ LOAD DỮ LIỆU ĐIỂM NGẬP ============
async function loadFloodZones() {
    showLoadingOnMap();
    
    try {
        const response = await fetch('/api/flood-data/');
        const data = await response.json();
        
        if (data && data.features) {
            displayFloodZonesOnMap(data);
            console.log(`✅ Đã cập nhật ${data.features.length} điểm ngập`);
            
            // Thông báo cập nhật thành công
            const notification = document.getElementById('update-notification');
            if (notification) {
                notification.innerHTML = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        <i class="fas fa-check-circle me-2"></i>
                        Đã cập nhật ${data.features.length} điểm ngập lúc ${new Date().toLocaleTimeString('vi-VN')}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
                
                // Tự động ẩn sau 5 giây
                setTimeout(() => {
                    const alert = notification.querySelector('.alert');
                    if (alert) {
                        const bsAlert = new bootstrap.Alert(alert);
                        bsAlert.close();
                    }
                }, 5000);
            }
        } else {
            console.warn('⚠️ Không có dữ liệu điểm ngập');
        }
    } catch (error) {
        console.error('❌ Lỗi tải dữ liệu điểm ngập:', error);
        showNotification('Không thể tải dữ liệu điểm ngập. Vui lòng thử lại.', 'error');
    } finally {
        hideLoadingOnMap();
    }
}async function loadFloodZones() {
    showLoadingOnMap();
    
    try {
        const response = await fetch('/api/flood-data/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📊 Dữ liệu từ API:', data); 
        
        // Xử lý cấu trúc dữ liệu đơn giản
        let features = [];
        
        if (data && data.data && data.data.flood_zones) {
            // Cấu trúc: {data: {flood_zones: [...]}}
            features = data.data.flood_zones;
            console.log(`✅ Đã nhận ${features.length} điểm ngập (cấu trúc data.flood_zones)`);
        } else if (data && data.flood_zones) {
            // Cấu trúc: {flood_zones: [...]}
            features = data.flood_zones;
            console.log(`✅ Đã nhận ${features.length} điểm ngập (cấu trúc flood_zones)`);
        } else if (data && data.features) {
            // Cấu trúc GeoJSON chuẩn
            features = data.features;
            console.log(`✅ Đã nhận ${features.length} điểm ngập (cấu trúc features)`);
        } else {
            console.warn('⚠️ Không có dữ liệu điểm ngập hoặc cấu trúc không đúng:', data);
            features = [];
        }
        
        // Tạo GeoJSON chuẩn để hiển thị
        const geojsonData = {
            type: 'FeatureCollection',
            features: features
        };
        
        displayFloodZonesOnMap(geojsonData);
        
        if (features.length > 0) {
            showNotification(`Đã cập nhật ${features.length} điểm ngập`, 'success');
        }
        
    } catch (error) {
        console.error('❌ Lỗi tải dữ liệu điểm ngập:', error);
        showNotification('Không thể tải dữ liệu điểm ngập', 'error');
        
        // Fallback: Hiển thị bản đồ không có dữ liệu
        displayFloodZonesOnMap({
            type: 'FeatureCollection',
            features: []
        });
        
    } finally {
        hideLoadingOnMap();
    }
}
function displayFloodZonesOnMap(geojsonData) {
    if (floodZonesLayer) {
        map.removeLayer(floodZonesLayer);
    }
    if (!geojsonData || !geojsonData.features) {
        console.log('ℹ️ Không có điểm ngập nào để hiển thị');
        return;
    }
    
    const features = geojsonData.features;
    
    if (features.length === 0) {
        console.log('ℹ️ Không có điểm ngập nào để hiển thị');
        return;
    }
    
    console.log(`🔍 Có ${features.length} điểm ngập để hiển thị`);
    floodZonesLayer = L.geoJSON(geojsonData, {
        style: function(feature) {
            const props = feature.properties || {};
            const zoneType = props.zone_type || props.type;
            let color = '#95a5a6';
            if (zoneType === 'black') color = '#c0392b';
            else if (zoneType === 'frequent') color = '#e74c3c';
            else if (zoneType === 'seasonal') color = '#f39c12';
            else if (zoneType === 'rain') color = '#3498db';
            else if (zoneType === 'tide') color = '#9b59b6';
            
            return {
                color: color,
                weight: 2,
                opacity: 0.7,
                fillColor: color,
                fillOpacity: 0.2
            };
        },
        onEachFeature: function(feature, layer) {
            const props = feature.properties || {};
            const name = props.name || 'Điểm ngập';
            const zoneTypeDisplay = props.zone_type_display || props.type_display || props.zone_type || props.type || 'Không xác định';
            const district = props.district || '';
            const maxDepth = props.max_depth_cm || props.max_depth || 0;
            const street = props.street || '';
            const lastReported = props.last_reported || '';
            
            const popupContent = `
                <div style="min-width: 250px; padding: 10px;">
                    <h6 style="color: #2c3e50; margin-bottom: 8px;">
                        <i class="fas fa-water me-2"></i>${escapeHtml(name)}
                    </h6>
                    
                    <div style="margin-bottom: 10px;">
                        <span class="badge" style="background-color: ${props.zone_type === 'black' ? '#c0392b' : 
                                                              props.zone_type === 'frequent' ? '#e74c3c' : 
                                                              props.zone_type === 'seasonal' ? '#f39c12' : 
                                                              props.zone_type === 'rain' ? '#3498db' : '#95a5a6'}">
                            ${escapeHtml(zoneTypeDisplay)}
                        </span>
                        ${district ? `<span class="badge bg-secondary ms-1">${escapeHtml(district)}</span>` : ''}
                    </div>
                    
                    <div style="font-size: 12px;">
                        ${maxDepth > 0 ? `
                            <p style="margin: 5px 0;">
                                <i class="fas fa-ruler-vertical me-1"></i>
                                <strong>Độ sâu:</strong> ${maxDepth}cm
                            </p>
                        ` : ''}
                        
                        ${street ? `
                            <p style="margin: 5px 0;">
                                <i class="fas fa-map-marker-alt me-1"></i>
                                <strong>Đường:</strong> ${escapeHtml(street)}
                            </p>
                        ` : ''}
                        
                        ${lastReported ? `
                            <p style="margin: 5px 0;">
                                <i class="fas fa-clock me-1"></i>
                                <strong>Cập nhật:</strong> ${escapeHtml(lastReported)}
                            </p>
                        ` : ''}
                    </div>
                </div>
            `;
            
            layer.bindPopup(popupContent);
            
            // Click vào zone để kiểm tra - SỬA LẠI
            layer.on('click', function(e) {
                if (e.latlng) {
                    // Gọi hàm đúng tên - checkFloodAtLocation
                    checkFloodAtLocation(e.latlng.lat, e.latlng.lng, name);
                }
            });
        }
    }).addTo(map);
    
    console.log(`✅ Đã hiển thị ${features.length} điểm ngập`);
}

// ============ BÁO CÁO NGẬP ============
function setupMapClickHandler() {
    map.on('click', function(e) {
        // Kiểm tra có trong Hà Nội không
        if (!HANOI_BOUNDS.contains(e.latlng)) {
            showNotification('Vui lòng chọn vị trí trong khu vực Hà Nội', 'warning');
            return;
        }
        
        // Update coordinates in report modal
        document.getElementById('flood-lat').value = e.latlng.lat.toFixed(6);
        document.getElementById('flood-lng').value = e.latlng.lng.toFixed(6);
        
        // Add click marker
        if (clickMarker) {
            map.removeLayer(clickMarker);
        }
        
        clickMarker = L.marker(e.latlng, {
            icon: L.divIcon({
                html: '<div style="width:25px;height:25px;background:#e74c3c;border-radius:50%;border:3px solid white;box-shadow:0 0 10px rgba(0,0,0,0.3);"></div>',
                className: 'click-marker',
                iconSize: [25, 25]
            }),
            draggable: true
        }).addTo(map);
        
        // Update coordinates when marker is dragged
        clickMarker.on('dragend', function(e) {
            const pos = clickMarker.getLatLng();
            document.getElementById('flood-lat').value = pos.lat.toFixed(6);
            document.getElementById('flood-lng').value = pos.lng.toFixed(6);
        });
        
        // Show popup với các tùy chọn
        L.popup()
            .setLatLng(e.latlng)
            .setContent(`
                <div style="text-align: center; min-width: 200px; padding: 10px;">
                    <p class="mb-2">Tọa độ:</p>
                    <p class="mb-3"><small>${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}</small></p>
                    <button class="btn btn-sm btn-primary w-100 mb-2" 
                            onclick="map.closePopup(); checkFloodAtLocation(${e.latlng.lat}, ${e.latlng.lng})">
                        <i class="fas fa-search me-1"></i>Kiểm tra ngập tại đây
                    </button>
                    <button class="btn btn-sm btn-secondary w-100" 
                            onclick="map.closePopup(); showReportAtLocation(${e.latlng.lat}, ${e.latlng.lng})">
                        <i class="fas fa-exclamation-triangle me-1"></i>Báo cáo ngập
                    </button>
                </div>
            `)
            .openOn(map);
    });
}

function showReportAtLocation(lat, lng) {
    // Cập nhật tọa độ
    const latInput = document.getElementById('flood-lat');
    const lngInput = document.getElementById('flood-lng');
    const addressInput = document.getElementById('flood-address');
    
    if (latInput) latInput.value = lat.toFixed(6);
    if (lngInput) lngInput.value = lng.toFixed(6);
    
    // Lấy thông tin địa chỉ từ tọa độ
    if (addressInput) {
        fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&addressdetails=1`)
            .then(response => response.json())
            .then(data => {
                const address = data.display_name || '';
                addressInput.value = address;
            })
            .catch(error => {
                console.error('Reverse geocode error:', error);
                addressInput.value = `Vị trí: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
            });
    }
    
    // Hiển thị modal
    const modalElement = document.getElementById('reportModal');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}

async function submitFloodReport() {
    const addressInput = document.getElementById('flood-address');
    const waterDepthInput = document.getElementById('water-depth');
    const latInput = document.getElementById('flood-lat');
    const lngInput = document.getElementById('flood-lng');
    const descriptionInput = document.getElementById('flood-description');
    const reporterNameInput = document.getElementById('reporter-name');
    const reporterPhoneInput = document.getElementById('reporter-phone');
    const areaSizeInput = document.getElementById('area-size');
    
    if (!addressInput || !waterDepthInput || !latInput || !lngInput) {
        showNotification('Lỗi: Không tìm thấy form. Vui lòng làm mới trang!', 'error');
        return;
    }
    
    const address = addressInput.value.trim();
    const waterDepth = waterDepthInput.value;
    const lat = latInput.value;
    const lng = lngInput.value;
    const description = descriptionInput ? descriptionInput.value.trim() : '';
    const reporterName = reporterNameInput ? reporterNameInput.value.trim() : '';
    const reporterPhone = reporterPhoneInput ? reporterPhoneInput.value.trim() : '';
    const areaSize = areaSizeInput ? areaSizeInput.value.trim() : '';
    
    // Validation
    if (!address || !waterDepth || !lat || !lng) {
        showNotification('Vui lòng điền đầy đủ thông tin và chọn vị trí trên bản đồ!', 'error');
        return;
    }
    
    // Kiểm tra có trong Hà Nội không
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);
    
    if (!HANOI_BOUNDS.contains([latNum, lngNum])) {
        showNotification('Vị trí phải nằm trong khu vực Hà Nội', 'error');
        return;
    }
    
    const reportData = {
        address: address,
        water_depth: parseFloat(waterDepth),
        lat: latNum,
        lng: lngNum,
        description: description,
        reporter_name: reporterName,
        reporter_phone: reporterPhone,
        area_size: areaSize
    };
    
    console.log('📤 Gửi báo cáo:', reportData);
    
    // Hiển thị loading
    const submitBtn = document.querySelector('#reportModal .btn-primary');
    if (!submitBtn) {
        showNotification('Lỗi: Không tìm thấy nút gửi báo cáo', 'error');
        return;
    }
    
    const originalText = submitBtn.innerHTML;
    const originalDisabled = submitBtn.disabled;
    
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Đang gửi...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/report-flood/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(reportData)
        });
        
        const data = await response.json();
        console.log('📥 Phản hồi từ server:', data);
        
        if (data.success) {
            showNotification(data.message || '✅ Báo cáo đã được gửi thành công!', 'success');
            
            // Reset form
            const fieldsToReset = [
                'flood-address', 'water-depth', 'flood-description',
                'reporter-name', 'reporter-phone', 'area-size'
            ];
            
            fieldsToReset.forEach(id => {
                const element = document.getElementById(id);
                if (element) element.value = '';
            });
            
            // Remove marker
            if (clickMarker) {
                map.removeLayer(clickMarker);
                clickMarker = null;
            }
            
            // Close modal
            const modalElement = document.getElementById('reportModal');
            if (modalElement) {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }
            }
            
            // Reload data sau 2 giây
            setTimeout(() => {
                loadFloodZones();
                showNotification('🔄 Đang cập nhật điểm ngập mới...', 'info');
            }, 2000);
            
        } else {
            showNotification('❌ Lỗi: ' + (data.error || 'Có lỗi xảy ra'), 'error');
        }
    } catch (error) {
        console.error('❌ Lỗi gửi báo cáo:', error);
        showNotification('❌ Không thể gửi báo cáo. Vui lòng thử lại.', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = originalDisabled;
    }
}

// ============ THÔNG TIN THỜI TIẾT ============
function setupWeatherAutoUpdate() {
    // Cập nhật thời tiết mỗi 10 phút
    weatherUpdateInterval = setInterval(() => {
        const center = map.getCenter();
        updateWeatherInfo(center.lat, center.lng);
    }, 10 * 60 * 1000);
}

async function updateWeatherInfo(lat, lon) {
    try {
        const response = await fetch(`/api/weather/?lat=${lat}&lng=${lon}`);
        const data = await response.json();
        
        if (data.success) {
            displayWeatherInfo(data.current, data.alerts || []);
        }
    } catch (error) {
        console.error('❌ Lỗi cập nhật thời tiết:', error);
    }
}

function displayWeatherInfo(weather, alerts) {
    if (!weather) return;
    
    let panel = document.getElementById('weather-panel');
    
    // Tạo panel nếu chưa có
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'weather-panel';
        panel.className = 'weather-panel';
        panel.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            background: white;
            border-radius: 12px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            padding: 15px;
            width: 280px;
            transition: all 0.3s ease;
            display: none;
        `;
        document.body.appendChild(panel);
    }
    
    let html = `
        <div class="weather-info, style="display: none"">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h6 style="margin: 0; color: #2c3e50; font-weight: 600;">
                    <i class="fas fa-cloud-sun me-2" style="color: #3498db;"></i>Thời tiết
                </h6>
                <button onclick="closePanel('weather-panel')" 
                        style="background: none; border: none; color: #7f8c8d; cursor: pointer; font-size: 14px;">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div class="row align-items-center mt-2 display: none">
                <div class="col-4 text-center">
                    <img src="https://openweathermap.org/img/wn/${weather.icon || '01d'}@2x.png" 
                         alt="${weather.description || 'Nắng'}" width="50" height="50">
                </div>
                <div class="col-8 display: none">
                    <h4 style="color: #2c3e50; margin: 0;">${Math.round(weather.temp || 25)}°C</h4>
                    <p style="text-transform: capitalize; color: #7f8c8d; margin: 5px 0 8px 0;">
                        ${weather.description || 'Nắng'}
                    </p>
                    <div class="row">
                        <div class="col-6">
                            <small><i class="fas fa-tint me-1" style="color: #3498db;"></i> ${weather.humidity || 60}%</small>
                        </div>
                        <div class="col-6">
                            <small><i class="fas fa-wind me-1" style="color: #9b59b6;"></i> ${weather.wind_speed || 1.5} m/s</small>
                        </div>
                    </div>
                </div>
            </div>
    `;
    
    if (weather.rain > 0) {
        html += `
            <div class="mt-3">
                <div class="alert alert-info py-2 mb-2" style="font-size: 0.85rem;">
                    <i class="fas fa-cloud-rain me-2"></i>
                    <strong>Lượng mưa:</strong> ${weather.rain} mm/h
                </div>
            </div>
        `;
    }
    
    if (alerts.length > 0) {
        html += `<div class="mt-3">`;
        alerts.forEach(alert => {
            const alertClass = alert.level === 'high' ? 'danger' : 
                              alert.level === 'medium' ? 'warning' : 'info';
            html += `
                <div class="alert alert-${alertClass} py-2 mb-2" style="font-size: 0.85rem;">
                    <i class="fas ${alert.icon || 'fa-exclamation-circle'} me-2"></i>
                    <small>${escapeHtml(alert.message || 'Cảnh báo thời tiết')}</small>
                </div>
            `;
        });
        html += `</div>`;
    }
    
    html += `
            <div class="text-end mt-3">
                <small class="text-muted">
                    <i class="fas fa-clock me-1"></i>
                    ${new Date().toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'})}
                </small>
            </div>
        </div>
    `;
    
    panel.innerHTML = html;
    panel.style.display = 'none';
}

// ============ HÀM TIỆN ÍCH ============
function createPanel(id, title) {
    const panel = document.createElement('div');
    panel.id = id;
    panel.className = id;
    panel.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 1000;
        background: white;
        border-radius: 12px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        padding: 20px;
        width: 380px;
        max-height: 80vh;
        overflow-y: auto;
        display: none;
        transition: all 0.3s ease;
        animation: fadeIn 0.3s ease;
    `;
    document.body.appendChild(panel);
    return panel;
}

function closePanel(panelId) {
    const panel = document.getElementById(panelId);
    if (panel) {
        panel.style.opacity = '0';
        setTimeout(() => {
            panel.style.display = 'none';
            panel.style.opacity = '1';
        }, 300);
    }
}

function closeFloodCheckPanel() {
    closePanel('flood-check-panel');
}

function updateStatsPanel(data) {
    // Cập nhật thống kê trên control panel
    const stats = data.stats || {};
    
    if (stats.total_zones !== undefined) {
        const element = document.getElementById('total-zones');
        if (element) element.textContent = stats.total_zones;
    }
    
    if (stats.total_reports !== undefined) {
        const element = document.getElementById('total-reports');
        if (element) element.textContent = stats.total_reports;
    }
}

function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('vi-VN', {
        timeZone: 'Asia/Ho_Chi_Minh',
        hour12: false,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
    
    setTimeout(updateCurrentTime, 1000);
}

function setupAutoUpdate() {
    const autoUpdateCheckbox = document.getElementById('auto-update');
    
    if (!autoUpdateCheckbox) return;
    
    autoUpdateCheckbox.addEventListener('change', function(e) {
        if (e.target.checked && !floodCheckInterval) {
            floodCheckInterval = setInterval(loadFloodZones, 5 * 60 * 1000);
            showNotification('✅ Đã bật cập nhật tự động (5 phút/lần)', 'success');
        } else if (!e.target.checked && floodCheckInterval) {
            clearInterval(floodCheckInterval);
            floodCheckInterval = null;
            showNotification('🔄 Đã tắt cập nhật tự động', 'info');
        }
    });
    
    if (autoUpdateCheckbox.checked && !floodCheckInterval) {
        floodCheckInterval = setInterval(loadFloodZones, 5 * 60 * 1000);
    }
}

function toggleControlPanel() {
    const panel = document.querySelector('.control-panel');
    const toggleIcon = panel.querySelector('.panel-toggle i');
    
    panel.classList.toggle('collapsed');
    
    if (panel.classList.contains('collapsed')) {
        toggleIcon.className = 'fas fa-chevron-right';
    } else {
        toggleIcon.className = 'fas fa-chevron-left';
    }
}

function showLoadingOnMap() {
    const loadingDiv = document.getElementById('map-loading');
    if (loadingDiv) {
        loadingDiv.style.display = 'flex';
    }
}

function hideLoadingOnMap() {
    const loadingDiv = document.getElementById('map-loading');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

// ============ HÀM XỬ LÝ CHUỖI ============
function escapeHtml(text) {
    if (!text) return '';
    
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.toString().replace(/[&<>"']/g, function(m) { 
        return map[m]; 
    });
}

function escapeString(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

function truncateString(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
}

function decodeUnicode(str) {
    if (!str) return '';
    try {
        return str.replace(/\\u([\d\w]{4})/gi, function(match, grp) {
            return String.fromCharCode(parseInt(grp, 16));
        });
    } catch (e) {
        return str;
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ============ THÔNG BÁO ============
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        padding: 15px 20px;
        min-width: 300px;
        max-width: 400px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        animation: slideIn 0.3s ease;
        border-left: 4px solid ${type === 'success' ? '#2ecc71' : 
                              type === 'error' ? '#e74c3c' : 
                              type === 'warning' ? '#f39c12' : '#3498db'};
    `;
    
    notification.innerHTML = `
        <div style="flex: 1; margin-right: 15px;">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 
                           type === 'error' ? 'fa-exclamation-circle' : 
                           type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'} 
               me-2" style="color: ${type === 'success' ? '#2ecc71' : 
                             type === 'error' ? '#e74c3c' : 
                             type === 'warning' ? '#f39c12' : '#3498db'}"></i>
            ${escapeHtml(message)}
        </div>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: #7f8c8d; cursor: pointer; font-size: 14px;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
}

// ============ DEBUG & TEST ============
function testSearchConnection() {
    fetch('/api/test/')
        .then(response => response.json())
        .then(data => {
            showNotification(data.message || '✅ Kết nối search API hoạt động tốt!', 'success');
        })
        .catch(error => {
            showNotification('❌ Lỗi kết nối search API', 'error');
        });
}

function debugSearchSystem() {
    console.log('🔧 Debug Search System:');
    console.log('- Search input:', document.getElementById('search-location'));
    console.log('- Dropdown:', searchResultsDropdown);
    console.log('- Map bounds:', HANOI_BOUNDS);
    console.log('- Current view:', map.getCenter(), 'zoom:', map.getZoom());
}

// ============ EVENT LISTENERS ============
document.addEventListener('click', function(event) {
    const searchInput = document.getElementById('search-location');
    
    if (searchResultsDropdown && searchInput) {
        if (!searchInput.contains(event.target) && !searchResultsDropdown.contains(event.target)) {
            searchResultsDropdown.style.display = 'none';
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Tìm kiếm khi nhấn Enter
    const searchInput = document.getElementById('search-location');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                searchLocation();
            }
        });
    }
    
    // Thêm CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .search-results-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
            max-height: 400px;
            overflow-y: auto;
            z-index: 10000;
            margin-top: 2px;
            animation: fadeIn 0.2s ease;
        }
        
        .search-result-item {
            transition: all 0.2s;
        }
        
        .search-result-item:hover {
            background-color: #f8f9fa;
        }
        
        .click-marker {
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        #map-loading {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 2000;
            animation: fadeIn 0.3s ease;
        }
        
        .stat-box {
            transition: all 0.3s ease;
            border: 1px solid #e9ecef;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        }
        
        .stat-box:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .flood-check-panel, .area-status-panel {
                width: calc(100vw - 40px) !important;
                right: 0px !important;
                left: 20px !important;
                top: 20px !important;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Thêm loading div vào map
    const mapContainer = document.getElementById('map');
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'map-loading';
    loadingDiv.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="h5" style="color: #2c3e50;">Đang kiểm tra ngập...</p>
        </div>
    `;
    mapContainer.appendChild(loadingDiv);
    
    // Thêm container cho notification
    const notificationContainer = document.createElement('div');
    notificationContainer.id = 'update-notification';
    notificationContainer.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9998;
        min-width: 300px;
        max-width: 400px;
    `;
    document.body.appendChild(notificationContainer);
    
    // Khởi tạo map
    initMap();
    
    console.log('🚀 Ứng dụng Giám sát Ngập lụt Hà Nội đã sẵn sàng!');
});


function updateControlPanelStats() {
    // Cập nhật thống kê
    fetch('/api/statistics/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.stats;
                document.getElementById('total-zones').textContent = stats.zones?.total || 0;
                document.getElementById('active-zones').textContent = stats.zones?.active || 0;
                document.getElementById('total-reports').textContent = stats.reports?.total || 0;
                document.getElementById('verified-reports').textContent = stats.reports?.verified || 0;
            }
        });
}

// Gọi khi khởi tạo
updateControlPanelStats();


// ============ LẤY VỊ TRÍ HIỆN TẠI ============
async function getCurrentLocation() {
    console.log('📍 Đang lấy vị trí hiện tại...');
    
    // Hiển thị loading
    showNotification('📍 Đang lấy vị trí của bạn...', 'info');
    
    // Kiểm tra trình duyệt có hỗ trợ Geolocation API không
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
        
        // Kiểm tra xem có trong Hà Nội không
        if (!HANOI_BOUNDS.contains([lat, lng])) {
            showNotification('📍 Vị trí của bạn không nằm trong Hà Nội', 'warning');
            // Vẫn hiển thị nhưng cảnh báo
        }
        
        // Di chuyển bản đồ đến vị trí hiện tại
        map.setView([lat, lng], 16);
        
        // Xóa marker cũ nếu có
        if (userLocationMarker) {
            map.removeLayer(userLocationMarker);
        }
        
        // Tạo marker mới cho vị trí hiện tại
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
    
    // Vị trí mặc định: Hồ Gươm, Hà Nội
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
    // Cập nhật thông tin thời tiết trên control panel
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

document.addEventListener('DOMContentLoaded', function() {
    // Kiểm tra quyền vị trí sau khi bản đồ được khởi tạo
    setTimeout(checkLocationPermission, 3000);
});