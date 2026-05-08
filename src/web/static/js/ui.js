// ui.js - toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerText = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }
  
  // notification dropdown
  async function fetchNotifications() {
    const res = await fetch('/api/notifications');
    const data = await res.json();
    const badge = document.getElementById('notif-badge');
    const unread = data.filter(n => !n.read).length;
    badge.innerText = unread > 0 ? unread : '';
    // remplir dropdown
  }