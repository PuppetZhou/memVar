import { useMemo, useState } from "react";
import { ExpressionGroup, ExpressionItem, ExpressionModality } from "../../lib/api";
import { Disclosure } from "../ui/disclosure";
import { SourceContext } from "../ui/source-context";
import { EXPRESSION_SPECS, ExpressionDisplayGroup, detailText, formatExpressionValue, formatSourceRelease, ihcLevel, modalityGroups, numericValue, sourceTerm } from "./model";
import { ExpressionModalityIcon } from "./modality-icon";

type SortMode = "body" | "name" | "value";

function valueSortKey(group: ExpressionDisplayGroup): number {
  return Math.max(-Infinity, ...group.items.map(numericValue).filter((value): value is number => value !== null));
}

function compareIhcDistribution(left: ExpressionDisplayGroup, right: ExpressionDisplayGroup): number {
  for (const level of ["High", "Medium", "Low", "Not detected", "Missing"] as const) {
    const difference = right.items.filter((item) => ihcLevel(item.raw_value) === level).length - left.items.filter((item) => ihcLevel(item.raw_value) === level).length;
    if (difference) return difference;
  }
  return left.displayLabel.localeCompare(right.displayLabel);
}

function itemContext(item: ExpressionItem): string {
  return detailText(item, "paxdb_dataset_name") ?? detailText(item, "paxdb_dataset_id") ?? detailText(item, "cell_type") ?? "Not applicable";
}

function DetailGroup({ modality, group }: { modality: ExpressionModality; group: ExpressionDisplayGroup }) {
  return <article id={`expression-detail-${modality}-${encodeURIComponent(group.columnId)}`} className="expression-detail-group" tabIndex={-1}>
    <header><div><h4>{group.displayLabel}</h4><p>{group.bodySystem} · raw term{group.rawTerms.length === 1 ? "" : "s"}: {group.rawTerms.join(", ")}</p></div><strong>{group.items.length} {modality === "paxdb" ? (group.items.length === 1 ? "dataset" : "datasets") : (group.items.length === 1 ? "record" : "records")}</strong></header>
    <div className="table-scroll"><table className="expression-detail-table"><thead><tr><th>Raw tissue/organ</th><th>Raw value</th><th>Unit</th><th>{modality === "paxdb" ? "Dataset" : modality === "hpa_ihc" ? "Cell type" : "Source identifier"}</th><th>Reliability</th><th>Source/release</th></tr></thead>
      <tbody>{group.items.map((item, index) => <tr key={`${sourceTerm(item)}-${itemContext(item)}-${index}`}><th scope="row">{sourceTerm(item)}</th><td>{formatExpressionValue(item.raw_value)}</td><td>{item.unit}</td><td>{itemContext(item)}</td><td>{detailText(item, "reliability") ?? "Not applicable"}</td><td>{item.source_database} · {formatSourceRelease(item.source_release)}</td></tr>)}</tbody>
    </table></div>
  </article>;
}

export function ExpressionDetails({ group, open, onToggle }: { group: ExpressionGroup; open: boolean; onToggle: () => void }) {
  const [showAll, setShowAll] = useState(false);
  const [sort, setSort] = useState<SortMode>("body");
  const spec = EXPRESSION_SPECS.find((item) => item.key === group.modality)!;
  const grouped = useMemo(() => {
    const items = modalityGroups(group);
    return [...items].sort((left, right) => sort === "name" ? left.displayLabel.localeCompare(right.displayLabel) : sort === "value" ? (group.modality === "hpa_ihc" ? compareIhcDistribution(left, right) : valueSortKey(right) - valueSortKey(left) || left.displayLabel.localeCompare(right.displayLabel)) : left.order - right.order || left.displayLabel.localeCompare(right.displayLabel));
  }, [group, sort]);
  const visible = showAll ? grouped : grouped.slice(0, 12);
  const missing = group.items.filter((item) => item.raw_value === null || item.raw_value === undefined || item.raw_value === "").length;
  const sources = Array.from(new Set(group.items.map((item) => item.source_database))).join(", ") || "Source unavailable";
  const releases = Array.from(new Set(group.items.map((item) => formatSourceRelease(item.source_release)))).join(", ") || "release unavailable";
  const summary = <span className="expression-disclosure-summary"><strong><ExpressionModalityIcon modality={group.modality} />{spec.label}</strong><span><b>{grouped.length}</b> tissues/organs · <b>{group.items.length}</b> records · {spec.unit}{missing ? ` · ${missing} missing` : ""}</span></span>;

  return <Disclosure id={`expression-details-${group.modality}`} open={open} onToggle={onToggle} label={summary} className={`expression-modality-disclosure modality-${group.modality}`}>
    <SourceContext source={sources} release={releases} recordGrain={`Tissue-level ${spec.label} source records`} caveat={`Values use the source ${spec.unit} unit; raw terms and missing states remain source-specific.`} className="expression-source-context" />
    <div className="expression-detail-toolbar"><label>Sort groups<select value={sort} onChange={(event) => setSort(event.target.value as SortMode)}><option value="body">Body system</option><option value="name">Name</option><option value="value">{group.modality === "hpa_ihc" ? "Staining distribution" : "Highest individual value"}</option></select></label></div>
    <div className="expression-detail-groups">{visible.map((item, index) => <div key={item.columnId}>{showAll && (index === 0 || visible[index - 1]?.bodySystem !== item.bodySystem) && sort === "body" && <h3 className="expression-body-system">{item.bodySystem}</h3>}<DetailGroup modality={group.modality} group={item} /></div>)}</div>
    {grouped.length > 12 && <button className="quiet-button expression-show-all" type="button" onClick={() => setShowAll((current) => !current)}>{showAll ? "Show first 12 tissues" : `Show all ${grouped.length} tissues`}</button>}
  </Disclosure>;
}
