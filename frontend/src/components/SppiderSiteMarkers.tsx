import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { HoverCard } from 'radix-ui';
import { interfaceFetch } from './InterfaceAnnotations';
import { groupSppiderMarkers, type SppiderSite } from './sppider-sites';
import type { Range } from './SequenceAnnotations';
import './sppider-site-markers.css';

type Partner = {
  partner_sequence_key: string; accessions: string[]; score: number;
  sources: { dataset_id: string; provider: string | null }[];
};
const COLORS = ['#377ca9', '#9366a8', '#47957e', '#c37d48'];
function partnerColor(key: string) {
  return COLORS[[...key].reduce((sum, char) => sum * 31 + char.charCodeAt(0) >>> 0, 0) % COLORS.length];
}

function SiteMarker({ accession, sequence, sites, range, onSelect }: {
  accession: string; sequence: string; sites: SppiderSite[]; range: Range; onSelect: (position: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState(sites[0].position);
  const [page, setPage] = useState(0);
  const details = useQuery({
    queryKey: ['sppider-marker-partners', accession, position, page], enabled: open,
    queryFn: ({ signal }) => interfaceFetch<{ items: Partner[]; has_more: boolean }>(
      `/proteins/${accession}/interface/sppider-markers/${position}?offset=${page * 6}&limit=6`, signal),
  });
  const first = sites[0].position, last = sites[sites.length - 1].position;
  const label = sites.length === 1 ? `${sequence[first - 1]}${first}` : `${first}–${last} · ${sites.length} sites`;
  const count = sites.find(site => site.position === position)?.partner_count ?? 0;
  const left = ((first + last) / 2 - range[0] + .5) / (range[1] - range[0] + 1) * 100;
  return <HoverCard.Root open={open} onOpenChange={setOpen} openDelay={150} closeDelay={220}>
    <HoverCard.Trigger asChild><button type="button" className={`sppider-site-dot ${sites.length > 1 ? 'is-cluster' : ''}`}
      style={{ left: `${left}%` }} aria-label={`SPPIDER predicted binding ${label}`} aria-expanded={open}
      onClick={() => setOpen(value => !value)} onKeyDown={event => { if (event.key === 'Escape') setOpen(false); }}>
      <span />
    </button></HoverCard.Trigger>
    <HoverCard.Portal><HoverCard.Content className="sppider-site-card" side="top" sideOffset={10} collisionPadding={18} role="dialog" aria-label="SPPIDER predicted binding partners">
      <header><div><small>SPPIDER-seq · predicted binding</small><strong>{sequence[position - 1]}{position} <span>· {count.toLocaleString()} {count === 1 ? 'partner' : 'partners'}</span></strong></div><button type="button" className="text-button" aria-label="Close predicted binding partners" onClick={() => setOpen(false)}>×</button></header>
      {sites.length > 1 && <label className="sppider-site-choice">Nearby residues<select aria-label="SPPIDER marker residue" value={position} onChange={event => { setPosition(Number(event.target.value)); setPage(0); }}>
        {sites.map(site => <option key={site.position} value={site.position}>{sequence[site.position - 1]}{site.position} · {site.partner_count} {site.partner_count === 1 ? 'partner' : 'partners'}</option>)}
      </select></label>}
      <div className="sppider-card-columns"><span>Interaction partner</span><span>PPI source</span><span>Score</span></div>
      <div className="sppider-card-partners">
        {details.isPending ? <p role="status">Loading partners…</p> : details.isError ? <p role="alert">Partners unavailable. <button onClick={() => details.refetch()}>Retry</button></p> : details.data.items.map(partner => {
          const sources = [...new Set(partner.sources.map(source => source.provider || 'Unresolved source'))];
          return <div className="sppider-card-partner" key={partner.partner_sequence_key}>
            <div><i style={{ background: partnerColor(partner.partner_sequence_key) }} /><span>{partner.accessions.length ? partner.accessions.map((id, index) => <span key={id}>{index > 0 && ' / '}<a href={`https://www.uniprot.org/uniprotkb/${encodeURIComponent(id)}/entry`} target="_blank" rel="noreferrer">{id}</a></span>) : partner.partner_sequence_key}</span></div>
            <span>{sources.join(' · ') || 'Not available'}</span><strong>{partner.score.toPrecision(4)}</strong>
          </div>;
        })}
      </div>
      {count > 6 && <nav aria-label="SPPIDER partners pagination"><button className="button" disabled={!page || details.isFetching} onClick={() => setPage(value => value - 1)}>Previous</button><span>{page * 6 + 1}–{Math.min((page + 1) * 6, count)} / {count}</span><button className="button" disabled={!details.data?.has_more || details.isFetching} onClick={() => setPage(value => value + 1)}>Next</button></nav>}
      <footer><span>Query as receptor · score ≥ 0.5</span><button className="text-button" onClick={() => { setOpen(false); onSelect(position); }}>View residue evidence →</button></footer>
      <p className="sppider-card-note">PPI sources describe the input association; sites are predicted by SPPIDER-seq. Multiple IDs on one row share a partner sequence.</p>
      <HoverCard.Arrow className="sppider-card-arrow" />
    </HoverCard.Content></HoverCard.Portal>
  </HoverCard.Root>;
}

export default function SppiderSiteMarkers({ accession, sequence, range, onSelect }: {
  accession: string; sequence: string; range: Range; onSelect: (position: number) => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1000);
  useEffect(() => {
    if (!host.current) return;
    const observer = new ResizeObserver(entries => setWidth(Math.max(1, entries[0].contentRect.width)));
    observer.observe(host.current);
    return () => observer.disconnect();
  }, []);
  const markers = useQuery({ queryKey: ['sppider-markers', accession], queryFn: ({ signal }) =>
    interfaceFetch<{ items: SppiderSite[] }>(`/proteins/${accession}/interface/sppider-markers`, signal) });
  const groups = groupSppiderMarkers(markers.data?.items ?? [], range, width);
  return <div className="sppider-axis-markers" ref={host} aria-label="SPPIDER predicted sites on residue axis">
    {markers.isPending ? <span className="sppider-axis-status">Loading predicted sites…</span> : markers.isError ? <button className="sppider-axis-status text-button" onClick={() => markers.refetch()}>Predicted sites unavailable · retry</button> : !groups.length ? <span className="sppider-axis-status">No predicted sites in this window</span> : groups.map(sites =>
      <SiteMarker key={`${accession}:${sites.map(site => site.position).join(',')}`} accession={accession} sequence={sequence} sites={sites} range={range} onSelect={onSelect} />)}
  </div>;
}
