import { ReactNode, ComponentProps } from 'react';
import { View, Text, Pressable, ScrollView, StyleSheet, TextInput } from 'react-native';
import { colors, spacing } from './theme';

export function Screen({ title, subtitle, children, action }: {
  title: string; subtitle?: string; children: ReactNode; action?: ReactNode;
}) {
  return (
    <ScrollView contentContainerStyle={styles.screen} keyboardShouldPersistTaps="handled">
      <View style={styles.head}>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{title}</Text>
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        </View>
        {action}
      </View>
      {children}
    </ScrollView>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: object }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Pill({ label, tone = 'default' }: { label: string; tone?: 'default' | 'brand' | 'ok' | 'warn' }) {
  const toneStyle = tone === 'brand' ? styles.pillBrand : tone === 'ok' ? styles.pillOk : tone === 'warn' ? styles.pillWarn : null;
  return <View style={[styles.pill, toneStyle]}><Text style={styles.pillText}>{label}</Text></View>;
}

export function Button({ label, onPress, kind = 'primary', disabled }: {
  label: string; onPress: () => void; kind?: 'primary' | 'ghost'; disabled?: boolean;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.button,
        kind === 'ghost' ? styles.ghost : styles.primary,
        pressed && { opacity: 0.8 },
        disabled && { opacity: 0.4 },
      ]}
    >
      <Text style={kind === 'ghost' ? styles.ghostText : styles.primaryText}>{label}</Text>
    </Pressable>
  );
}

export function Field({ label, ...props }: { label: string } & ComponentProps<typeof TextInput>) {
  return (
    <View style={{ gap: 5, marginBottom: spacing.md }}>
      <Text style={styles.label}>{label}</Text>
      <TextInput placeholderTextColor={colors.muted} style={styles.input} {...props} />
    </View>
  );
}

export function Empty({ title, body }: { title: string; body: string }) {
  return <Card style={{ alignItems: 'center', paddingVertical: 30 }}><Text style={styles.emptyTitle}>{title}</Text><Text style={styles.subtitle}>{body}</Text></Card>;
}

const styles = StyleSheet.create({
  screen: { padding: spacing.lg, paddingBottom: 40, gap: spacing.md },
  head: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 2 },
  title: { fontSize: 26, fontWeight: '800', color: colors.ink, letterSpacing: -0.6 },
  subtitle: { color: colors.muted, fontSize: 13, lineHeight: 19, marginTop: 3 },
  card: { backgroundColor: colors.panel, borderRadius: 14, borderWidth: 1, borderColor: colors.line, padding: spacing.md, gap: 8 },
  pill: { alignSelf: 'flex-start', backgroundColor: colors.bg, borderRadius: 999, paddingHorizontal: 8, paddingVertical: 2, borderWidth: 1, borderColor: colors.line },
  pillBrand: { backgroundColor: colors.soft, borderColor: colors.brand },
  pillOk: { backgroundColor: '#ecfdf3', borderColor: '#abefc6' },
  pillWarn: { backgroundColor: '#fff7ed', borderColor: '#fed7aa' },
  pillText: { fontSize: 10, fontWeight: '700', color: colors.muted },
  button: { borderRadius: 10, paddingVertical: 11, paddingHorizontal: 14, alignItems: 'center' },
  primary: { backgroundColor: colors.brand },
  ghost: { backgroundColor: colors.panel, borderWidth: 1, borderColor: colors.line },
  primaryText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  ghostText: { color: colors.ink, fontWeight: '700', fontSize: 14 },
  label: { fontSize: 11, fontWeight: '700', color: colors.muted, textTransform: 'uppercase', letterSpacing: 0.4 },
  input: { borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, borderRadius: 9, paddingHorizontal: 11, paddingVertical: 9, fontSize: 15, color: colors.ink },
  emptyTitle: { fontSize: 16, fontWeight: '700', color: colors.ink },
});
