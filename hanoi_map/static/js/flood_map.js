// ============ DRAINAGE PREDICTION UI CLASS ============

class DrainagePredictionUI {
    constructor() {
        this.modal = null;
        this.currentFloodReportId = null;
        this.currentPredictionData = null;
        this.currentLocation = null;
        
        this.initializeModal();
        this.initializeControls();
        this.initializeCSS();
        
        console.log("✅ DrainagePredictionUI đã khởi tạo");
    }

    // ============ MODAL MANAGEMENT ============

    initializeModal() {
        if (!document.getElementById('drainagePredictionModal')) {
            this.createModalStructure();
        }
        this.modal = new bootstrap.Modal(document.getElementById('drainagePredictionModal'));
    }

    createModalStructure() {
        const modalHTML = `
            <div class="modal fade" id="drainagePredictionModal" tabindex="-1" aria-labelledby="drainageModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-warning text-white">
                            <h5 class="modal-title" id="drainageModalLabel">
                                <i class="fas fa-hourglass-half me-2"></i>
                                Dự đoán thời gian cạn nước
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        
                        <div class="modal-body">
                            <!-- Loading State -->
                            <div id="drainageLoading" class="text-center py-5">
                                <div class="spinner-border text-warning" style="width: 3rem; height: 3rem;" role="status">
                                    <span class="visually-hidden">Đang tải...</span>
                                </div>
                                <p class="mt-3 text-muted">Đang tính toán thời gian cạn...</p>
                            </div>
                            
                            <!-- Results State -->
                            <div id="drainageResults" class="drainage-prediction-results" style="display: none;">
                                <!-- Results will be dynamically populated -->
                            </div>
                            
                            <!-- Error State -->
                            <div id="drainageError" class="text-center py-5" style="display: none;">
                                <div class="alert alert-danger">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    <strong id="errorMessage">Đã xảy ra lỗi khi dự đoán</strong>
                                </div>
                                <button class="btn btn-warning" onclick="window.drainageUI.retryPrediction()">
                                    <i class="fas fa-redo me-1"></i>Thử lại
                                </button>
                            </div>
                        </div>
                        
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times me-1"></i>Đóng
                            </button>
                            <div id="modalActionButtons" style="display: none;">
                                <button type="button" class="btn btn-outline-warning" onclick="window.drainageUI.sharePrediction()">
                                    <i class="fas fa-share-alt me-1"></i>Chia sẻ
                                </button>
                                <button type="button" class="btn btn-warning" onclick="window.drainageUI.updatePrediction()">
                                    <i class="fas fa-sync-alt me-1"></i>Cập nhật
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    // ============ UI STATE MANAGEMENT ============

    showLoading() {
        document.getElementById('drainageLoading').style.display = 'block';
        document.getElementById('drainageResults').style.display = 'none';
        document.getElementById('drainageError').style.display = 'none';
        document.getElementById('modalActionButtons').style.display = 'none';
    }

    showResults() {
        document.getElementById('drainageLoading').style.display = 'none';
        document.getElementById('drainageResults').style.display = 'block';
        document.getElementById('drainageError').style.display = 'none';
        document.getElementById('modalActionButtons').style.display = 'flex';
    }

    showError(message) {
        document.getElementById('drainageLoading').style.display = 'none';
        document.getElementById('drainageResults').style.display = 'none';
        document.getElementById('drainageError').style.display = 'block';
        document.getElementById('modalActionButtons').style.display = 'none';
        document.getElementById('errorMessage').textContent = message;
    }

    // ============ CSRF TOKEN MANAGEMENT ============

    getCsrfToken() {
        // Cách 1: Từ input ẩn trong form (phổ biến nhất)
        const tokenFromInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenFromInput && tokenFromInput.value) {
            console.log('✅ CSRF token từ input:', tokenFromInput.value.substring(0, 10) + '...');
            return tokenFromInput.value;
        }
        
        // Cách 2: Từ cookie (fallback)
        const cookieValue = this.getCookie('csrftoken');
        if (cookieValue) {
            console.log('✅ CSRF token từ cookie:', cookieValue.substring(0, 10) + '...');
            return cookieValue;
        }
        
        // Cách 3: Từ meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken && metaToken.content) {
            console.log('✅ CSRF token từ meta:', metaToken.content.substring(0, 10) + '...');
            return metaToken.content;
        }
        
        console.warn('⚠️ Không tìm thấy CSRF token');
        return '';
    }

    getCookie(name) {
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

    // ============ PREDICTION FUNCTIONS ============

   async predictForLocation(lat, lng, locationName, depth, floodReportId = null) {
    console.log(`📍 Dự đoán thời gian cạn: ${locationName}`);
    console.log(`📍 Tọa độ: ${lat}, ${lng}, Độ sâu: ${depth}cm`);
    
    this.currentFloodReportId = floodReportId;
    this.currentLocation = { lat, lng, name: locationName, depth };
    
    this.showModal();
    this.showLoading();
    
    try {
        const csrfToken = this.getCsrfToken();
        if (!csrfToken) {
            throw new Error('Không tìm thấy CSRF token. Vui lòng làm mới trang.');
        }
        
        if (floodReportId) {
            console.log(`✅ Đã có flood_report_id=${floodReportId}, gọi API GET`);
            
            const response = await fetch(`/api/predict-drainage/?flood_report_id=${floodReportId}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.currentPredictionData = data.data || data;
                this.displayPrediction(this.currentPredictionData);
            } else {
                throw new Error(data.error || 'Không thể dự đoán thời gian cạn');
            }
        }
        else {
            console.log(`⚠️ Chưa có flood_report_id, dùng API location`);
            const response = await fetch('/api/predict-drainage-location/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    lat: lat,
                    lng: lng,
                    location_name: locationName,
                    water_depth_cm: depth
                })
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.currentPredictionData = data.data || data;
                this.currentFloodReportId = data.data?.flood_report_id;
                this.displayPrediction(this.currentPredictionData);
            } else {
                throw new Error(data.error || 'Không thể dự đoán thời gian cạn');
            }
        }
        
    } catch (error) {
        console.error('❌ Lỗi dự đoán:', error);
        this.showError(this.formatErrorMessage(error.message));
    }
}

    // ============ DISPLAY FUNCTIONS ============

    displayPrediction(predictionData) {
        this.showResults();
        
        const resultsContainer = document.getElementById('drainageResults');
        resultsContainer.innerHTML = this.generateResultsHTML(predictionData);
        this.updateProgressBar(predictionData.estimated_drainage_time_hours, 0);
        this.startProgressTimer(predictionData.estimated_drainage_time_hours);
    }

    generateResultsHTML(predictionData) {
        const levelClass = this.getLevelClass(predictionData.drainage_level);
        const levelText = predictionData.drainage_level_text;
        const isLongTerm = predictionData.estimated_drainage_time_hours >= 24;
        const hoursText = isLongTerm ? 
            `${predictionData.estimated_drainage_time_hours} giờ (${(predictionData.estimated_drainage_time_hours / 24).toFixed(1)} ngày)` : 
            `${predictionData.estimated_drainage_time_hours} giờ`;
        
        return `
            <!-- Main Prediction Card -->
            <div class="card border-warning mb-4">
                <div class="card-body text-center">
                    <div class="mb-3">
                        <i class="fas fa-water fa-3x text-warning mb-3"></i>
                        <h4 class="card-title">Thời gian cạn dự kiến</h4>
                    </div>
                    
                    <div class="display-2 fw-bold text-warning mb-2">${predictionData.estimated_drainage_time_hours}</div>
                    <div class="h5 mb-4">${hoursText}</div>
                    
                    <div class="alert ${levelClass.replace('bg-', 'alert-')}">
                        <i class="fas fa-info-circle me-2"></i>
                        ${this.escapeHtml(predictionData.message)}
                    </div>
                </div>
            </div>
            
            <!-- Details Section -->
            <div class="row mb-4">
                <!-- Location Info -->
                <div class="col-md-6 mb-3">
                    <div class="card h-100">
                        <div class="card-header bg-light">
                            <i class="fas fa-map-marker-alt me-2"></i>Thông tin vị trí
                        </div>
                        <div class="card-body">
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Địa điểm:</span>
                                    <strong>${this.escapeHtml(this.currentLocation?.name || 'Không xác định')}</strong>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Độ sâu hiện tại:</span>
                                    <strong class="text-warning">${predictionData.water_depth_cm} cm</strong>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Thời điểm bắt đầu:</span>
                                    <strong>${new Date().toLocaleTimeString('vi-VN')}</strong>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Dự kiến cạn lúc:</span>
                                    <strong>${predictionData.completion_time_formatted}</strong>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Mức độ:</span>
                                    <span class="badge ${levelClass}">${levelText}</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <!-- Factors & Recommendations -->
                <div class="col-md-6 mb-3">
                    <div class="card h-100">
                        <div class="card-header bg-light">
                            <i class="fas fa-chart-line me-2"></i>Yếu tố & Khuyến nghị
                        </div>
                        <div class="card-body">
                            <!-- Factors -->
                            <h6 class="text-muted mb-2">Yếu tố ảnh hưởng:</h6>
                            <div id="factorsList" class="mb-3">
                                ${predictionData.factors_considered?.map(factor => `
                                    <div class="d-flex align-items-center mb-2">
                                        <i class="fas fa-check-circle text-success me-2"></i>
                                        <small>${this.escapeHtml(factor)}</small>
                                    </div>
                                `).join('') || '<p class="text-muted small">Không có thông tin</p>'}
                            </div>
                            
                            <!-- Recommendations -->
                            <h6 class="text-muted mb-2">Khuyến nghị:</h6>
                            <div id="recommendationsList" class="recommendations-list">
                                ${predictionData.recommendations?.map(rec => `
                                    <div class="d-flex align-items-start mb-2">
                                        <i class="fas fa-chevron-right text-warning mt-1 me-2"></i>
                                        <small>${this.escapeHtml(rec)}</small>
                                    </div>
                                `).join('') || '<p class="text-muted small">Không có khuyến nghị</p>'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Progress Bar -->
            <div class="card">
                <div class="card-header bg-light">
                    <i class="fas fa-hourglass-half me-2"></i>Tiến độ cạn nước
                </div>
                <div class="card-body">
                    <div class="progress" style="height: 30px; border-radius: 15px;">
                        <div id="drainageProgress" class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 0%; border-radius: 15px;">
                            <span id="progressText" class="fw-bold">0%</span>
                        </div>
                    </div>
                    <div class="mt-3 text-center">
                        <small class="text-muted" id="remainingTimeText">
                            <i class="fas fa-clock me-1"></i>
                            Còn khoảng <strong id="remainingHours">${predictionData.estimated_drainage_time_hours}</strong> giờ để nước rút hết
                        </small>
                    </div>
                </div>
            </div>
            
            <!-- Database Info -->
            ${predictionData.flood_report_id ? `
            <div class="alert alert-success mt-3 small">
                <div class="d-flex align-items-center">
                    <i class="fas fa-database me-2"></i>
                    <div>
                        <strong>Đã lưu vào hệ thống</strong>
                        <div class="mt-1">
                            <span class="badge bg-secondary me-2">Report #${predictionData.flood_report_id}</span>
                            ${predictionData.prediction_id ? 
                                `<span class="badge bg-primary">Prediction #${predictionData.prediction_id}</span>` : 
                                ''
                            }
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
        `;
    }

    getLevelClass(level) {
        const classes = {
            'fast': 'bg-success',
            'medium': 'bg-warning',
            'slow': 'bg-danger',
            'very_slow': 'bg-dark'
        };
        return classes[level] || 'bg-secondary';
    }

    updateProgressBar(totalHours, elapsedHours) {
        const progress = Math.min(100, (elapsedHours / totalHours) * 100);
        const progressBar = document.getElementById('drainageProgress');
        const progressText = document.getElementById('progressText');
        const remainingHours = Math.max(0, totalHours - elapsedHours);
        
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `${progress.toFixed(1)}%`;
            
            // Update color based on progress
            if (progress < 30) {
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-danger';
            } else if (progress < 70) {
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
            } else {
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-success';
            }
            
            // Update remaining time text
            const remainingElement = document.getElementById('remainingTimeText');
            if (remainingElement) {
                if (remainingHours > 0) {
                    remainingElement.innerHTML = `
                        <i class="fas fa-clock me-1"></i>
                        Còn khoảng <strong>${remainingHours.toFixed(1)}</strong> giờ để nước rút hết
                    `;
                } else {
                    remainingElement.innerHTML = `
                        <i class="fas fa-check-circle me-1 text-success"></i>
                        <strong>Nước đã rút hết</strong>
                    `;
                }
            }
        }
    }

    startProgressTimer(totalHours) {
        let elapsedHours = 0;
        
        const timer = setInterval(() => {
            elapsedHours += 0.0167; // 1 phút = 0.0167 giờ
            
            if (elapsedHours >= totalHours) {
                elapsedHours = totalHours;
                clearInterval(timer);
            }
            
            this.updateProgressBar(totalHours, elapsedHours);
        }, 60000); // Update mỗi phút
    }

    // ============ CONTROL FUNCTIONS ============

    initializeControls() {
        this.addControlPanelButton();
    }

    addControlPanelButton() {
        const controlPanel = document.querySelector('.control-panel .panel-content');
        if (controlPanel && !controlPanel.querySelector('#drainageDashboardBtn')) {
            const btnHTML = `
                <div class="mt-3">
                    <button id="drainageDashboardBtn" class="btn btn-warning w-100" onclick="window.drainageUI.showDashboard()">
                        <i class="fas fa-hourglass-half me-1"></i>
                        Dashboard dự đoán cạn
                    </button>
                </div>
            `;
            controlPanel.insertAdjacentHTML('beforeend', btnHTML);
        }
    }

    // ============ ACTION FUNCTIONS ============

    retryPrediction() {
        if (this.currentFloodReportId) {
            this.predictForReport(this.currentFloodReportId);
        } else if (this.currentLocation) {
            const { lat, lng, name, depth } = this.currentLocation;
            this.predictForLocation(lat, lng, name, depth);
        }
    }

    updatePrediction() {
        this.retryPrediction();
        this.showToast('Đang cập nhật dự đoán...', 'info');
    }

    async sharePrediction() {
        if (!this.currentPredictionData) return;
        
        const hours = this.currentPredictionData.estimated_drainage_time_hours;
        const location = this.currentLocation?.name || 'Vị trí được chọn';
        const message = `🚨 Dự đoán thời gian cạn nước: ${hours} giờ\n📍 ${location}\n📊 Hệ thống giám sát ngập lụt Hà Nội`;
        
        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Dự đoán thời gian cạn nước',
                    text: message,
                    url: window.location.href
                });
            } catch (error) {
                if (error.name !== 'AbortError') {
                    this.copyToClipboard(message);
                }
            }
        } else {
            this.copyToClipboard(message);
        }
    }

    copyToClipboard(text) {
        navigator.clipboard.writeText(text)
            .then(() => this.showToast('Đã sao chép thông tin dự đoán!', 'success'))
            .catch(() => this.showToast('Không thể sao chép', 'error'));
    }

    // ============ DASHBOARD FUNCTIONS ============

    async showDashboard() {
        if (!document.getElementById('drainageDashboardModal')) {
            this.createDashboardModal();
        }
        
        const modal = new bootstrap.Modal(document.getElementById('drainageDashboardModal'));
        await this.loadDashboardData();
        modal.show();
    }

    createDashboardModal() {
        const modalHTML = `
            <div class="modal fade" id="drainageDashboardModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-warning text-dark">
                            <h5 class="modal-title">
                                <i class="fas fa-hourglass-half me-2"></i>
                                Dashboard Dự đoán Cạn Nước
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-0">
                            <!-- Loading -->
                            <div id="dashboardLoading" class="text-center py-5">
                                <div class="spinner-border text-warning" style="width: 3rem; height: 3rem;"></div>
                                <p class="mt-3 text-muted">Đang tải dashboard...</p>
                            </div>
                            
                            <!-- Content will be loaded here -->
                            <div id="dashboardContent" style="display: none;"></div>
                            
                            <!-- Error -->
                            <div id="dashboardError" style="display: none;" class="text-center py-5">
                                <div class="alert alert-danger">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    <strong>Không thể tải dữ liệu dashboard</strong>
                                </div>
                                <button class="btn btn-warning" onclick="window.drainageUI.loadDashboardData()">
                                    <i class="fas fa-redo me-1"></i>Thử lại
                                </button>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times me-1"></i>Đóng
                            </button>
                            <button type="button" class="btn btn-warning" onclick="window.drainageUI.loadDashboardData()">
                                <i class="fas fa-sync-alt me-1"></i>Tải lại
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    async loadDashboardData() {
        try {
            document.getElementById('dashboardLoading').style.display = 'block';
            document.getElementById('dashboardContent').style.display = 'none';
            document.getElementById('dashboardError').style.display = 'none';
            
            const response = await fetch('/api/drainage-dashboard/');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('dashboardLoading').style.display = 'none';
                document.getElementById('dashboardContent').style.display = 'block';
                document.getElementById('dashboardContent').innerHTML = this.generateDashboardHTML(data.data);
            } else {
                throw new Error(data.error || 'Không thể tải dữ liệu');
            }
            
        } catch (error) {
            console.error('❌ Lỗi dashboard:', error);
            document.getElementById('dashboardLoading').style.display = 'none';
            document.getElementById('dashboardError').style.display = 'block';
        }
    }

    generateDashboardHTML(dashboardData) {
        const { summary, soonest_completions } = dashboardData;
        
        return `
            <!-- Summary Stats -->
            <div class="row g-3 p-3 bg-light">
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 shadow-sm">
                        <div class="card-body py-4">
                            <div class="display-5 fw-bold text-primary">${summary.total_active_predictions}</div>
                            <div class="text-muted small">Tổng dự đoán</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 shadow-sm">
                        <div class="card-body py-4">
                            <div class="display-5 fw-bold text-success">${summary.fast_drainage_count}</div>
                            <div class="text-muted small">Cạn nhanh (≤2h)</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 shadow-sm">
                        <div class="card-body py-4">
                            <div class="display-5 fw-bold text-warning">${summary.medium_drainage_count}</div>
                            <div class="text-muted small">Cạn TB (2-6h)</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 shadow-sm">
                        <div class="card-body py-4">
                            <div class="display-5 fw-bold text-danger">${summary.slow_drainage_count}</div>
                            <div class="text-muted small">Cạn chậm (>6h)</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Active Predictions -->
            <div class="p-3">
                <div class="card border-0 shadow-sm">
                    <div class="card-header bg-white border-bottom">
                        <h6 class="mb-0">
                            <i class="fas fa-clock me-2"></i>
                            Dự đoán đang hoạt động
                            <span class="badge bg-warning ms-2">${soonest_completions?.length || 0}</span>
                        </h6>
                    </div>
                    <div class="card-body p-0">
                        ${soonest_completions && soonest_completions.length > 0 ? `
                            <div class="table-responsive">
                                <table class="table table-hover mb-0">
                                    <thead class="table-light">
                                        <tr>
                                            <th>Địa điểm</th>
                                            <th>Quận</th>
                                            <th>Độ sâu</th>
                                            <th>Thời gian còn lại</th>
                                            <th>Trạng thái</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${soonest_completions.map(pred => `
                                            <tr>
                                                <td>${this.escapeHtml(pred.address || 'Không xác định')}</td>
                                                <td><span class="badge bg-secondary">${this.escapeHtml(pred.district || '')}</span></td>
                                                <td><span class="badge bg-primary">${pred.current_depth || 0}cm</span></td>
                                                <td>
                                                    <div class="progress" style="height: 20px;">
                                                        <div class="progress-bar ${pred.remaining_hours <= 2 ? 'bg-success' : pred.remaining_hours <= 6 ? 'bg-warning' : 'bg-danger'}" 
                                                             style="width: ${Math.min(100, 100 - (pred.remaining_hours / 24 * 100))}%">
                                                            ${pred.remaining_hours?.toFixed(1) || 0}h
                                                        </div>
                                                    </div>
                                                </td>
                                                <td>
                                                    ${pred.remaining_hours <= 2 ? 
                                                        '<span class="badge bg-success">Sắp cạn</span>' : 
                                                        pred.remaining_hours <= 6 ?
                                                        '<span class="badge bg-warning">Đang cạn</span>' :
                                                        '<span class="badge bg-danger">Lâu cạn</span>'
                                                    }
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        ` : `
                            <div class="text-center py-5">
                                <i class="fas fa-clock fa-3x text-muted mb-3"></i>
                                <p class="text-muted">Không có dự đoán nào đang hoạt động</p>
                            </div>
                        `}
                    </div>
                </div>
            </div>
            
            <!-- District Distribution -->
            ${summary.districts && Object.keys(summary.districts).length > 0 ? `
            <div class="p-3">
                <div class="card border-0 shadow-sm">
                    <div class="card-header bg-white">
                        <h6 class="mb-0"><i class="fas fa-map-marker-alt me-2"></i>Phân bố theo quận</h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            ${Object.entries(summary.districts).map(([district, count]) => `
                                <div class="col-md-4 col-6 mb-2">
                                    <div class="d-flex justify-content-between align-items-center p-2 border rounded">
                                        <span class="fw-medium">${this.escapeHtml(district || 'Không xác định')}</span>
                                        <span class="badge bg-warning">${count}</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
        `;
    }

    // ============ UTILITY FUNCTIONS ============

    showModal() {
        this.modal.show();
    }

    hideModal() {
        this.modal.hide();
    }

    showToast(message, type = 'info') {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.className = `toast-alert alert alert-${type} shadow`;
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                <span>${this.escapeHtml(message)}</span>
            </div>
        `;
        
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 99999;
            min-width: 300px;
            animation: fadeInDown 0.3s, fadeOutUp 0.3s 2.7s;
        `;
        
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ============ CSS STYLES ============

    initializeCSS() {
        if (!document.getElementById('drainage-ui-styles')) {
            const style = document.createElement('style');
            style.id = 'drainage-ui-styles';
            style.textContent = `
                /* Drainage UI Styles */
                .drainage-prediction-results .progress {
                    background-color: #f0f0f0;
                    border-radius: 15px;
                }
                
                .drainage-prediction-results .progress-bar {
                    border-radius: 15px;
                    font-weight: 600;
                }
                
                .recommendations-list {
                    max-height: 200px;
                    overflow-y: auto;
                    padding-right: 10px;
                }
                
                .recommendations-list::-webkit-scrollbar {
                    width: 6px;
                }
                
                .recommendations-list::-webkit-scrollbar-track {
                    background: #f1f1f1;
                    border-radius: 3px;
                }
                
                .recommendations-list::-webkit-scrollbar-thumb {
                    background: #f6ad55;
                    border-radius: 3px;
                }
                
                .recommendations-list::-webkit-scrollbar-thumb:hover {
                    background: #ed8936;
                }
                
                /* Toast animations */
                @keyframes fadeInDown {
                    from { opacity: 0; transform: translateY(-20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                @keyframes fadeOutUp {
                    from { opacity: 1; transform: translateY(0); }
                    to { opacity: 0; transform: translateY(-20px); }
                }
                
                .toast-alert {
                    animation: fadeInDown 0.3s, fadeOutUp 0.3s 2.7s;
                }
                
                /* Responsive adjustments */
                @media (max-width: 768px) {
                    .drainage-prediction-results .display-2 {
                        font-size: 3.5rem;
                    }
                    
                    .modal-dialog.modal-lg {
                        margin: 10px;
                        max-width: calc(100% - 20px);
                    }
                }
                
                @media (max-width: 576px) {
                    .drainage-prediction-results .display-2 {
                        font-size: 2.5rem;
                    }
                    
                    .modal-footer {
                        flex-direction: column;
                        gap: 10px;
                    }
                    
                    .modal-footer button {
                        width: 100%;
                    }
                }
            `;
            
            document.head.appendChild(style);
        }
    }

    // ============ GLOBAL INTEGRATION FUNCTIONS ============

    static predictAndShowDashboard(lat, lng, locationName, depth, floodReportId = null) {
        if (!window.drainageUI) {
            window.drainageUI = new DrainagePredictionUI();
        }
        window.drainageUI.showToast('Đang dự đoán thời gian cạn...', 'info');
        window.drainageUI.predictForLocation(lat, lng, locationName, depth, floodReportId)
            .then(() => {
                // Sau khi dự đoán thành công, mở dashboard
                setTimeout(() => {
                    window.drainageUI.showDashboard();
                }, 1500);
            })
            .catch(error => {
                console.error('Lỗi dự đoán:', error);
                // Vẫn mở dashboard khi có lỗi
                setTimeout(() => {
                    window.drainageUI.showDashboard();
                }, 500);
            });
    }

    /**
     * Dự đoán cho flood report
     */
    static predictDrainageTime(reportId) {
        if (!window.drainageUI) {
            window.drainageUI = new DrainagePredictionUI();
        }
        window.drainageUI.predictForReport(reportId);
    }
}

// ============ GLOBAL FUNCTIONS ============

/**
 * Hàm escape string cho onclick
 */
function escapeString(str) {
    if (!str) return '';
    return str
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r');
}

/**
 * Hàm escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============ GLOBAL INITIALIZATION ============

// Khởi tạo khi DOM sẵn sàng
document.addEventListener('DOMContentLoaded', function() {
    // Tạo instance global
    window.drainageUI = new DrainagePredictionUI();
    
    // Thêm các hàm global để tương thích với code cũ
    window.predictDrainageTime = (reportId) => DrainagePredictionUI.predictDrainageTime(reportId);
    window.predictDrainageForFloodLocation = (lat, lng, name, depth, reportId = null) => 
        DrainagePredictionUI.predictAndShowDashboard(lat, lng, name, depth, reportId);
    window.showDrainageDashboard = () => window.drainageUI?.showDashboard();
    
    console.log("🌊 Hệ thống dự đoán thời gian cạn đã sẵn sàng");
});