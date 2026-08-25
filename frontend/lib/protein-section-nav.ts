export type ProteinSectionId = "overview" | "sequence" | "structure" | "variants" | "anatomy" | "expression" | "qtl" | "alphagenome" | "interactions" | "diseases";

export type ProteinSectionDescriptor = {
  id: ProteinSectionId;
  label: string;
};

export type ProteinSectionGroup = {
  key: "foundation" | "genetic" | "molecular" | "network";
  label: string;
  description: string;
  sections: ProteinSectionDescriptor[];
};

export const PROTEIN_SECTION_GROUPS: ProteinSectionGroup[] = [
  { key: "foundation", label: "Foundation", description: "Identity, sequence and structure", sections: [{ id: "overview", label: "Overview" }, { id: "sequence", label: "Sequence" }, { id: "structure", label: "Structure" }] },
  { key: "genetic", label: "Genetic evidence", description: "Protein-linked variants", sections: [{ id: "variants", label: "Variants" }] },
  { key: "molecular", label: "Molecular context", description: "Tissue and regulation", sections: [{ id: "anatomy", label: "Anatomy" }, { id: "expression", label: "Expression" }, { id: "qtl", label: "QTL" }, { id: "alphagenome", label: "AlphaGenome" }] },
  { key: "network", label: "Network & clinical", description: "Interactions and assertions", sections: [{ id: "interactions", label: "Interactions" }, { id: "diseases", label: "Diseases" }] },
];

export const PROTEIN_SECTIONS = PROTEIN_SECTION_GROUPS.flatMap((group) => group.sections);

// 7.25rem deep-link offset in globals.css × the site's default 16px root font size.
export const PROTEIN_SECTION_SCROLL_OFFSET_PX = 116;

// Kept as the single source passed to IntersectionObserver by ProteinSectionNav.
export const PROTEIN_SECTION_OBSERVER_OPTIONS = {
  rootMargin: `-${PROTEIN_SECTION_SCROLL_OFFSET_PX}px 0px -58% 0px`,
  threshold: [0, .01, .12],
};

export type SectionObservation = {
  id: ProteinSectionId;
  isIntersecting: boolean;
  top: number;
  intersectionRatio: number;
};

/** Choose the most recently passed visible section; fall back to the nearest upcoming one. */
export function chooseActiveSection(observations: SectionObservation[], fallback: ProteinSectionId = "overview", anchorOffset = PROTEIN_SECTION_SCROLL_OFFSET_PX): ProteinSectionId {
  const known = observations.filter((item) => PROTEIN_SECTIONS.some((section) => section.id === item.id));
  const intersecting = known.filter((item) => item.isIntersecting);
  if (!intersecting.length) return fallback;
  const passed = intersecting.filter((item) => item.top <= anchorOffset);
  if (passed.length) return [...passed].sort((left, right) => right.top - left.top || right.intersectionRatio - left.intersectionRatio)[0].id;
  return [...intersecting].sort((left, right) => left.top - right.top || right.intersectionRatio - left.intersectionRatio)[0].id;
}

export function isProteinSectionId(value: string | null): value is ProteinSectionId {
  return value !== null && PROTEIN_SECTIONS.some((section) => section.id === value);
}
