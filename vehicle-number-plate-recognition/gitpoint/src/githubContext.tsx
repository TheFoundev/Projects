import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { CacheStore, type KeyValueStore } from './store';
import { GitHubClient, type Issue, type Repo, type RateLimit } from './github';
import { issues as seedIssues, repos as seedRepos, profile as seedProfile } from './data';

const backend: KeyValueStore = {
  getItem: (key) => AsyncStorage.getItem(key),
  setItem: (key, value) => AsyncStorage.setItem(key, value),
  removeItem: (key) => AsyncStorage.removeItem(key),
};

const cache = new CacheStore(backend);

type GitHubContextValue = {
  repos: Repo[];
  issues: Issue[];
  profile: typeof seedProfile;
  rateLimit: RateLimit | null;
  loading: boolean;
  error: string | null;
  /** True when the data comes from the cache and not from the API. */
  offline: boolean;
  refresh(): Promise<void>;
};

const GitHubContext = createContext<GitHubContextValue | null>(null);

/** The user the app shows. */
export const GITHUB_USER = 'alexr-dev';

const client = new GitHubClient({
  token: process.env.EXPO_PUBLIC_GITHUB_TOKEN ?? '',
});

/**
 * Loads the repositories, the issues and the profile.
 *
 * The cache is shown first, so the app has something to show right away, and
 * the API is asked afterwards. When the API cannot be reached the seed data
 * is the last fallback.
 */
export function GitHubProvider({ children }: { children: React.ReactNode }) {
  const [repos, setRepos] = useState<Repo[]>(seedRepos as unknown as Repo[]);
  const [issues, setIssues] = useState<Issue[]>(seedIssues as unknown as Issue[]);
  const [profile, setProfile] = useState(seedProfile);
  const [rateLimit, setRateLimit] = useState<RateLimit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);

  const load = useCallback(async () => {
    // The cache first.
    const cachedRepos = await cache.repos();
    if (cachedRepos?.value?.length) setRepos(cachedRepos.value as unknown as Repo[]);
    const cachedIssues = await cache.issues();
    if (cachedIssues?.value?.length) setIssues(cachedIssues.value as unknown as Issue[]);

    try {
      const [repoAnswer, issueAnswer, profileAnswer] = await Promise.all([
        client.listRepos(GITHUB_USER),
        client.listIssues(GITHUB_USER),
        client.getProfile(GITHUB_USER),
      ]);
      setRepos(repoAnswer.repos);
      setIssues(issueAnswer.issues);
      setRateLimit(repoAnswer.rateLimit);
      setOffline(false);
      setError(null);

      await cache.saveRepos(repoAnswer.repos);
      await cache.saveIssues(issueAnswer.issues);
      if (profileAnswer && profileAnswer.login) {
        const answer = profileAnswer as Record<string, unknown>;
        const next = {
          ...seedProfile,
          name: String(answer.name ?? seedProfile.name),
          handle: String(answer.login ?? seedProfile.handle),
          bio: String(answer.bio ?? seedProfile.bio),
          location: String(answer.location ?? seedProfile.location),
          followers: Number(answer.followers ?? seedProfile.followers),
          following: Number(answer.following ?? seedProfile.following),
          repos: Number(answer.public_repos ?? seedProfile.repos),
        };
        setProfile(next);
        await cache.saveProfile(next);
      }
    } catch (failure) {
      setOffline(true);
      setError(failure instanceof Error ? failure.message : 'The API could not be reached.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const value = useMemo(
    () => ({ repos, issues, profile, rateLimit, loading, error, offline, refresh: load }),
    [repos, issues, profile, rateLimit, loading, error, offline, load],
  );

  return <GitHubContext.Provider value={value}>{children}</GitHubContext.Provider>;
}

/** The data of the app. Throws when it is used outside the provider. */
export function useGitHub(): GitHubContextValue {
  const value = useContext(GitHubContext);
  if (!value) throw new Error('useGitHub must be used inside a GitHubProvider');
  return value;
}
