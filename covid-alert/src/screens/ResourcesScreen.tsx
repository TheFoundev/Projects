import { View, Text, StyleSheet, Linking, Pressable } from 'react-native';
import { Screen, Card, Pill } from '../components';
import { colors } from '../theme';
import { resources } from '../data';

export default function ResourcesScreen() {
  return (
    <Screen title="Resources" subtitle="Where to get real help.">
      <Card>
        <Text style={styles.heading}>If this is an emergency</Text>
        <Text style={styles.body}>Call 911 (or your local emergency number) for severe breathing difficulty or chest pain.</Text>
      </Card>
      {resources.map((item) => (
        <Pressable key={item.name} onPress={() => item.detail.includes('1-') ? Linking.openURL(`tel:${item.detail.split(' ')[0]}`) : null}>
          <Card>
            <View style={styles.rowBetween}>
              <Text style={styles.name}>{item.name}</Text>
              <Pill label={item.detail.includes('1-') ? 'call' : 'info'} />
            </View>
            <Text style={styles.body}>{item.detail}</Text>
          </Card>
        </Pressable>
      ))}
      <Text style={styles.footnote}>Resources are placeholders for the demo. Use your local health authority's official numbers.</Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  heading: { fontWeight: '700', color: colors.ink, fontSize: 15 },
  body: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  name: { fontWeight: '700', color: colors.ink, fontSize: 14 },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  footnote: { color: colors.muted, fontSize: 11, lineHeight: 16, textAlign: 'center' },
});
