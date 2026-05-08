// notifications.js - Gestion des notifications UI

import apiRequest from './api.js';

let notifications = [];
let notificationBadge = null;
let notificationPanel = null;

export async function loadNotifications() {
  try {
    const data = await apiRequest('/notifications');
    notifications = data.notifications || [];
    updateBadge();
    renderNotifications();
  } catch (err) {
    console.error('Erreur chargement notifications', err);
  }
}

function updateBadge() {
  const unread = notifications.filter(n => !n.read).length;
  if (notificationBadge) {
    notificationBadge.textContent = unread > 0 ? unread : '';
    notificationBadge.style.display = unread > 0 ? 'flex' : 'none';
  }
}

function renderNotifications() {
  if (!notificationPanel) return;
  if (notifications.length === 0) {
    notificationPanel.innerHTML = '<div class="notification-empty">Aucune notification</div>';
    return;
  }
  notificationPanel.innerHTML = notifications.map(n => `
    <div class="notification-item ${!n.read ? 'unread' : ''}" data-id="${n.id}">
      <div class="notification-avatar">${getIcon(n.type)}</div>
      <div class="notification-content">
        <div class="notification-title">${escapeHtml(n.title)}</div>
        <div class="notification-message">${escapeHtml(n.message)}</div>
        <div class="notification-time">${formatDate(n.created_at)}</div>
      </div>
    </div>
  `).join('');
  // Attacher événements
  document.querySelectorAll('.notification-item').forEach(el => {
    el.addEventListener('click', () => markAsRead(el.dataset.id));
  });
}

async function markAsRead(id) {
  await apiRequest(`/notifications/${id}/read`, 'POST');
  notifications = notifications.map(n => n.id == id ? { ...n, read: true } : n);
  updateBadge();
  renderNotifications();
}

export function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container') || (() => {
    const div = document.createElement('div');
    div.id = 'toast-container';
    div.className = 'toast-container';
    document.body.appendChild(div);
    return div;
  })();
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span><button class="toast-close">✕</button>`;
  container.appendChild(toast);
  toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
  setTimeout(() => toast.remove(), 5000);
}

function getIcon(type) {
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  return icons[type] || '📢';
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;
  if (diff < 60000) return 'À l’instant';
  if (diff < 3600000) return `${Math.floor(diff / 60000)} min`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} h`;
  return date.toLocaleDateString();
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>]/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[m] || m));
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
  notificationBadge = document.getElementById('notif-badge');
  notificationPanel = document.getElementById('notifications-panel');
  if (notificationBadge) loadNotifications();
});
