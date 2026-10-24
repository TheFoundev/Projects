export type Post = {
  id: string;
  author: string;
  handle: string;
  text: string;
  time: string;
  likes: number;
  replies: number;
  topic: string;
  mine?: boolean;
};

export const seedPosts: Post[] = [
  {
    id: 'p1',
    author: 'Mina Park',
    handle: 'mina.bsky.social',
    text: 'Spent the morning deleting features. The app is faster and the demo is finally easy to explain.',
    time: '12m',
    likes: 18,
    replies: 3,
    topic: 'buildinpublic',
  },
  {
    id: 'p2',
    author: 'Devon Reed',
    handle: 'devon.dev',
    text: 'Hot take: a README with a working quickstart is worth more than three architecture diagrams.',
    time: '48m',
    likes: 42,
    replies: 7,
    topic: 'engineering',
  },
  {
    id: 'p3',
    author: 'Ari Chen',
    handle: 'ari.codes',
    text: 'Tiny win: our first-year students shipped their class project to a real URL today. Nobody had to install anything.',
    time: '2h',
    likes: 31,
    replies: 2,
    topic: 'teaching',
  },
  {
    id: 'p4',
    author: 'You',
    handle: 'you.bsky.social',
    text: 'Testing a small feed client for a class project. Still deciding how much state belongs in the screens.',
    time: '3h',
    likes: 6,
    replies: 1,
    topic: 'buildinpublic',
    mine: true,
  },
];

export const suggestedFeeds = [
  { name: 'Build in public', description: 'Ship logs, small wins and honest postmortems.', members: '12.4k' },
  { name: 'Design critique', description: 'Screens, flows and typography with useful feedback.', members: '8.1k' },
  { name: 'Student projects', description: 'Coursework and side projects from people learning in public.', members: '3.7k' },
];

export const topics = ['#buildinpublic', '#engineering', '#design', '#teaching', '#opensource'];
