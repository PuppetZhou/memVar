"use client";

import { useState } from "react";
import { ChevronRight } from "lucide-react";
import type { AlphaGenomeJunctionResponse, AlphaGenomeTile } from "../lib/api";

function compact(value: number) {
  if (value !== 0 && Math.abs(value) < .001) return value.toExponential(2);
  return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
}

export function AlphaGenomeJunctions({ response, tile, axisStart = tile.window_start_0based, axisEnd = tile.window_end_0based }: { response: AlphaGenomeJunctionResponse; tile: AlphaGenomeTile; axisStart?: number; axisEnd?: number }) {
  const [pinnedRank, setPinnedRank] = useState<number | null>(null);
  const width = axisEnd - axisStart;
  const x = (position: number) => 26 + ((position - axisStart) / width) * 948;
  const pinned = response.items.find((item) => item.rank === pinnedRank);
  return <div className="alphagenome-junction-figure">
    <div className="alphagenome-figure-heading"><div><strong>Reference-sequence splice-junction prediction</strong><span>Arc height and stroke encode the prepared model signal; they are not observed junction counts.</span></div><span>{response.returned_count.toLocaleString()} displayed</span></div>
    <svg viewBox="0 0 1000 250" role="group" aria-label={`Interactive prediction view with ${response.returned_count} highest predicted splice junctions in the selected model window`}>
      <line x1="26" x2="974" y1="220" y2="220" className="junction-baseline" />
      {response.items.map((item) => {
        const start = Math.max(26, Math.min(974, x(item.start_0based)));
        const end = Math.max(26, Math.min(974, x(item.end_0based)));
        const midpoint = (start + end) / 2;
        const height = Math.max(18, Math.min(180, Math.sqrt(Math.abs(end - start) / 948) * 190));
        const stroke = Math.max(1, Math.min(5, 1 + Math.log10(item.value + 1)));
        const pinnedClass = pinnedRank === item.rank ? " is-pinned" : "";
        const label = `${item.chromosome}:${(item.start_0based + 1).toLocaleString()}–${item.end_0based.toLocaleString()} · ${item.strand} · predicted signal ${compact(item.value)}`;
        return <path key={`${item.rank}-${item.start_0based}-${item.end_0based}`} className={`alphagenome-junction-path${pinnedClass}`} d={`M ${start} 220 Q ${midpoint} ${220 - height} ${end} 220`} style={{ strokeWidth: stroke }} role="button" tabIndex={0} aria-label={`${pinnedRank === item.rank ? "Unpin" : "Pin"} junction ${label}`} aria-pressed={pinnedRank === item.rank} onClick={() => setPinnedRank((current) => current === item.rank ? null : item.rank)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setPinnedRank((current) => current === item.rank ? null : item.rank); } }}><title>{label}</title></path>;
      })}
      <text x="26" y="242">{(axisStart + 1).toLocaleString()}</text><text x="974" y="242" textAnchor="end">{axisEnd.toLocaleString()}</text>
    </svg>
    <div className="alphagenome-junction-pin" role="status" aria-live="polite">{pinned ? <><strong>Pinned junction</strong><span>{pinned.chromosome}:{(pinned.start_0based + 1).toLocaleString()}–{pinned.end_0based.toLocaleString()} · {pinned.strand} strand · predicted signal {compact(pinned.value)}</span><button type="button" onClick={() => setPinnedRank(null)}>Clear pinned junction</button></> : "Select a junction arc by click, touch, or keyboard to keep its interval and value visible."}</div>
    <p className="alphagenome-junction-note">Showing {response.returned_count.toLocaleString()} of {response.available_count.toLocaleString()} prepared junctions{response.truncated ? " · highest predicted signals first" : ""}.</p>
    <details className="alphagenome-data-alternative"><summary><ChevronRight aria-hidden="true" size={16} strokeWidth={2} />View junction table</summary><div className="table-scroll"><table><thead><tr><th>Rank</th><th>GRCh38 interval</th><th>Strand</th><th>Predicted signal</th></tr></thead><tbody>{response.items.map((item) => <tr key={`${item.rank}-${item.start_0based}`}><td>{item.rank}</td><td>{item.chromosome}:{(item.start_0based + 1).toLocaleString()}–{item.end_0based.toLocaleString()}</td><td>{item.strand}</td><td>{compact(item.value)}</td></tr>)}</tbody></table></div></details>
  </div>;
}
