import { View, Text, StyleSheet } from 'react-native';
import { Screen, Card, Pill, Button, Empty } from '../components';
import { colors } from '../theme';
import { useFeed } from '../feedContext';
import { likeCount, myPosts, profileStats } from '../feed';

export default function ProfileScreen() {
  const { posts, liked } = useFeed();
  const mine = myPosts(posts);
  const stats = profileStats(posts, liked);
  return (
    <Screen title="Profile" subtitle="Your account in this demo.">
      <Card>
        <View style={styles.top}>
          <View style={styles.avatar}><Text style={styles.avatarText}>Y</Text></View>
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>You</Text>
            <Text style={styles.handle}>@you.bsky.social</Text>
          </View>
          <Pill label="demo" tone="warn" />
        </View>
        <Text style={styles.bio}>
          Third-year engineering student. Building small apps to learn how the
          pieces fit together. Currently interested in mobile state and offline data.
        </Text>
        <View style={styles.stats}>
          <View><Text style={styles.stat}>{stats.posts}</Text><Text style={styles.statLabel}>posts</Text></View>
          <View><Text style={styles.stat}>{stats.likes}</Text><Text style={styles.statLabel}>likes</Text></View>
          <View><Text style={styles.stat}>{stats.replies}</Text><Text style={styles.statLabel}>replies</Text></View>
        </View>
        <Button label="Edit profile (not wired)" kind="ghost" onPress={() => {}} />
      </Card>

      <Text style={styles.section}>Your posts</Text>
      {mine.length === 0 ? (
        <Empty title="No posts yet" body="Write something from the Home tab and it will show up here, and it stays after you close the app." />
      ) : mine.map((post) => (
        <Card key={post.id}>
          <Text style={styles.post}>{post.text}</Text>
          <Text style={styles.handle}>{post.time} · {likeCount(post, liked)} likes</Text>
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  top: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  avatar: { width: 54, height: 54, borderRadius: 27, backgroundColor: colors.soft, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: colors.brand, fontSize: 22, fontWeight: '800' },
  name: { fontSize: 18, fontWeight: '800', color: colors.ink },
  handle: { color: colors.muted, fontSize: 12 },
  bio: { color: colors.ink, fontSize: 13, lineHeight: 19 },
  stats: { flexDirection: 'row', gap: 26, paddingVertical: 6 },
  stat: { fontSize: 16, fontWeight: '800', color: colors.ink },
  statLabel: { fontSize: 11, color: colors.muted },
  section: { fontWeight: '700', color: colors.ink, marginTop: 4 },
  post: { color: colors.ink, fontSize: 14, lineHeight: 20 },
});
