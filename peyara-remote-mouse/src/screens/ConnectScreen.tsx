import { useEffect, useState } from 'react';
import { Text, StyleSheet, View } from 'react-native';
import { Screen, Card, Button, Field, Pill } from '../components';
import { colors } from '../theme';
import { connect, disconnect, loadLastHost, useConnectionStatus } from '../data';
import { validateHost } from '../protocol';

export default function ConnectScreen() {
  const connection = useConnectionStatus();
  const [host, setHost] = useState(connection.host);
  const [problem, setProblem] = useState<string | null>(null);

  // The address of the last relay is remembered on the device.
  useEffect(() => {
    let cancelled = false;
    loadLastHost().then((saved) => {
      if (!cancelled && saved) setHost(saved);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  function start() {
    const complaint = validateHost(host);
    setProblem(complaint);
    if (complaint) return;
    connect(host);
  }

  const busy = connection.phase === 'connecting' || connection.phase === 'waiting';

  return (
    <Screen title="Peyara" subtitle="Remote mouse and keyboard for your computer.">
      <Card>
        <View style={styles.rowBetween}>
          <Text style={styles.heading}>Relay status</Text>
          <Pill label={connection.label} tone={connection.connected ? 'ok' : 'warn'} />
        </View>
        <Text style={styles.body}>{connection.message}</Text>
        {connection.attempt > 0 && connection.phase === 'waiting' ? (
          <Text style={styles.meta}>Try {connection.attempt} of 5. The app keeps trying on its own.</Text>
        ) : null}
        <Text style={styles.meta}>Last event: {connection.lastEvent}</Text>
      </Card>

      <Card>
        <Field
          label="Computer address"
          value={host}
          onChangeText={(value) => {
            setHost(value);
            setProblem(null);
          }}
          autoCapitalize="none"
          placeholder="192.168.1.10:8765"
        />
        {problem ? <Text style={styles.problem}>{problem}</Text> : null}
        <View style={styles.buttons}>
          <Button label={busy ? 'Connecting…' : 'Connect'} onPress={start} disabled={busy} />
          <Button label="Disconnect" kind="ghost" onPress={disconnect} disabled={connection.phase === 'idle' || connection.phase === 'closed'} />
        </View>
      </Card>

      <Card>
        <Text style={styles.heading}>Setup</Text>
        <Text style={styles.body}>1. Run `cd server && npm install && npm start` on the computer.</Text>
        <Text style={styles.body}>2. Find the computer's LAN IP (for example `192.168.1.10`).</Text>
        <Text style={styles.body}>3. Enter `IP:8765` above and connect from the same Wi-Fi.</Text>
        <Text style={styles.body}>4. Without `robotjs`, events are only logged on the computer.</Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  heading: { fontWeight: '700', color: colors.ink, fontSize: 15 },
  body: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  meta: { color: colors.muted, fontSize: 11 },
  problem: { color: '#b42318', fontSize: 12 },
  buttons: { flexDirection: 'row', gap: 8 },
});
