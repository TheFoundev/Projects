import { useRef } from 'react';
import { View, Text, PanResponder, StyleSheet } from 'react-native';
import { Screen, Button } from '../components';
import { colors } from '../theme';
import { send, useConnectionStatus } from '../data';

export default function TouchpadScreen() {
  const connection = useConnectionStatus();
  const last = useRef({ x: 0, y: 0 });

  const responder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (_, gesture) => {
        last.current = { x: gesture.x0, y: gesture.y0 };
      },
      onPanResponderMove: (_, gesture) => {
        const dx = gesture.moveX - last.current.x;
        const dy = gesture.moveY - last.current.y;
        if (Math.abs(dx) + Math.abs(dy) > 1) {
          send({ type: 'move', dx: Math.round(dx), dy: Math.round(dy) });
          last.current = { x: gesture.moveX, y: gesture.moveY };
        }
      },
    })
  ).current;

  return (
    <Screen
      title="Touchpad"
      subtitle={
        connection.connected
          ? 'Connected — drag to move.'
          : connection.phase === 'waiting'
            ? `Reconnecting (try ${connection.attempt})…`
            : 'Connect first, then drag.'
      }
    >
      <View style={styles.pad} {...responder.panHandlers}>
        <Text style={styles.padText}>drag here</Text>
        <Text style={styles.padHint}>movement is sent as small dx/dy events</Text>
      </View>
      <View style={styles.row}>
        <Button label="Left click" onPress={() => send({ type: 'click', button: 'left' })} disabled={!connection.connected} />
        <Button label="Right click" kind="ghost" onPress={() => send({ type: 'click', button: 'right' })} disabled={!connection.connected} />
      </View>
      <View style={styles.row}>
        <Button label="Scroll up" kind="ghost" onPress={() => send({ type: 'scroll', dy: -3 })} disabled={!connection.connected} />
        <Button label="Scroll down" kind="ghost" onPress={() => send({ type: 'scroll', dy: 3 })} disabled={!connection.connected} />
      </View>
      <Text style={styles.meta}>Sensitivity is fixed at 1.5× on the relay. Adjust `server/index.js` to taste.</Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  pad: {
    height: 300, borderRadius: 18, borderWidth: 2, borderStyle: 'dashed', borderColor: colors.brand,
    backgroundColor: colors.soft, alignItems: 'center', justifyContent: 'center', gap: 6,
  },
  padText: { color: colors.brand, fontWeight: '800', fontSize: 20 },
  padHint: { color: colors.muted, fontSize: 11 },
  row: { flexDirection: 'row', gap: 8 },
  meta: { color: colors.muted, fontSize: 11, textAlign: 'center' },
});
