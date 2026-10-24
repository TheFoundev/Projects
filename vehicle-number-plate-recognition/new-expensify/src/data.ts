export type Expense = { id: string; title: string; amount: number; date: string; category: string };
export type Report = { id: string; title: string; status: 'draft' | 'submitted' | 'approved'; currency: string; expenses: Expense[] };
export type Message = { id: string; sender: string; body: string; time: string; mine?: boolean };

export const reports: Report[] = [
  {
    id: 'rep1', title: 'Client visit — Montreal', status: 'submitted', currency: 'CAD',
    expenses: [
      { id: 'e1', title: 'Train ticket', amount: 96.4, date: 'Apr 21', category: 'Travel' },
      { id: 'e2', title: 'Hotel, one night', amount: 184.0, date: 'Apr 21', category: 'Lodging' },
      { id: 'e3', title: 'Team dinner', amount: 62.75, date: 'Apr 22', category: 'Meals' },
    ],
  },
  {
    id: 'rep2', title: 'Lab supplies', status: 'draft', currency: 'CAD',
    expenses: [
      { id: 'e4', title: 'USB-C cables (3)', amount: 27.99, date: 'Apr 18', category: 'Equipment' },
      { id: 'e5', title: 'Sensor kit', amount: 74.5, date: 'Apr 18', category: 'Equipment' },
    ],
  },
  {
    id: 'rep3', title: 'Conference — Toronto', status: 'approved', currency: 'CAD',
    expenses: [
      { id: 'e6', title: 'Registration', amount: 240.0, date: 'Mar 30', category: 'Events' },
      { id: 'e7', title: 'Transit', amount: 18.25, date: 'Mar 31', category: 'Travel' },
    ],
  },
];

export const initialMessages: Message[] = [
  { id: 'm1', sender: 'Priya', body: 'Did the Montreal receipts go through?', time: '09:12' },
  { id: 'm2', sender: 'You', body: 'Submitted last night. Waiting on approval.', time: '09:14', mine: true },
  { id: 'm3', sender: 'Jon', body: 'I can approve it after the 10am standup.', time: '09:18' },
  { id: 'm4', sender: 'Priya', body: 'Reminder: attach the train PDF next time, the photo was hard to read.', time: '09:21' },
];

export const settings = { name: 'Alex Rivera', email: 'alex@school.edu', currency: 'CAD', notifications: true };
