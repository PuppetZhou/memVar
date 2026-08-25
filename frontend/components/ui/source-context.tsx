import { Database, ExternalLink, Info } from "lucide-react";
import { formatSourceRelease } from "../../lib/display-labels";
import { sourceRecordMetadataText } from "../../lib/source-context";

type SourceContextProps = {
  source: string;
  release?: string | null;
  recordGrain?: string | null;
  caveat?: string;
  href?: string | null;
  linkLabel?: string;
  className?: string;
};

/**
 * Persistent provenance for a bounded evidence collection. It deliberately
 * displays an unavailable release rather than implying that one exists.
 */
export function SourceContext({
  source,
  release,
  recordGrain,
  caveat,
  href,
  linkLabel = "Open source record",
  className = "",
}: SourceContextProps) {
  const releaseText = release === undefined ? "Not reported in this response" : formatSourceRelease(release);
  const grainText = sourceRecordMetadataText(recordGrain);
  return <aside className={`source-context ${className}`.trim()} aria-label={`${source} source context`}>
    <div className="source-context-heading"><Database aria-hidden="true" size={18} strokeWidth={1.9} /><strong>{source}</strong></div>
    <dl className="source-context-fields">
      <div><dt>Release</dt><dd>{releaseText}</dd></div>
      <div><dt>Record grain</dt><dd>{grainText}</dd></div>
    </dl>
    {(caveat || href) && <div className="source-context-actions">
      {caveat && <p><Info aria-hidden="true" size={16} strokeWidth={1.9} /><span>{caveat}</span></p>}
      {href && <a href={href} target="_blank" rel="noreferrer"><ExternalLink aria-hidden="true" size={16} strokeWidth={1.9} />{linkLabel}</a>}
    </div>}
  </aside>;
}
