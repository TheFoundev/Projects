import { useState } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Screen, Card, Pill, Empty } from '../components';
import { colors } from '../theme';
import { issues } from '../data';

export default function IssuesScreen() {
  const [filter, setFilter] = useState<'open' | 'closed'>('open');
  const visible = issues.filter((issue) => issue.state === filter);

  return (
    <Screen title="Issues" subtitle="Open work across your repositories.">
      <View style={styles.tabs}>
        {(['open', 'closed'] as const).map((state) => (
          <Pressable key={state} onPress={() => setFilter(state)} style={[styles.tab, filter === state && styles.tabActive]}>
            <Text style={[styles.tabText, filter === state && styles.tabTextActive]}>{state} ({issues.filter((i) => i.state === state).length})</Text>
          </Pressable>
        ))}
      </View>
      {visible.map((issue) => (
        <Card key={issue.id}>
          <View style={styles.rowBetween}>
            <Text style={styles.repo}>{issue.repo} #{issue.number}</Text>
            <Pill label={issue.state} tone={issue.state === 'open' ? 'ok' : 'default'} />
          </View>
          <Text style={styles.title}>{issue.title}</Text>
          <View style={styles.labels}>
            {issue.labels.map((label) => <Pill key={label} label={label} tone="brand" />)}
          </View>
          <Text style={styles.meta}>{issue.author} · {issue.comments} comments</Text>
        </Card>
      ))}
      {visible.length === 0 ? <Empty title="Nothing here" body={`No ${filter} issues in the mock data.`} /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  tabs: { flexDirection: 'row', gap: 8 },
  tab: { borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 5 },
  tabActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  tabText: { color: colors.muted, fontSize: 12, fontWeight: '600' },
  tabTextActive: { color: '#fff' },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  repo: { color: colors.muted, fontSize: 11, fontWeight: '700' },
  title: { color: colors.ink, fontSize: 15, fontWeight: '700', lineHeight: 20 },
  labels: { flexDirection: 'row', flexWrap: 'wrap', gap: 5 },
  meta: { color: colors.muted, fontSize: 11 },
});
