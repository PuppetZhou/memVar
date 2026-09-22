import { useSyncExternalStore } from 'react';

const mediaQuery = typeof window === 'undefined' ? null : window.matchMedia('(prefers-reduced-motion: reduce)');
const getSnapshot = () => mediaQuery?.matches ?? false;
const getServerSnapshot = () => true;
const subscribe = (onChange: () => void) => {
  mediaQuery?.addEventListener('change', onChange);
  return () => mediaQuery?.removeEventListener('change', onChange);
};

/** Motion's installed hook snapshots only at mount; this also handles live OS changes. */
export function useReducedMotion() {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
