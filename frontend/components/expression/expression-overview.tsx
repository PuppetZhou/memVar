import { CSSProperties } from "react";
import { ExpressionGroup, ExpressionItem, ExpressionModality } from "../../lib/api";
import { resolveTissueDisplay } from "../../lib/tissue-display-crosswalk";
import { EXPRESSION_SPECS, ExpressionDisplayGroup, IHC_LEVELS, detailText, formatExpressionValue, formatSourceRelease, ihcLevel, modalityGroups, numericScaleMaximum, numericValue, sourceTerm, transformedValue } from "./model";
import { ExpressionModalityIcon } from "./modality-icon";

type Props = {
  groups: Partial<Record<ExpressionModality, ExpressionGroup>>;
  onSelect: (modality: ExpressionModality, columnId: string) => void;
};

function mixHex(low: string, high: string, amount: number): string {
  const parse = (value: string) => [1, 3, 5].map((index) => Number.parseInt(value.slice(index, index + 2), 16));
  const [lr, lg, lb] = parse(low); const [hr, hg, hb] = parse(high);
  const channel = (left: number, right: number) => Math.round(left + (right - left) * Math.max(0, Math.min(1, amount))).toString(16).padStart(2, "0");
  return `#${channel(lr, hr)}${channel(lg, hg)}${channel(lb, hb)}`;
}

function cellValueSummary(modality: ExpressionModality, items: ExpressionItem[], unit: string): string {
  if (modality === "hpa_ihc") {
    const counts = IHC_LEVELS.map((level) => [level, items.filter((item) => ihcLevel(item.raw_value) === level).length] as const).filter(([, count]) => count > 0);
    const missing = items.filter((item) => ihcLevel(item.raw_value) === "Missing").length;
    return [...counts.map(([level, count]) => `${level} ${count}`), missing ? `Missing ${missing}` : ""].filter(Boolean).join(" · ");
  }
  const values = items.map(numericValue).filter((value): value is number => value !== null);
  if (!values.length) return `Missing ${unit}`;
  if (values.length === 1) return `${formatExpressionValue(values[0])} ${unit}`;
  return `${formatExpressionValue(Math.min(...values))}–${formatExpressionValue(Math.max(...values))} ${unit}`;
}

function numericSegments(spec: (typeof EXPRESSION_SPECS)[number], group: ExpressionDisplayGroup, maximum: number) {
  return group.items.map((item, index) => {
    const value = numericValue(item);
    const intensity = value === null || maximum === 0 ? 0 : Math.min(1, transformedValue(spec.key, value) / maximum);
    return <i key={index} className={value === null ? "is-null" : value === 0 ? "is-zero" : ""} style={value === null ? undefined : { "--expression-fill": mixHex(spec.low, spec.high, intensity) } as CSSProperties} />;
  });
}

function ihcSegments(items: ExpressionItem[]) {
  const levels = [...IHC_LEVELS, "Missing"] as const;
  return levels.map((level) => {
    const count = items.filter((item) => ihcLevel(item.raw_value) === level).length;
    if (!count) return null;
    return <i key={level} className={`ihc-${level.toLocaleLowerCase().replaceAll(" ", "-")}`} style={{ flexGrow: count }}><span className="sr-only">{count} {level}</span></i>;
  });
}

function ExpressionCell({ modality, group, maximum, onSelect }: { modality: ExpressionModality; group: ExpressionDisplayGroup | undefined; maximum: number; onSelect: () => void }) {
  if (!group) return <span className="expression-cell no-records" aria-label="No source record for this display tissue"><span aria-hidden="true">—</span></span>;
  const spec = EXPRESSION_SPECS.find((item) => item.key === modality)!;
  const description = `${spec.label} · ${group.displayLabel}. ${cellValueSummary(modality, group.items, spec.unit)}. ${group.items.length} source ${group.items.length === 1 ? "record" : "records"}.`;
  return <button type="button" className={`expression-cell has-records modality-${modality}`} title={description} aria-label={`${description}. Open source details.`} onClick={onSelect}>
    <span className="expression-cell-strips" aria-hidden="true">{modality === "hpa_ihc" ? ihcSegments(group.items) : numericSegments(spec, group, maximum)}</span>
    <span role="tooltip" className="expression-cell-tooltip"><strong>{spec.label} · {group.displayLabel}</strong><span>{cellValueSummary(modality, group.items, spec.unit)}</span><small>{group.items.length} source {group.items.length === 1 ? "record" : "records"} · Open details</small></span>
  </button>;
}

export function ExpressionOverview({ groups, onSelect }: Props) {
  const grouped = Object.fromEntries(EXPRESSION_SPECS.map((spec) => [spec.key, modalityGroups(groups[spec.key])])) as Record<ExpressionModality, ExpressionDisplayGroup[]>;
  const columnMap = new Map<string, ExpressionDisplayGroup>();
  for (const modality of EXPRESSION_SPECS) for (const group of grouped[modality.key]) if (!columnMap.has(group.columnId)) columnMap.set(group.columnId, group);
  const columns = Array.from(columnMap.values()).sort((left, right) => left.order - right.order || left.displayLabel.localeCompare(right.displayLabel));
  const maxima = Object.fromEntries(EXPRESSION_SPECS.map((spec) => [spec.key, numericScaleMaximum(groups[spec.key])])) as Record<ExpressionModality, number>;

  if (!columns.length) return <p className="empty-value">No expression records are available for this protein.</p>;
  const style = { "--expression-columns": columns.length } as CSSProperties;
  return <>
    <div className="expression-overview-scroll">
      <div className="expression-overview-grid" style={style}>
        <span className="expression-corner">Modality</span>
        {columns.map((column) => <span className="expression-column-label" key={column.columnId} title={`${column.bodySystem}; display navigation label only`}>{column.displayLabel}</span>)}
        {EXPRESSION_SPECS.map((spec) => <div className="expression-grid-row" key={spec.key}>
          <div className={`expression-row-label modality-${spec.key}`}><strong><ExpressionModalityIcon modality={spec.key} />{spec.label}</strong><span>{spec.unit}</span></div>
          {columns.map((column) => <ExpressionCell key={column.columnId} modality={spec.key} group={grouped[spec.key].find((item) => item.columnId === column.columnId)} maximum={maxima[spec.key]} onSelect={() => onSelect(spec.key, column.columnId)} />)}
        </div>)}
      </div>
    </div>
    <div className="expression-legends" aria-label="Independent expression legends">
      {EXPRESSION_SPECS.map((spec) => <div className={`modality-${spec.key}`} key={spec.key}><strong><ExpressionModalityIcon modality={spec.key} />{spec.label}</strong><small>{spec.unit}</small>{spec.key === "hpa_ihc" ? <span className="ihc-legend">{IHC_LEVELS.map((level) => <i key={level} className={`ihc-${level.toLocaleLowerCase().replaceAll(" ", "-")}`}>{level}</i>)}</span> : <><i className="expression-gradient" style={{ background: `linear-gradient(90deg, ${spec.low}, ${spec.high})` }} /><span className="expression-scale-key"><b>0 / zero</b><b>95th percentile (capped)</b></span></>}</div>)}
    </div>
    <details className="expression-scale-notes"><summary>Scale and missing-value notes</summary><div>{EXPRESSION_SPECS.map((spec) => <p key={spec.key}><strong><ExpressionModalityIcon modality={spec.key} />{spec.label}</strong><span>{spec.explanation}</span></p>)}<p><strong>Missing values</strong><span>Hatched cells are missing source measurements; bordered pale cells are measured zero. Display columns aid navigation and do not imply cross-source biological equivalence.</span></p></div></details>
    <details className="expression-accessible-table">
      <summary>View accessible source-record table</summary>
      <div className="table-scroll"><table><thead><tr><th>Modality</th><th>Display group</th><th>Raw tissue/organ</th><th>Raw value</th><th>Unit</th><th>Source/release</th><th>Dataset or cell type</th><th>Reliability</th></tr></thead>
        <tbody>{EXPRESSION_SPECS.flatMap((spec) => (groups[spec.key]?.items ?? []).map((item, index) => { const term = resolveTissueDisplay(item.source_database, sourceTerm(item)); return <tr key={`${spec.key}-${sourceTerm(item)}-${index}`}><th scope="row">{spec.label}</th><td>{term.displayLabel}</td><td>{sourceTerm(item)}</td><td>{formatExpressionValue(item.raw_value)}</td><td>{item.unit}</td><td>{item.source_database} · {formatSourceRelease(item.source_release)}</td><td>{detailText(item, "paxdb_dataset_name") ?? detailText(item, "paxdb_dataset_id") ?? detailText(item, "cell_type") ?? "Not applicable"}</td><td>{detailText(item, "reliability") ?? "Not applicable"}</td></tr>; }))}</tbody>
      </table></div>
    </details>
  </>;
}
