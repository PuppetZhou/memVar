export type VariantOptionalColumn = "evidence" | "predictions" | "population";
export type VariantViewPreset = "balanced" | "clinical" | "protein" | "custom";

export const VARIANT_OPTIONAL_COLUMNS: { key: VariantOptionalColumn; label: string; description: string }[] = [
  { key: "evidence", label: "Source evidence", description: "ClinVar, COSMIC and other source-specific entry points" },
  { key: "predictions", label: "Model context", description: "AlphaMissense and ThermoMPNN outputs" },
  { key: "population", label: "Population & IDs", description: "gnomAD frequencies and dbSNP identifiers" },
];

export const VARIANT_VIEW_PRESETS: Record<Exclude<VariantViewPreset, "custom">, VariantOptionalColumn[]> = {
  balanced: ["evidence", "predictions", "population"],
  clinical: ["evidence", "population"],
  protein: ["evidence", "predictions"],
};

export function columnsForPreset(preset: Exclude<VariantViewPreset, "custom">): VariantOptionalColumn[] {
  return [...VARIANT_VIEW_PRESETS[preset]];
}

export function toggleVariantColumn(columns: VariantOptionalColumn[], column: VariantOptionalColumn): VariantOptionalColumn[] {
  return columns.includes(column) ? columns.filter((item) => item !== column) : [...columns, column];
}

export function variantTableColumnCount(columns: VariantOptionalColumn[]): number {
  // Protein variant and effect/genomic identity are the two non-hideable columns.
  return 2 + columns.length;
}
