/** Typography only: callers retain their existing units, precision and missing-value rules. */
export default function EvidenceNumber({ text }: { text: string }) {
  const scientific = text.match(/^([+-]?\d+(?:\.\d+)?)e([+-]?\d+)(%)?$/i);
  return <span className="evidence-number">{scientific
    ? <>{scientific[1]} × 10<sup>{String(Number(scientific[2])).replace('-', '−')}</sup>{scientific[3] ?? ''}</>
    : text}</span>;
}
