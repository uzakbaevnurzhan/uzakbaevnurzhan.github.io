import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import {
  Card,
  Title,
  Text,
  TextInput,
  Button,
  ActivityIndicator,
  Avatar,
} from 'react-native-paper';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/apiService';

const ChatScreen = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const flatListRef = useRef(null);

  useEffect(() => {
    loadMessages();
    const interval = setInterval(loadMessages, 5000); // Обновление каждые 5 секунд
    return () => clearInterval(interval);
  }, []);

  const loadMessages = async () => {
    try {
      const response = await apiService.getChat();
      
      // Парсим HTML для извлечения сообщений
      const messageMatches = response.match(/<div[^>]*class="[^"]*message[^"]*"[^>]*>([\s\S]*?)<\/div>/g);
      const parsedMessages = messageMatches
        ? messageMatches.map(match => {
            const userMatch = match.match(/<strong[^>]*>([^<]+)<\/strong>/);
            const timeMatch = match.match(/<small[^>]*>([^<]+)<\/small>/);
            const textMatch = match.match(/<div[^>]*>([^<]+)<\/div>/);
            
            return {
              id: Math.random().toString(),
              user: userMatch ? userMatch[1].trim() : 'Unknown',
              timestamp: timeMatch ? timeMatch[1].trim() : '',
              text: textMatch ? textMatch[1].trim() : '',
            };
          })
        : [];
      
      setMessages(parsedMessages);
      setLoading(false);
    } catch (error) {
      console.error('Error loading messages:', error);
      if (!loading) {
        Alert.alert('Ошибка', 'Не удалось загрузить сообщения');
      }
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    try {
      setSending(true);
      await apiService.sendChatMessage(newMessage.trim());
      setNewMessage('');
      await loadMessages(); // Перезагружаем сообщения
    } catch (error) {
      console.error('Error sending message:', error);
      Alert.alert('Ошибка', 'Не удалось отправить сообщение');
    } finally {
      setSending(false);
    }
  };

  const renderMessage = ({ item }) => {
    const isOwnMessage = item.user === user?.username;
    
    return (
      <View style={[
        styles.messageContainer,
        isOwnMessage ? styles.ownMessage : styles.otherMessage
      ]}>
        <View style={[
          styles.messageBubble,
          isOwnMessage ? styles.ownBubble : styles.otherBubble
        ]}>
          {!isOwnMessage && (
            <View style={styles.messageHeader}>
              <Avatar.Text 
                size={24} 
                label={item.user.charAt(0).toUpperCase()}
                style={styles.avatar}
              />
              <Text style={styles.userName}>{item.user}</Text>
            </View>
          )}
          <Text style={[
            styles.messageText,
            isOwnMessage ? styles.ownText : styles.otherText
          ]}>
            {item.text}
          </Text>
          <Text style={styles.timestamp}>{item.timestamp}</Text>
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#60a5fa" />
        <Text style={styles.loadingText}>Загрузка чата...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      {/* Заголовок */}
      <Card style={styles.headerCard}>
        <Card.Content>
          <Title style={styles.headerTitle}>Чат</Title>
          <Text style={styles.headerSubtitle}>
            {messages.length} сообщений
          </Text>
        </Card.Content>
      </Card>

      {/* Список сообщений */}
      <Card style={styles.messagesCard}>
        <Card.Content style={styles.messagesContent}>
          {messages.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>Сообщений пока нет</Text>
              <Text style={styles.emptySubtext}>
                Будьте первым, кто напишет сообщение!
              </Text>
            </View>
          ) : (
            <FlatList
              ref={flatListRef}
              data={messages}
              renderItem={renderMessage}
              keyExtractor={(item) => item.id}
              showsVerticalScrollIndicator={false}
              onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
              onLayout={() => flatListRef.current?.scrollToEnd()}
            />
          )}
        </Card.Content>
      </Card>

      {/* Поле ввода */}
      <Card style={styles.inputCard}>
        <Card.Content style={styles.inputContent}>
          <View style={styles.inputContainer}>
            <TextInput
              mode="outlined"
              placeholder="Введите сообщение..."
              value={newMessage}
              onChangeText={setNewMessage}
              style={styles.textInput}
              multiline
              maxLength={500}
              right={
                <TextInput.Icon
                  icon="send"
                  onPress={sendMessage}
                  disabled={sending || !newMessage.trim()}
                />
              }
            />
          </View>
        </Card.Content>
      </Card>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b1220',
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
  headerCard: {
    backgroundColor: '#0f1724',
    margin: 16,
    marginBottom: 8,
    borderRadius: 12,
    elevation: 4,
  },
  headerTitle: {
    color: '#e6eef8',
    fontSize: 18,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    color: '#98a0b3',
    fontSize: 14,
    marginTop: 4,
  },
  messagesCard: {
    backgroundColor: '#0f1724',
    marginHorizontal: 16,
    marginBottom: 8,
    borderRadius: 12,
    elevation: 4,
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    flex: 1,
  },
  messageContainer: {
    marginBottom: 12,
  },
  ownMessage: {
    alignItems: 'flex-end',
  },
  otherMessage: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
  },
  ownBubble: {
    backgroundColor: '#60a5fa',
    borderBottomRightRadius: 4,
  },
  otherBubble: {
    backgroundColor: '#1e293b',
    borderBottomLeftRadius: 4,
  },
  messageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  avatar: {
    marginRight: 8,
    backgroundColor: '#60a5fa',
  },
  userName: {
    color: '#60a5fa',
    fontSize: 12,
    fontWeight: 'bold',
  },
  messageText: {
    fontSize: 16,
    lineHeight: 20,
  },
  ownText: {
    color: '#ffffff',
  },
  otherText: {
    color: '#e6eef8',
  },
  timestamp: {
    fontSize: 10,
    color: '#98a0b3',
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    color: '#98a0b3',
    fontSize: 16,
    textAlign: 'center',
  },
  emptySubtext: {
    color: '#6b7280',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 8,
  },
  inputCard: {
    backgroundColor: '#0f1724',
    margin: 16,
    marginTop: 8,
    borderRadius: 12,
    elevation: 4,
  },
  inputContent: {
    padding: 0,
  },
  inputContainer: {
    padding: 16,
  },
  textInput: {
    backgroundColor: '#1a2332',
  },
});

export default ChatScreen;