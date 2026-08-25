import { ReactNode } from "react";
import { Button } from "./button";

export function Disclosure({ open, onToggle, label, children, id, className = "" }: { open: boolean; onToggle: () => void; label: ReactNode; children: ReactNode; id: string; className?: string }) {
  return <div className={`ui-disclosure ${className}`.trim()}>
    <Button variant="quiet" className="disclosure-trigger" type="button" aria-expanded={open} aria-controls={id} onClick={onToggle}><span aria-hidden="true">{open ? "▾" : "▸"}</span>{label}</Button>
    {open && <div id={id} className="disclosure-panel" data-open="true">{children}</div>}
  </div>;
}
