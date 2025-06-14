import {
    initializeCharts,
    updateSSHChart
} from './charts.js';

import { renderServices } from './services.js';
import { renderAlerts } from './alerts.js';
import { updateCpu, updateRam, updateDisk } from './metrics.js';

document.addEventListener('DOMContentLoaded', function () {
    const sshSelector = document.getElementById('sshSelector');
    
    window.selectedHost = sshSelector.value;

    sshSelector.addEventListener('change', function () {
        window.selectedHost = this.value;
    });

    const sshSocket = new WebSocket(`ws://${window.location.host}/ws/ssh-metrics/`);

    sshSocket.onopen = function () {
        console.log("✅ WebSocket SSH connected");
    };

    sshSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        if (data.host === window.selectedHost) {
            console.log("🎯 SSH dane:", data);
            updateSSHChart(data);
        }
    };

    sshSocket.onerror = function (e) {
        console.error("❌ SSH WebSocket error:", e);
    };

    sshSocket.onclose = function () {
        console.warn("⚠️ SSH WebSocket closed");
    };

    initializeCharts();
});
