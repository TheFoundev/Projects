/**
 * The protocol between the phone and the relay.
 *
 * Pure functions, no imports, so both halves of the app (the Expo client and
 * the Node relay) can be tested without a React Native or a network.
 */

export type RelayEvent =
  | { type: 'move'; dx: number; dy: number }
  | { type: 'click'; button: 'left' | 'right' }
  | { type: 'scroll'; dy: number }
  | { type: 'text'; text: string }
  | { type: 'key'; key: string };

export type EventType = RelayEvent['type'];

/** The events the relay understands. */
export const EVENT_TYPES: EventType[] = ['move', 'click', 'scroll', 'text', 'key'];

/** The special keys the relay can press. */
export const SPECIAL_KEYS = ['enter', 'backspace', 'tab', 'escape'];

/** The longest text the relay accepts in one message. */
export const MAX_TEXT_LENGTH = 4096;

/** The result of decoding a message that came from the phone. */
export type ParseResult =
  | { ok: true; event: RelayEvent }
  | { ok: false; error: string };

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

/** Decode and validate a message that came from the phone. */
export function parseEvent(raw: unknown): ParseResult {
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    return { ok: false, error: 'the message is not an object' };
  }
  const message = raw as Record<string, unknown>;
  const type = message.type;
  if (typeof type !== 'string' || !EVENT_TYPES.includes(type as EventType)) {
    return { ok: false, error: `unknown event type: ${String(type)}` };
  }

  switch (type as EventType) {
    case 'move': {
      if (!isFiniteNumber(message.dx) || !isFiniteNumber(message.dy)) {
        return { ok: false, error: 'a move needs the numbers dx and dy' };
      }
      return {
        ok: true,
        event: {
          type: 'move',
          dx: clamp(message.dx),
          dy: clamp(message.dy),
        },
      };
    }
    case 'click': {
      const button = message.button ?? 'left';
      if (button !== 'left' && button !== 'right') {
        return { ok: false, error: `unknown mouse button: ${String(button)}` };
      }
      return { ok: true, event: { type: 'click', button } };
    }
    case 'scroll': {
      if (!isFiniteNumber(message.dy)) {
        return { ok: false, error: 'a scroll needs the number dy' };
      }
      return { ok: true, event: { type: 'scroll', dy: clamp(message.dy) } };
    }
    case 'text': {
      if (typeof message.text !== 'string') {
        return { ok: false, error: 'a text event needs the string text' };
      }
      if (message.text.length > MAX_TEXT_LENGTH) {
        return { ok: false, error: 'the text is too long' };
      }
      return { ok: true, event: { type: 'text', text: message.text } };
    }
    case 'key': {
      if (typeof message.key !== 'string' || message.key.length === 0) {
        return { ok: false, error: 'a key event needs the name of the key' };
      }
      return { ok: true, event: { type: 'key', key: message.key.toLowerCase() } };
    }
    default:
      return { ok: false, error: `unknown event type: ${type}` };
  }
}

/** Encode an event for the wire. */
export function encodeEvent(event: RelayEvent): string {
  return JSON.stringify(event);
}

/** Decode a message that arrived as text. */
export function decodeMessage(data: unknown): ParseResult {
  if (typeof data !== 'string') {
    return { ok: false, error: 'the message is not text' };
  }
  try {
    return parseEvent(JSON.parse(data));
  } catch {
    return { ok: false, error: 'the message is not valid JSON' };
  }
}

/** Keep the numbers small enough to be safe to send to the computer. */
export function clamp(value: number, limit = 2000): number {
  if (value > limit) return limit;
  if (value < -limit) return -limit;
  return Math.round(value);
}

/** The URL of the relay for the address the user typed. */
export function relayUrl(host: string): string {
  const trimmed = host.trim();
  if (trimmed.startsWith('ws://') || trimmed.startsWith('wss://')) return trimmed;
  return `ws://${trimmed}`;
}

/** The problem with the address the user typed, or null when it is fine. */
export function validateHost(host: string): string | null {
  const trimmed = host.trim();
  if (!trimmed) return 'Enter the address of the computer.';
  const url = relayUrl(trimmed);
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return 'That is not a valid address.';
  }
  if (!parsed.hostname) return 'That is not a valid address.';
  return null;
}
