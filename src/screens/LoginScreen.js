import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import {
  TextInput,
  Button,
  Text,
  Card,
  Title,
  Paragraph,
} from 'react-native-paper';
import { useAuth } from '../context/AuthContext';

const LoginScreen = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('Ошибка', 'Пожалуйста, заполните все поля');
      return;
    }

    setLoading(true);
    try {
      const result = await login(username.trim(), password);
      
      if (!result.success) {
        Alert.alert('Ошибка входа', result.error);
      }
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось подключиться к серверу');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.content}>
          <Card style={styles.card}>
            <Card.Content>
              <Title style={styles.title}>Uzakbaevnurzhan Mirror</Title>
              <Paragraph style={styles.subtitle}>
                Локальная копия сайта
              </Paragraph>
              
              <TextInput
                label="Имя пользователя"
                value={username}
                onChangeText={setUsername}
                mode="outlined"
                style={styles.input}
                autoCapitalize="none"
                autoCorrect={false}
              />
              
              <TextInput
                label="Пароль"
                value={password}
                onChangeText={setPassword}
                mode="outlined"
                style={styles.input}
                secureTextEntry
                autoCapitalize="none"
                autoCorrect={false}
              />
              
              <Button
                mode="contained"
                onPress={handleLogin}
                loading={loading}
                disabled={loading}
                style={styles.button}
                contentStyle={styles.buttonContent}
              >
                Войти
              </Button>
              
              <Text style={styles.hint}>
                Используйте учетные данные администратора
              </Text>
            </Card.Content>
          </Card>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b1220',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  content: {
    padding: 20,
  },
  card: {
    backgroundColor: '#0f1724',
    borderRadius: 12,
    elevation: 8,
  },
  title: {
    textAlign: 'center',
    color: '#e6eef8',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    textAlign: 'center',
    color: '#98a0b3',
    marginBottom: 24,
  },
  input: {
    marginBottom: 16,
    backgroundColor: '#1a2332',
  },
  button: {
    marginTop: 8,
    backgroundColor: '#60a5fa',
    borderRadius: 8,
  },
  buttonContent: {
    paddingVertical: 8,
  },
  hint: {
    textAlign: 'center',
    color: '#98a0b3',
    fontSize: 12,
    marginTop: 16,
  },
});

export default LoginScreen;