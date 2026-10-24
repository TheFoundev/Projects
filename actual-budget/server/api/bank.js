/**
 * Bank providers.
 *
 * Real bank aggregation needs a provider account and credentials. None is
 * configured here and none is faked: the endpoint reports the truth and the UI
 * shows it. Import from a CSV export is implemented for real in import.js.
 */

/** Providers this build knows how to talk to. Empty until one is implemented. */
export const PROVIDERS = [];

export function registerBank(router) {
  router.get('/api/bank/providers', () => ({
    configured: false,
    providers: [],
    message: 'No bank provider is configured. Import a CSV export instead.',
  }));
}
