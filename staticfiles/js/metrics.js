let currentTimeRange = '5m';
let selectedSite = null;

// 🚨 Error Logging
window.addEventListener("error", function (e) {
    console.error("🚨 JavaScript Error:", e.message, "at", e.filename + ":" + e.lineno);
});

// 📉 Reset HTTP chart
function resetChart() {
    if (window.responseChart) {
        window.responseChart.data.labels = ["Oczekiwanie..."];
        window.responseChart.data.datasets[0].data = [null];
        window.responseChart.update();
    }
}

// 🔁 Load chart data (static)
function loadChartData(websiteId) {
    fetch(`/api/chart-data/?website_id=${websiteId}&range=${currentTimeRange}`)
        .then(response => response.json())
        .then(data => {
            if (window.responseChart) {
                window.responseChart.data.labels = data.labels; // już są HH:MM:SS
                window.responseChart.data.datasets[0].data = data.response_times;
                window.responseChart.statusCodes = data.status_codes;
                window.responseChart.update();
            }
        });
}

// 🔌 WebSocket (dynamic 5m range only)
const ws = new WebSocket("ws://" + window.location.host + "/ws/metrics/");
ws.onmessage = function (event) {
    const data = JSON.parse(event.data);
    if (currentTimeRange !== "5m") return;
    if (selectedSite && parseInt(data.website_id) !== parseInt(selectedSite)) return;

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

// 🧠 KPI Update
function updateKPI() {
    fetch("/api/kpi/")
        .then(res => res.json())
        .then(data => {
            document.getElementById("activeServicesCount").textContent = data.active_services;
            document.getElementById("cpuUsageValue").textContent = `${data.cpu_avg}%`;
            document.getElementById("memoryUsageValue").textContent = `${data.ram_avg} MB`;
            const uptimeEl = document.getElementById("uptimeValue");
            if (uptimeEl) uptimeEl.textContent = `${data.uptime_avg}%`;
        })
        .catch(err => console.error("❌ KPI error:", err));
}

// 🚀 On Ready
window.addEventListener("DOMContentLoaded", () => {
    const siteSelector = document.getElementById("siteSelector");

    if (siteSelector) {
        fetch("/api/sites/")
            .then(res => res.json())
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

        siteSelector.addEventListener("change", e => {
            selectedSite = parseInt(e.target.value);
            resetChart();
            loadChartData(selectedSite);
        });
    }

    document.querySelectorAll(".chart-range-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            document.querySelectorAll(".chart-range-btn").forEach(b => b.classList.remove("active"));
            this.classList.add("active");
            currentTimeRange = this.dataset.range;
            if (selectedSite) {
                resetChart();
                loadChartData(selectedSite);
            }
        });
    });

    updateKPI();
    setInterval(updateKPI, 15000);
});
