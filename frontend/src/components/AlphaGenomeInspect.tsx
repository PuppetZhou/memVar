import type { CSSProperties, ReactNode } from 'react';

/** Shared readable tooltip hierarchy: modality, genomic context, then source values. */
export function GenomeInspector({ title, coordinate, children, left = 12 }: {
  title: string; coordinate: string; children: ReactNode; left?: number;
}) {
  return <div className="agx-genome-inspector" role="tooltip" style={{ '--inspector-left': `${left}%` } as CSSProperties}>
    <header>{title}</header><strong>{coordinate}</strong><div className="agx-inspector-values">{children}</div>
  </div>;
}
