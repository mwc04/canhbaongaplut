// Flood Map Real-time Updates
class FloodMapUpdater {
    constructor(map) {
        this.map = map;
        this.floodLayer = null;
        this.reportLayer = null;
        this.updateInterval = 30000; // 30 giây
        this.lastUpdate = null;
    }
    
    init() {
        this.loadFloodData();
        this.setupAutoUpdate();
    }
    
    loadFloodData() {
        fetch('/api/flood-data/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.updateMap(data.data);
                    this.lastUpdate = new Date();
                    this.updateStatus();
                }
            })
            .catch(error => {
                console.error('Error loading flood data:', error);
            });
    }
    
    updateMap(floodData) {
        // Xóa layer cũ
        if (this.floodLayer) {
            this.map.removeLayer(this.floodLayer);
        }
        if (this.reportLayer) {
            this.map.removeLayer(this.reportLayer);
        }
        
        // Thêm điểm ngập (polygon)
        const floodZones = L.geoJSON(floodData.flood_zones, {
            style: function(feature) {
                const zoneType = feature.properties.zone_type;
                const colors = {
                    'black': '#000000',
                    'frequent': '#ff0000',
                    'seasonal': '#ff9900',
                    'rain': '#0066ff',
                    'tide': '#00ccff'
                };
                
                return {
                    fillColor: colors[zoneType] || '#999999',
                    color: '#ffffff',
                    weight: 2,
                    opacity: 0.7,
                    fillOpacity: 0.3
                };
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties;
                const popupContent = `
                    <div class="flood-popup">
                        <h4>${props.name}</h4>
                        <p><strong>Loại:</strong> ${props.zone_type_display}</p>
                        <p><strong>Quận:</strong> ${props.district}</p>
                        <p><strong>Độ sâu tối đa:</strong> ${props.max_depth} cm</p>
                        <p><strong>Số báo cáo:</strong> ${props.report_count}</p>
                        <p><strong>Cập nhật:</strong> ${props.last_reported}</p>
                        ${props.description ? `<p>${props.description}</p>` : ''}
                    </div>
                `;
                layer.bindPopup(popupContent);
            }
        });
        
        this.floodLayer = floodZones;
        floodZones.addTo(this.map);
        
        // Thêm báo cáo ngập (marker)
        const reportIcon = L.divIcon({
            className: 'flood-report-marker',
            html: '<div class="flood-marker" style="background-color: #ff4444; border: 2px solid white; border-radius: 50%; width: 20px; height: 20px; box-shadow: 0 0 10px rgba(255,0,0,0.5);"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
        
        const reports = L.geoJSON(floodData.flood_reports, {
            pointToLayer: function(feature, latlng) {
                return L.marker(latlng, {icon: reportIcon});
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties;
                const popupContent = `
                    <div class="report-popup">
                        <h4>📢 Báo cáo ngập</h4>
                        <p><strong>Địa chỉ:</strong> ${props.address}</p>
                        <p><strong>Độ sâu:</strong> ${props.water_depth} cm</p>
                        <p><strong>Mức độ:</strong> ${props.severity_display}</p>
                        <p><strong>Thời gian:</strong> ${props.created_at}</p>
                        ${props.reporter_name ? `<p><strong>Người báo:</strong> ${props.reporter_name}</p>` : ''}
                        ${props.description ? `<p>${props.description}</p>` : ''}
                        ${props.photo_url ? `<img src="${props.photo_url}" style="max-width: 200px; margin-top: 10px;" />` : ''}
                    </div>
                `;
                layer.bindPopup(popupContent);
            }
        });
        
        this.reportLayer = reports;
        reports.addTo(this.map);
    }
    
    setupAutoUpdate() {
        setInterval(() => {
            this.loadFloodData();
        }, this.updateInterval);
    }
    
    updateStatus() {
        const statusElement = document.getElementById('update-status');
        if (statusElement) {
            statusElement.textContent = `Cập nhật: ${this.lastUpdate.toLocaleTimeString()}`;
        }
    }
    
    // Thêm báo cáo mới vào bản đồ ngay lập tức
    addNewReport(reportData) {
        const marker = L.marker([reportData.lat, reportData.lng], {
            icon: L.divIcon({
                className: 'new-report-marker',
                html: '<div class="new-flood-marker" style="background-color: #ff0000; border: 3px solid yellow; border-radius: 50%; width: 24px; height: 24px; box-shadow: 0 0 15px rgba(255,255,0,0.8); animation: pulse 1s infinite;"></div>',
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            })
        });
        
        const popupContent = `
            <div class="new-report-popup">
                <h4>🎯 Báo cáo mới!</h4>
                <p><strong>Địa chỉ:</strong> ${reportData.address}</p>
                <p><strong>Độ sâu:</strong> ${reportData.water_depth} cm</p>
                <p><strong>Thời gian:</strong> Vừa xong</p>
                <p class="text-success">✅ Đã thêm vào bản đồ</p>
            </div>
        `;
        
        marker.bindPopup(popupContent).addTo(this.map);
        marker.openPopup();
        
        // Tự động đóng popup sau 10 giây
        setTimeout(() => {
            marker.closePopup();
        }, 10000);
    }
}

// Khởi tạo
document.addEventListener('DOMContentLoaded', function() {
    // Khởi tạo bản đồ Leaflet
    const map = L.map('flood-map').setView([21.0285, 105.8542], 12);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Khởi tạo updater
    const updater = new FloodMapUpdater(map);
    updater.init();
    
    // Xử lý form báo cáo
    const reportForm = document.getElementById('flood-report-form');
    if (reportForm) {
        reportForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                lat: document.getElementById('report-lat').value,
                lng: document.getElementById('report-lng').value,
                address: document.getElementById('report-address').value,
                water_depth: document.getElementById('water-depth').value,
                area_size: document.getElementById('area-size').value,
                description: document.getElementById('description').value,
                reporter_name: document.getElementById('reporter-name').value,
                auto_verify: true // Tự động xác nhận cho demo
            };
            
            fetch('/api/report-flood/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    
                    // Thêm marker mới vào bản đồ
                    updater.addNewReport({
                        lat: formData.lat,
                        lng: formData.lng,
                        address: formData.address,
                        water_depth: formData.water_depth
                    });
                    
                    // Tải lại dữ liệu sau 5 giây
                    setTimeout(() => {
                        updater.loadFloodData();
                    }, 5000);
                    
                    // Reset form
                    reportForm.reset();
                } else {
                    alert('Lỗi: ' + data.error);
                }
            })
            .catch(error => {
                alert('Lỗi kết nối: ' + error);
            });
        });
    }
});