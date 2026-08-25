export type AnatomyImageFrame = {
  href: string;
  sourceWidth: number;
  sourceHeight: number;
  displayWidth: number;
  displayHeight: number;
  preserveAspectRatio: "xMidYMid slice";
};

/**
 * Development-only preview geometry for biorender-human-anatomy.svg.
 *
 * The embedded BioRender artwork has a landscape 2752 × 1536 viewBox.  The
 * navigator presents it in a 200 × 350 portrait frame using SVG
 * `xMidYMid slice`. M18 intentionally has no marker geometry: the illustration
 * is an orientation background and tissue selection lives in the named index.
 *
 * Release permission for this preview remains to be verified; see
 * docs/15_m17_asset_provenance.md.
 */
export const ANATOMY_IMAGE: AnatomyImageFrame = {
  href: "/assets/biorender-human-anatomy.svg",
  sourceWidth: 2752,
  sourceHeight: 1536,
  displayWidth: 200,
  displayHeight: 350,
  preserveAspectRatio: "xMidYMid slice",
};
