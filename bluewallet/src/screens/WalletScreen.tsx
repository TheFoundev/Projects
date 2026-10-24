import { useState } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Screen, Card, Pill, Button } from '../components';
import { colors } from '../theme';
import { formatSats, satsToBtc } from '../data';
import { useWallet } from '../walletContext';

export default function WalletScreen() {
  const { core, balance, transactions } = useWallet();
  const [hidden, setHidden] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const total = balance.confirmed + balance.unconfirmed;

  function sync() {
    setSyncing(true);
    setTimeout(() => setSyncing(false), 900);
  }

  return (
    <Screen title={core.name} subtitle="Bitcoin balance and recent activity.">
      <Card style={styles.balanceCard}>
        <View style={styles.balanceTop}>
          <Text style={styles.balanceLabel}>Balance</Text>
          <Pressable onPress={() => setHidden((value) => !value)}>
            <Text style={styles.eye}>{hidden ? 'show' : 'hide'}</Text>
          </Pressable>
        </View>
        <Text style={styles.balance}>{hidden ? '•••••• sats' : `${formatSats(total)} sats`}</Text>
        <Text style={styles.btc}>{hidden ? '•••••••• BTC' : `${satsToBtc(total)} BTC`}</Text>
        <Button label={syncing ? 'Syncing…' : 'Sync wallet'} kind="ghost" onPress={sync} disabled={syncing} />
      </Card>

      <View style={styles.disclaimer}>
        <Text style={styles.disclaimerText}>
          Demo wallet. The balance is the sum of the transactions below; no keys
          exist and nothing is signed or broadcast unless a real Electrum server
          is configured.
        </Text>
      </View>

      <Text style={styles.section}>Recent transactions</Text>
      {transactions.map((tx) => (
        <Card key={tx.id} style={styles.tx}>
          <View style={styles.txIcon}><Text style={{ color: tx.type === 'received' ? colors.ok : colors.danger }}>{tx.type === 'received' ? '↓' : '↑'}</Text></View>
          <View style={{ flex: 1 }}>
            <Text style={styles.txTitle}>{tx.type === 'received' ? 'Received' : 'Sent'}</Text>
            <Text style={styles.txMeta}>{tx.counterparty} · {tx.date}</Text>
          </View>
          <View style={{ alignItems: 'flex-end' }}>
            <Text style={[styles.amount, { color: tx.type === 'received' ? colors.ok : colors.ink }]}>
              {tx.type === 'received' ? '+' : '-'}{formatSats(tx.amountSats)}
            </Text>
            <Pill label={tx.status} tone={tx.status === 'confirmed' ? 'ok' : 'warn'} />
          </View>
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  balanceCard: { backgroundColor: colors.brand, borderColor: colors.brand, gap: 4 },
  balanceTop: { flexDirection: 'row', justifyContent: 'space-between' },
  balanceLabel: { color: '#fffbeb', fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.6 },
  eye: { color: '#fffbeb', fontSize: 12, fontWeight: '700' },
  balance: { color: '#fff', fontSize: 30, fontWeight: '800', marginTop: 4 },
  btc: { color: '#fef3c7', fontSize: 13, marginBottom: 8 },
  disclaimer: { backgroundColor: '#fffbeb', borderWidth: 1, borderColor: '#fde68a', borderRadius: 10, padding: 10 },
  disclaimerText: { color: '#92400e', fontSize: 12, lineHeight: 17 },
  section: { fontWeight: '700', color: colors.ink, marginTop: 4 },
  tx: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  txIcon: { width: 30, height: 30, borderRadius: 15, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center' },
  txTitle: { fontWeight: '700', color: colors.ink, fontSize: 14 },
  txMeta: { color: colors.muted, fontSize: 11 },
  amount: { fontWeight: '700', fontSize: 13 },
});
