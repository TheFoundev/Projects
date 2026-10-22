/**
 * The logic of the relay.
 *
 * The relay receives the events of the phone and turns them into actions on
 * the computer. The actions are executed with robotjs when it is installed;
 * when it is not, the relay logs them instead, so the protocol can still be
 * seen working.
 *
 * No `ws` and no `robotjs` import, so the whole module can be tested with
 * node's own test runner.
 */

/** The actions the relay understands. */
const ACTION_TYPES = ['move', 'click', 'scroll', 'text', 'key'];

/** The special keys robotjs can press. */
const SPECIAL_KEYS = {
  enter: 'enter',
  backspace: 'backspace',
  escape: 'escape',
  esc: 'escape',
  tab: 'tab',
};

/** How much the phone movement is multiplied by on the computer. */
const DEFAULT_SENSITIVITY = 1.5;

/**
 * The robotjs interface the relay uses.
 *
 * Only the four calls the relay needs, so a fake can be used in the tests.
 */
function robotAdapter(robot) {
  return {
    getMousePos() {
      return robot.getMousePos();
    },
    moveMouse(x, y) {
      robot.moveMouse(x, y);
    },
    mouseClick(button) {
      robot.mouseClick(button);
    },
    scrollMouse(horizontal, vertical) {
      robot.scrollMouse(horizontal, vertical);
    },
    typeString(text) {
      robot.typeString(text);
    },
    keyTap(key) {
      robot.keyTap(key);
    },
  };
}

/**
 * Turn a decoded event into the action the relay performs.
 *
 * Returns null when the event does not mean anything for the computer.
 */
function toAction(event, sensitivity) {
  switch (event.type) {
    case 'move': {
      const dx = Number(event.dx) || 0;
      const dy = Number(event.dy) || 0;
      return { type: 'move', dx: dx * sensitivity, dy: dy * sensitivity };
    }
    case 'click': {
      const button = event.button === 'right' ? 'right' : 'left';
      return { type: 'click', button };
    }
    case 'scroll': {
      const dy = Number(event.dy) || 0;
      return { type: 'scroll', horizontal: 0, dy };
    }
    case 'text': {
      const text = String(event.text ?? '');
      if (!text) return null;
      return { type: 'type', text };
    }
    case 'key': {
      const key = String(event.key ?? '').toLowerCase();
      const mapped = SPECIAL_KEYS[key] || key;
      return { type: 'key', key: mapped };
    }
    default:
      return null;
  }
}

/**
 * Create a relay.
 *
 * `robot` is the robotjs module or null. `logger` receives the lines the
 * relay would print.
 */
function createRelay(options = {}) {
  const logger = options.logger || console;
  const sensitivity = Number(options.sensitivity ?? DEFAULT_SENSITIVITY);
  const robot = options.robot ? robotAdapter(options.robot) : null;

  const state = {
    connected: 0,
    handled: 0,
    ignored: 0,
    invalid: 0,
  };

  /** Perform an action on the computer. */
  function perform(action) {
    if (!robot) {
      logger.log('event:', JSON.stringify(action));
      return false;
    }
    switch (action.type) {
      case 'move': {
        const point = robot.getMousePos();
        robot.moveMouse(point.x + action.dx, point.y + action.dy);
        return true;
      }
      case 'click':
        robot.mouseClick(action.button);
        return true;
      case 'scroll':
        robot.scrollMouse(action.horizontal, action.dy);
        return true;
      case 'type':
        robot.typeString(action.text);
        return true;
      case 'key':
        robot.keyTap(action.key);
        return true;
      default:
        return false;
    }
  }

  /**
   * Handle one message of the phone.
   *
   * Returns what happened, so the tests can check it and the server can log
   * it.
   */
  function handleMessage(raw) {
    let event;
    try {
      event = JSON.parse(String(raw));
    } catch {
      state.invalid += 1;
      logger.log('ignored invalid message');
      return { status: 'invalid', reason: 'the message is not valid JSON' };
    }

    if (typeof event !== 'object' || event === null || !ACTION_TYPES.includes(event.type)) {
      state.ignored += 1;
      logger.log('ignored unsupported event');
      return { status: 'ignored', reason: `unsupported event: ${String(event && event.type)}` };
    }

    const action = toAction(event, sensitivity);
    if (!action) {
      state.ignored += 1;
      return { status: 'ignored', reason: 'the event means nothing to perform' };
    }

    state.handled += 1;
    const performed = perform(action);
    return { status: 'ok', action, performed };
  }

  /** A phone connected to the relay. */
  function onConnection() {
    state.connected += 1;
    logger.log('phone connected');
  }

  /** A phone left the relay. */
  function onDisconnection() {
    logger.log('phone disconnected');
  }

  /** The counters of the relay, for the status line. */
  function stats() {
    return { ...state };
  }

  /** True when the relay can move the real cursor. */
  function hasRobot() {
    return robot !== null;
  }

  return { handleMessage, onConnection, onDisconnection, stats, hasRobot, perform };
}

module.exports = { createRelay, toAction, DEFAULT_SENSITIVITY };
