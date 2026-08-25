/**
 * Display-only anatomy metadata. `body_region_id` remains the explicit,
 * website-owned crosswalk identity; this module neither normalizes source
 * tissue terms nor infers anatomical equivalence from text.
 */
export type TissueSystemId =
  | "nervous_sensory"
  | "cardiovascular"
  | "respiratory"
  | "digestive_hepatobiliary"
  | "urinary"
  | "endocrine"
  | "female_reproductive_breast"
  | "male_reproductive"
  | "immune_hematopoietic"
  | "musculoskeletal"
  | "integument_soft_tissue"
  | "other_non_anatomical";

export type TissueIconKey =
  | "brain"
  | "heart"
  | "respiratory"
  | "digestive"
  | "urinary"
  | "endocrine"
  | "female_reproductive"
  | "male_reproductive"
  | "immune"
  | "musculoskeletal"
  | "soft_tissue"
  | "other";

export type TissueSystemVisual = {
  id: TissueSystemId;
  label: string;
  iconKey: TissueIconKey;
};

export type TissueIconAsset = {
  /** Original Healthicons file name, retained for source traceability. */
  originalName: string;
  outlinePath: `/assets/healthicons/outline/${string}.svg`;
  filledPath: `/assets/healthicons/filled/${string}.svg`;
};

/**
 * The site ships this small, controlled Healthicons subset locally. It is a
 * visual aid for the display system only; it does not normalize source tissue
 * terms or introduce a new anatomy crosswalk.
 */
export const TISSUE_ICON_ASSETS: Readonly<Record<Exclude<TissueIconKey, "other">, TissueIconAsset>> = {
  brain: {
    originalName: "neurology",
    outlinePath: "/assets/healthicons/outline/neurology.svg",
    filledPath: "/assets/healthicons/filled/neurology.svg",
  },
  heart: {
    originalName: "heart-organ",
    outlinePath: "/assets/healthicons/outline/heart-organ.svg",
    filledPath: "/assets/healthicons/filled/heart-organ.svg",
  },
  respiratory: {
    originalName: "lungs",
    outlinePath: "/assets/healthicons/outline/lungs.svg",
    filledPath: "/assets/healthicons/filled/lungs.svg",
  },
  digestive: {
    originalName: "liver",
    outlinePath: "/assets/healthicons/outline/liver.svg",
    filledPath: "/assets/healthicons/filled/liver.svg",
  },
  urinary: {
    originalName: "kidneys",
    outlinePath: "/assets/healthicons/outline/kidneys.svg",
    filledPath: "/assets/healthicons/filled/kidneys.svg",
  },
  endocrine: {
    originalName: "thyroid",
    outlinePath: "/assets/healthicons/outline/thyroid.svg",
    filledPath: "/assets/healthicons/filled/thyroid.svg",
  },
  female_reproductive: {
    originalName: "female-reproductive_system",
    outlinePath: "/assets/healthicons/outline/female-reproductive_system.svg",
    filledPath: "/assets/healthicons/filled/female-reproductive_system.svg",
  },
  male_reproductive: {
    originalName: "testicles",
    outlinePath: "/assets/healthicons/outline/testicles.svg",
    filledPath: "/assets/healthicons/filled/testicles.svg",
  },
  immune: {
    originalName: "blood-cells",
    outlinePath: "/assets/healthicons/outline/blood-cells.svg",
    filledPath: "/assets/healthicons/filled/blood-cells.svg",
  },
  musculoskeletal: {
    originalName: "skeleton",
    outlinePath: "/assets/healthicons/outline/skeleton.svg",
    filledPath: "/assets/healthicons/filled/skeleton.svg",
  },
  soft_tissue: {
    originalName: "tissue",
    outlinePath: "/assets/healthicons/outline/tissue.svg",
    filledPath: "/assets/healthicons/filled/tissue.svg",
  },
} as const;

/** `other` deliberately has no organ-shaped visual surrogate. */
export function tissueIconAssetForKey(iconKey: TissueIconKey): TissueIconAsset | null {
  return iconKey === "other" ? null : TISSUE_ICON_ASSETS[iconKey];
}

export type BodyRegionVisual = TissueSystemVisual & {
  bodyRegionId: string;
  /** The index uses a shared system icon; `other` intentionally has no organ surrogate. */
  iconSpecificity: "system" | "non_anatomical";
  /** Reserved for the later local EBI anatomogram spike; never used to place a marker today. */
  anatomogramTarget: "planned_exact" | "index_only";
};

export const TISSUE_SYSTEMS: readonly TissueSystemVisual[] = [
  { id: "nervous_sensory", label: "Nervous & sensory", iconKey: "brain" },
  { id: "cardiovascular", label: "Cardiovascular", iconKey: "heart" },
  { id: "respiratory", label: "Respiratory", iconKey: "respiratory" },
  { id: "digestive_hepatobiliary", label: "Digestive & hepatobiliary", iconKey: "digestive" },
  { id: "urinary", label: "Urinary", iconKey: "urinary" },
  { id: "endocrine", label: "Endocrine", iconKey: "endocrine" },
  { id: "female_reproductive_breast", label: "Female reproductive & breast", iconKey: "female_reproductive" },
  { id: "male_reproductive", label: "Male reproductive", iconKey: "male_reproductive" },
  { id: "immune_hematopoietic", label: "Immune & hematopoietic", iconKey: "immune" },
  { id: "musculoskeletal", label: "Musculoskeletal", iconKey: "musculoskeletal" },
  { id: "integument_soft_tissue", label: "Integument & soft tissue", iconKey: "soft_tissue" },
  { id: "other_non_anatomical", label: "Other / non-anatomical", iconKey: "other" },
] as const;

const SYSTEM_BY_ID = new Map(TISSUE_SYSTEMS.map((system) => [system.id, system] as const));

function region(bodyRegionId: string, systemId: TissueSystemId, anatomogramTarget: BodyRegionVisual["anatomogramTarget"] = "planned_exact"): BodyRegionVisual {
  const system = SYSTEM_BY_ID.get(systemId);
  if (!system) throw new Error(`Unknown tissue system visual: ${systemId}`);
  return {
    ...system,
    bodyRegionId,
    iconSpecificity: systemId === "other_non_anatomical" ? "non_anatomical" : "system",
    anatomogramTarget,
  };
}

/*
 * Every key is declared here deliberately. Do not replace this with substring
 * matching: a display system is not a biological source-term normalization.
 */
const BODY_REGION_VISUALS: Record<string, BodyRegionVisual> = {
  brain: region("brain", "nervous_sensory"),
  thyroid: region("thyroid", "endocrine"),
  lung: region("lung", "respiratory"),
  heart: region("heart", "cardiovascular"),
  liver: region("liver", "digestive_hepatobiliary"),
  stomach: region("stomach", "digestive_hepatobiliary"),
  pancreas: region("pancreas", "digestive_hepatobiliary"),
  spleen: region("spleen", "immune_hematopoietic"),
  kidney: region("kidney", "urinary"),
  small_intestine: region("small_intestine", "digestive_hepatobiliary"),
  colon: region("colon", "digestive_hepatobiliary"),
  bladder: region("bladder", "urinary"),
  skin: region("skin", "integument_soft_tissue", "index_only"),
  skeletal_muscle: region("skeletal_muscle", "musculoskeletal"),
  adipose: region("adipose", "integument_soft_tissue"),
  bone_marrow: region("bone_marrow", "immune_hematopoietic"),
  blood: region("blood", "immune_hematopoietic"),
  breast: region("breast", "female_reproductive_breast"),
  uterus: region("uterus", "female_reproductive_breast"),
  ovary: region("ovary", "female_reproductive_breast"),
  testis: region("testis", "male_reproductive"),
  prostate: region("prostate", "male_reproductive"),
  adrenal_gland: region("adrenal_gland", "endocrine"),
  appendix: region("appendix", "digestive_hepatobiliary"),
  esophagus: region("esophagus", "digestive_hepatobiliary"),
  fallopian_tube: region("fallopian_tube", "female_reproductive_breast"),
  gallbladder: region("gallbladder", "digestive_hepatobiliary"),
  eye: region("eye", "nervous_sensory"),
  lymph_node: region("lymph_node", "immune_hematopoietic"),
  oral_cavity: region("oral_cavity", "digestive_hepatobiliary"),
  placenta: region("placenta", "female_reproductive_breast"),
  parathyroid: region("parathyroid", "endocrine", "index_only"),
  pituitary: region("pituitary", "endocrine"),
  salivary_gland: region("salivary_gland", "digestive_hepatobiliary"),
  spinal_cord: region("spinal_cord", "nervous_sensory"),
  thymus: region("thymus", "immune_hematopoietic", "index_only"),
  tonsil: region("tonsil", "immune_hematopoietic"),
  vagina: region("vagina", "female_reproductive_breast"),
  vasculature: region("vasculature", "cardiovascular", "index_only"),
  peripheral_nerve: region("peripheral_nerve", "nervous_sensory"),
  bone: region("bone", "musculoskeletal", "index_only"),
  cartilage: region("cartilage", "musculoskeletal", "index_only"),
  smooth_muscle: region("smooth_muscle", "musculoskeletal"),
  connective_tissue: region("connective_tissue", "integument_soft_tissue", "index_only"),
  male_reproductive_tract: region("male_reproductive_tract", "male_reproductive", "index_only"),
  upper_airway: region("upper_airway", "respiratory", "index_only"),
  other: region("other", "other_non_anatomical", "index_only"),
};

export const BODY_REGION_VISUAL_IDS = Object.freeze(Object.keys(BODY_REGION_VISUALS));

export function tissueVisualForRegion(bodyRegionId: string): BodyRegionVisual {
  const visual = BODY_REGION_VISUALS[bodyRegionId];
  if (!visual) throw new Error(`Missing explicit tissue visual mapping for body_region_id: ${bodyRegionId}`);
  return visual;
}

export function groupRegionsByTissueSystem<T extends { body_region_id: string }>(regions: readonly T[]) {
  const grouped = new Map<TissueSystemId, T[]>();
  for (const regionSummary of regions) {
    const systemId = tissueVisualForRegion(regionSummary.body_region_id).id;
    const members = grouped.get(systemId) ?? [];
    members.push(regionSummary);
    grouped.set(systemId, members);
  }
  return TISSUE_SYSTEMS.flatMap((system) => {
    const members = grouped.get(system.id);
    return members?.length ? [{ system, regions: members }] : [];
  });
}
