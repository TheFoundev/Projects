export type Repo = {
  id: string;
  name: string;
  description: string;
  language: string;
  stars: number;
  forks: number;
  updated: string;
};

export type Issue = {
  id: string;
  repo: string;
  number: number;
  title: string;
  state: 'open' | 'closed';
  labels: string[];
  comments: number;
  author: string;
};

export const repos: Repo[] = [
  { id: 'r1', name: 'campus-map', description: 'A small map of buildings, labs and quiet study spots.', language: 'TypeScript', stars: 84, forks: 12, updated: '2 hours ago' },
  { id: 'r2', name: 'sensor-logger', description: 'Arduino sketch and Python parser for a lab temperature sensor.', language: 'Python', stars: 37, forks: 6, updated: 'yesterday' },
  { id: 'r3', name: 'notes-cli', description: 'A command-line notes tool that stores markdown files in a folder.', language: 'Go', stars: 126, forks: 19, updated: '3 days ago' },
  { id: 'r4', name: 'timeline-ui', description: 'Experiment with animated timelines for a history class project.', language: 'JavaScript', stars: 21, forks: 2, updated: 'last week' },
];

export const issues: Issue[] = [
  { id: 'i1', repo: 'campus-map', number: 42, title: 'Labels overlap at low zoom levels', state: 'open', labels: ['bug', 'ui'], comments: 5, author: 'mina' },
  { id: 'i2', repo: 'campus-map', number: 39, title: 'Add accessible route option', state: 'open', labels: ['enhancement', 'a11y'], comments: 8, author: 'devon' },
  { id: 'i3', repo: 'sensor-logger', number: 17, title: 'Parser fails when the timestamp is missing', state: 'open', labels: ['bug'], comments: 2, author: 'ari' },
  { id: 'i4', repo: 'notes-cli', number: 11, title: 'Support nested tags', state: 'closed', labels: ['feature'], comments: 4, author: 'you' },
  { id: 'i5', repo: 'timeline-ui', number: 6, title: 'Reduce animation jank on older phones', state: 'open', labels: ['performance'], comments: 3, author: 'sam' },
];

export const profile = {
  name: 'Alex Rivera',
  handle: 'alexr-dev',
  bio: 'Third-year software engineering student. Mostly TypeScript and Python, currently learning Go.',
  location: 'Waterloo, Canada',
  followers: 74,
  following: 51,
  repos: 18,
  contributions: 642,
};
