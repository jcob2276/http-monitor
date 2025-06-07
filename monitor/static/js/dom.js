// dom.js
export function setupEventListeners() {}
export function updateCurrentTime() {
    const now = new Date().toLocaleString();
    const el = document.getElementById('current-time');
    if (el) el.textContent = now;
}
export function closeModal() {}
