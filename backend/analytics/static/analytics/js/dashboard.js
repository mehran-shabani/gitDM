// Dashboard JavaScript
let glucoseTrendChart = null;
let hba1cDistributionChart = null;
let dashboardData = {};

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    loadDashboardData();
});

function initializeDashboard() {
    // Set default date values
    const today = new Date();
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
    
    document.querySelector('input[name="end_date"]').value = today.toISOString().split('T')[0];
    document.querySelector('input[name="start_date"]').value = lastMonth.toISOString().split('T')[0];
}

function setupEventListeners() {
    // Period buttons
    document.querySelectorAll('[data-period]').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('[data-period]').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            updateGlucoseTrend(this.dataset.period);
        });
    });
    
    // Report type change
    document.querySelector('select[name="report_type"]').addEventListener('change', function() {
        const patientContainer = document.getElementById('patient-select-container');
        if (this.value === 'patient_summary') {
            patientContainer.style.display = 'block';
            loadPatientsList();
        } else {
            patientContainer.style.display = 'none';
        }
    });
}

async function loadDashboardData() {
    try {
        // Load summary data
        const summaryResponse = await fetch('/api/analytics/dashboard/summary/', {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!summaryResponse.ok) throw new Error('Failed to load dashboard summary');
        
        const summaryData = await summaryResponse.json();
        updateSummaryCards(summaryData);
        
        // Load charts data
        await Promise.all([
            loadGlucoseTrend('week'),
            loadHbA1cDistribution(),
            loadAttentionPatients(),
            loadRecentAlerts()
        ]);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showNotification('خطا در بارگذاری داده‌ها', 'error');
    }
}

function updateSummaryCards(data) {
    // Update stat cards
    document.getElementById('total-patients').textContent = data.total_patients || 0;
    document.getElementById('active-patients').textContent = data.active_patients || 0;
    document.getElementById('today-encounters').textContent = data.total_encounters_today || 0;
    document.getElementById('pending-alerts').textContent = data.pending_alerts || 0;
    
    // Update trends
    if (data.patient_trend) {
        const trendElement = document.getElementById('patients-trend');
        const change = data.patient_trend.change_percentage;
        trendElement.innerHTML = `<i class="fas fa-arrow-${change >= 0 ? 'up' : 'down'}"></i> ${Math.abs(change)}%`;
        trendElement.className = change >= 0 ? 'text-success' : 'text-danger';
    }
    
    // Update average values
    document.getElementById('avg-hba1c').textContent = data.avg_hba1c ? `${data.avg_hba1c.toFixed(1)}%` : '-';
    document.getElementById('goal-achievement').textContent = data.goal_achievement_rate ? `${data.goal_achievement_rate.toFixed(1)}%` : '-';
}

async function loadGlucoseTrend(period = 'week') {
    try {
        const response = await fetch(`/api/analytics/system-analytics/trend_chart/?metric=glucose&period=${period}`, {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error('Failed to load glucose trend');
        
        const chartData = await response.json();
        renderGlucoseTrendChart(chartData);
        
    } catch (error) {
        console.error('Error loading glucose trend:', error);
    }
}

function renderGlucoseTrendChart(data) {
    const ctx = document.getElementById('glucose-trend-chart').getContext('2d');
    
    if (glucoseTrendChart) {
        glucoseTrendChart.destroy();
    }
    
    glucoseTrendChart = new Chart(ctx, {
        type: data.chart_type || 'line',
        data: {
            labels: data.labels,
            datasets: data.datasets
        },
        options: {
            ...data.options,
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                tooltip: {
                    rtl: true,
                    textDirection: 'rtl',
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} mg/dL`;
                        }
                    }
                }
            }
        }
    });
}

async function loadHbA1cDistribution() {
    try {
        const response = await fetch('/api/analytics/doctor-analytics/patient_distribution/', {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error('Failed to load HbA1c distribution');
        
        const chartData = await response.json();
        renderHbA1cDistributionChart(chartData);
        
    } catch (error) {
        console.error('Error loading HbA1c distribution:', error);
    }
}

function renderHbA1cDistributionChart(data) {
    const ctx = document.getElementById('hba1c-distribution-chart').getContext('2d');
    
    if (hba1cDistributionChart) {
        hba1cDistributionChart.destroy();
    }
    
    hba1cDistributionChart = new Chart(ctx, {
        type: data.chart_type || 'doughnut',
        data: {
            labels: data.labels,
            datasets: data.datasets
        },
        options: {
            ...data.options,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    rtl: true,
                    labels: {
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    rtl: true,
                    textDirection: 'rtl',
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

async function loadAttentionPatients() {
    try {
        const response = await fetch('/api/analytics/patient-analytics/batch_analytics/?patient_ids[]=all', {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error('Failed to load patients data');
        
        const patients = await response.json();
        renderAttentionPatients(patients);
        
    } catch (error) {
        console.error('Error loading attention patients:', error);
        document.getElementById('attention-patients').innerHTML = 
            '<tr><td colspan="4" class="text-center text-muted">خطا در بارگذاری داده‌ها</td></tr>';
    }
}

function renderAttentionPatients(patients) {
    const tbody = document.getElementById('attention-patients');
    
    // Filter patients needing attention (HbA1c > 8)
    const attentionPatients = patients
        .filter(p => p.avg_hba1c && p.avg_hba1c > 8)
        .sort((a, b) => b.avg_hba1c - a.avg_hba1c)
        .slice(0, 5);
    
    if (attentionPatients.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">بیماری نیازمند توجه فوری یافت نشد</td></tr>';
        return;
    }
    
    tbody.innerHTML = attentionPatients.map(patient => {
        const status = getHbA1cStatus(patient.avg_hba1c);
        return `
            <tr>
                <td>${patient.patient_name}</td>
                <td>${patient.avg_hba1c.toFixed(1)}%</td>
                <td><span class="badge badge-${status.class}">${status.text}</span></td>
                <td>
                    <a href="/patients/${patient.patient}/detail/" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-eye"></i>
                    </a>
                </td>
            </tr>
        `;
    }).join('');
}

async function loadRecentAlerts() {
    try {
        const response = await fetch('/api/alerts/?limit=5&ordering=-created_at', {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error('Failed to load alerts');
        
        const alerts = await response.json();
        renderRecentAlerts(alerts.results || alerts);
        
    } catch (error) {
        console.error('Error loading alerts:', error);
        document.getElementById('recent-alerts').innerHTML = 
            '<div class="list-group-item text-center text-muted">خطا در بارگذاری هشدارها</div>';
    }
}

function renderRecentAlerts(alerts) {
    const container = document.getElementById('recent-alerts');
    
    if (alerts.length === 0) {
        container.innerHTML = '<div class="list-group-item text-center text-muted">هشدار جدیدی وجود ندارد</div>';
        return;
    }
    
    container.innerHTML = alerts.map(alert => {
        const severity = getSeverityInfo(alert.severity);
        return `
            <div class="list-group-item alert-item severity-${alert.severity}">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${alert.alert_type_display || alert.alert_type}</h6>
                    <small class="text-muted">${formatRelativeTime(alert.created_at)}</small>
                </div>
                <p class="mb-1">${alert.message}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">بیمار: ${alert.patient_name}</small>
                    <span class="badge bg-${severity.class}">${severity.text}</span>
                </div>
            </div>
        `;
    }).join('');
}

async function loadPatientsList() {
    try {
        const response = await fetch('/api/patients/', {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error('Failed to load patients');
        
        const patients = await response.json();
        const select = document.querySelector('select[name="patient_id"]');
        
        select.innerHTML = '<option value="">انتخاب کنید...</option>' +
            patients.results.map(p => `<option value="${p.id}">${p.full_name}</option>`).join('');
            
    } catch (error) {
        console.error('Error loading patients:', error);
    }
}

async function generateReport() {
    const form = document.getElementById('report-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    // Clean up data
    if (!data.patient_id) delete data.patient_id;
    if (!data.start_date) delete data.start_date;
    if (!data.end_date) delete data.end_date;
    data.include_charts = data.include_charts === 'on';
    
    try {
        const response = await fetch('/api/analytics/reports/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to generate report');
        }
        
        const report = await response.json();
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('reportModal'));
        modal.hide();
        
        showNotification('گزارش با موفقیت ایجاد شد', 'success');
        
        // Check report status periodically
        checkReportStatus(report.id);
        
    } catch (error) {
        console.error('Error generating report:', error);
        showNotification(error.message || 'خطا در ایجاد گزارش', 'error');
    }
}

async function checkReportStatus(reportId) {
    const checkInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/analytics/reports/${reportId}/`, {
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Failed to check report status');
            
            const report = await response.json();
            
            if (report.status === 'completed') {
                clearInterval(checkInterval);
                showNotification('گزارش آماده دانلود است', 'success');
                downloadReport(reportId);
            } else if (report.status === 'failed') {
                clearInterval(checkInterval);
                showNotification('خطا در تولید گزارش: ' + report.error_message, 'error');
            }
        } catch (error) {
            clearInterval(checkInterval);
            console.error('Error checking report status:', error);
        }
    }, 2000);
}

async function downloadReport(reportId) {
    window.location.href = `/api/analytics/reports/${reportId}/download/`;
}

function refreshDashboard() {
    showNotification('در حال بروزرسانی...', 'info');
    loadDashboardData().then(() => {
        showNotification('داشبورد بروزرسانی شد', 'success');
    });
}

async function exportDashboard() {
    try {
        const response = await fetch('/api/analytics/reports/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                report_type: 'system_overview',
                format: 'pdf',
                include_charts: true
            })
        });
        
        if (!response.ok) throw new Error('Failed to export dashboard');
        
        const report = await response.json();
        showNotification('در حال تولید گزارش داشبورد...', 'info');
        checkReportStatus(report.id);
        
    } catch (error) {
        console.error('Error exporting dashboard:', error);
        showNotification('خطا در صدور گزارش', 'error');
    }
}

// Helper functions
function getAuthToken() {
    // Get auth token from cookies or local storage
    return localStorage.getItem('authToken') || getCookie('authToken');
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function getHbA1cStatus(value) {
    if (value < 7) return { text: 'عالی', class: 'excellent' };
    if (value < 8) return { text: 'خوب', class: 'good' };
    if (value < 9) return { text: 'متوسط', class: 'fair' };
    return { text: 'نیاز به بهبود', class: 'poor' };
}

function getSeverityInfo(severity) {
    const severityMap = {
        'critical': { text: 'بحرانی', class: 'danger' },
        'high': { text: 'بالا', class: 'warning' },
        'medium': { text: 'متوسط', class: 'info' },
        'low': { text: 'پایین', class: 'success' }
    };
    return severityMap[severity] || { text: severity, class: 'secondary' };
}

function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 60) return `${minutes} دقیقه پیش`;
    if (hours < 24) return `${hours} ساعت پیش`;
    if (days < 7) return `${days} روز پیش`;
    
    return date.toLocaleDateString('fa-IR');
}

function showNotification(message, type = 'info') {
    // Create toast notification
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    toastContainer.appendChild(toastElement.firstElementChild);
    
    const toast = new bootstrap.Toast(toastContainer.lastElementChild);
    toast.show();
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// Update glucose trend when period changes
function updateGlucoseTrend(period) {
    loadGlucoseTrend(period);
}