/** Tests for the GitHub client and the cache. */
import assert from 'node:assert';
import test from 'node:test';

import {
  GitHubClient,
  GitHubError,
  readRateLimit,
  searchIssues,
  searchRepos,
  sortIssues,
  sortRepos,
  toIssue,
  toRepo,
} from '../src/github.ts';
import { CacheStore, createMemoryStore } from '../src/store.ts';

/** A fetch that answers with a fixed list. */
function fakeFetch(items: unknown[], status = 200, headers: Record<string, string> = {}) {
  const calls: string[] = [];
  const fn = (async (url: string) => {
    calls.push(url);
    return {
      ok: status >= 200 && status < 300,
      status,
      headers: {
        forEach: (callback: (value: string, key: string) => void) => {
          Object.entries(headers).forEach(([key, value]) => callback(value, key));
        },
      },
      json: async () => items,
      text: async () => JSON.stringify(items),
    } as unknown as Response;
  }) as unknown as typeof fetch;
  return { fn, calls };
}

const rawRepo = {
  id: 12,
  name: 'campus-map',
  full_name: 'alexr/campus-map',
  description: 'A map',
  language: 'TypeScript',
  stargazers_count: 84,
  forks_count: 12,
  open_issues_count: 3,
  updated_at: '2026-04-23T08:00:00Z',
  html_url: 'https://github.com/alexr/campus-map',
  private: false,
};

const rawIssue = {
  id: 99,
  number: 42,
  title: 'Labels overlap',
  state: 'open',
  labels: [{ name: 'bug' }, 'ui'],
  comments: 5,
  user: { login: 'mina' },
  created_at: '2026-04-22T08:00:00Z',
  html_url: 'https://github.com/alexr/campus-map/issues/42',
  repository_url: 'https://api.github.com/repos/alexr/campus-map',
};

test('a repository is turned into the shape the screens use', () => {
  const repo = toRepo(rawRepo);
  assert.equal(repo.id, '12');
  assert.equal(repo.fullName, 'alexr/campus-map');
  assert.equal(repo.stars, 84);
  assert.equal(repo.language, 'TypeScript');
  assert.equal(repo.private, false);
});

test('an issue is turned into the shape the screens use', () => {
  const issue = toIssue(rawIssue);
  assert.equal(issue.number, 42);
  assert.equal(issue.state, 'open');
  assert.deepEqual(issue.labels, ['bug', 'ui']);
  assert.equal(issue.author, 'mina');
  assert.equal(issue.repo, 'campus-map');
});

test('the rate limit is read from the headers', () => {
  const limit = readRateLimit({
    'x-ratelimit-limit': '60',
    'x-ratelimit-remaining': '42',
    'x-ratelimit-reset': '1770000000',
  });
  assert.equal(limit?.limit, 60);
  assert.equal(limit?.remaining, 42);
  assert.ok(limit?.reset.endsWith('Z'));
});

test('the rate limit is null when the headers are not there', () => {
  assert.equal(readRateLimit({}), null);
});

test('the client asks for the repositories of a user', async () => {
  const { fn, calls } = fakeFetch([rawRepo], 200, {
    'x-ratelimit-limit': '60',
    'x-ratelimit-remaining': '59',
  });
  const client = new GitHubClient({ fetchFn: fn });

  const { repos, rateLimit } = await client.listRepos('alexr');
  assert.equal(repos.length, 1);
  assert.equal(repos[0].name, 'campus-map');
  assert.equal(rateLimit?.remaining, 59);
  assert.ok(calls[0].includes('/users/alexr/repos'));
});

test('the client asks for the issues of a user', async () => {
  const { fn, calls } = fakeFetch([rawIssue]);
  const client = new GitHubClient({ fetchFn: fn });

  const { issues } = await client.listIssues('alexr');
  assert.equal(issues.length, 1);
  assert.equal(issues[0].title, 'Labels overlap');
  assert.ok(calls[0].includes('/users/alexr/issues'));
});

test('an error from the API becomes a GitHubError', async () => {
  const { fn } = fakeFetch([], 403);
  const client = new GitHubClient({ fetchFn: fn });

  await assert.rejects(() => client.listRepos('alexr'), (error: Error) => {
    assert.ok(error instanceof GitHubError);
    assert.equal((error as GitHubError).status, 403);
    return true;
  });
});

test('the repositories are sorted by the date they were updated', () => {
  const older = toRepo({ ...rawRepo, id: 1, name: 'older', updated_at: '2026-01-01T00:00:00Z' });
  const newer = toRepo({ ...rawRepo, id: 2, name: 'newer', updated_at: '2026-06-01T00:00:00Z' });
  assert.deepEqual(sortRepos([older, newer]).map((repo) => repo.name), ['newer', 'older']);
});

test('the issues are sorted by the date they were created', () => {
  const older = toIssue({ ...rawIssue, id: 1, created_at: '2026-01-01T00:00:00Z' });
  const newer = toIssue({ ...rawIssue, id: 2, created_at: '2026-06-01T00:00:00Z' });
  assert.deepEqual(sortIssues([older, newer]).map((issue) => issue.id), ['2', '1']);
});

test('the search looks in the name, the description and the language', () => {
  const repos = [toRepo(rawRepo), toRepo({ ...rawRepo, id: 2, name: 'notes-cli', language: 'Go' })];
  assert.equal(searchRepos(repos, 'typescript').length, 1);
  assert.equal(searchRepos(repos, 'notes').length, 1);
  assert.equal(searchRepos(repos, '').length, 2);
  assert.equal(searchRepos(repos, 'nothing').length, 0);
});

test('the issues can be filtered by their state', () => {
  const issues = [toIssue(rawIssue), toIssue({ ...rawIssue, id: 2, state: 'closed' })];
  assert.equal(searchIssues(issues, '', 'all').length, 2);
  assert.equal(searchIssues(issues, '', 'open').length, 1);
  assert.equal(searchIssues(issues, '', 'closed').length, 1);
});

test('the cache keeps the repositories and the issues', async () => {
  const cache = new CacheStore(createMemoryStore());
  await cache.saveRepos([{ id: '1', name: 'campus-map' }]);
  await cache.saveIssues([{ id: 'i1' }]);

  const repos = await cache.repos();
  assert.equal(repos?.value.length, 1);
  const issues = await cache.issues();
  assert.equal(issues?.value.length, 1);
});

test('the cache is empty when nothing was saved', async () => {
  const cache = new CacheStore(createMemoryStore());
  assert.equal(await cache.repos(), null);
  assert.equal(await cache.issues(), null);
});

test('the cache survives a corrupt value', async () => {
  const backend = createMemoryStore();
  await backend.setItem('gitpoint.repos.v1', 'not json');
  const cache = new CacheStore(backend);
  assert.equal(await cache.repos(), null);
});

test('the cache keeps working when the storage fails', async () => {
  const failing = {
    async getItem() { throw new Error('storage unavailable'); },
    async setItem() { throw new Error('storage unavailable'); },
    async removeItem() { throw new Error('storage unavailable'); },
  };
  const cache = new CacheStore(failing);
  assert.equal(await cache.repos(), null);
  assert.equal(await cache.saveRepos([]), false);
});

test('the cache can be cleared', async () => {
  const cache = new CacheStore(createMemoryStore());
  await cache.saveRepos([{ id: '1' }]);
  await cache.clear('gitpoint.repos.v1');
  assert.equal(await cache.repos(), null);
});
