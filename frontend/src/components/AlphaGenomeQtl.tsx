import { useState, type CSSProperties } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, X } from 'lucide-react';
import { api, number, params } from '../api';
import { GenomeInspector } from './AlphaGenomeInspect';
import {
  GENOMIC_PLOT,
  positionInView,
  projectX,
  type GenomicView,
} from './genomic-coordinates';
export type QtlDataset = {
  dataset_id: string;
  tissue: string;
  qtl_type: string;
  records: number;
};
const names: Record<string, string> = {
  eqtl: 'eQTL',
  sqtl: 'sQTL',
  apaqtl: 'apaQTL',
};
const colors: Record<string, string> = {
  eqtl: '#67a583',
  sqtl: '#7b95c6',
  apaqtl: '#f59c7c',
};
const tissueName = (s: string) => s.replaceAll('_', ' ');
export function QtlPicker({
  accession,
  gene,
  selected,
  onChange,
  onClose,
}: {
  accession: string;
  gene: string;
  selected: QtlDataset[];
  onChange: (items: QtlDataset[]) => void;
  onClose: () => void;
}) {
  const [tissue, setTissue] = useState('');
  const query = useQuery({
    queryKey: ['qtl-track-catalog', accession, gene],
    queryFn: ({ signal }) =>
      api<{ items: QtlDataset[] }>(
        `/proteins/${accession}/qtl/tracks?${params({ gene })}`,
        signal
      ),
  });
  const items = query.data?.items ?? [],
    tissues = [...new Set(items.map((d) => d.tissue))];
  return (
    <div className="agx-library agx-qtl-library">
      <div className="agx-library-heading">
        <h4>Add GTEx QTL tracks</h4>
        <button aria-label="Close QTL picker" onClick={onClose}>
          <X size={16} />
        </button>
      </div>
      {query.isPending ? (
        <p className="agx-selection-prompt">Loading GTEx tissues…</p>
      ) : query.error ? (
        <p role="alert">
          Could not load QTL tissues.{' '}
          <button onClick={() => query.refetch()}>Retry</button>
        </p>
      ) : !items.length ? (
        <p className="agx-selection-prompt">
          No GTEx QTL associations for this gene.
        </p>
      ) : (
        <>
          <div className="agx-picker-controls">
            <label className="agx-selector">
              <span>GTEx tissue</span>
              <select
                aria-label="GTEx tissue"
                data-selected={Boolean(tissue)}
                value={tissue}
                onChange={(e) => setTissue(e.target.value)}
              >
                <option value="" disabled>
                  Select tissue…
                </option>
                {tissues.map((t) => (
                  <option key={t} value={t}>
                    {tissueName(t)}
                  </option>
                ))}
              </select>
            </label>
            <span className="agx-selection-prompt">
              Independent of AlphaGenome biosamples
            </span>
          </div>
          {tissue ? (
            <div className="agx-library-results">
              {items
                .filter((d) => d.tissue === tissue)
                .map((d) => {
                  const added = selected.some(
                    (s) => s.dataset_id === d.dataset_id
                  );
                  return (
                    <div className="agx-candidate" key={d.dataset_id}>
                      <div>
                        <strong>{names[d.qtl_type]}</strong>
                        <span>
                          {d.records.toLocaleString()} gene-associated records
                        </span>
                      </div>
                      <button
                        className="agx-track-toggle"
                        aria-label={`${added ? 'Remove' : 'Add'} ${names[d.qtl_type]} ${tissueName(d.tissue)}`}
                        aria-pressed={added}
                        onClick={() =>
                          onChange(
                            added
                              ? selected.filter(
                                  (s) => s.dataset_id !== d.dataset_id
                                )
                              : [...selected, d]
                          )
                        }
                      >
                        {added ? <X size={14} /> : <Plus size={14} />}{' '}
                        {added ? 'Remove' : 'Add'}
                      </button>
                    </div>
                  );
                })}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
type Row = {
  source_row: number;
  variant_id: string;
  position: number;
  phenotype_id: string;
  pval_nominal: number | null;
  slope: number | null;
  slope_se: number | null;
  pval_nominal_threshold: number | null;
};
type Result = { items: Row[]; total: number; has_more: boolean };
export function QtlTrack({
  accession,
  gene,
  dataset,
  chromosome,
  view,
  hoverPosition,
  onHover,
  onRemove,
}: {
  accession: string;
  gene: string;
  dataset: QtlDataset;
  chromosome: string;
  view: GenomicView;
  hoverPosition: number | null;
  onHover: (p: number | null) => void;
  onRemove: () => void;
}) {
  const [offset, setOffset] = useState(0),
    [active, setActive] = useState<Row | null>(null);
  const query = useQuery({
    queryKey: [
      'qtl-track',
      accession,
      gene,
      dataset.dataset_id,
      chromosome,
      ...view,
      offset,
    ],
    queryFn: ({ signal }) =>
      api<Result>(
        `/proteins/${accession}/qtl/track?${params({ gene, dataset: dataset.dataset_id, chromosome, start: view[0], end: view[1], offset })}`,
        signal
      ),
  });
  const items = query.data?.items ?? [],
    valid = items.filter(
      (r) =>
        r.pval_nominal !== null && r.pval_nominal > 0 && r.pval_nominal <= 1
    ),
    max = Math.max(1, ...valid.map((r) => -Math.log10(r.pval_nominal!))),
    color = colors[dataset.qtl_type];
  const x = (p: number) => projectX(p - 1, view),
    y = (r: Row) => 110 - (-Math.log10(r.pval_nominal!) / max) * 90;
  return (
    <article
      className="agx-track agx-qtl-track"
      style={{ '--ag-color': color } as CSSProperties}
    >
      <header>
        <div className="agx-track-title">
          <span className="agx-track-kind">{names[dataset.qtl_type]}</span>
          <strong>{tissueName(dataset.tissue)}</strong>
          <small>GTEx v11 · association</small>
        </div>
        <div className="agx-track-actions">
          <button
            aria-label={`Remove QTL track ${dataset.dataset_id}`}
            onClick={onRemove}
          >
            <X size={15} />
          </button>
        </div>
      </header>
      <div className="agx-track-body">
        <div className="agx-track-meta">−log₁₀(P)</div>
        {query.isPending ? (
          <p>Loading QTL associations…</p>
        ) : query.error ? (
          <p role="alert">
            Could not load this QTL track.{' '}
            <button onClick={() => query.refetch()}>Retry</button>
          </p>
        ) : (
          <>
            <div
              className="agx-plot-frame"
              onMouseLeave={() => {
                setActive(null);
                onHover(null);
              }}
            >
              <svg
                className="agx-signal agx-qtl-plot"
                viewBox="0 0 1000 130"
                preserveAspectRatio="none"
                role="img"
                aria-label={`${names[dataset.qtl_type]} ${tissueName(dataset.tissue)} association positions. Drag to zoom.`}
              >
                {[0, 0.5, 1].map((f) => (
                  <g key={f}>
                    <line
                      x1={GENOMIC_PLOT.left}
                      x2={GENOMIC_PLOT.right}
                      y1={110 - f * 90}
                      y2={110 - f * 90}
                      stroke="#d9dcdf"
                    />
                    <text
                      x="44"
                      y={114 - f * 90}
                      textAnchor="end"
                      fontSize="11"
                      fill="#303438"
                    >
                      {number(max * f, 2)}
                    </text>
                  </g>
                ))}
                {valid.map((r) => (
                  <circle
                    key={r.source_row}
                    cx={x(r.position)}
                    cy={y(r)}
                    r="3.5"
                    fill={color}
                    tabIndex={0}
                    aria-label={`${r.variant_id}, P ${r.pval_nominal}, ${r.phenotype_id}`}
                    onMouseEnter={() => {
                      setActive(r);
                      onHover(r.position);
                    }}
                    onFocus={() => {
                      setActive(r);
                      onHover(r.position);
                    }}
                    onBlur={() => {
                      setActive(null);
                      onHover(null);
                    }}
                  />
                ))}
                {hoverPosition !== null &&
                  positionInView(hoverPosition, view) && (
                    <line
                      x1={x(hoverPosition)}
                      x2={x(hoverPosition)}
                      y1="8"
                      y2="115"
                      stroke="#2656c9"
                      pointerEvents="none"
                    />
                  )}
              </svg>
              {active && (
                <GenomeInspector
                  title={`GTEx · ${names[dataset.qtl_type]} · ${tissueName(dataset.tissue)}`}
                  coordinate={`${chromosome}:${active.position.toLocaleString()} ${active.variant_id.split('_').slice(2, 4).join(' → ')}`}
                >
                  <dl>
                    <div>
                      <dt>Nominal P</dt>
                      <dd>{number(active.pval_nominal, 5)}</dd>
                    </div>
                    <div>
                      <dt>Effect · slope</dt>
                      <dd>{number(active.slope, 5)}</dd>
                    </div>
                  </dl>
                  <p className="agx-inspector-note">{active.phenotype_id}</p>
                </GenomeInspector>
              )}
            </div>
            <div className="agx-inspect">
              {query.data?.total
                ? `${offset + 1}–${offset + items.length} of ${query.data.total.toLocaleString()} associations in view`
                : 'No associations in this interval'}
            </div>
            {items.length !== valid.length && (
              <p className="agx-footnote">
                {items.length - valid.length} records have zero, missing or
                invalid P and cannot be plotted on a logarithmic axis; original
                values remain below.
              </p>
            )}
            <details>
              <summary>Association records · original values</summary>
              <div className="agx-junction-table">
                <table>
                  <thead>
                    <tr>
                      <th>Variant</th>
                      <th>Phenotype</th>
                      <th>P</th>
                      <th>Slope</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((r) => (
                      <tr key={r.source_row}>
                        <td>{r.variant_id}</td>
                        <td>{r.phenotype_id}</td>
                        <td>{number(r.pval_nominal, 5)}</td>
                        <td>{number(r.slope, 5)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
            {(offset > 0 || query.data?.has_more) && (
              <div className="agx-qtl-pages">
                <button
                  disabled={!offset}
                  onClick={() => {
                    setActive(null);
                    setOffset(Math.max(0, offset - 2000));
                  }}
                >
                  Previous
                </button>
                <span>Source order · 2,000 per page</span>
                <button
                  disabled={!query.data?.has_more}
                  onClick={() => {
                    setActive(null);
                    setOffset(offset + 2000);
                  }}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </article>
  );
}
