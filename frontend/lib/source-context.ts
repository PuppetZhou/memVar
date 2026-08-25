/**
 * A source context may summarize a release or grain only when every displayed
 * record supplies the same non-empty value. Returning null prevents a UI card
 * from silently merging heterogeneous source metadata.
 */
export function sharedSourceRecordValue(records: Record<string, unknown>[], field: string): string | null {
  if (!records.length) return null;
  const values = sourceRecordValues(records, field);
  if (values.some((value) => value === null)) return null;
  return new Set(values).size === 1 ? values[0]! : null;
}

/** True when all displayed records agree, including the explicit all-missing state. */
export function sourceRecordMetadataIsUniform(records: Record<string, unknown>[], field: string): boolean {
  return records.length > 0 && new Set(sourceRecordValues(records, field)).size === 1;
}

/** User-facing fallback for source metadata absent from the current response. */
export function sourceRecordMetadataText(value: string | null | undefined): string {
  return typeof value === "string" && value.trim() ? value.trim() : "Not reported in this response";
}

function sourceRecordValues(records: Record<string, unknown>[], field: string) {
  return records.map((record) => {
    const value = record[field];
    return typeof value === "string" && value.trim() ? value.trim() : null;
  });
}
