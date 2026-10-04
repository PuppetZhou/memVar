import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { X } from 'lucide-react';
import { api, params } from '../api';
import { StructurePredictorSite, type PredictorExtrema, type PredictorSite } from './StructurePredictor';
import { ClinicalBadge } from './VariantEvidencePanels';
import './structure-site.css';

type SiteVariant = {
  variant_id: string;
  annotation_id: string;
  canonical_positions?: { position: number; ref_aa?: string; alt_aa?: string }[];
  clinvar?: { classification?: string | null; oncogenicity?: string | null }[];
};

/** Only verified canonical mappings supply the substitution; clinical labels stay source-specific. */
export default function StructureSiteInspector({ accession, position, residue, chain, onClose, onEnter, onLeave, predictor }: {
  accession: string; position: number; residue: string; chain: string;
  predictor?:{data?:PredictorExtrema;site?:PredictorSite;loading:boolean};
  onClose: () => void; onEnter: () => void; onLeave: () => void;
}) {
  const query = useQuery({
    queryKey: ['structure-site-variants', accession, position],
    queryFn: ({ signal }) => api<{ items: SiteVariant[]; next_cursor: string | null }>(
      `/proteins/${accession}/variants?${params({ canonical_start: position, canonical_end: position, limit: 8, predictors: 'none' })}`, signal),
    staleTime: 300000,
  });
  const rows = query.data?.items ?? [];
  return <aside className="structure-site-inspector" aria-label={`Residue ${residue}${position} variant summary`}
    onMouseEnter={onEnter} onMouseLeave={onLeave} onFocusCapture={onEnter} onKeyDown={event => { if (event.key === 'Escape') onClose(); }}>
    <header><div><strong>{residue}{position}</strong><span>Chain {chain} · canonical position</span></div><button aria-label="Close residue summary" onClick={onClose}><X size={16}/></button></header>
    {predictor&&<StructurePredictorSite accession={accession} {...predictor}/>}
    <div className="structure-site-columns"><span>Substitution</span><span>ClinVar classification</span></div>
    <div className="structure-site-records">
      {query.isPending ? <p>Loading variant evidence…</p> : query.isError ? <p role="alert">Variant evidence unavailable. <button onClick={() => query.refetch()}>Retry</button></p> : !rows.length ? <p>No verified variants recorded at this residue.</p> : rows.map(row => {
        const mapped = row.canonical_positions?.find(item => item.position === position);
        const classifications = [...new Set(row.clinvar?.map(item => item.classification).filter(value => value && value !== '-' && value !== '.') ?? [])];
        const oncogenicity = [...new Set(row.clinvar?.map(item => item.oncogenicity).filter(value => value && value !== '-' && value !== '.') ?? [])];
        return <article key={`${row.variant_id}:${row.annotation_id}`}>
          <div><strong>{mapped?.ref_aa ?? '?'}{position} → {mapped?.alt_aa ?? '?'}</strong><small>{row.variant_id.replace(/^GRCh38:/, '')}</small></div>
          <div>{classifications.length ? classifications.map(value => <ClinicalBadge key={value} value={value}/>) : <span className="structure-site-unclassified">Not classified</span>}
            {oncogenicity.map(value => <small key={value}>Oncogenicity: {value}</small>)}</div>
        </article>;
      })}
    </div>
    <footer><span>{query.data?.next_cursor ? 'First 8 annotation rows · ' : ''}Reference structure; substitutions are annotations.</span>
      <Link to={`/protein/${accession}?variants_canonical_start=${position}&variants_canonical_end=${position}&variants_range_origin=structure#variants`}>View variant evidence →</Link></footer>
  </aside>;
}
