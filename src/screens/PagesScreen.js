import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  Alert,
  TextInput,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Text,
  ActivityIndicator,
  Searchbar,
  List,
  Divider,
} from 'react-native-paper';
import { apiService } from '../services/apiService';

const PagesScreen = ({ navigation }) => {
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredPages, setFilteredPages] = useState([]);

  useEffect(() => {
    loadPages();
  }, []);

  useEffect(() => {
    filterPages();
  }, [searchQuery, pages]);

  const loadPages = async () => {
    try {
      setLoading(true);
      const response = await apiService.getPages();
      
      // Парсим HTML для извлечения списка страниц
      const pageMatches = response.match(/href="([^"]+)"/g);
      const pageUrls = pageMatches
        ? pageMatches.map(match => match.replace('href="', '').replace('"', ''))
        : [];
      
      setPages(pageUrls);
    } catch (error) {
      console.error('Error loading pages:', error);
      Alert.alert('Ошибка', 'Не удалось загрузить страницы');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPages();
    setRefreshing(false);
  };

  const filterPages = () => {
    if (!searchQuery.trim()) {
      setFilteredPages(pages);
    } else {
      const filtered = pages.filter(page =>
        page.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredPages(filtered);
    }
  };

  const handlePagePress = (pageUrl) => {
    navigation.navigate('ViewPage', { url: pageUrl });
  };

  const handleSearch = (query) => {
    setSearchQuery(query);
  };

  const renderPageItem = ({ item }) => (
    <List.Item
      title={item}
      description="Нажмите для просмотра"
      left={(props) => <List.Icon {...props} icon="file-document" />}
      right={(props) => <List.Icon {...props} icon="chevron-right" />}
      onPress={() => handlePagePress(item)}
      style={styles.listItem}
      titleStyle={styles.pageTitle}
      descriptionStyle={styles.pageDescription}
    />
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#60a5fa" />
        <Text style={styles.loadingText}>Загрузка страниц...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Поиск */}
      <View style={styles.searchContainer}>
        <Searchbar
          placeholder="Поиск страниц..."
          onChangeText={handleSearch}
          value={searchQuery}
          style={styles.searchbar}
          iconColor="#60a5fa"
        />
      </View>

      {/* Статистика */}
      <Card style={styles.statsCard}>
        <Card.Content>
          <Title style={styles.statsTitle}>Статистика</Title>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{pages.length}</Text>
              <Text style={styles.statLabel}>Всего страниц</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{filteredPages.length}</Text>
              <Text style={styles.statLabel}>Найдено</Text>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Список страниц */}
      <Card style={styles.listCard}>
        <Card.Content style={styles.cardContent}>
          <Title style={styles.listTitle}>Страницы</Title>
          {filteredPages.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>
                {searchQuery ? 'Страницы не найдены' : 'Страницы не загружены'}
              </Text>
            </View>
          ) : (
            <FlatList
              data={filteredPages}
              renderItem={renderPageItem}
              keyExtractor={(item, index) => index.toString()}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
              ItemSeparatorComponent={() => <Divider />}
              showsVerticalScrollIndicator={false}
            />
          )}
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
  searchContainer: {
    padding: 16,
    paddingBottom: 8,
  },
  searchbar: {
    backgroundColor: '#0f1724',
    borderRadius: 8,
  },
  statsCard: {
    backgroundColor: '#0f1724',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 12,
    elevation: 4,
  },
  statsTitle: {
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
  listCard: {
    backgroundColor: '#0f1724',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 12,
    elevation: 4,
    flex: 1,
  },
  cardContent: {
    padding: 0,
  },
  listTitle: {
    color: '#e6eef8',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  listItem: {
    backgroundColor: 'transparent',
  },
  pageTitle: {
    color: '#e6eef8',
    fontSize: 16,
  },
  pageDescription: {
    color: '#98a0b3',
    fontSize: 14,
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
});

export default PagesScreen;