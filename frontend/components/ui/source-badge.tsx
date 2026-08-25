import { ReactNode } from "react";
import { Database } from "lucide-react";
import { type VariantSourceTone } from "../../lib/variant-evidence";

export function SourceBadge({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "conflict" | VariantSourceTone }) {
  return <span className={`source-badge source-badge-${tone}`}>{tone !== "conflict" && <Database aria-hidden="true" size={14} strokeWidth={1.9} />}{children}</span>;
}
