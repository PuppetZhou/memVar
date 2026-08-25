"use client";

import { ReactNode, useId } from "react";

export function Tooltip({ label, children }: { label: ReactNode; children: ReactNode }) {
  const id = useId();
  return <span className="ui-tooltip"><span tabIndex={0} aria-describedby={id}>{children}</span><span id={id} role="tooltip" className="ui-tooltip-content">{label}</span></span>;
}
