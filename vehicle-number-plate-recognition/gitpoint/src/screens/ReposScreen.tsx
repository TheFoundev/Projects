import { useState } from 'react';
import { View, Text, TextInput, StyleSheet } from 'react-native';
import { Screen, Card, Pill, Empty } from '../components';
import { colors } from '../theme';
import { useGitHub } from '../githubContext';
import { searchRepos } from '../github';

const languageColor: Record<string, string> = {
  TypeScript: '#3178c6', Python: '#3572A5', Go: '#00ADD8', JavaScript: '#f1e05a',
};

export default function ReposScreen() {
  const { repos, loading, offline, error, refresh, rateLimit } = useGitHub();
  const [query, setQuery] = useState('');
  const visible = searchRepos(repos, query);

  return (
    <Screen title="Repositories" subtitle="Your public projects and class work.">
      {offline ? (
        <Text style={styles.desc}>
          {error ? `Offline: ${error}. ` : 'Offline: showing the saved data. '}
          <Text onPress={refresh}>Try again</Text>
        </Text>
      ) : null}
      {rateLimit ? (
        <Text style={styles.metaText}>
          {rateLimit.remaining} of {rateLimit.limit} requests left this hour
        </Text>
      ) : null}
      <TextInput
        value={query}
        onChangeText={setQuery}
        placeholder="Search repositories"
        placeholderTextColor={colors.muted}
        style={styles.search}
      />
      {visible.length === 0 ? <Empty title="No matches" body="Try a different language or project name." /> : visible.map((repo) => (
        <Card key={repo.id}>
          <View style={styles.rowBetween}>
            <Text style={styles.name}>{repo.name}</Text>
            <Pill label="public" />
          </View>
          <Text style={styles.desc}>{repo.description}</Text>
          <View style={styles.meta}>
            <View style={[styles.dot, { backgroundColor: languageColor[repo.language] ?? colors.muted }]} />
            <Text style={styles.metaText}>{repo.language}</Text>
            <Text style={styles.metaText}>★ {repo.stars}</Text>
            <Text style={styles.metaText}>⑂ {repo.forks}</Text>
            <Text style={styles.metaText}>Updated {repo.updated}</Text>
          </View>
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  search: { borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, borderRadius: 9, paddingHorizontal: 11, paddingVertical: 9, color: colors.ink },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  name: { fontSize: 16, fontWeight: '700', color: colors.brand },
  desc: { color: colors.muted, fontSize: 13, lineHeight: 18 },
  meta: { flexDirection: 'row', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginTop: 2 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  metaText: { color: colors.muted, fontSize: 11 },
});
