export type Channel = { id: string; name: string; topic: string; unread: number; members: number; private?: boolean };
export type ChatMessage = { id: string; channelId: string; sender: string; body: string; time: string; mine?: boolean };

export const channels: Channel[] = [
  { id: 'general', name: 'general', topic: 'Announcements and everyday questions', unread: 2, members: 38 },
  { id: 'engineering', name: 'engineering', topic: 'Builds, incidents and code review', unread: 0, members: 14 },
  { id: 'design', name: 'design', topic: 'Screens, critique and usability notes', unread: 1, members: 9, private: true },
];

export const initialMessages: ChatMessage[] = [
  { id: 'm1', channelId: 'general', sender: 'Priya', body: 'Welcome to the new workspace. The old server is read-only from today.', time: '08:40' },
  { id: 'm2', channelId: 'general', sender: 'Jon', body: 'I moved the onboarding docs into the wiki. Link is pinned.', time: '08:52' },
  { id: 'm3', channelId: 'engineering', sender: 'Alex', body: 'The cache fix is on staging. Build time dropped by half.', time: '09:12' },
  { id: 'm4', channelId: 'engineering', sender: 'Sam', body: 'Nice. I will run the load test after lunch and post numbers.', time: '09:18' },
  { id: 'm5', channelId: 'design', sender: 'Mina', body: 'Empty states: one sentence of orientation and one action. That is the whole rule.', time: '10:02' },
  { id: 'm6', channelId: 'design', sender: 'You', body: 'Agreed. I will update the settings screen this afternoon.', time: '10:05', mine: true },
];

export const profile = {
  name: 'Alex Rivera',
  handle: 'alex.r',
  status: 'online',
  server: 'chat.school.example',
  role: 'member',
};
