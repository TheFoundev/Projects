import { useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Screen, Card, Button, Pill } from '../components';
import { colors } from '../theme';
import { useExposure } from '../exposureContext';
import { lastCheck, nextCheckDue } from '../exposure';

export default function StatusScreen() {
  const { checks, service, runCheck } = useExposure();
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState('');

  const latest = lastCheck(checks);
  const due = nextCheckDue(checks, 1);

  async function onCheck() {
    setChecking(true);
    setError('');
    try {
      await runCheck();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'The check could not be run.');
    } finally {
      setChecking(false);
    }
  }

  return (
    <Screen title="COVID Alert" subtitle="Exposure checks for this demo.">
      <Card style={styles.statusCard}>
        <Pill label={`${service.name} source`} tone="ok" />
        <Text style={styles.status}>
          {latest && latest.result === 'exposed' ? 'An exposure was detected' : 'No exposures detected'}
        </Text>
        <Text style={styles.statusBody}>
          The check runs against the {service.name} exposure service. A real
          build would compare anonymous codes with a public-health server
          without revealing who you are.
        </Text>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Button label={checking ? 'Checking…' : 'Check for exposures'} onPress={onCheck} disabled={checking} />
        <Text style={styles.last}>
          Last check: {latest ? latest.date : 'never'}
          {due !== null ? ` · next check due in ${due} day${due === 1 ? '' : 's'}` : ''}
        </Text>
      </Card>

      <Text style={styles.heading}>Recent checks</Text>
      {checks.map((check) => (
        <Card key={check.id} style={styles.row}>
          <View style={{ flex: 1 }}>
            <Text style={styles.date}>{check.date}</Text>
            <Text style={styles.note}>{check.note}</Text>
          </View>
          <Pill label={check.result} tone={check.result === 'clear' ? 'ok' : 'warn'} />
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  error: { color: colors.danger, fontSize: 12, marginBottom: 6 },
  statusCard: { gap: 8, borderColor: '#bbf7d0', backgroundColor: '#f0fdf4' },
  status: { fontSize: 22, fontWeight: '800', color: colors.ok },
  statusBody: { color: colors.muted, fontSize: 13, lineHeight: 19, marginBottom: 4 },
  last: { color: colors.muted, fontSize: 11, textAlign: 'center' },
  heading: { fontWeight: '700', color: colors.ink },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  date: { fontWeight: '700', color: colors.ink, fontSize: 13 },
  note: { color: colors.muted, fontSize: 11, marginTop: 2 },
});
