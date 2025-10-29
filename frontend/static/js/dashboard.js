/**
 * Dashboard Modülü
 * Admin dashboard için istatistik yönetimi ve grafik gösterimi
 */

// Dashboard chart instances
let peakHoursChart = null;
let peakDaysChart = null;

/**
 * Dashboard'u aç ve istatistikleri yükle
 */
async function openDashboard() {
    const modal = document.getElementById('dashboard-modal');
    const content = document.getElementById('dashboard-content');

    modal.classList.add('active');
    content.innerHTML = '<p class="loading">İstatistikler yükleniyor...</p>';

    try {
        const response = await fetch(`${API_URL}/api/admin/dashboard`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (!response.ok) {
            if (response.status === 403) {
                throw new Error('Bu sayfaya erişim yetkiniz bulunmamaktadır');
            }
            throw new Error('İstatistikler alınamadı');
        }

        const data = await response.json();

        if (data.success) {
            renderDashboard(data.statistics);
        } else {
            content.innerHTML = `<p class="error">${data.message || 'İstatistikler alınamadı'}</p>`;
        }
    } catch (error) {
        console.error('Dashboard error:', error);
        content.innerHTML = `<p class="error">${error.message}</p>`;
    }
}

/**
 * Dashboard UI'yi oluştur
 */
function renderDashboard(stats) {
    const content = document.getElementById('dashboard-content');

    const html = `
        <div class="dashboard-grid">
            <!-- Kullanım İstatistikleri -->
            <div class="dashboard-section">
                <h4>📊 Kullanım İstatistikleri (Son 30 Gün)</h4>
                <div class="stats-cards">
                    <div class="stat-card">
                        <div class="stat-label">Toplam Kullanıcı</div>
                        <div class="stat-value">${stats.usage.ToplamKullanici || 0}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Toplam Session</div>
                        <div class="stat-value">${stats.usage.ToplamSession || 0}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Toplam Mesaj</div>
                        <div class="stat-value">${stats.usage.ToplamMesaj || 0}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Aktif Gün</div>
                        <div class="stat-value">${stats.usage.AktifGunSayisi || 0}</div>
                    </div>
                </div>
            </div>

            <!-- Başarı Oranı -->
            <div class="dashboard-section">
                <h4>✅ Başarı Oranı</h4>
                <div class="stats-cards">
                    <div class="stat-card success">
                        <div class="stat-label">Olumlu Feedback</div>
                        <div class="stat-value">${stats.success_rate.OlumluFeedback || 0}</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-label">Olumsuz Feedback</div>
                        <div class="stat-value">${stats.success_rate.OlumsuzFeedback || 0}</div>
                    </div>
                    <div class="stat-card info">
                        <div class="stat-label">Başarı Oranı</div>
                        <div class="stat-value">${(stats.success_rate.BasariOrani || 0).toFixed(1)}%</div>
                    </div>
                </div>
            </div>

            <!-- En Çok Sorulan Sorular -->
            <div class="dashboard-section">
                <h4>🔥 En Çok Sorulan Sorular (Top 10)</h4>
                <div class="top-questions">
                    ${renderTopQuestions(stats.top_questions)}
                </div>
            </div>

            <!-- Kullanıcı Başına Soru Sayısı -->
            <div class="dashboard-section">
                <h4>👥 En Aktif Kullanıcılar (Top 10)</h4>
                <div class="user-questions">
                    ${renderUserQuestions(stats.questions_per_user)}
                </div>
            </div>

            <!-- Yoğun Kullanım Saatleri -->
            <div class="dashboard-section full-width">
                <h4>⏰ Yoğun Kullanım Saatleri</h4>
                <canvas id="peak-hours-chart" height="80"></canvas>
            </div>

            <!-- Haftalık Kullanım -->
            <div class="dashboard-section full-width">
                <h4>📅 Haftalık Kullanım Dağılımı</h4>
                <canvas id="peak-days-chart" height="80"></canvas>
            </div>
        </div>
    `;

    content.innerHTML = html;

    // Grafikleri çiz
    setTimeout(() => {
        renderPeakHoursChart(stats.peak_times.hourly);
        renderPeakDaysChart(stats.peak_times.daily);
    }, 100);
}

/**
 * En çok sorulan soruları listele
 */
function renderTopQuestions(questions) {
    if (!questions || questions.length === 0) {
        return '<p class="no-data">Henüz veri bulunmuyor</p>';
    }

    return `
        <div class="questions-list">
            ${questions.map((q, index) => `
                <div class="question-item">
                    <div class="question-rank">${index + 1}</div>
                    <div class="question-text">${escapeHtml(q.Soru)}</div>
                    <div class="question-count">${q.SoruSayisi} kez</div>
                </div>
            `).join('')}
        </div>
    `;
}

/**
 * Kullanıcı başına soru sayısını listele
 */
function renderUserQuestions(users) {
    if (!users || users.length === 0) {
        return '<p class="no-data">Henüz veri bulunmuyor</p>';
    }

    return `
        <table class="user-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Kullanıcı</th>
                    <th>Soru Sayısı</th>
                    <th>Son Soru</th>
                </tr>
            </thead>
            <tbody>
                ${users.slice(0, 10).map((user, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${escapeHtml(user.AdSoyad || user.TcKimlikNo)}</td>
                        <td><strong>${user.SoruSayisi}</strong></td>
                        <td>${formatDate(user.SonSoruTarihi)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

/**
 * Saatlik kullanım grafiği
 */
function renderPeakHoursChart(hourlyData) {
    const canvas = document.getElementById('peak-hours-chart');
    if (!canvas) return;

    // Destroy existing chart
    if (peakHoursChart) {
        peakHoursChart.destroy();
    }

    // Prepare data - ensure all 24 hours are represented
    const hours = Array.from({length: 24}, (_, i) => i);
    const messageCountsByHour = hours.map(hour => {
        const data = hourlyData.find(d => d.Saat === hour);
        return data ? data.MesajSayisi : 0;
    });

    const ctx = canvas.getContext('2d');
    peakHoursChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours.map(h => `${h}:00`),
            datasets: [{
                label: 'Mesaj Sayısı',
                data: messageCountsByHour,
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

/**
 * Günlük kullanım grafiği
 */
function renderPeakDaysChart(dailyData) {
    const canvas = document.getElementById('peak-days-chart');
    if (!canvas) return;

    // Destroy existing chart
    if (peakDaysChart) {
        peakDaysChart.destroy();
    }

    // Sort by GunNumarasi to ensure correct order
    const sortedData = [...dailyData].sort((a, b) => a.GunNumarasi - b.GunNumarasi);

    const ctx = canvas.getContext('2d');
    peakDaysChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedData.map(d => d.Gun),
            datasets: [{
                label: 'Mesaj Sayısı',
                data: sortedData.map(d => d.MesajSayisi),
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)',   // Pazar - Red
                    'rgba(59, 130, 246, 0.8)',   // Pazartesi - Blue
                    'rgba(16, 185, 129, 0.8)',  // Salı - Green
                    'rgba(245, 158, 11, 0.8)',  // Çarşamba - Amber
                    'rgba(139, 92, 246, 0.8)',  // Perşembe - Purple
                    'rgba(236, 72, 153, 0.8)',  // Cuma - Pink
                    'rgba(99, 102, 241, 0.8)'   // Cumartesi - Indigo
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

/**
 * Tarih formatlama
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * HTML escape
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
