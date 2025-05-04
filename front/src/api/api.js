import axios from 'axios';
import { useErrorModalStore } from '@/stores/errorModal';

const api = axios.create({
  baseURL: 'https://egoriktut.ru/api_ks_app/v1/',
  headers: {
    'Content-Type': 'application/json',
    // "token": localStorage.getItem('token'),
  },
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

const handleError = (error) => {
  console.error('Error:', error);

  const errorModal = useErrorModalStore();
  let errorMessage = 'Произошла ошибка';

  if (error.response) {
    // Ошибка от сервера с кодом статуса
    errorMessage = error.response.data.detail || `Ошибка сервера: ${error.response.status}`;
  } else if (error.request) {
    // Запрос был сделан, но ответ не получен
    errorMessage = 'Не удалось получить ответ от сервера';
  } else {
    // Ошибка при настройке запроса
    errorMessage = error.message || 'Ошибка при выполнении запроса';
  }

  errorModal.openModal(errorMessage);
  console.log(errorMessage);
  throw error;
};

export const getData = async (endpoint) => {
  try {
    const response = await api.get(endpoint);
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

export const postData = async (endpoint, data) => {
  try {
    const response = await api.post(endpoint, data);
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

export const putData = async (endpoint, data) => {
  try {
    const response = await api.put(endpoint, data);
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};

export const deleteData = async (endpoint) => {
  try {
    const response = await api.delete(endpoint);
    return response.data;
  } catch (error) {
    return handleError(error);
  }
};