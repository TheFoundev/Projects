import { useState } from 'react';
import { View, Text, Switch, StyleSheet, Alert } from 'react-native';
import { Screen, Card, Button, Pill } from '../components';
import { colors } from '../theme';
import { settings } from '../data';

export default function SettingsScreen() {
  const [notifications, setNotifications] = useState(settings.notifications);
  const [currency, setCurrency] = useState(settings.currency);

  return (
    <Screen title="Settings" subtitle="Account and app preferences.">
      <Card>
        <View style={styles.row}>
          <View style={styles.avatar}><Text style={styles.avatarText}>AR</Text></View>
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{settings.name}</Text>
            <Text style={styles.meta}>{settings.email}</Text>
          </View>
          <Pill label="member" />
        </View>
      </Card>

      <Card>
        <Text style={styles.heading}>Preferences</Text>
        <View style={styles.settingRow}>
          <View><Text style={styles.setting}>Push notifications</Text><Text style={styles.meta}>Approval updates and chat mentions</Text></View>
          <Switch value={notifications} onValueChange={setNotifications} trackColor={{ true: colors.brand }} />
        </View>
        <View style={styles.settingRow}>
          <View><Text style={styles.setting}>Currency</Text><Text style={styles.meta}>Used for new reports</Text></View>
          <View style={styles.currencyRow}>
            {['CAD', 'USD'].map((code) => (
              <Text key={code} onPress={() => setCurrency(code)} style={[styles.currency, currency === code && styles.currencyActive]}>{code}</Text>
            ))}
          </View>
        </View>
      </Card>

      <Card>
        <Text style={styles.heading}>About</Text>
        <Text style={styles.meta}>
          A student project inspired by New Expensify. Expense reports and chat are
          mock data; there is no bank connection or reimbursement backend.
        </Text>
        <Button label="Sign out (not wired)" kind="ghost" onPress={() => Alert.alert('Demo', 'Sign out is not connected.')} />
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  avatar: { width: 46, height: 46, borderRadius: 23, backgroundColor: colors.brand, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#fff', fontWeight: '800' },
  name: { fontWeight: '700', color: colors.ink, fontSize: 15 },
  meta: { color: colors.muted, fontSize: 11, lineHeight: 16 },
  heading: { fontWeight: '700', color: colors.ink, fontSize: 15, marginBottom: 4 },
  settingRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 9, borderBottomWidth: 1, borderBottomColor: colors.line },
  setting: { color: colors.ink, fontSize: 13 },
  currencyRow: { flexDirection: 'row', gap: 6 },
  currency: { borderWidth: 1, borderColor: colors.line, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3, fontSize: 11, color: colors.muted },
  currencyActive: { borderColor: colors.brand, color: colors.brand, fontWeight: '700' },
});
