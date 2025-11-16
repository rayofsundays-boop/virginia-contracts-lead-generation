import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// API functions
export const rfpAPI = {
  getAll: (params) => api.get('/rfps/', { params }),
  getById: (id) => api.get(`/rfps/${id}/`),
  getMyBookmarks: () => api.get('/rfps/my_bookmarks/'),
  bookmark: (id, data) => api.post(`/rfps/${id}/bookmark/`, data),
  unbookmark: (id) => api.post(`/rfps/${id}/unbookmark/`),
  getStatistics: () => api.get('/rfps/statistics/'),
};

export const statesAPI = {
  getAll: () => api.get('/states/'),
  getById: (id) => api.get(`/states/${id}/`),
  getCities: (id) => api.get(`/states/${id}/cities/`),
};

export const citiesAPI = {
  getAll: (params) => api.get('/states/cities/', { params }),
  search: (params) => api.get('/cities/', { params }),
};

export const userAPI = {
  getMe: () => api.get('/auth/users/me/'),
  updateProfile: (data) => api.patch('/auth/users/update_profile/', data),
  getSettings: () => api.get('/auth/users/settings/'),
  updateSettings: (data) => api.patch('/auth/users/settings/', data),
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/token/', data),
};

export const notificationsAPI = {
  getAll: () => api.get('/notifications/'),
  markAsRead: (id) => api.post(`/notifications/${id}/mark_as_read/`),
};

export default api;
