import { View, Text, StyleSheet } from 'react-native';
import { Screen, Card, Pill, Button } from '../components';
import { colors } from '../theme';
import { profile } from '../data';

export default function ProfileScreen() {
  return (
    <Screen title="Profile" subtitle="Your GitHub identity in this demo.">
      <Card>
        <View style={styles.top}>
          <View style={styles.avatar}><Text style={styles.avatarText}>AR</Text></View>
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{profile.name}</Text>
            <Text style={styles.handle}>@{profile.handle}</Text>
          </View>
        </View>
        <Text style={styles.bio}>{profile.bio}</Text>
        <Text style={styles.meta}>⌖ {profile.location}</Text>
        <View style={styles.stats}>
          <View><Text style={styles.stat}>{profile.followers}</Text><Text style={styles.statLabel}>followers</Text></View>
          <View><Text style={styles.stat}>{profile.following}</Text><Text style={styles.statLabel}>following</Text></View>
          <View><Text style={styles.stat}>{profile.repos}</Text><Text style={styles.statLabel}>repos</Text></View>
        </View>
      </Card>

      <Card>
        <View style={styles.rowBetween}>
          <Text style={styles.heading}>Contributions</Text>
          <Pill label="this year" />
        </View>
        <Text style={styles.contrib}>{profile.contributions}</Text>
        <Text style={styles.meta}>A real client would draw a contribution calendar here.</Text>
      </Card>

      <Card>
        <Text style={styles.heading}>Settings</Text>
        {['Notifications', 'Appearance', 'GitHub token'].map((item) => (
          <View key={item} style={styles.setting}><Text style={styles.settingText}>{item}</Text><Text style={styles.chevron}>›</Text></View>
        ))}
        <Button label="Sign out (not wired)" kind="ghost" onPress={() => {}} />
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  top: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  avatar: { width: 56, height: 56, borderRadius: 28, backgroundColor: colors.brand, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#fff', fontWeight: '800', fontSize: 19 },
  name: { fontSize: 18, fontWeight: '800', color: colors.ink },
  handle: { color: colors.muted, fontSize: 12 },
  bio: { color: colors.ink, fontSize: 13, lineHeight: 19 },
  meta: { color: colors.muted, fontSize: 11 },
  stats: { flexDirection: 'row', gap: 24, paddingTop: 4 },
  stat: { fontSize: 16, fontWeight: '800', color: colors.ink },
  statLabel: { fontSize: 11, color: colors.muted },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  heading: { fontWeight: '700', color: colors.ink, fontSize: 15 },
  contrib: { fontSize: 32, fontWeight: '800', color: colors.brand },
  setting: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 9, borderBottomWidth: 1, borderBottomColor: colors.line },
  settingText: { color: colors.ink, fontSize: 13 },
  chevron: { color: colors.muted, fontSize: 16 },
});
