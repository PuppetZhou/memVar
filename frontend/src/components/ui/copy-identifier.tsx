import { useEffect, useRef, useState } from 'react';
import { Check, Copy } from 'lucide-react';

export function CopyIdentifier({ value }: { value: string }) {
  const [state, setState] = useState<'idle' | 'copied' | 'failed'>('idle');
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);
  async function copy() {
    clearTimeout(timer.current);
    try { await navigator.clipboard.writeText(value); setState('copied'); }
    catch { setState('failed'); }
    timer.current = setTimeout(() => setState('idle'), 1800);
  }
  const message = state === 'copied' ? 'Identifier copied' : state === 'failed' ? 'Copy unavailable; select the identifier to copy it.' : '';
  return <><button type="button" className="copy-identifier" onClick={copy} aria-label={`Copy ${value}`} title={message || `Copy ${value}`}>{state === 'copied' ? <Check size={14}/> : <Copy size={14}/>}</button><span className="sr-only" role="status">{message}</span></>;
}
