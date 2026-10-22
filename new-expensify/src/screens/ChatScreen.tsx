import { useState } from 'react';
import { View, Text, TextInput, Pressable, StyleSheet } from 'react-native';
import { Screen, Card } from '../components';
import { colors } from '../theme';
import { initialMessages, Message } from '../data';

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [draft, setDraft] = useState('');

  function send() {
    const body = draft.trim();
    if (!body) return;
    setMessages([...messages, { id: `m-${Date.now()}`, sender: 'You', body, time: 'now', mine: true }]);
    setDraft('');
  }

  return (
    <Screen title="Team chat" subtitle="#finance-help">
      <Card style={{ gap: 10 }}>
        {messages.map((message) => (
          <View key={message.id} style={[styles.message, message.mine && styles.mine]}>
            <Text style={styles.sender}>{message.sender}</Text>
            <Text style={styles.body}>{message.body}</Text>
            <Text style={styles.time}>{message.time}</Text>
          </View>
        ))}
      </Card>
      <View style={styles.composer}>
        <TextInput
          value={draft}
          onChangeText={setDraft}
          placeholder="Message the team"
          placeholderTextColor={colors.muted}
          style={styles.input}
          onSubmitEditing={send}
        />
        <Pressable onPress={send} style={styles.send}><Text style={styles.sendText}>Send</Text></Pressable>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  message: { backgroundColor: colors.bg, borderRadius: 11, padding: 10, maxWidth: '90%' },
  mine: { alignSelf: 'flex-end', backgroundColor: colors.soft },
  sender: { color: colors.brand, fontSize: 11, fontWeight: '700' },
  body: { color: colors.ink, fontSize: 13, lineHeight: 18, marginTop: 2 },
  time: { color: colors.muted, fontSize: 10, marginTop: 3, alignSelf: 'flex-end' },
  composer: { flexDirection: 'row', gap: 8 },
  input: { flex: 1, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, borderRadius: 9, paddingHorizontal: 11, color: colors.ink },
  send: { backgroundColor: colors.brand, borderRadius: 9, paddingHorizontal: 16, justifyContent: 'center' },
  sendText: { color: '#fff', fontWeight: '700', fontSize: 13 },
});
