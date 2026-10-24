import { View, Text, StyleSheet } from 'react-native';
import { Screen, Card, Pill } from '../components';
import { colors } from '../theme';
import { channels } from '../data';

export default function ChannelsScreen() {
  const unread = channels.reduce((sum, channel) => sum + channel.unread, 0);
  return (
    <Screen title="Channels" subtitle={`${unread} unread across ${channels.length} channels.`}>
      {channels.map((channel) => (
        <Card key={channel.id} style={styles.channel}>
          <View style={styles.icon}><Text style={styles.hash}>{channel.private ? '▣' : '#'}</Text></View>
          <View style={{ flex: 1 }}>
            <View style={styles.rowBetween}>
              <Text style={styles.name}>{channel.name}</Text>
              {channel.unread > 0 ? <Pill label={`${channel.unread} new`} tone="brand" /> : <Pill label="read" />}
            </View>
            <Text style={styles.topic}>{channel.topic}</Text>
            <Text style={styles.meta}>{channel.members} members{channel.private ? ' · private' : ''}</Text>
          </View>
        </Card>
      ))}
      <Text style={styles.footnote}>Open the Chat tab to read and reply. Channel selection is local.</Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  channel: { flexDirection: 'row', gap: 10, alignItems: 'flex-start' },
  icon: { width: 34, height: 34, borderRadius: 10, backgroundColor: colors.soft, alignItems: 'center', justifyContent: 'center' },
  hash: { color: colors.brand, fontWeight: '800', fontSize: 16 },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  name: { fontWeight: '700', color: colors.ink, fontSize: 15 },
  topic: { color: colors.muted, fontSize: 12, lineHeight: 17, marginTop: 2 },
  meta: { color: colors.muted, fontSize: 10, marginTop: 3 },
  footnote: { color: colors.muted, fontSize: 11, textAlign: 'center' },
});
