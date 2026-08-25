"use client";

import { type ReactNode, useEffect, useRef, useState } from "react";
import { LAZY_PROTEIN_SECTION_OBSERVER_OPTIONS, shouldMountLazyProteinSection } from "../lib/lazy-protein-section";

export function LazyProteinSection({ id, label, children }: { id?: string; label: string; children: ReactNode }) {
  const placeholderRef = useRef<HTMLElement>(null);
  const [mounted, setMounted] = useState(() => typeof window !== "undefined" && shouldMountLazyProteinSection(id, window.location.hash, false));

  useEffect(() => {
    if (mounted) return;
    const mountForHash = () => {
      if (shouldMountLazyProteinSection(id, window.location.hash, false)) setMounted(true);
    };
    const placeholder = placeholderRef.current;
    if (!placeholder) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) setMounted(true);
    }, LAZY_PROTEIN_SECTION_OBSERVER_OPTIONS);
    observer.observe(placeholder);
    window.addEventListener("hashchange", mountForHash);
    mountForHash();
    return () => {
      observer.disconnect();
      window.removeEventListener("hashchange", mountForHash);
    };
  }, [id, mounted]);

  if (mounted) return <>{children}</>;
  return <section id={id} ref={placeholderRef} className="overview-section lazy-protein-section" aria-label={label}>
    <div className="lazy-protein-section-placeholder" role="status"><strong>{label}</strong><span>Loads when this section approaches the viewport.</span></div>
  </section>;
}
