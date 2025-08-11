import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Text,
  ActivityIndicator,
  TextInput,
  List,
  Divider,
  Chip,
} from 'react-native-paper';
import { apiService } from '../services/apiService';

const AdminScreen = () => {
  const [adminData, setAdminData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [creatingUser, setCreatingUser] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    role: 'user',
  });

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getAdmin();
      
      // Парсим HTML для извлечения данных админ панели
      const pagesMatch = response.match(/Страниц: (\d+)/);
      const versionsMatch = response.match(/Версий: (\d+)/);
      const sizeMatch = response.match(/Размер: ([\d.]+) МБ/);
      
      setAdminData({
        pagesCount: pagesMatch ? parseInt(pagesMatch[1]) : 0,
        versionsCount: versionsMatch ? parseInt(versionsMatch[1]) : 0,
        siteSizeMB: sizeMatch ? parseFloat(sizeMatch[1]) : 0,
        users: [], // Пока пустой массив пользователей
      });
    } catch (error) {
      console.error('Error loading admin data:', error);
      Alert.alert('Ошибка', 'Не удалось загрузить данные админ панели');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    if (!newUser.username.trim() || !newUser.password.trim()) {
      Alert.alert('Ошибка', 'Заполните все поля');
      return;
    }

    try {
      setCreatingUser(true);
      await apiService.createUser(newUser.username, newUser.password, newUser.role);
      Alert.alert('Успех', 'Пользователь создан');
      setNewUser({ username: '', password: '', role: 'user' });
    } catch (error) {
      console.error('Error creating user:', error);
      Alert.alert('Ошибка', 'Не удалось создать пользователя');
    } finally {
      setCreatingUser(false);
    }
  };

  const handleCleanup = async () => {
    try {
      Alert.alert(
        'Очистка',
        'Выполнить очистку старых версий?',
        [
          { text: 'Отмена', style: 'cancel' },
          {
            text: 'Очистить',
            onPress: async () => {
              await apiService.cleanup();
              Alert.alert('Успех', 'Очистка выполнена');
              loadAdminData();
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось выполнить очистку');
    }
  };

  const handleForceCrawl = async () => {
    try {
      Alert.alert(
        'Принудительное сканирование',
        'Запустить принудительное сканирование сайта?',
        [
          { text: 'Отмена', style: 'cancel' },
          {
            text: 'Сканировать',
            onPress: async () => {
              await apiService.forceCrawl();
              Alert.alert('Успех', 'Сканирование запущено');
              loadAdminData();
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось запустить сканирование');
    }
  };

  const handleDownloadBackup = async () => {
    try {
      await apiService.downloadBackup();
      Alert.alert('Успех', 'Резервная копия скачана');
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось скачать резервную копию');
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#60a5fa" />
        <Text style={styles.loadingText}>Загрузка админ панели...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Статистика */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Статистика системы</Title>
            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{adminData?.pagesCount || 0}</Text>
                <Text style={styles.statLabel}>Страниц</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{adminData?.versionsCount || 0}</Text>
                <Text style={styles.statLabel}>Версий</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{adminData?.siteSizeMB || 0}</Text>
                <Text style={styles.statLabel}>МБ</Text>
              </View>
            </View>
          </Card.Content>
        </Card>

        {/* Создание пользователя */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Создать пользователя</Title>
            <TextInput
              label="Имя пользователя"
              value={newUser.username}
              onChangeText={(text) => setNewUser({ ...newUser, username: text })}
              mode="outlined"
              style={styles.input}
            />
            <TextInput
              label="Пароль"
              value={newUser.password}
              onChangeText={(text) => setNewUser({ ...newUser, password: text })}
              mode="outlined"
              secureTextEntry
              style={styles.input}
            />
            <View style={styles.roleContainer}>
              <Text style={styles.roleLabel}>Роль:</Text>
              <View style={styles.roleButtons}>
                <Button
                  mode={newUser.role === 'user' ? 'contained' : 'outlined'}
                  onPress={() => setNewUser({ ...newUser, role: 'user' })}
                  style={styles.roleButton}
                >
                  Пользователь
                </Button>
                <Button
                  mode={newUser.role === 'admin' ? 'contained' : 'outlined'}
                  onPress={() => setNewUser({ ...newUser, role: 'admin' })}
                  style={styles.roleButton}
                >
                  Администратор
                </Button>
              </View>
            </View>
            <Button
              mode="contained"
              onPress={handleCreateUser}
              loading={creatingUser}
              disabled={creatingUser}
              style={styles.createButton}
            >
              Создать пользователя
            </Button>
          </Card.Content>
        </Card>

        {/* Управление системой */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Управление системой</Title>
            
            <List.Item
              title="Очистка старых версий"
              description="Удалить старые версии страниц для экономии места"
              left={(props) => <List.Icon {...props} icon="delete-sweep" />}
              right={(props) => (
                <Button
                  mode="outlined"
                  onPress={handleCleanup}
                  style={styles.actionButton}
                >
                  Очистить
                </Button>
              )}
              style={styles.listItem}
            />
            
            <Divider />
            
            <List.Item
              title="Принудительное сканирование"
              description="Запустить сканирование сайта для поиска обновлений"
              left={(props) => <List.Icon {...props} icon="refresh" />}
              right={(props) => (
                <Button
                  mode="outlined"
                  onPress={handleForceCrawl}
                  style={styles.actionButton}
                >
                  Сканировать
                </Button>
              )}
              style={styles.listItem}
            />
            
            <Divider />
            
            <List.Item
              title="Скачать резервную копию"
              description="Создать и скачать резервную копию всех данных"
              left={(props) => <List.Icon {...props} icon="download" />}
              right={(props) => (
                <Button
                  mode="outlined"
                  onPress={handleDownloadBackup}
                  style={styles.actionButton}
                >
                  Скачать
                </Button>
              )}
              style={styles.listItem}
            />
          </Card.Content>
        </Card>

        {/* Информация о системе */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Информация о системе</Title>
            <Paragraph style={styles.systemInfo}>
              Uzakbaevnurzhan Mirror - система для создания и управления локальными копиями веб-сайтов.
            </Paragraph>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Версия:</Text>
              <Text style={styles.infoValue}>1.0.0</Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Статус:</Text>
              <Chip style={styles.statusChip} textStyle={styles.statusText}>
                Активен
              </Chip>
            </View>
          </Card.Content>
        </Card>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b1220',
  },
  content: {
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0b1220',
  },
  loadingText: {
    color: '#e6eef8',
    marginTop: 16,
  },
  card: {
    backgroundColor: '#0f1724',
    marginBottom: 16,
    borderRadius: 12,
    elevation: 4,
  },
  cardTitle: {
    color: '#e6eef8',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    color: '#60a5fa',
    fontSize: 24,
    fontWeight: 'bold',
  },
  statLabel: {
    color: '#98a0b3',
    fontSize: 14,
    marginTop: 4,
  },
  input: {
    marginBottom: 16,
    backgroundColor: '#1a2332',
  },
  roleContainer: {
    marginBottom: 16,
  },
  roleLabel: {
    color: '#e6eef8',
    fontSize: 16,
    marginBottom: 8,
  },
  roleButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  roleButton: {
    flex: 1,
    marginHorizontal: 4,
    borderColor: '#60a5fa',
  },
  createButton: {
    backgroundColor: '#60a5fa',
  },
  listItem: {
    backgroundColor: 'transparent',
  },
  actionButton: {
    borderColor: '#60a5fa',
  },
  systemInfo: {
    color: '#98a0b3',
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  infoLabel: {
    color: '#98a0b3',
    fontSize: 16,
  },
  infoValue: {
    color: '#e6eef8',
    fontSize: 16,
    fontWeight: 'bold',
  },
  statusChip: {
    backgroundColor: '#10b981',
  },
  statusText: {
    color: '#ffffff',
  },
});

export default AdminScreen;