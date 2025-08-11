import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  Alert,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Text,
  ActivityIndicator,
  List,
  Divider,
  Chip,
} from 'react-native-paper';
import { apiService } from '../services/apiService';

const AuditScreen = () => {
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadAuditLogs();
  }, []);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      const response = await apiService.getAudit();
      
      // Парсим HTML для извлечения логов аудита
      const logMatches = response.match(/<tr[^>]*>([\s\S]*?)<\/tr>/g);
      const logs = logMatches
        ? logMatches.slice(1).map(match => {
            const cells = match.match(/<td[^>]*>([\s\S]*?)<\/td>/g);
            if (cells && cells.length >= 4) {
              return {
                timestamp: cells[0].replace(/<[^>]*>/g, '').trim(),
                user: cells[1].replace(/<[^>]*>/g, '').trim(),
                action: cells[2].replace(/<[^>]*>/g, '').trim(),
                details: cells[3].replace(/<[^>]*>/g, '').trim(),
              };
            }
            return null;
          }).filter(Boolean)
        : [];
      
      setAuditLogs(logs);
    } catch (error) {
      console.error('Error loading audit logs:', error);
      Alert.alert('Ошибка', 'Не удалось загрузить журнал аудита');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadAuditLogs();
    setRefreshing(false);
  };

  const getActionColor = (action) => {
    if (action.includes('login')) return '#10b981';
    if (action.includes('logout')) return '#6b7280';
    if (action.includes('update')) return '#3b82f6';
    if (action.includes('create')) return '#8b5cf6';
    if (action.includes('delete')) return '#ef4444';
    return '#60a5fa';
  };

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('ru-RU');
    } catch {
      return timestamp;
    }
  };

  const renderAuditItem = ({ item, index }) => (
    <List.Item
      title={item.action}
      description={`${item.user} • ${formatTimestamp(item.timestamp)}`}
      left={(props) => (
        <View style={[styles.actionIcon, { backgroundColor: getActionColor(item.action) }]}>
          <Text style={styles.actionIconText}>
            {item.action.charAt(0).toUpperCase()}
          </Text>
        </View>
      )}
      right={(props) => (
        <View style={styles.detailsContainer}>
          {item.details && (
            <Chip style={styles.detailsChip} textStyle={styles.detailsText}>
              {item.details.length > 30 ? `${item.details.substring(0, 30)}...` : item.details}
            </Chip>
          )}
        </View>
      )}
      style={styles.listItem}
      titleStyle={styles.auditTitle}
      descriptionStyle={styles.auditDescription}
    />
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#60a5fa" />
        <Text style={styles.loadingText}>Загрузка журнала...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Статистика */}
      <Card style={styles.statsCard}>
        <Card.Content>
          <Title style={styles.statsTitle}>Журнал аудита</Title>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{auditLogs.length}</Text>
              <Text style={styles.statLabel}>Записей</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>
                {new Set(auditLogs.map(log => log.user)).size}
              </Text>
              <Text style={styles.statLabel}>Пользователей</Text>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Список логов */}
      <Card style={styles.listCard}>
        <Card.Content style={styles.cardContent}>
          {auditLogs.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>Журнал аудита пуст</Text>
            </View>
          ) : (
            <FlatList
              data={auditLogs}
              renderItem={renderAuditItem}
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
  statsCard: {
    backgroundColor: '#0f1724',
    margin: 16,
    marginBottom: 8,
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
  listItem: {
    backgroundColor: 'transparent',
  },
  actionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  actionIconText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  auditTitle: {
    color: '#e6eef8',
    fontSize: 16,
    fontWeight: 'bold',
  },
  auditDescription: {
    color: '#98a0b3',
    fontSize: 14,
  },
  detailsContainer: {
    alignItems: 'flex-end',
  },
  detailsChip: {
    backgroundColor: '#1e3a8a',
    maxWidth: 120,
  },
  detailsText: {
    color: '#e6eef8',
    fontSize: 12,
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

export default AuditScreen;