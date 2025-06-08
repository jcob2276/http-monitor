let currentTimeRange = '5m';
let selectedSite = null;

window.addEventListener("error", function (e) {
    console.error("🚨 JavaScript Error:", e.message, "at", e.filename + ":" + e.lineno);
});

// 🛰️ Ładowanie danych HTTP dla wykresu odpowiedzi
function loadChartData(websiteId) {
    fetch(`/chart_data?website_id=${websiteId}&range=${currentTimeRange}`)
        .then(response => response.json())
        .then(data => {
            console.log("📈 Załadowano dane do wykresu:", data);
            if (window.responseChart) {
                window.responseChart.data.labels = data.labels;
                window.responseChart.data.datasets[0].data = data.response_times;
                window.responseChart.statusCodes = data.status_codes;
                window.responseChart.update();
            }
        });
}

// 🧠 Ładowanie danych zdalnych (CPU, RAM) przez SSH
function loadSSHChart(host) {
    fetch(`/api/ssh_metrics/?host=${host}`)
        .then(response => response.json())
        .then(data => {
            const canvas = document.getElementById('resourceChart');
            if (!canvas) {
                console.warn("⚠️ Nie znaleziono <canvas id='resourceChart'> w DOM – wykres SSH nie zostanie załadowany.");
                return;
            }
            const ctx = canvas.getContext('2d');
            console.log("🎨 Rysuję wykres SSH na #resourceChart", data);

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

// 🔄 Resetuje wykres odpowiedzi
function resetChart() {
    if (window.responseChart) {
        window.responseChart.data.labels = ["Oczekiwanie..."];
        window.responseChart.data.datasets[0].data = [null];
        window.responseChart.update();
    }
}

// 🔌 WebSocket do realtime metryk
const ws = new WebSocket("ws://" + window.location.host + "/ws/metrics/");
ws.onmessage = function (event) {
    const data = JSON.parse(event.data);
    console.log("📡 Realtime dane z WebSocket:", data);

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

// 📦 Główna inicjalizacja po załadowaniu DOM
window.addEventListener("DOMContentLoaded", () => {
    // Obsługa selektora HTTP
    const selector = document.getElementById("siteSelector");
    if (!selector) {
        console.warn("⚠️ Brak elementu #siteSelector w DOM-ie");
    } else {
        fetch("/api/sites/")
            .then(response => response.json())
            .then(sites => {
                if (sites.length === 0) {
                    console.warn("❌ Brak stron do wyboru");
                    return;
                }

                sites.forEach(site => {
                    const option = document.createElement("option");
                    option.value = site.id;
                    option.textContent = site.name;
                    selector.appendChild(option);
                });

                selectedSite = sites[0].id;
                selector.value = selectedSite;
                resetChart();
                loadChartData(selectedSite);
            });

        selector.addEventListener("change", (e) => {
            selectedSite = parseInt(e.target.value);
            console.log("🌐 Wybrana strona:", selectedSite);
            resetChart();
            loadChartData(selectedSite);
        });
    }

    // Obsługa selektora SSH
    const sshSelector = document.getElementById("sshSelector");
    if (!sshSelector) {
        console.warn("⚠️ Nie znaleziono #sshSelector w DOM");
    } else {
        const hosts = ["10.10.12.13"];
        hosts.forEach(host => {
            const option = document.createElement("option");
            option.value = host;
            option.textContent = host;
            sshSelector.appendChild(option);
        });

        const defaultHost = hosts[0];
        sshSelector.value = defaultHost;
        console.log("🔌 Domyślnie ładujemy wykres SSH dla:", defaultHost);
        loadSSHChart(defaultHost);

        sshSelector.addEventListener("change", (e) => {
            const selectedHost = e.target.value;
            console.log("🔄 Zmieniono host SSH na:", selectedHost);
            loadSSHChart(selectedHost);
        });
    }
});

// 🕒 Obsługa przycisków zakresu czasu
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