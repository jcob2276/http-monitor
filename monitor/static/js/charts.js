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
        maintainAspectRatio: false, // ← TO TU!
        scales: {
            y: { beginAtZero: true }
        }
    }
});
