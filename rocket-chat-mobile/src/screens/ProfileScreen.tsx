import { View, Text, StyleSheet, Alert } from 'react-native';
import { Screen, Card, Pill, Button } from '../components';
import { colors } from '../theme';
import { profile } from '../data';

export default function ProfileScreen() {
  return (
    <Screen title="Profile" subtitle="Your account on this workspace.">
      <Card>
        <View style={styles.top}>
          <View style={styles.avatar}><Text style={styles.avatarText}>AR</Text></View>
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{profile.name}</Text>
            <Text style={styles.meta}>@{profile.handle} · {profile.role}</Text>
          </View>
          <Pill label={profile.status} tone="ok" />
        </View>
        <View style={styles.setting}>
          <Text style={styles.label}>Server</Text>
          <Text style={styles.value}>{profile.server}</Text>
        </View>
        <View style={styles.setting}>
          <Text style={styles.label}>Status</Text>
          <Text style={styles.value}>Online</Text>
        </View>
        <View style={styles.setting}>
          <Text style={styles.label}>Notifications</Text>
          <Text style={styles.value}>Mentions and direct messages</Text>
        </View>
      </Card>

      <Card>
        <Text style={styles.heading}>About this build</Text>
        <Text style={styles.meta}>
          A student project inspired by Rocket.Chat Mobile. It demonstrates the
          channel/message UI without a server connection, login or push setup.
        </Text>
        <Button label="Sign out (not wired)" kind="ghost" onPress={() => Alert.alert('Demo', 'There is no session to sign out of.')} />
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  top: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  avatar: { width: 50, height: 50, borderRadius: 25, backgroundColor: colors.brand, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#fff', fontWeight: '800' },
  name: { fontWeight: '800', color: colors.ink, fontSize: 16 },
  meta: { color: colors.muted, fontSize: 11, lineHeight: 16 },
  heading: { fontWeight: '700', color: colors.ink, fontSize: 15 },
  setting: { paddingVertical: 8, borderTopWidth: 1, borderTopColor: colors.line, gap: 1 },
  label: { color: colors.muted, fontSize: 10, fontWeight: '700', textTransform: 'uppercase' },
  value: { color: colors.ink, fontSize: 13 },
});
