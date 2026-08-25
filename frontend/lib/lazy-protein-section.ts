export const LAZY_PROTEIN_SECTION_OBSERVER_OPTIONS = {
  rootMargin: "600px 0px",
  threshold: 0,
};

export function shouldMountLazyProteinSection(sectionId: string | undefined, hash: string, isNearViewport: boolean) {
  return isNearViewport || (sectionId !== undefined && hash === `#${sectionId}`);
}
