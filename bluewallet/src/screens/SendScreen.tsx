import { useEffect, useState } from 'react';
import { View, Text, Alert, StyleSheet } from 'react-native';
import { Screen, Card, Button, Field } from '../components';
import { colors } from '../theme';
import { formatSats } from '../data';
import { useWallet } from '../walletContext';
import { isValidAddress } from '../address';

export default function SendScreen() {
  const { send, quoteFee } = useWallet();
  const [address, setAddress] = useState('');
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [fee, setFee] = useState(0);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    const sats = Number(amount);
    if (!Number.isFinite(sats) || sats <= 0) {
      setFee(0);
      return;
    }
    let cancelled = false;
    quoteFee(sats).then((value) => {
      if (!cancelled) setFee(value);
    });
    return () => {
      cancelled = true;
    };
  }, [amount, quoteFee]);

  async function onSend() {
    const sats = Number(amount);
    if (!isValidAddress(address.trim())) {
      setError('Enter a valid Bitcoin address.');
      return;
    }
    if (!Number.isInteger(sats) || sats <= 0) {
      setError('Enter an amount in satoshis.');
      return;
    }
    setError('');
    setSending(true);
    try {
      const id = await send(address.trim(), sats);
      setAddress('');
      setAmount('');
      setNote('');
      Alert.alert('Sent', `${formatSats(sats)} sats\n\nTransaction ${id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'The transaction could not be sent.');
    } finally {
      setSending(false);
    }
  }

  return (
    <Screen title="Send" subtitle="Build a transaction (simulation only).">
      <Card>
        <Field label="Destination address" value={address} onChangeText={setAddress} autoCapitalize="none" placeholder="bc1q…" />
        <Field label="Amount (sats)" value={amount} onChangeText={setAmount} keyboardType="number-pad" placeholder="25000" />
        <Field label="Note (optional)" value={note} onChangeText={setNote} placeholder="Split dinner" />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <View style={styles.feeRow}>
          <Text style={styles.feeLabel}>Estimated fee</Text>
          <Text style={styles.fee}>{fee > 0 ? `~ ${formatSats(fee)} sats` : '—'}</Text>
        </View>
        <Button label={sending ? 'Sending…' : 'Send payment'} onPress={onSend} disabled={sending} />
      </Card>

      <Card>
        <Text style={styles.heading}>What this screen does not do</Text>
        <Text style={styles.body}>
          The transaction is built from the wallet's unspent outputs, the fee is
          estimated from its size and the address is validated against the
          bech32 rules. Signing and broadcasting need a real Electrum server
          and the device's key material, so the demo wallet records the payment
          locally instead.
        </Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  error: { color: colors.danger, fontSize: 12, marginBottom: 8 },
  feeRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
  feeLabel: { color: colors.muted, fontSize: 12 },
  fee: { color: colors.ink, fontSize: 12, fontWeight: '700' },
  heading: { fontWeight: '700', color: colors.ink },
  body: { color: colors.muted, fontSize: 13, lineHeight: 19 },
});
