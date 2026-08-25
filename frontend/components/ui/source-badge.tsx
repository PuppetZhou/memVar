import { ReactNode } from "react";
import { Database } from "lucide-react";

export function SourceBadge({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "conflict" }) {
  return <span className={`source-badge source-badge-${tone}`}>{tone === "default" && <Database aria-hidden="true" size={14} strokeWidth={1.9} />}{children}</span>;
}
