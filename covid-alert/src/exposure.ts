/**
 * The exposure check and the symptom model.
 *
 * Pure logic, no imports, so it can be unit tested without a React Native
 * runtime.
 */

export type Check = {
  id: string;
  /** The stamp shown in the history, for example "Apr 23, 08:10". */
  date: string;
  /** The same moment as an ISO timestamp, so it can be compared reliably. */
  checkedAt: string;
  result: 'clear' | 'exposed';
  note: string;
  source: string;
};

export type ExposureResult = {
  status: 'clear' | 'exposed';
  checkedAt: string;
  source: string;
  detail: string;
};

/**
 * Where an exposure check comes from.
 *
 * The app ships with the simulated implementation. A real build would add an
 * implementation on top of the platform's exposure notification API without
 * changing anything above this line.
 */
export type ExposureService = {
  readonly name: string;
  check(): Promise<ExposureResult>;
};

/** The check the app runs when no platform API is available. */
export class SimulatedExposureService implements ExposureService {
  readonly name = 'simulated';
  private matches: number;
  private now: () => Date;

  constructor(matches = 0, now: () => Date = () => new Date()) {
    this.matches = matches;
    this.now = now;
  }

  async check(): Promise<ExposureResult> {
    const checkedAt = this.now().toISOString();
    if (this.matches > 0) {
      return {
        status: 'exposed',
        checkedAt,
        source: this.name,
        detail: `${this.matches} matching code${this.matches === 1 ? '' : 's'} in the last 14 days.`,
      };
    }
    return {
      status: 'clear',
      checkedAt,
      source: this.name,
      detail: 'No matching codes in the last 14 days.',
    };
  }
}

/** The format the check history uses. */
export function formatCheckStamp(date: Date): string {
  const day = date.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
  const time = date.toLocaleTimeString('en-CA', { hour: '2-digit', minute: '2-digit' });
  return `${day}, ${time}`;
}

/** The result of an exposure check, as it is stored in the history. */
export function toCheck(result: ExposureResult, id: string): Check {
  return {
    id,
    date: formatCheckStamp(new Date(result.checkedAt)),
    checkedAt: result.checkedAt,
    result: result.status,
    note: result.detail,
    source: result.source,
  };
}

/** The most recent check, or null when there is none. */
export function lastCheck(checks: Check[]): Check | null {
  return checks.length > 0 ? checks[0] : null;
}

/**
 * How many days until the next check is due.
 *
 * Returns null when there is no check yet, or when the last check is already
 * older than the interval.
 */
export function nextCheckDue(checks: Check[], intervalDays = 1): number | null {
  const latest = lastCheck(checks);
  if (!latest) return null;
  // The ISO timestamp is used when it is there; the display stamp is the
  // fallback for rows written by an older version.
  const stamp = latest.checkedAt ? Date.parse(latest.checkedAt) : Date.parse(latest.date);
  if (Number.isNaN(stamp)) return null;
  const elapsedDays = (Date.now() - stamp) / 86_400_000;
  const remaining = intervalDays - elapsedDays;
  return remaining > 0 ? Math.ceil(remaining) : null;
}

// ---------------------------------------------------------------------------
// The symptom checklist
// ---------------------------------------------------------------------------

/** How much each symptom counts towards the risk score. */
export const SYMPTOM_WEIGHTS: Record<string, number> = {
  fever: 3,
  cough: 2,
  breath: 3,
  taste: 2,
  throat: 1,
  fatigue: 1,
};

export type RiskLevel = 'low' | 'moderate' | 'high';

export type RiskAssessment = {
  score: number;
  level: RiskLevel;
  advice: string;
};

/**
 * Turn the ticked symptoms into a risk score.
 *
 * The score is the sum of the weights of the ticked symptoms. Three points
 * or more is a high risk, two is moderate and anything below that is low.
 */
export function assessSymptoms(selected: string[]): RiskAssessment {
  const unique = [...new Set(selected)];
  const score = unique.reduce((sum, id) => sum + (SYMPTOM_WEIGHTS[id] ?? 0), 0);

  if (score >= 3) {
    return {
      score,
      level: 'high',
      advice: 'Contact a health professional today. Call emergency services for severe breathing difficulty.',
    };
  }
  if (score === 2) {
    return {
      score,
      level: 'moderate',
      advice: 'Stay home, avoid close contact and get tested. Call a health professional if it gets worse.',
    };
  }
  return {
    score,
    level: 'low',
    advice: 'Keep watching your symptoms. This is not a diagnosis and not medical advice.',
  };
}

/** The disclaimer shown with every assessment. */
export const DISCLAIMER =
  'This is a demo, not a medical device. It does not diagnose anything and it is not medical advice.';
