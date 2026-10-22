import { useState } from 'react';
import { View, Text, TextInput, Pressable, StyleSheet } from 'react-native';
import { Screen, Card, Button } from '../components';
import { colors } from '../theme';
import { send, useConnectionStatus } from '../data';

const quickKeys = [
  { label: 'Enter', key: 'enter' },
  { label: 'Backspace', key: 'backspace' },
  { label: 'Tab', key: 'tab' },
  { label: 'Esc', key: 'escape' },
];

export default function KeyboardScreen() {
  const connection = useConnectionStatus();
  const [text, setText] = useState('');

  function sendText() {
    if (!text.trim()) return;
    if (send({ type: 'text', text })) setText('');
  }

  return (
    <Screen
      title="Keyboard"
      subtitle={
        connection.connected
          ? 'Type and send to the computer.'
          : connection.phase === 'waiting'
            ? `Reconnecting (try ${connection.attempt})…`
            : 'Connect to send keys.'
      }
    >
      <Card>
        <TextInput
          value={text}
          onChangeText={setText}
          placeholder="Type something…"
          placeholderTextColor={colors.muted}
          style={styles.input}
          multiline
          onSubmitEditing={sendText}
        />
        <Button label="Send text" onPress={sendText} disabled={!connection.connected || !text.trim()} />
      </Card>

      <View style={styles.keys}>
        {quickKeys.map((item) => (
          <Pressable key={item.key} onPress={() => send({ type: 'key', key: item.key })} disabled={!connection.connected} style={styles.key}>
            <Text style={styles.keyText}>{item.label}</Text>
          </Pressable>
        ))}
      </View>

      <Text style={styles.meta}>
        Text is typed with `robotjs.typeString` when available. Special keys map to
        enter, backspace, tab and escape.
      </Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  input: { borderWidth: 1, borderColor: colors.line, borderRadius: 9, padding: 11, minHeight: 80, textAlignVertical: 'top', color: colors.ink },
  keys: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  key: { borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, borderRadius: 9, paddingVertical: 10, paddingHorizontal: 14 },
  keyText: { color: colors.ink, fontWeight: '600', fontSize: 13 },
  meta: { color: colors.muted, fontSize: 11, textAlign: 'center', lineHeight: 16 },
});
