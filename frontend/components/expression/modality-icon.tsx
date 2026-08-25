import { Database, Dna, Microscope, ScanLine } from "lucide-react";
import { ExpressionModality } from "../../lib/api";

const ICONS = {
  hpa_rna: Dna,
  hpa_ms: ScanLine,
  hpa_ihc: Microscope,
  paxdb: Database,
} satisfies Record<ExpressionModality, typeof Dna>;

export function ExpressionModalityIcon({ modality }: { modality: ExpressionModality }) {
  const Icon = ICONS[modality];
  return <Icon className={`expression-modality-icon modality-${modality}`} aria-hidden="true" size={16} strokeWidth={2} />;
}
