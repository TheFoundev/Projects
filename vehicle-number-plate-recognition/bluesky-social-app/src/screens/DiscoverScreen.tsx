import { View, Text, StyleSheet } from 'react-native';
import { Screen, Card, Pill } from '../components';
import { colors } from '../theme';
import { suggestedFeeds, topics } from '../data';

export default function DiscoverScreen() {
  return (
    <Screen title="Discover" subtitle="Feeds and topics worth a look.">
      <Card>
        <Text style={styles.heading}>Suggested feeds</Text>
        {suggestedFeeds.map((feed) => (
          <View key={feed.name} style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.name}>{feed.name}</Text>
              <Text style={styles.desc}>{feed.description}</Text>
            </View>
            <Pill label={feed.members} />
          </View>
        ))}
      </Card>

      <Card>
        <Text style={styles.heading}>Topics</Text>
        <View style={styles.wrap}>
          {topics.map((topic) => <Pill key={topic} label={topic} tone="brand" />)}
        </View>
        <Text style={styles.desc}>
          Topics are just a local filter in this build. A real client would fetch
          feed generators from the network.
        </Text>
      </Card>

      <Card>
        <Text style={styles.heading}>How feeds work</Text>
        <Text style={styles.desc}>
          A feed is a list of posts selected by a rule you choose. The rule can be
          as simple as "people I follow" or as specific as "posts about robotics
          from the last week".
        </Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  heading: { fontSize: 15, fontWeight: '700', color: colors.ink, marginBottom: 6 },
  row: { flexDirection: 'row', gap: 10, alignItems: 'flex-start', paddingVertical: 8, borderTopWidth: 1, borderTopColor: colors.line },
  name: { fontWeight: '700', color: colors.ink, fontSize: 14 },
  desc: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginVertical: 4 },
});
