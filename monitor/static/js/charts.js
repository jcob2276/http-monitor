// 📊 Wykres HTTP - Czas odpowiedzi
function createResponseChart() {
    const ctx = document.getElementById('responseTimeChart')?.getContext('2d');
    if (!ctx) return;

    window.responseChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Czas odpowiedzi (ms)',
                data: [],
                borderColor: 'rgba(75,192,192,1)',
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'ms'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Czas'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const statusCodes = window.responseChart.statusCodes || [];
                            const code = statusCodes[context.dataIndex] || 'brak';
                            return `Czas: ${context.raw} ms (HTTP ${code})`;
                        }
                    }
                }
            }
        }
    });
}

// 📊 Wykres SSH - CPU i RAM
function createSSHChart() {
    const sshCtx = document.getElementById('resourceChart')?.getContext('2d');
    if (!sshCtx) return;

    window.sshChart = new Chart(sshCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'CPU (%)',
                    data: [],
                    borderColor: 'orange',
                    borderWidth: 2,
                    fill: false
                },
                {
                    label: 'RAM (%)',
                    data: [],
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
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '%'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Czas'
                    }
                }
            }
        }
    });
}

// 🔁 Aktualizacja SSH Chart
function updateSSHChart(data) {
    if (!window.sshChart) {
        console.warn("⚠️ sshChart not found");
        return;
    }

    console.log("🟢 updateSSHChart CALLED with:", data);

    if (!data.timestamp || data.cpu == null || data.ram_used == null || data.ram_total == null) {
        console.warn("❌ Niekompletne dane:", data);
        return;
    }

    const labels = window.sshChart.data.labels;
    const cpuData = window.sshChart.data.datasets[0].data;
    const ramData = window.sshChart.data.datasets[1].data;

    if (labels.length > 20) {
        labels.shift();
        cpuData.shift();
        ramData.shift();
    }

    labels.push(data.timestamp);
    cpuData.push(data.cpu);
    ramData.push((data.ram_used / data.ram_total * 100).toFixed(2));

    window.sshChart.update();
}



// 🚀 Główna funkcja inicjalizacji
function initializeCharts() {
    createResponseChart();
    createSSHChart();
    console.log("✅ Wykresy zainicjalizowane");
}

export { initializeCharts, updateSSHChart };
