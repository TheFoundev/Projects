import { useState } from 'react';
import { View, Text, TextInput, Pressable, StyleSheet } from 'react-native';
import { Screen, Card, Button, Pill } from '../components';
import { colors, spacing } from '../theme';
import { topics } from '../data';
import { useFeed } from '../feedContext';
import { filterByTopic, likeCount, MAX_POST_LENGTH } from '../feed';

export default function FeedScreen() {
  const { posts, liked, publish, toggle } = useFeed();
  const [draft, setDraft] = useState('');
  const [filter, setFilter] = useState('All');

  function onPublish() {
    if (publish(draft)) setDraft('');
  }

  const visible = filterByTopic(posts, filter);

  return (
    <Screen title="Bluesky" subtitle="A small feed for people building things.">
      <View style={styles.chips}>
        {['All', 'buildinpublic', 'engineering', 'design'].map((topic) => (
          <Pressable key={topic} onPress={() => setFilter(topic)}>
            <Pill label={topic === 'All' ? 'All' : `#${topic}`} tone={filter === topic ? 'brand' : 'default'} />
          </Pressable>
        ))}
      </View>

      <Card>
        <TextInput
          value={draft}
          onChangeText={setDraft}
          placeholder="What are you working on?"
          placeholderTextColor={colors.muted}
          style={styles.composer}
          multiline
          maxLength={MAX_POST_LENGTH}
        />
        <View style={styles.rowBetween}>
          <Text style={styles.counter}>{draft.length}/{MAX_POST_LENGTH}</Text>
          <Button label="Post" onPress={onPublish} disabled={!draft.trim()} />
        </View>
      </Card>

      {visible.map((post) => {
        const isLiked = Boolean(liked[post.id]);
        const likes = likeCount(post, liked);
        return (
          <Card key={post.id}>
            <View style={styles.avatarRow}>
              <View style={styles.avatar}><Text style={styles.avatarText}>{post.author[0]}</Text></View>
              <View style={{ flex: 1 }}>
                <Text style={styles.author}>{post.author} {post.mine ? <Text style={styles.you}>you</Text> : null}</Text>
                <Text style={styles.handle}>@{post.handle} · {post.time}</Text>
              </View>
              <Pill label={`#${post.topic}`} />
            </View>
            <Text style={styles.body}>{post.text}</Text>
            <View style={styles.actions}>
              <Text style={styles.action}>◌ {post.replies} replies</Text>
              <Pressable onPress={() => toggle(post.id)}>
                <Text style={[styles.action, isLiked && styles.liked]}>
                  {isLiked ? '♥' : '♡'} {likes} likes
                </Text>
              </Pressable>
              <Text style={styles.action}>↗ share</Text>
            </View>
          </Card>
        );
      })}

      <Text style={styles.topics}>{topics.join('   ')}</Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  chips: { flexDirection: 'row', gap: 6, flexWrap: 'wrap' },
  composer: { minHeight: 64, fontSize: 15, color: colors.ink, textAlignVertical: 'top' },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  counter: { color: colors.muted, fontSize: 12 },
  avatarRow: { flexDirection: 'row', alignItems: 'center', gap: 9 },
  avatar: { width: 34, height: 34, borderRadius: 17, backgroundColor: colors.soft, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: colors.brand, fontWeight: '800' },
  author: { fontWeight: '700', color: colors.ink, fontSize: 14 },
  you: { color: colors.brand, fontSize: 11 },
  handle: { color: colors.muted, fontSize: 11, marginTop: 1 },
  body: { color: colors.ink, fontSize: 15, lineHeight: 21 },
  actions: { flexDirection: 'row', gap: 16, marginTop: 2 },
  action: { color: colors.muted, fontSize: 12 },
  liked: { color: '#e11d48', fontWeight: '700' },
  topics: { color: colors.muted, fontSize: 12, textAlign: 'center', marginTop: 4 },
});
