// 🛰️ Funkcja do pobrania danych z endpointu chart_data
function loadChartData(websiteId) {
    fetch(`/chart_data?website_id=${websiteId}&range=${currentTimeRange}`)
        .then(response => response.json())
        .then(data => {
            console.log("📈 Załadowano dane do wykresu:", data);

            if (window.responseChart) {
                window.responseChart.data.labels = data.labels;
                window.responseChart.data.datasets[0].data = data.response_times;

                // ⬇⬇⬇ DODAJ TO TUTAJ
                window.responseChart.statusCodes = data.status_codes;

                window.responseChart.update();
            }
        });
}



// 🔄 Reset wykresu do placeholdera
function resetChart() {
    if (window.responseChart) {
        window.responseChart.data.labels = ["Oczekiwanie..."];
        window.responseChart.data.datasets[0].data = [null];
        window.responseChart.update();
    }
}


let currentTimeRange = '5m';

// 🔧 Przycisk czasowy (5m, 1h, 24h)
document.querySelectorAll(".chart-range-btn").forEach(btn => {
    btn.addEventListener("click", function () {
        document.querySelectorAll(".chart-range-btn").forEach(b => b.classList.remove("active"));
        this.classList.add("active");

        currentTimeRange = this.dataset.range;
        if (selectedSite) {
            resetChart();                  // czyść stary wykres
            loadChartData(selectedSite);  // ładuj nowe dane
        }
    });
});



// 🔧 Obsługa dropdowna i ładowanie stron
window.addEventListener("DOMContentLoaded", () => {
    const selector = document.getElementById("siteSelector");
    if (!selector) {
        console.warn("⚠️ Brak elementu #siteSelector w DOM-ie");
        return;
    }

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

            resetChart(); // ⬅️ Placeholder zanim przyjdą dane
            loadChartData(selectedSite);
        });

    selector.addEventListener("change", (e) => {
        selectedSite = parseInt(e.target.value);
        console.log("🌐 Wybrana strona:", selectedSite);

        resetChart();               // 🔁 zresetuj wykres
        loadChartData(selectedSite); // 🔁 wczytaj dane
    });
});


// 🔌 Połączenie WebSocket
const ws = new WebSocket("ws://" + window.location.host + "/ws/metrics/");

// 🎯 Obsługa wiadomości z backendu
ws.onmessage = function (event) {
    const data = JSON.parse(event.data);
    console.log("📡 Realtime dane z WebSocket:", data);

    // Filtruj dane dla wybranej strony
    if (selectedSite && data.website_id !== selectedSite) return;

    // 🔁 Jeśli zakres to '5m' – tylko wtedy realtime
    if (currentTimeRange !== "5m") return;

    if (window.responseChart) {
        // ⛔️ Limitujemy do ostatnich 50 punktów
        if (window.responseChart.data.labels.length > 50) {
            window.responseChart.data.labels.shift();
            window.responseChart.data.datasets[0].data.shift();
        }

        window.responseChart.data.labels.push(data.timestamp);
        window.responseChart.data.datasets[0].data.push(data.response_time);
        window.responseChart.update();
    }
};
