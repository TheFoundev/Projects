import { useState } from 'react';
import { View, Text, TextInput, Pressable, StyleSheet } from 'react-native';
import { Screen, Card, Pill } from '../components';
import { colors } from '../theme';
import { useChat } from '../chatContext';
import { messagesOf } from '../chat';

export default function ChatScreen() {
  const { channels, messages, connection, error, send, reconnect } = useChat();
  const [active, setActive] = useState('general');
  const [draft, setDraft] = useState('');
  const channel = channels.find((item) => item.id === active) ?? channels[0];
  const visible = messagesOf(messages, active);

  function onSend() {
    const body = draft.trim();
    if (!body) return;
    send(active, body);
    setDraft('');
  }

  return (
    <Screen title={`# ${channel.name}`} subtitle={channel.topic}>
      <View style={styles.tabs}>
        {channels.map((item) => (
          <Pressable key={item.id} onPress={() => setActive(item.id)}>
            <Pill label={item.name} tone={active === item.id ? 'brand' : 'default'} />
          </Pressable>
        ))}
      </View>

      {connection !== 'connected' ? (
        <Text style={styles.body}>
          {error ? `${error} ` : 'Offline: showing the saved messages. '}
          <Text onPress={reconnect}>Try again</Text>
        </Text>
      ) : null}

      <Card style={{ gap: 9 }}>
        {visible.map((message) => (
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
          placeholder={`Message #${channel.name}`}
          placeholderTextColor={colors.muted}
          style={styles.input}
          onSubmitEditing={onSend}
        />
        <Pressable onPress={onSend} style={styles.send}><Text style={styles.sendText}>Send</Text></Pressable>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  tabs: { flexDirection: 'row', gap: 6, flexWrap: 'wrap' },
  message: { backgroundColor: colors.bg, borderRadius: 11, padding: 10, maxWidth: '91%' },
  mine: { alignSelf: 'flex-end', backgroundColor: colors.soft },
  sender: { color: colors.brand, fontSize: 11, fontWeight: '700' },
  body: { color: colors.ink, fontSize: 13, lineHeight: 18, marginTop: 2 },
  time: { color: colors.muted, fontSize: 10, marginTop: 3, alignSelf: 'flex-end' },
  composer: { flexDirection: 'row', gap: 8 },
  input: { flex: 1, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, borderRadius: 9, paddingHorizontal: 11, color: colors.ink },
  send: { backgroundColor: colors.brand, borderRadius: 9, paddingHorizontal: 16, justifyContent: 'center' },
  sendText: { color: '#fff', fontWeight: '700', fontSize: 13 },
});
