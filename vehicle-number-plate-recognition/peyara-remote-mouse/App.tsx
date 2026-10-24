import { useState } from 'react';
import { SafeAreaView, View, Text, Pressable, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { colors } from './src/theme';
import ConnectScreen from './src/screens/ConnectScreen';
import TouchpadScreen from './src/screens/TouchpadScreen';
import KeyboardScreen from './src/screens/KeyboardScreen';

const TABS = [
  { key: 'connect', label: 'Connect', icon: '◈', component: ConnectScreen },
  { key: 'touchpad', label: 'Touchpad', icon: '▭', component: TouchpadScreen },
  { key: 'keyboard', label: 'Keyboard', icon: '⌨', component: KeyboardScreen },
] as const;

export default function App() {
  const [active, setActive] = useState<(typeof TABS)[number]['key']>(TABS[0].key);
  const current = TABS.find((tab) => tab.key === active) ?? TABS[0];
  const Screen = current.component;

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="dark" />
      <View style={styles.body}>
        <Screen />
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
