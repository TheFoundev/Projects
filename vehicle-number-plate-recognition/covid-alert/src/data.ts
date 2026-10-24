import type { Check } from './exposure';

export type { Check };

export const initialChecks: Check[] = [
  {
    id: 'c1',
    date: 'Apr 23, 08:10',
    checkedAt: '2024-04-23T08:10:00.000Z',
    result: 'clear',
    note: 'No matching codes in the last 14 days.',
    source: 'simulated',
  },
  {
    id: 'c2',
    date: 'Apr 20, 19:42',
    checkedAt: '2024-04-20T19:42:00.000Z',
    result: 'clear',
    note: 'No matching codes in the last 14 days.',
    source: 'simulated',
  },
  {
    id: 'c3',
    date: 'Apr 16, 07:55',
    checkedAt: '2024-04-16T07:55:00.000Z',
    result: 'clear',
    note: 'No matching codes in the last 14 days.',
    source: 'simulated',
  },
];

export const symptomItems = [
  { id: 'fever', label: 'Fever or chills' },
  { id: 'cough', label: 'New or worsening cough' },
  { id: 'breath', label: 'Shortness of breath' },
  { id: 'taste', label: 'Loss of taste or smell' },
  { id: 'throat', label: 'Sore throat' },
  { id: 'fatigue', label: 'Unusual fatigue' },
];

export const resources = [
  { name: 'Local public health line', detail: '1-800-555-0199 · 8:00–20:00 daily' },
  { name: 'Emergency services', detail: '911 for severe breathing difficulty' },
  { name: 'Vaccination info', detail: 'Book through your provincial health portal' },
  { name: 'Mental health support', detail: '1-866-555-0142 · free and confidential' },
];
