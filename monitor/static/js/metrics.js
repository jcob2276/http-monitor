let currentTimeRange = '5m';
let selectedSite = null;
let sshIntervalId = null;

window.addEventListener("error", function (e) {
    console.error("🚨 JavaScript Error:", e.message, "at", e.filename + ":" + e.lineno);
});

// 📡 HTTP Chart
function loadChartData(websiteId) {
    fetch(`/chart_data?website_id=${websiteId}&range=${currentTimeRange}`)
        .then(response => response.json())
        .then(data => {
            if (window.responseChart) {
                window.responseChart.data.labels = data.labels;
                window.responseChart.data.datasets[0].data = data.response_times;
                window.responseChart.statusCodes = data.status_codes;
                window.responseChart.update();
            }
        });
}

// 🧠 SSH Chart
function loadSSHChart(host) {
    fetch(`/api/ssh_metrics/?host=${host}&range=${currentTimeRange}`)
        .then(response => response.json())
        .then(data => {
            const canvas = document.getElementById('resourceChart');
            if (!canvas) {
                console.warn("⚠️ <canvas id='resourceChart'> not found");
                return;
            }
            const ctx = canvas.getContext('2d');

            if (window.resourceChart && typeof window.resourceChart.destroy === 'function') {
                window.resourceChart.destroy();
            }

            window.resourceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.timestamps,
                    datasets: [
                        {
                            label: 'CPU (%)',
                            data: data.cpu,
                            borderColor: 'orange',
                            borderWidth: 2,
                            fill: false
                        },
                        {
                            label: 'RAM użyte (MB)',
                            data: data.ram_used,
                            borderColor: 'blue',
                            borderWidth: 2,
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        });
}

// 🔁 Interval refresher (SSH, tylko dla 5m)
function startSSHRefresh(host) {
    clearInterval(sshIntervalId);
    if (currentTimeRange === "5m") {
        sshIntervalId = setInterval(() => {
            loadSSHChart(host);
        }, 10000); // co 10s
    }
}

// 🔄 Reset HTTP Chart
function resetChart() {
    if (window.responseChart) {
        window.responseChart.data.labels = ["Oczekiwanie..."];
        window.responseChart.data.datasets[0].data = [null];
        window.responseChart.update();
    }
}

// 🔌 WebSocket (HTTP realtime only)
const ws = new WebSocket("ws://" + window.location.host + "/ws/metrics/");
ws.onmessage = function (event) {
    const data = JSON.parse(event.data);
    if (selectedSite && data.website_id !== selectedSite) return;
    if (currentTimeRange !== "5m") return;

    if (window.responseChart) {
        if (window.responseChart.data.labels.length > 50) {
            window.responseChart.data.labels.shift();
            window.responseChart.data.datasets[0].data.shift();
        }

        window.responseChart.data.labels.push(data.timestamp);
        window.responseChart.data.datasets[0].data.push(data.response_time);
        window.responseChart.update();
    }
};

// 📊 KPI Loader
let previousUptime = null;

function updateKPI() {
    fetch("/api/kpi/")
        .then(res => res.json())
        .then(data => {
            // 🔢 Aktywne Usługi
            document.getElementById("activeServicesCount").textContent = data.active_services;

            // 🧠 CPU
            document.getElementById("cpuUsageValue").textContent = `${data.cpu_avg}%`;

            // 📦 RAM
            document.getElementById("memoryUsageValue").textContent = `${data.ram_avg} MB`;

            // ⏱️ UPTIME
            const uptimeEl = document.getElementById("uptimeValue");
            if (uptimeEl) {
                uptimeEl.textContent = `${data.uptime_avg}%`;
            }
        })
        .catch(err => console.error("❌ KPI error:", err));
}


// 🚀 Init All
window.addEventListener("DOMContentLoaded", () => {
    const siteSelector = document.getElementById("siteSelector");
    const sshSelector = document.getElementById("sshSelector");

    // Init HTTP
    if (siteSelector) {
        fetch("/api/sites/")
            .then(response => response.json())
            .then(sites => {
                if (sites.length === 0) return;
                sites.forEach(site => {
                    const option = document.createElement("option");
                    option.value = site.id;
                    option.textContent = site.name;
                    siteSelector.appendChild(option);
                });

                selectedSite = sites[0].id;
                siteSelector.value = selectedSite;
                resetChart();
                loadChartData(selectedSite);
            });

        siteSelector.addEventListener("change", (e) => {
            selectedSite = parseInt(e.target.value);
            resetChart();
            loadChartData(selectedSite);
        });
    }

    // Init SSH
    if (sshSelector) {
        const hosts = ["10.10.12.13"];
        hosts.forEach(host => {
            const option = document.createElement("option");
            option.value = host;
            option.textContent = host;
            sshSelector.appendChild(option);
        });

        const defaultHost = hosts[0];
        sshSelector.value = defaultHost;
        loadSSHChart(defaultHost);
        startSSHRefresh(defaultHost);

        sshSelector.addEventListener("change", (e) => {
            const host = e.target.value;
            loadSSHChart(host);
            startSSHRefresh(host);
        });
    }

    // ⏱️ Zakresy czasu
    document.querySelectorAll(".chart-range-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            document.querySelectorAll(".chart-range-btn").forEach(b => b.classList.remove("active"));
            this.classList.add("active");

            currentTimeRange = this.dataset.range;

            if (selectedSite) {
                resetChart();
                loadChartData(selectedSite);
            }

            const sshHost = sshSelector?.value;
            if (sshHost) {
                loadSSHChart(sshHost);
                startSSHRefresh(sshHost);
            }
        });
    });

    // 🧠 KPI start
    updateKPI();
    setInterval(updateKPI, 15000);
});
