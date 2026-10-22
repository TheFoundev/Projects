import { useState } from 'react';
import { View, Text, StyleSheet, Clipboard } from 'react-native';
import { Screen, Card, Button, Pill } from '../components';
import { colors } from '../theme';
import { wallet } from '../data';

export default function ReceiveScreen() {
  const [copied, setCopied] = useState(false);

  function copy() {
    Clipboard.setString(wallet.address);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <Screen title="Receive" subtitle="Share this address to receive bitcoin.">
      <Card style={{ alignItems: 'center', gap: 12 }}>
        <View style={styles.qr}>
          <Text style={styles.qrText}>QR</Text>
          <Text style={styles.qrHint}>placeholder</Text>
        </View>
        <Pill label="demo address" tone="warn" />
        <Text selectable style={styles.address}>{wallet.address}</Text>
        <Button label={copied ? 'Copied' : 'Copy address'} onPress={copy} />
      </Card>

      <Card>
        <Text style={styles.heading}>Before you use this</Text>
        <Text style={styles.body}>
          This address is a placeholder generated for the demo. Any real wallet
          would show a fresh receive address from the device's key material and
          verify it on screen before use.
        </Text>
      </Card>

      <Card>
        <Text style={styles.heading}>Address type</Text>
        <Text style={styles.body}>Native SegWit (bech32) · Bitcoin mainnet placeholder</Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  qr: { width: 150, height: 150, borderRadius: 12, borderWidth: 2, borderColor: colors.ink, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg },
  qrText: { fontSize: 34, fontWeight: '800', color: colors.ink },
  qrHint: { fontSize: 11, color: colors.muted },
  address: { fontSize: 12, color: colors.ink, textAlign: 'center', lineHeight: 18 },
  heading: { fontWeight: '700', color: colors.ink },
  body: { color: colors.muted, fontSize: 13, lineHeight: 19 },
});
