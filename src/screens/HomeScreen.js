import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Alert,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Text,
  ActivityIndicator,
  Chip,
} from 'react-native-paper';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/apiService';

const HomeScreen = ({ navigation }) => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [updates, setUpdates] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [homeData, updatesData] = await Promise.all([
        apiService.getHome(),
        apiService.checkUpdates(),
      ]);
      
      // Парсим HTML для извлечения статистики
      const pagesMatch = homeData.match(/Страниц: (\d+)/);
      const pagesCount = pagesMatch ? parseInt(pagesMatch[1]) : 0;
      
      setStats({
        pagesCount,
        baseSite: 'https://sites.google.com/view/uzakbaevnurzhan',
      });
      
      setUpdates(updatesData);
    } catch (error) {
      console.error('Error loading home data:', error);
      Alert.alert('Ошибка', 'Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleUpdate = async () => {
    try {
      Alert.alert(
        'Обновление',
        'Применить обновления?',
        [
          { text: 'Отмена', style: 'cancel' },
          {
            text: 'Обновить',
            onPress: async () => {
              await apiService.doUpdate();
              Alert.alert('Успех', 'Обновления применены');
              loadData();
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось применить обновления');
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#60a5fa" />
        <Text style={styles.loadingText}>Загрузка...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.content}>
        {/* Приветствие */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.title}>Добро пожаловать!</Title>
            <Paragraph style={styles.subtitle}>
              Привет, {user?.username || 'Пользователь'}
            </Paragraph>
          </Card.Content>
        </Card>

        {/* Статистика */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Статистика</Title>
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{stats?.pagesCount || 0}</Text>
                <Text style={styles.statLabel}>Страниц</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>
                  {user?.role === 'admin' ? 'Админ' : 'Пользователь'}
                </Text>
                <Text style={styles.statLabel}>Роль</Text>
              </View>
            </View>
          </Card.Content>
        </Card>

        {/* Обновления */}
        {updates && (updates.changed || updates.new) && (
          <Card style={styles.card}>
            <Card.Content>
              <Title style={styles.cardTitle}>Доступны обновления</Title>
              <View style={styles.updatesInfo}>
                {updates.changed > 0 && (
                  <Chip style={styles.chip} textStyle={styles.chipText}>
                    Изменено: {updates.changed}
                  </Chip>
                )}
                {updates.new > 0 && (
                  <Chip style={styles.chip} textStyle={styles.chipText}>
                    Новых: {updates.new}
                  </Chip>
                )}
              </View>
              <Button
                mode="contained"
                onPress={handleUpdate}
                style={styles.updateButton}
              >
                Применить обновления
              </Button>
            </Card.Content>
          </Card>
        )}

        {/* Быстрые действия */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Быстрые действия</Title>
            <View style={styles.actionsGrid}>
              <Button
                mode="outlined"
                onPress={() => navigation.navigate('Pages')}
                style={styles.actionButton}
                icon="file-document"
              >
                Страницы
              </Button>
              <Button
                mode="outlined"
                onPress={() => navigation.navigate('Audit')}
                style={styles.actionButton}
                icon="history"
              >
                Журнал
              </Button>
              <Button
                mode="outlined"
                onPress={() => navigation.navigate('Chat')}
                style={styles.actionButton}
                icon="chat"
              >
                Чат
              </Button>
              {user?.role === 'admin' && (
                <Button
                  mode="outlined"
                  onPress={() => navigation.navigate('Admin')}
                  style={styles.actionButton}
                  icon="shield-account"
                >
                  Админ
                </Button>
              )}
            </View>
          </Card.Content>
        </Card>

        {/* Информация о сайте */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>О сайте</Title>
            <Paragraph style={styles.siteInfo}>
              Локальная копия сайта: {stats?.baseSite}
            </Paragraph>
            <Paragraph style={styles.description}>
              Это приложение позволяет просматривать локальную копию сайта,
              отслеживать изменения и управлять содержимым.
            </Paragraph>
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
  title: {
    color: '#e6eef8',
    fontSize: 24,
    fontWeight: 'bold',
  },
  subtitle: {
    color: '#98a0b3',
    fontSize: 16,
  },
  cardTitle: {
    color: '#e6eef8',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  statsRow: {
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
  updatesInfo: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  chip: {
    marginRight: 8,
    backgroundColor: '#1e3a8a',
  },
  chipText: {
    color: '#e6eef8',
  },
  updateButton: {
    backgroundColor: '#60a5fa',
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionButton: {
    width: '48%',
    marginBottom: 8,
    borderColor: '#60a5fa',
  },
  siteInfo: {
    color: '#60a5fa',
    fontWeight: 'bold',
  },
  description: {
    color: '#98a0b3',
    marginTop: 8,
  },
});

export default HomeScreen;