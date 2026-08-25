export type TissueDisplayTerm = {
  key: string;
  source: string;
  rawTerm: string;
  displayLabel: string;
  bodySystem: string;
  order: number;
};

const BODY_SYSTEM_ORDER = [
  "Nervous system",
  "Cardiovascular system",
  "Respiratory system",
  "Digestive system",
  "Urinary system",
  "Endocrine system",
  "Reproductive system",
  "Immune and lymphatic system",
  "Musculoskeletal system",
  "Skin and soft tissue",
  "Other tissues",
] as const;

const BODY_SYSTEM_TERMS: Record<string, string[]> = {
  "Nervous system": ["brain", "cerebral", "cortex", "cerebell", "spinal", "nerve", "retina", "astrocyte"],
  "Cardiovascular system": ["heart", "cardiac", "artery", "aorta", "blood vessel", "vein"],
  "Respiratory system": ["lung", "bronch", "nasopharynx"],
  "Digestive system": ["stomach", "duodenum", "jejunum", "ileum", "colon", "rectum", "appendix", "liver", "gallbladder", "pancreas", "salivary", "esophagus", "oral", "tongue"],
  "Urinary system": ["kidney", "urinary", "bladder"],
  "Endocrine system": ["adrenal", "thyroid", "pituitary", "parathyroid"],
  "Reproductive system": ["testis", "epididym", "prostate", "seminal", "ovary", "fallopian", "endometrium", "cervix", "vagina", "placenta", "breast"],
  "Immune and lymphatic system": ["blood", "bone marrow", "lymph", "spleen", "tonsil", "thymus", "immune"],
  "Musculoskeletal system": ["muscle", "skeletal", "bone", "cartilage"],
  "Skin and soft tissue": ["skin", "adipose", "soft tissue", "fibroblast"],
};

const DISPLAY_OVERRIDES = new Map<string, string>([
  ["HPA\u0000cerebral cortex", "Cerebral cortex"],
  ["HPA\u0000blood vessel", "Blood vessel"],
  ["PaxDB\u0000BRAIN", "Brain"],
  ["PaxDB\u0000ADRENAL_GLAND", "Adrenal gland"],
]);

export function tissueDisplayKey(source: string, rawTerm: string): string {
  return `${source}\u0000${rawTerm}`;
}

function displayFallback(rawTerm: string): string {
  const words = rawTerm.trim().replaceAll("_", " ").replace(/\s+/g, " ").toLocaleLowerCase();
  return words ? words[0].toLocaleUpperCase() + words.slice(1) : "Source term unavailable";
}

export function resolveTissueDisplay(source: string, rawTerm: string): TissueDisplayTerm {
  const key = tissueDisplayKey(source, rawTerm);
  const displayLabel = DISPLAY_OVERRIDES.get(key) ?? displayFallback(rawTerm);
  const normalized = displayLabel.toLocaleLowerCase();
  const bodySystem = Object.entries(BODY_SYSTEM_TERMS).find(([, terms]) => terms.some((term) => normalized.includes(term)))?.[0] ?? "Other tissues";
  return {
    key,
    source,
    rawTerm,
    displayLabel,
    bodySystem,
    order: BODY_SYSTEM_ORDER.indexOf(bodySystem as (typeof BODY_SYSTEM_ORDER)[number]),
  };
}
