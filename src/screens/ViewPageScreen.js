import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Alert,
  Share,
  Linking,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Text,
  ActivityIndicator,
  IconButton,
  Menu,
  Divider,
} from 'react-native-paper';
import { WebView } from 'react-native-webview';
import { apiService } from '../services/apiService';

const ViewPageScreen = ({ route, navigation }) => {
  const { url } = route.params;
  const [pageContent, setPageContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [menuVisible, setMenuVisible] = useState(false);
  const [viewMode, setViewMode] = useState('webview'); // 'webview' or 'raw'

  useEffect(() => {
    loadPageContent();
  }, [url]);

  const loadPageContent = async () => {
    try {
      setLoading(true);
      const response = await apiService.getPage(url);
      setPageContent(response);
    } catch (error) {
      console.error('Error loading page content:', error);
      Alert.alert('Ошибка', 'Не удалось загрузить содержимое страницы');
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: `Просмотр страницы: ${url}`,
        url: url,
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const handleOpenInBrowser = async () => {
    try {
      await Linking.openURL(url);
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось открыть ссылку');
    }
  };

  const handleDownload = async () => {
    try {
      Alert.alert(
        'Скачивание',
        'Скачать страницу?',
        [
          { text: 'Отмена', style: 'cancel' },
          {
            text: 'Скачать',
            onPress: async () => {
              await apiService.downloadPage(url);
              Alert.alert('Успех', 'Страница скачана');
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось скачать страницу');
    }
  };

  const toggleViewMode = () => {
    setViewMode(viewMode === 'webview' ? 'raw' : 'webview');
  };

  const renderWebView = () => (
    <WebView
      source={{ html: pageContent }}
      style={styles.webview}
      javaScriptEnabled={true}
      domStorageEnabled={true}
      startInLoadingState={true}
      renderLoading={() => (
        <View style={styles.webviewLoading}>
          <ActivityIndicator size="large" color="#60a5fa" />
        </View>
      )}
    />
  );

  const renderRawContent = () => (
    <ScrollView style={styles.rawContainer}>
      <Text style={styles.rawText}>{pageContent}</Text>
    </ScrollView>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#60a5fa" />
        <Text style={styles.loadingText}>Загрузка страницы...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Заголовок */}
      <Card style={styles.headerCard}>
        <Card.Content>
          <View style={styles.headerRow}>
            <View style={styles.headerInfo}>
              <Title style={styles.pageTitle}>Просмотр страницы</Title>
              <Paragraph style={styles.pageUrl}>{url}</Paragraph>
            </View>
            <Menu
              visible={menuVisible}
              onDismiss={() => setMenuVisible(false)}
              anchor={
                <IconButton
                  icon="dots-vertical"
                  onPress={() => setMenuVisible(true)}
                  iconColor="#60a5fa"
                />
              }
            >
              <Menu.Item
                onPress={() => {
                  setMenuVisible(false);
                  handleShare();
                }}
                title="Поделиться"
                leadingIcon="share"
              />
              <Menu.Item
                onPress={() => {
                  setMenuVisible(false);
                  handleOpenInBrowser();
                }}
                title="Открыть в браузере"
                leadingIcon="open-in-new"
              />
              <Menu.Item
                onPress={() => {
                  setMenuVisible(false);
                  handleDownload();
                }}
                title="Скачать"
                leadingIcon="download"
              />
              <Divider />
              <Menu.Item
                onPress={() => {
                  setMenuVisible(false);
                  toggleViewMode();
                }}
                title={viewMode === 'webview' ? 'Показать код' : 'Показать страницу'}
                leadingIcon={viewMode === 'webview' ? 'code-tags' : 'eye'}
              />
            </Menu>
          </View>
        </Card.Content>
      </Card>

      {/* Переключатель режима просмотра */}
      <View style={styles.viewModeContainer}>
        <Button
          mode={viewMode === 'webview' ? 'contained' : 'outlined'}
          onPress={() => setViewMode('webview')}
          style={styles.viewModeButton}
          icon="eye"
        >
          Страница
        </Button>
        <Button
          mode={viewMode === 'raw' ? 'contained' : 'outlined'}
          onPress={() => setViewMode('raw')}
          style={styles.viewModeButton}
          icon="code-tags"
        >
          Код
        </Button>
      </View>

      {/* Содержимое страницы */}
      <Card style={styles.contentCard}>
        <Card.Content style={styles.cardContent}>
          {viewMode === 'webview' ? renderWebView() : renderRawContent()}
        </Card.Content>
      </Card>
    </View>
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
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerInfo: {
    flex: 1,
  },
  pageTitle: {
    color: '#e6eef8',
    fontSize: 18,
    fontWeight: 'bold',
  },
  pageUrl: {
    color: '#60a5fa',
    fontSize: 14,
    marginTop: 4,
  },
  viewModeContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  viewModeButton: {
    flex: 1,
    marginHorizontal: 4,
    borderColor: '#60a5fa',
  },
  contentCard: {
    backgroundColor: '#0f1724',
    margin: 16,
    marginTop: 8,
    borderRadius: 12,
    elevation: 4,
    flex: 1,
  },
  cardContent: {
    padding: 0,
    flex: 1,
  },
  webview: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  webviewLoading: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  rawContainer: {
    flex: 1,
    padding: 16,
  },
  rawText: {
    color: '#e6eef8',
    fontSize: 12,
    fontFamily: 'monospace',
  },
});

export default ViewPageScreen;