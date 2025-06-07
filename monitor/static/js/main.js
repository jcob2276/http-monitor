import { initializeCharts, updateChartTimeRange, updateCharts, updateResponseTimeChart } from './charts.js';
import { renderServices } from './services.js';
import { renderAlerts } from './alerts.js';
import { updateCpu, updateRam, updateDisk } from './metrics.js';
import { setupEventListeners, updateCurrentTime } from './dom.js';

document.addEventListener('DOMContentLoaded', function () {
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);

    renderServices();
    renderAlerts();
    initializeCharts();
    setupEventListeners();

    // Podłącz WebSocket
    const socket = new WebSocket("ws://" + window.location.host + "/ws/metrics/");
    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        updateCpu(data.cpu);
        updateRam(data.ram);
        updateDisk(data.disk);
    };
});
