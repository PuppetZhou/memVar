import { useLayoutEffect, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

/** Keep genomic inspectors outside the clipped track stack and within the viewport. */
export function GenomeTooltip({ className, children, left, top = 8, percent = false }: {
  className: string; children: ReactNode; left: number; top?: number; percent?: boolean;
}) {
  const anchor = useRef<HTMLSpanElement>(null), panel = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const host = anchor.current?.parentElement, floating = panel.current;
    if (!host || !floating) return;
    const place = () => {
      const box = host.getBoundingClientRect(), size = floating.getBoundingClientRect();
      const viewportWidth = document.documentElement.clientWidth, viewportHeight = window.innerHeight;
      const preferredLeft = box.left + (percent ? box.width * left / 100 : left);
      const preferredTop = box.top + top;
      const y = preferredTop + size.height > viewportHeight - 12 ? box.top - size.height - 8 : preferredTop;
      floating.style.left = `${Math.max(12, Math.min(viewportWidth - size.width - 12, preferredLeft))}px`;
      floating.style.top = `${Math.max(12, Math.min(viewportHeight - size.height - 12, y))}px`;
      floating.style.visibility = 'visible';
    };
    place();
    const observer = new ResizeObserver(place);
    observer.observe(host); observer.observe(floating);
    window.addEventListener('resize', place);
    window.addEventListener('scroll', place, true);
    return () => {
      observer.disconnect(); window.removeEventListener('resize', place); window.removeEventListener('scroll', place, true);
    };
  }, [left, top, percent, children]);
  return <><span ref={anchor} hidden/>{createPortal(<div ref={panel} className={`${className} agx-floating-tooltip`} role="tooltip" style={{ visibility: 'hidden' }}>{children}</div>, document.body)}</>;
}

/** Shared readable tooltip hierarchy: modality, genomic context, then source values. */
export function GenomeInspector({ title, coordinate, children, left = 12 }: {
  title: string; coordinate: string; children: ReactNode; left?: number;
}) {
  return <GenomeTooltip className="agx-genome-inspector" left={left} percent>
    <header>{title}</header><strong>{coordinate}</strong><div className="agx-inspector-values">{children}</div>
  </GenomeTooltip>;
}
