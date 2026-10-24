import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ExpenseStore, type KeyValueStore } from './store';
import {
  addExpense as addExpenseTo,
  addMessage as addMessageTo,
  moveReport,
  type Expense,
  type Message,
  type Report,
  type ReportStatus,
} from './model';
import { initialMessages, reports as seedReports, settings as seedSettings } from './data';

const backend: KeyValueStore = {
  getItem: (key) => AsyncStorage.getItem(key),
  setItem: (key, value) => AsyncStorage.setItem(key, value),
  removeItem: (key) => AsyncStorage.removeItem(key),
};

const store = new ExpenseStore(backend);

type ExpenseContextValue = {
  reports: Report[];
  messages: Message[];
  settings: typeof seedSettings;
  ready: boolean;
  /** Move a report to another state. */
  submit(reportId: string): { ok: boolean; error?: string };
  /** Add an expense to a report. */
  addExpense(reportId: string, expense: Expense): void;
  /** Send a message in the chat. */
  sendMessage(body: string): void;
  /** Change a setting. */
  updateSettings(next: Partial<typeof seedSettings>): void;
};

const ExpenseContext = createContext<ExpenseContextValue | null>(null);

/** Holds the reports, the chat and the settings, and keeps them on the device. */
export function ExpenseProvider({ children }: { children: React.ReactNode }) {
  const [reports, setReports] = useState<Report[]>(seedReports);
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [settings, setSettings] = useState(seedSettings);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const savedReports = await store.reports();
      const savedMessages = await store.messages();
      const savedSettings = await store.settings<typeof seedSettings>();
      if (cancelled) return;
      if (savedReports?.length) setReports(savedReports);
      if (savedMessages?.length) setMessages(savedMessages);
      if (savedSettings) setSettings(savedSettings);
      setReady(true);
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!ready) return;
    void store.saveReports(reports);
  }, [reports, ready]);

  useEffect(() => {
    if (!ready) return;
    void store.saveMessages(messages);
  }, [messages, ready]);

  useEffect(() => {
    if (!ready) return;
    void store.saveSettings(settings);
  }, [settings, ready]);

  const submit = useCallback(
    (reportId: string) => {
      const report = reports.find((item) => item.id === reportId);
      if (!report) return { ok: false, error: 'The report does not exist.' };
      const answer = moveReport(report, 'submitted');
      if ('error' in answer) return { ok: false, error: answer.error };
      setReports((current) => current.map((item) => (item.id === reportId ? answer.report : item)));
      return { ok: true };
    },
    [reports],
  );

  const addExpense = useCallback((reportId: string, expense: Expense) => {
    setReports((current) =>
      current.map((report) => (report.id === reportId ? addExpenseTo(report, expense) : report)),
    );
  }, []);

  const sendMessage = useCallback((body: string) => {
    const text = body.trim();
    if (!text) return;
    const now = new Date();
    const message: Message = {
      id: `m-${now.getTime()}`,
      sender: 'You',
      body: text,
      time: now.toLocaleTimeString('en-CA', { hour: '2-digit', minute: '2-digit' }),
      mine: true,
    };
    setMessages((current) => addMessageTo(current, message));
  }, []);

  const updateSettings = useCallback((next: Partial<typeof seedSettings>) => {
    setSettings((current) => ({ ...current, ...next }));
  }, []);

  const value = useMemo(
    () => ({ reports, messages, settings, ready, submit, addExpense, sendMessage, updateSettings }),
    [reports, messages, settings, ready, submit, addExpense, sendMessage, updateSettings],
  );

  return <ExpenseContext.Provider value={value}>{children}</ExpenseContext.Provider>;
}

/** The state of the app. Throws when it is used outside the provider. */
export function useExpenses(): ExpenseContextValue {
  const value = useContext(ExpenseContext);
  if (!value) throw new Error('useExpenses must be used inside an ExpenseProvider');
  return value;
}
