const ctx = document.getElementById('responseTimeChart').getContext('2d');

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
