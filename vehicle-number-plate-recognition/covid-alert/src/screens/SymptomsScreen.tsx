import { useState } from 'react';
import { View, Text, Switch, StyleSheet, Alert } from 'react-native';
import { Screen, Card, Button, Pill } from '../components';
import { colors } from '../theme';
import { symptomItems } from '../data';
import { assessSymptoms, DISCLAIMER } from '../exposure';

export default function SymptomsScreen() {
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const ticked = Object.keys(selected).filter((id) => selected[id]);
  const count = ticked.length;
  const assessment = assessSymptoms(ticked);

  function toggle(id: string) {
    setSelected((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function save() {
    Alert.alert(
      `Check-in saved (${assessment.level} risk)`,
      `${count} symptom${count === 1 ? '' : 's'} selected.\n\n${assessment.advice}`,
    );
  }

  return (
    <Screen title="Symptoms" subtitle="A quick self-check, not a diagnosis.">
      <Card>
        <Text style={styles.heading}>How are you feeling today?</Text>
        <Text style={styles.body}>Select anything that applies. The result is only a prompt to seek advice.</Text>
        {symptomItems.map((item) => (
          <View key={item.id} style={styles.symptomRow}>
            <Text style={styles.label}>{item.label}</Text>
            <Switch value={Boolean(selected[item.id])} onValueChange={() => toggle(item.id)} trackColor={{ true: colors.brand }} />
          </View>
        ))}
      </Card>

      <Card style={{ borderColor: assessment.level === 'high' ? '#fecaca' : assessment.level === 'moderate' ? '#fed7aa' : '#bbf7d0' }}>
        <View style={styles.rowBetween}>
          <Text style={styles.heading}>Summary</Text>
          <Pill
            label={count === 0 ? 'none selected' : `${count} selected · ${assessment.level} risk`}
            tone={assessment.level === 'low' ? 'ok' : 'warn'}
          />
        </View>
        <Text style={styles.body}>{assessment.advice}</Text>
        <Text style={styles.score}>Risk score: {assessment.score}</Text>
        <Text style={styles.disclaimer}>{DISCLAIMER}</Text>
        <Button label="Save check-in" onPress={save} kind="ghost" />
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  heading: { fontWeight: '700', color: colors.ink, fontSize: 15 },
  body: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  symptomRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 7, borderBottomWidth: 1, borderBottomColor: colors.line },
  label: { color: colors.ink, fontSize: 14 },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  score: { color: colors.ink, fontSize: 12, fontWeight: '700', marginTop: 6 },
  disclaimer: { color: colors.muted, fontSize: 11, lineHeight: 16, marginTop: 6 },
});
