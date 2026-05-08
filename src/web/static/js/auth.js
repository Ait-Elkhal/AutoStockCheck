// auth.js - Gestion de l’authentification

import apiRequest from './api.js';

export async function login(username, password) {
  const data = await apiRequest('/login', 'POST', { username, password });
  if (data.status === 'success') {
    localStorage.setItem('token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    window.location.href = data.redirect_url || '/dashboard';
  }
  return data;
}

export function logout() {
  fetch('/api/logout', { method: 'POST' }).finally(() => {
    localStorage.clear();
    window.location.href = '/login';
  });
}

export function isAuthenticated() {
  return !!localStorage.getItem('token');
}

export function getUser() {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
}
