import { initMap, updateCurrentTime, setupAutoUpdate, toggleControlPanel } from './modules/map.js';
import { setupSearchEvents } from './modules/search.js';
import { loadFloodZones } from './modules/flood-zones.js';
import { getCurrentLocation } from './modules/location.js';
import { setupMapClickHandler, showReportAtLocation, submitFloodReport } from './modules/report.js';
import { showNotification, addPopupStyles } from './modules/notifications.js';
import { checkFloodAtLocation, closeFloodCheckPanel } from './modules/flood-check.js';
import { checkAreaStatus } from './modules/area-status.js';
import { clearAllMarkers } from './utils.js';

// ============ KHỞI TẠO ỨNG DỤNG ============
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Ứng dụng Giám sát Ngập lụt Hà Nội đang khởi động...');
    addPopupStyles();
    addCustomStyles();
    initMap();
    setupSearchEvents();
    setupMapClickHandler();
    setupAutoUpdate();
    updateCurrentTime();
    setTimeout(() => {
        // getCurrentLocation(); // Có thể bật lại nếu cần
    }, 3000);
    
    console.log('✅ Ứng dụng đã sẵn sàng!');
});

// ============ THÊM CUSTOM STYLES ============
function addCustomStyles() {
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
    if (mapContainer) {
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
    }
    
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
}

// ============ GLOBAL FUNCTIONS CHO HTML ============

window.searchLocation = searchLocation; 
window.selectSearchResult = selectSearchResult; 
window.checkFloodAtLocation = checkFloodAtLocation;
window.showReportAtLocation = showReportAtLocation;
window.getCurrentLocation = getCurrentLocation;
window.clearAllMarkers = clearAllMarkers;
window.toggleControlPanel = toggleControlPanel;
window.closeFloodCheckPanel = closeFloodCheckPanel;
window.checkAreaStatus = checkAreaStatus;
window.submitFloodReport = submitFloodReport;

// ============ HÀM TIỆN ÍCH TOÀN CỤC BỔ SUNG ============
async function searchLocation() {
    const searchModule = await import('./modules/search.js');
    return searchModule.searchLocation();
}

async function selectSearchResult(lat, lon, name) {
    const searchModule = await import('./modules/search.js');
    return searchModule.selectSearchResult(lat, lon, name);
}

function clearAllMarkers() {
    console.log('🗑️ Xóa tất cả marker - Hàm cần được triển khai');
    showNotification('Chức năng đang được phát triển', 'info');
}
