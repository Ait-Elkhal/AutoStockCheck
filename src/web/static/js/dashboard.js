// dashboard.js - Chart.js initialisation et tableau d'activité

import apiRequest from './api.js';
import { showToast } from './notifications.js';

export async function initDashboard() {
  try {
    // Charger les données depuis l'API (exemple)
    const stats = await apiRequest('/dashboard/stats');
    updateStats(stats);
    initChart(stats.chartData);
    initActivityTable(stats.activities);
  } catch (err) {
    showToast('Erreur chargement dashboard', 'danger');
  }
}

function updateStats(stats) {
  document.getElementById('stat-stock-total').innerText = stats.stockTotal;
  document.getElementById('stat-entries').innerText = stats.entries;
  document.getElementById('stat-exits').innerText = stats.exits;
  document.getElementById('stat-alerts').innerText = stats.alerts;
}

function initChart(chartData) {
  const ctx = document.getElementById('stockTrendChart')?.getContext('2d');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.labels,
      datasets: [{
        label: 'Stock',
        data: chartData.values,
        borderColor: 'var(--primary)',
        backgroundColor: 'var(--primary-light)',
        tension: 0.3,
        fill: true,
      }]
    },
    options: { responsive: true, maintainAspectRatio: true }
  });
}

function initActivityTable(activities) {
  const tbody = document.getElementById('activity-table-body');
  if (!tbody) return;
  tbody.innerHTML = activities.map(a => `
    <tr>
      <td>${a.product}</td>
      <td>${a.action}</td>
      <td>${a.quantity}</td>
      <td>${a.date}</td>
    </tr>
  `).join('');
}