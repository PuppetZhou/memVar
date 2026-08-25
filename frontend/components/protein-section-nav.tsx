"use client";

import { useEffect, useState } from "react";
import { Activity, Dna, Fingerprint, Network } from "lucide-react";
import { chooseActiveSection, isProteinSectionId, PROTEIN_SECTION_GROUPS, PROTEIN_SECTIONS, PROTEIN_SECTION_OBSERVER_OPTIONS, type ProteinSectionId, type SectionObservation } from "../lib/protein-section-nav";

const GROUP_ICONS = {
  foundation: Fingerprint,
  genetic: Dna,
  molecular: Activity,
  network: Network,
} as const;

function initialSection() {
  if (typeof window === "undefined") return "overview" as ProteinSectionId;
  const hash = window.location.hash.slice(1);
  return isProteinSectionId(hash) ? hash : "overview";
}

export function ProteinSectionNav() {
  const [active, setActive] = useState<ProteinSectionId>(initialSection);

  useEffect(() => {
    const observations = new Map<ProteinSectionId, SectionObservation>();
    let frame: number | null = null;
    let initialHashFrame: number | null = null;
    let initialHashObserver: ResizeObserver | null = null;
    let initialHashTimeout: number | null = null;
    const refresh = () => {
      frame = null;
      setActive((current) => {
        const next = chooseActiveSection([...observations.values()], current);
        return current === next ? current : next;
      });
    };
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        const id = entry.target.id;
        if (isProteinSectionId(id)) observations.set(id, { id, isIntersecting: entry.isIntersecting, top: entry.boundingClientRect.top, intersectionRatio: entry.intersectionRatio });
      });
      if (frame === null) frame = window.requestAnimationFrame(refresh);
    }, PROTEIN_SECTION_OBSERVER_OPTIONS);
    PROTEIN_SECTIONS.forEach((section) => {
      const element = document.getElementById(section.id);
      if (element) observer.observe(element);
    });
    const onHashChange = () => {
      const hash = window.location.hash.slice(1);
      if (isProteinSectionId(hash)) setActive((current) => current === hash ? current : hash);
    };
    const stopInitialHashRestore = () => {
      if (initialHashFrame !== null) window.cancelAnimationFrame(initialHashFrame);
      initialHashFrame = null;
      initialHashObserver?.disconnect();
      initialHashObserver = null;
      if (initialHashTimeout !== null) window.clearTimeout(initialHashTimeout);
      initialHashTimeout = null;
      window.removeEventListener("pointerdown", stopInitialHashRestore);
      window.removeEventListener("wheel", stopInitialHashRestore);
      window.removeEventListener("keydown", stopInitialHashRestore);
    };
    const initialHash = window.location.hash.slice(1);
    if (isProteinSectionId(initialHash)) {
      // Protein sections are mounted only after the overview request resolves,
      // and panels above the target continue to settle asynchronously. Keep
      // the target aligned during that short loading window, but stop as soon
      // as the visitor expresses their own scroll or keyboard intent.
      const restoreInitialHash = () => {
        if (initialHashFrame !== null) window.cancelAnimationFrame(initialHashFrame);
        initialHashFrame = window.requestAnimationFrame(() => {
          document.getElementById(initialHash)?.scrollIntoView({ block: "start" });
        });
      };
      restoreInitialHash();
      initialHashObserver = new ResizeObserver(restoreInitialHash);
      initialHashObserver.observe(document.body);
      initialHashTimeout = window.setTimeout(stopInitialHashRestore, 4_000);
      window.addEventListener("pointerdown", stopInitialHashRestore, { once: true });
      window.addEventListener("wheel", stopInitialHashRestore, { once: true, passive: true });
      window.addEventListener("keydown", stopInitialHashRestore, { once: true });
    }
    window.addEventListener("hashchange", onHashChange);
    return () => { observer.disconnect(); window.removeEventListener("hashchange", onHashChange); if (frame !== null) window.cancelAnimationFrame(frame); stopInitialHashRestore(); };
  }, []);

  function goTo(id: ProteinSectionId) {
    setActive(id);
    window.location.hash = id;
  }

  return <nav className="protein-section-nav" aria-label="Protein page sections">
    <div className="protein-section-nav-desktop">{PROTEIN_SECTION_GROUPS.map((group) => { const Icon = GROUP_ICONS[group.key]; const groupActive = group.sections.some((section) => section.id === active); return <section key={group.key} className={`protein-section-nav-group group-${group.key} ${groupActive ? "is-group-active" : ""}`} aria-label={group.label}><header><span className="protein-nav-group-icon"><Icon aria-hidden="true" size={18} strokeWidth={1.9} /></span><span><strong>{group.label}</strong><small>{group.description}</small></span></header><div>{group.sections.map((section) => <a key={section.id} href={`#${section.id}`} aria-current={active === section.id ? "location" : undefined} className={active === section.id ? "is-active" : undefined}><span>{section.label}</span>{active === section.id && <span className="sr-only"> (current section)</span>}</a>)}</div></section>; })}</div>
    <label className="protein-section-nav-mobile"><span>Current section</span><select value={active} onChange={(event) => goTo(event.currentTarget.value as ProteinSectionId)}>{PROTEIN_SECTION_GROUPS.map((group) => <optgroup key={group.label} label={group.label}>{group.sections.map((section) => <option key={section.id} value={section.id}>{section.label}</option>)}</optgroup>)}</select></label>
  </nav>;
}
