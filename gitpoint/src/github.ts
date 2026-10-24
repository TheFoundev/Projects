/**
 * The GitHub client.
 *
 * The client talks to the REST API of GitHub and turns the answers into the
 * types the screens use. The fetch function is given to the client, so the
 * tests can answer without a network.
 *
 * No imports, so the client can be tested without a React Native runtime.
 */

export type Repo = {
  id: string;
  name: string;
  fullName: string;
  description: string;
  language: string;
  stars: number;
  forks: number;
  openIssues: number;
  updated: string;
  htmlUrl: string;
  private: boolean;
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
  createdAt: string;
  htmlUrl: string;
};

export type RateLimit = {
  limit: number;
  remaining: number;
  reset: string;
};

export class GitHubError extends Error {
  status: number;
  body: string;

  constructor(message: string, status: number, body = '') {
    super(message);
    this.name = 'GitHubError';
    this.status = status;
    this.body = body;
  }
}

/** The header of the answer that says how much of the rate limit is left. */
export function readRateLimit(headers: Record<string, string>): RateLimit | null {
  const limit = headers['x-ratelimit-limit'];
  const remaining = headers['x-ratelimit-remaining'];
  const reset = headers['x-ratelimit-reset'];
  if (limit === undefined || remaining === undefined) return null;
  return {
    limit: Number(limit),
    remaining: Number(remaining),
    reset: reset ? new Date(Number(reset) * 1000).toISOString() : '',
  };
}

/** The repositories of a user, in the shape the screens use. */
export function toRepo(raw: Record<string, unknown>): Repo {
  return {
    id: String(raw.id ?? ''),
    name: String(raw.name ?? ''),
    fullName: String(raw.full_name ?? raw.name ?? ''),
    description: String(raw.description ?? ''),
    language: String(raw.language ?? 'Unknown'),
    stars: Number(raw.stargazers_count ?? 0),
    forks: Number(raw.forks_count ?? 0),
    openIssues: Number(raw.open_issues_count ?? 0),
    updated: String(raw.updated_at ?? ''),
    htmlUrl: String(raw.html_url ?? ''),
    private: Boolean(raw.private),
  };
}

/** An issue, in the shape the screens use. */
export function toIssue(raw: Record<string, unknown>): Issue {
  const labels = Array.isArray(raw.labels)
    ? raw.labels.map((label) =>
        typeof label === 'string' ? label : String((label as Record<string, unknown>)?.name ?? ''),
      )
    : [];
  const user = raw.user as Record<string, unknown> | undefined;
  return {
    id: String(raw.id ?? ''),
    repo: String(raw.repository_url ?? '').split('/').pop() ?? '',
    number: Number(raw.number ?? 0),
    title: String(raw.title ?? ''),
    state: raw.state === 'closed' ? 'closed' : 'open',
    labels,
    comments: Number(raw.comments ?? 0),
    author: String(user?.login ?? 'unknown'),
    createdAt: String(raw.created_at ?? ''),
    htmlUrl: String(raw.html_url ?? ''),
  };
}

/** The repositories of a user, newest first. */
export function sortRepos(repos: Repo[]): Repo[] {
  return [...repos].sort((left, right) => right.updated.localeCompare(left.updated));
}

/** The issues of a user, newest first. */
export function sortIssues(issues: Issue[]): Issue[] {
  return [...issues].sort((left, right) => right.createdAt.localeCompare(left.createdAt));
}

/** The repositories that match a search. */
export function searchRepos(repos: Repo[], query: string): Repo[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return repos;
  return repos.filter((repo) =>
    `${repo.name} ${repo.description} ${repo.language}`.toLowerCase().includes(needle),
  );
}

/** The issues that match a search and a state. */
export function searchIssues(issues: Issue[], query: string, state: 'all' | 'open' | 'closed' = 'all'): Issue[] {
  const needle = query.trim().toLowerCase();
  return issues.filter((issue) => {
    if (state !== 'all' && issue.state !== state) return false;
    if (!needle) return true;
    return `${issue.title} ${issue.repo} ${issue.author} ${issue.labels.join(' ')}`
      .toLowerCase()
      .includes(needle);
  });
}

/**
 * The GitHub client.
 *
 * The token is optional: without it the API answers with fewer requests an
 * hour, but everything still works.
 */
export class GitHubClient {
  private baseUrl: string;
  private token: string;
  private fetchFn: typeof fetch;

  constructor(options: { baseUrl?: string; token?: string; fetchFn?: typeof fetch } = {}) {
    this.baseUrl = options.baseUrl ?? 'https://api.github.com';
    this.token = options.token ?? '';
    this.fetchFn = options.fetchFn ?? ((...args: Parameters<typeof fetch>) => fetch(...args));
  }

  /** The headers every request carries. */
  private headers(): Record<string, string> {
    const headers: Record<string, string> = {
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'gitpoint-foundev',
    };
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    return headers;
  }

  /** One request, with the errors turned into a GitHubError. */
  private async request(path: string): Promise<{ items: Record<string, unknown>[]; rateLimit: RateLimit | null }> {
    const response = await this.fetchFn(`${this.baseUrl}${path}`, { headers: this.headers() });
    const headers: Record<string, string> = {};
    response.headers?.forEach?.((value: string, key: string) => {
      headers[key.toLowerCase()] = value;
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new GitHubError(`GitHub answered with ${response.status}`, response.status, body);
    }

    const items = (await response.json()) as Record<string, unknown>[];
    return { items: Array.isArray(items) ? items : [], rateLimit: readRateLimit(headers) };
  }

  /** The repositories of a user. */
  async listRepos(user: string, perPage = 30): Promise<{ repos: Repo[]; rateLimit: RateLimit | null }> {
    const { items, rateLimit } = await this.request(`/users/${encodeURIComponent(user)}/repos?per_page=${perPage}&sort=updated`);
    return { repos: sortRepos(items.map(toRepo)), rateLimit };
  }

  /** The issues of a user. */
  async listIssues(user: string, perPage = 30): Promise<{ issues: Issue[]; rateLimit: RateLimit | null }> {
    const { items, rateLimit } = await this.request(`/users/${encodeURIComponent(user)}/issues?per_page=${perPage}&state=all`);
    return { issues: sortIssues(items.map(toIssue)), rateLimit };
  }

  /** The profile of a user. */
  async getProfile(user: string): Promise<Record<string, unknown>> {
    const { items } = await this.request(`/users/${encodeURIComponent(user)}`);
    return items[0] ?? {};
  }
}
