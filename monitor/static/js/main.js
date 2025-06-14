document.addEventListener('DOMContentLoaded', function () {
    // 📡 Pobieranie hostów SSH z API
    fetch('/api/ssh-hosts/')
        .then(response => response.json())
        .then(data => {
            const sshSelector = document.getElementById('sshSelector');
            if (!sshSelector) {
                console.error("❌ Nie znaleziono dropdowna SSH (#sshSelector)");
                return;
            }

            sshSelector.innerHTML = ''; // Czyść dropdown

            data.forEach(host => {
                const option = document.createElement('option');
                option.value = host.hostname;
                option.textContent = host.hostname;
                sshSelector.appendChild(option);
            });

            // Ustaw domyślnie pierwszy host
            if (data.length > 0) {
                window.selectedHost = data[0].hostname;
                sshSelector.value = data[0].hostname;
                console.log("🎯 Domyślny host SSH:", window.selectedHost);
            }

            // 🔁 Zmiana hosta w dropdownie
            sshSelector.addEventListener('change', function () {
                window.selectedHost = this.value;
                console.log("🔄 Zmieniono host SSH na:", window.selectedHost);
            });

            // 🔌 WebSocket do SSH
            const sshSocketUrl = `ws://${window.location.host}/ws/ssh-metrics/`;
            console.log("🔌 Próba połączenia WebSocket SSH →", sshSocketUrl);

            const sshSocket = new WebSocket(sshSocketUrl);

            sshSocket.onopen = function () {
                console.log("✅ WebSocket SSH connected");
            };

            sshSocket.onmessage = function (e) {
                try {
                    const data = JSON.parse(e.data);
                    if (data.host === window.selectedHost) {
                        console.log("📡 Odebrano dane SSH:", data);
                        if (window.updateSSHChart) {
                            window.updateSSHChart(data);
                        } else {
                            console.warn("⚠️ Brak funkcji updateSSHChart!");
                        }
                    }
                } catch (err) {
                    console.error("❌ Błąd przetwarzania danych z WebSocket SSH:", err);
                }
            };

            sshSocket.onerror = function (e) {
                console.error("❌ WebSocket SSH error:", e);
            };

            sshSocket.onclose = function () {
                console.warn("⚠️ WebSocket SSH closed");
            };

            // 📊 Inicjalizacja wykresów i sekcji
            if (window.initializeCharts) window.initializeCharts();
            if (window.renderServices) window.renderServices();
            if (window.renderAlerts) window.renderAlerts();
            if (window.updateCpu) window.updateCpu();
            if (window.updateRam) window.updateRam();
            if (window.updateDisk) window.updateDisk();
        })
        .catch(error => {
            console.error("❌ Błąd pobierania hostów SSH:", error);
        });
});


document.querySelectorAll(".chart-range-btn").forEach(btn => {
    btn.addEventListener("click", function () {
        document.querySelectorAll(".chart-range-btn").forEach(b => b.classList.remove("active"));
        this.classList.add("active");
        const range = this.dataset.range;
        window.currentTimeRange = range;

        if (range === '5m') {
    if (window.selectedHost) {
        loadSSHChartData(window.selectedHost, '5m');  // 👈 dodaj fetch także dla 5m!
    }
    return;
}


        if (window.selectedHost) {
            loadSSHChartData(window.selectedHost, range);
        }
    });
});
