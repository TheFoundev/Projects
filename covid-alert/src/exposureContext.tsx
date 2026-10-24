import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { checkStore } from './persistence';
import {
  SimulatedExposureService,
  toCheck,
  type Check,
  type ExposureService,
} from './exposure';
import { initialChecks } from './data';

type ExposureContextValue = {
  checks: Check[];
  service: ExposureService;
  ready: boolean;
  /** Run an exposure check and add it to the history. */
  runCheck(): Promise<Check>;
};

const ExposureContext = createContext<ExposureContextValue | null>(null);

/** Holds the check history and the exposure service. */
export function ExposureProvider({
  children,
  service: injected,
}: {
  children: React.ReactNode;
  service?: ExposureService;
}) {
  const service = useMemo(() => injected ?? new SimulatedExposureService(), [injected]);
  const [checks, setChecks] = useState<Check[]>(initialChecks);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const saved = await checkStore.load();
      if (cancelled) return;
      if (saved.length > 0) setChecks(saved);
      setReady(true);
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!ready) return;
    void checkStore.save(checks);
  }, [checks, ready]);

  const runCheck = useCallback(async () => {
    const result = await service.check();
    const check = toCheck(result, `c-${Date.now()}`);
    setChecks((current) => [check, ...current]);
    return check;
  }, [service]);

  const value = useMemo(
    () => ({ checks, service, ready, runCheck }),
    [checks, service, ready, runCheck],
  );

  return <ExposureContext.Provider value={value}>{children}</ExposureContext.Provider>;
}

/** The exposure state. Throws when it is used outside the provider. */
export function useExposure(): ExposureContextValue {
  const value = useContext(ExposureContext);
  if (!value) throw new Error('useExposure must be used inside an ExposureProvider');
  return value;
}
