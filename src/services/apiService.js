import AsyncStorage from '@react-native-async-storage/async-storage';

// Конфигурация API
const API_BASE_URL = 'http://10.0.2.2:5000'; // Для Android эмулятора
// const API_BASE_URL = 'http://localhost:5000'; // Для iOS симулятора
// const API_BASE_URL = 'http://your-server-ip:5000'; // Для реального устройства

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async getAuthHeaders() {
    const token = await AsyncStorage.getItem('authToken');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async request(endpoint, options = {}) {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        headers,
        ...options,
      });

      if (response.status === 401) {
        // Неавторизованный доступ
        await AsyncStorage.removeItem('authToken');
        await AsyncStorage.removeItem('userData');
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text();
      }
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }

  // Аутентификация
  async login(username, password) {
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch(`${this.baseURL}/login`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const cookies = response.headers.get('set-cookie');
        if (cookies) {
          await AsyncStorage.setItem('sessionCookie', cookies);
        }
        
        return {
          success: true,
          token: 'session-token', // Flask использует сессии
          user: { username, role: 'user' }
        };
      } else {
        return {
          success: false,
          error: 'Неверные учетные данные'
        };
      }
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: 'Ошибка подключения к серверу'
      };
    }
  }

  // Получение главной страницы
  async getHome() {
    return this.request('/');
  }

  // Получение списка страниц
  async getPages() {
    return this.request('/pages');
  }

  // Просмотр страницы
  async getPage(url) {
    return this.request(`/view?url=${encodeURIComponent(url)}`);
  }

  // Получение сырого контента страницы
  async getRawPage(url) {
    return this.request(`/raw?url=${encodeURIComponent(url)}`);
  }

  // Скачивание страницы
  async downloadPage(url) {
    return this.request(`/download_page?url=${encodeURIComponent(url)}`);
  }

  // Проверка обновлений
  async checkUpdates() {
    return this.request('/check_updates');
  }

  // Применение обновлений
  async doUpdate() {
    return this.request('/do_update', {
      method: 'POST',
    });
  }

  // Скачивание резервной копии
  async downloadBackup() {
    return this.request('/download_backup');
  }

  // Получение журнала аудита
  async getAudit() {
    return this.request('/audit');
  }

  // Получение сообщений чата
  async getChat() {
    return this.request('/chat');
  }

  // Отправка сообщения в чат
  async sendChatMessage(message) {
    const formData = new FormData();
    formData.append('message', message);

    return fetch(`${this.baseURL}/chat_send`, {
      method: 'POST',
      body: formData,
    });
  }

  // Админ панель
  async getAdmin() {
    return this.request('/admin');
  }

  // Создание пользователя (админ)
  async createUser(username, password, role = 'user') {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('role', role);

    return fetch(`${this.baseURL}/admin/create_user`, {
      method: 'POST',
      body: formData,
    });
  }

  // Очистка (админ)
  async cleanup() {
    return this.request('/admin/cleanup', {
      method: 'POST',
    });
  }

  // Принудительное сканирование (админ)
  async forceCrawl() {
    return this.request('/admin/force_crawl', {
      method: 'POST',
    });
  }

  // Смена пароля
  async changePassword(oldPassword, newPassword) {
    const formData = new FormData();
    formData.append('old', oldPassword);
    formData.append('new', newPassword);

    return fetch(`${this.baseURL}/change_password`, {
      method: 'POST',
      body: formData,
    });
  }

  // Поиск
  async search(query) {
    return this.request(`/search?q=${encodeURIComponent(query)}`);
  }
}

export const apiService = new ApiService();