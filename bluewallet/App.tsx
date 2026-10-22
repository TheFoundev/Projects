import { useState } from 'react';
import { SafeAreaView, View, Text, Pressable, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { colors } from './src/theme';
import { WalletProvider } from './src/walletContext';
import WalletScreen from './src/screens/WalletScreen';
import ReceiveScreen from './src/screens/ReceiveScreen';
import SendScreen from './src/screens/SendScreen';

const TABS = [
  { key: 'wallet', label: 'Wallet', icon: '◉', component: WalletScreen },
  { key: 'receive', label: 'Receive', icon: '↓', component: ReceiveScreen },
  { key: 'send', label: 'Send', icon: '↑', component: SendScreen },
] as const;

export default function App() {
  const [active, setActive] = useState(TABS[0].key);
  const current = TABS.find((tab) => tab.key === active) ?? TABS[0];
  const Screen = current.component;

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="dark" />
      <View style={styles.body}>
        <WalletProvider>
          <Screen />
        </WalletProvider>
      </View>
      <View style={styles.tabBar}>
        {TABS.map((tab) => (
          <Pressable
            key={tab.key}
            onPress={() => setActive(tab.key)}
            style={[styles.tab, active === tab.key && styles.tabActive]}
          >
            <Text style={[styles.tabIcon, active === tab.key && styles.tabTextActive]}>{tab.icon}</Text>
            <Text style={[styles.tabText, active === tab.key && styles.tabTextActive]}>{tab.label}</Text>
          </Pressable>
        ))}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  body: { flex: 1 },
  tabBar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: colors.line,
    backgroundColor: colors.panel,
    paddingTop: 6,
    paddingBottom: 8,
  },
  tab: { flex: 1, alignItems: 'center', gap: 2, paddingVertical: 4 },
  tabActive: {},
  tabIcon: { fontSize: 18, color: colors.muted },
  tabText: { fontSize: 11, fontWeight: '600', color: colors.muted },
  tabTextActive: { color: colors.brand },
});
