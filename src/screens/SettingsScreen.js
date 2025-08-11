import React, { useState } from 'react';
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
  List,
  Divider,
  Switch,
  TextInput,
} from 'react-native-paper';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/apiService';

const SettingsScreen = () => {
  const { user, logout } = useAuth();
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [notifications, setNotifications] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const handleChangePassword = async () => {
    if (!passwordData.oldPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
      Alert.alert('Ошибка', 'Заполните все поля');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      Alert.alert('Ошибка', 'Новые пароли не совпадают');
      return;
    }

    if (passwordData.newPassword.length < 6) {
      Alert.alert('Ошибка', 'Новый пароль должен содержать минимум 6 символов');
      return;
    }

    try {
      setChangingPassword(true);
      await apiService.changePassword(passwordData.oldPassword, passwordData.newPassword);
      Alert.alert('Успех', 'Пароль изменен');
      setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error) {
      console.error('Error changing password:', error);
      Alert.alert('Ошибка', 'Не удалось изменить пароль');
    } finally {
      setChangingPassword(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Выход',
      'Вы уверены, что хотите выйти?',
      [
        { text: 'Отмена', style: 'cancel' },
        {
          text: 'Выйти',
          style: 'destructive',
          onPress: logout,
        },
      ]
    );
  };

  const handleClearCache = () => {
    Alert.alert(
      'Очистка кэша',
      'Очистить кэш приложения?',
      [
        { text: 'Отмена', style: 'cancel' },
        {
          text: 'Очистить',
          onPress: () => {
            // Здесь можно добавить логику очистки кэша
            Alert.alert('Успех', 'Кэш очищен');
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Профиль пользователя */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Профиль</Title>
            <View style={styles.profileInfo}>
              <Text style={styles.profileLabel}>Пользователь:</Text>
              <Text style={styles.profileValue}>{user?.username}</Text>
            </View>
            <View style={styles.profileInfo}>
              <Text style={styles.profileLabel}>Роль:</Text>
              <Text style={styles.profileValue}>
                {user?.role === 'admin' ? 'Администратор' : 'Пользователь'}
              </Text>
            </View>
          </Card.Content>
        </Card>

        {/* Смена пароля */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Смена пароля</Title>
            <TextInput
              label="Текущий пароль"
              value={passwordData.oldPassword}
              onChangeText={(text) => setPasswordData({ ...passwordData, oldPassword: text })}
              mode="outlined"
              secureTextEntry
              style={styles.input}
            />
            <TextInput
              label="Новый пароль"
              value={passwordData.newPassword}
              onChangeText={(text) => setPasswordData({ ...passwordData, newPassword: text })}
              mode="outlined"
              secureTextEntry
              style={styles.input}
            />
            <TextInput
              label="Подтвердите новый пароль"
              value={passwordData.confirmPassword}
              onChangeText={(text) => setPasswordData({ ...passwordData, confirmPassword: text })}
              mode="outlined"
              secureTextEntry
              style={styles.input}
            />
            <Button
              mode="contained"
              onPress={handleChangePassword}
              loading={changingPassword}
              disabled={changingPassword}
              style={styles.changePasswordButton}
            >
              Изменить пароль
            </Button>
          </Card.Content>
        </Card>

        {/* Настройки приложения */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Настройки приложения</Title>
            
            <List.Item
              title="Уведомления"
              description="Получать уведомления о обновлениях"
              left={(props) => <List.Icon {...props} icon="bell" />}
              right={(props) => (
                <Switch
                  value={notifications}
                  onValueChange={setNotifications}
                  color="#60a5fa"
                />
              )}
              style={styles.listItem}
            />
            
            <Divider />
            
            <List.Item
              title="Автообновление"
              description="Автоматически обновлять данные"
              left={(props) => <List.Icon {...props} icon="refresh" />}
              right={(props) => (
                <Switch
                  value={autoRefresh}
                  onValueChange={setAutoRefresh}
                  color="#60a5fa"
                />
              )}
              style={styles.listItem}
            />
          </Card.Content>
        </Card>

        {/* Управление данными */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Управление данными</Title>
            
            <List.Item
              title="Очистить кэш"
              description="Удалить временные файлы приложения"
              left={(props) => <List.Icon {...props} icon="delete-sweep" />}
              onPress={handleClearCache}
              style={styles.listItem}
            />
            
            <Divider />
            
            <List.Item
              title="Экспорт данных"
              description="Скачать все данные приложения"
              left={(props) => <List.Icon {...props} icon="download" />}
              onPress={() => Alert.alert('Информация', 'Функция в разработке')}
              style={styles.listItem}
            />
          </Card.Content>
        </Card>

        {/* Информация о приложении */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>О приложении</Title>
            <Paragraph style={styles.appInfo}>
              Uzakbaevnurzhan Mirror - мобильное приложение для управления локальными копиями веб-сайтов.
            </Paragraph>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Версия:</Text>
              <Text style={styles.infoValue}>1.0.0</Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Разработчик:</Text>
              <Text style={styles.infoValue}>Uzakbaevnurzhan</Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Лицензия:</Text>
              <Text style={styles.infoValue}>MIT</Text>
            </View>
          </Card.Content>
        </Card>

        {/* Выход */}
        <Card style={styles.card}>
          <Card.Content>
            <Button
              mode="outlined"
              onPress={handleLogout}
              style={styles.logoutButton}
              textColor="#ef4444"
              buttonColor="transparent"
            >
              Выйти из аккаунта
            </Button>
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
  profileInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  profileLabel: {
    color: '#98a0b3',
    fontSize: 16,
  },
  profileValue: {
    color: '#e6eef8',
    fontSize: 16,
    fontWeight: 'bold',
  },
  input: {
    marginBottom: 16,
    backgroundColor: '#1a2332',
  },
  changePasswordButton: {
    backgroundColor: '#60a5fa',
  },
  listItem: {
    backgroundColor: 'transparent',
  },
  appInfo: {
    color: '#98a0b3',
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
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
  logoutButton: {
    borderColor: '#ef4444',
  },
});

export default SettingsScreen;