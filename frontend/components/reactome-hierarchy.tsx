"use client";

import { ChevronRight, ExternalLink } from "lucide-react";
import { type KeyboardEvent, useEffect, useMemo, useState } from "react";
import { ReactomeHierarchyNode, ReactomeHierarchyResponse } from "../lib/api";
import { useJsonResource } from "../lib/use-json-resource";

type HierarchyIndex = {
  nodes: Map<string, ReactomeHierarchyNode>;
  roots: ReactomeHierarchyNode[];
  canonicalParents: Map<string, string | null>;
};

function pathwayName(node: ReactomeHierarchyNode) {
  return node.pathway_name?.trim() || "Unnamed Reactome pathway";
}

function compareNodes(left: ReactomeHierarchyNode, right: ReactomeHierarchyNode) {
  return pathwayName(left).localeCompare(pathwayName(right), "en", { sensitivity: "base" })
    || left.pathway_id.localeCompare(right.pathway_id);
}

function buildIndex(response: ReactomeHierarchyResponse): HierarchyIndex {
  const nodes = new Map(response.nodes.map((node) => [node.pathway_id, node]));
  const roots = response.roots.flatMap((id) => {
    const node = nodes.get(id);
    return node ? [node] : [];
  }).sort(compareNodes);
  const canonicalParents = new Map<string, string | null>();

  for (const node of response.nodes) {
    const parents = node.parent_ids.flatMap((id) => {
      const parent = nodes.get(id);
      return parent ? [parent] : [];
    }).sort(compareNodes);
    canonicalParents.set(node.pathway_id, parents[0]?.pathway_id ?? null);
  }

  return { nodes, roots, canonicalParents };
}

function orderedChildren(node: ReactomeHierarchyNode, nodes: Map<string, ReactomeHierarchyNode>) {
  return node.child_ids.flatMap((id) => {
    const child = nodes.get(id);
    return child ? [child] : [];
  }).sort(compareNodes);
}

function branchSize(rootId: string, nodes: Map<string, ReactomeHierarchyNode>) {
  const visited = new Set<string>();
  const pending = [rootId];
  while (pending.length) {
    const id = pending.pop()!;
    if (visited.has(id)) continue;
    visited.add(id);
    const node = nodes.get(id);
    if (node) pending.push(...node.child_ids);
  }
  return visited.size;
}

function canonicalPath(id: string, canonicalParents: Map<string, string | null>) {
  const path: string[] = [];
  const visited = new Set<string>();
  let current: string | null | undefined = id;
  while (current && !visited.has(current)) {
    visited.add(current);
    path.push(current);
    current = canonicalParents.get(current);
  }
  return path.reverse();
}

function domToken(id: string) {
  return id.replace(/[^a-zA-Z0-9_-]/g, "-");
}

function countLabel(value: number, singular: string, plural = `${singular}s`) {
  return `${value.toLocaleString()} ${value === 1 ? singular : plural}`;
}

function EvidenceSummary({ node }: { node: ReactomeHierarchyNode }) {
  const codes = node.evidence_codes.filter(Boolean);
  if (!codes.length && node.evidence_count === null) return null;
  return <span className="reactome-evidence">
    {codes.length ? `Evidence ${codes.join(", ")}` : "Evidence available"}
    {node.evidence_count !== null && ` · ${countLabel(node.evidence_count, "record")}`}
  </span>;
}

type BranchProps = {
  node: ReactomeHierarchyNode;
  index: HierarchyIndex;
  expanded: Set<string>;
  onToggle: (id: string) => void;
  onLocate: (id: string) => void;
  root?: boolean;
};

function PathwayBranch({ node, index, expanded, onToggle, onLocate, root = false }: BranchProps) {
  const children = orderedChildren(node, index.nodes);
  const open = expanded.has(node.pathway_id);
  const token = domToken(node.pathway_id);
  const panelId = `reactome-children-${token}`;
  const triggerId = `reactome-trigger-${token}`;
  const occurrenceId = `reactome-node-${token}`;
  const isShared = node.parent_ids.length > 1;

  function handleEscape(event: KeyboardEvent<HTMLLIElement>) {
    if (event.key !== "Escape" || !open) return;
    event.stopPropagation();
    onToggle(node.pathway_id);
    window.requestAnimationFrame(() => document.getElementById(triggerId)?.focus());
  }

  return <li className={root ? "reactome-root-item" : "reactome-tree-item"} onKeyDown={handleEscape}>
    <div id={occurrenceId} className={root ? "reactome-root-row" : "reactome-node-row"} tabIndex={-1}>
      <div className="reactome-node-main">
        {children.length ? <button
          id={triggerId}
          className="reactome-disclosure"
          type="button"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => onToggle(node.pathway_id)}
        >
          <span className="reactome-chevron" aria-hidden="true"><ChevronRight size={18} strokeWidth={2.25} /></span>
          <span className="reactome-pathway-copy">
            <strong>{pathwayName(node)}</strong>
            {root
              ? <span>{countLabel(branchSize(node.pathway_id, index.nodes), "pathway")} in this branch · {countLabel(children.length, "immediate subpathway")}</span>
              : <span>{countLabel(children.length, "immediate subpathway")}</span>}
          </span>
        </button> : <div className="reactome-leaf-copy">
          <span className="reactome-leaf-marker" aria-hidden="true" />
          <span className="reactome-pathway-copy"><strong>{pathwayName(node)}</strong><span>Terminal pathway in this view</span></span>
        </div>}
        <div className="reactome-node-meta">
          {isShared && <span className="reactome-shared-badge">Shared pathway</span>}
          <EvidenceSummary node={node} />
        </div>
      </div>
      {node.pathway_url && <a className="reactome-external-link" href={node.pathway_url} target="_blank" rel="noreferrer" aria-label={`Open ${pathwayName(node)} in Reactome (new tab)`}><span>Reactome</span><ExternalLink size={15} strokeWidth={2.25} aria-hidden="true" /></a>}
    </div>
    {children.length > 0 && open && <ul id={panelId} className="reactome-branch-list">
      {children.map((child) => index.canonicalParents.get(child.pathway_id) === node.pathway_id
        ? <PathwayBranch key={child.pathway_id} node={child} index={index} expanded={expanded} onToggle={onToggle} onLocate={onLocate} />
        : <SharedPathwayReference key={child.pathway_id} node={child} onLocate={onLocate} />)}
    </ul>}
  </li>;
}

function SharedPathwayReference({ node, onLocate }: { node: ReactomeHierarchyNode; onLocate: (id: string) => void }) {
  return <li className="reactome-tree-item reactome-shared-reference">
    <div className="reactome-shared-copy">
      <span className="reactome-shared-marker" aria-hidden="true"><ChevronRight size={17} strokeWidth={2.25} /></span>
      <span><strong>{pathwayName(node)}</strong><small>Shared pathway · fully shown under another parent</small></span>
    </div>
    <button type="button" className="reactome-locate-button" onClick={() => onLocate(node.pathway_id)} aria-label={`Show the main branch for ${pathwayName(node)}`}>Show main branch</button>
  </li>;
}

export function ReactomeHierarchy({ accession }: { accession: string }) {
  const state = useJsonResource<ReactomeHierarchyResponse>(
    `/proteins/${encodeURIComponent(accession)}/reactome-hierarchy`,
    "Unable to load Reactome pathways.",
  );
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());

  useEffect(() => {
    setExpanded(new Set());
  }, [accession]);

  const response = state.kind === "ready" ? state.response : undefined;
  const index = useMemo(() => response ? buildIndex(response) : null, [response]);

  function toggle(id: string) {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function locateCanonical(id: string) {
    if (!index) return;
    const path = canonicalPath(id, index.canonicalParents);
    setExpanded((current) => new Set([...current, ...path]));
    window.requestAnimationFrame(() => window.requestAnimationFrame(() => {
      const target = document.getElementById(`reactome-node-${domToken(id)}`);
      target?.scrollIntoView({ block: "center" });
      target?.focus({ preventScroll: true });
    }));
  }

  return <article className="info-card reactome-hierarchy-card" aria-labelledby="reactome-heading">
    <div className="reactome-heading">
      <div><p className="eyebrow">Curated pathway hierarchy</p><h2 id="reactome-heading">Reactome pathways</h2></div>
      {state.kind === "ready" && response && response.node_total > 0 && <span>{countLabel(response.node_total, "pathway")}</span>}
    </div>
    {state.kind === "loading" && <p className="reactome-status" role="status">Loading pathway hierarchy…</p>}
    {state.kind === "error" && <div className="reactome-status reactome-error" role="alert"><strong>Reactome hierarchy unavailable</strong><span>{state.error}</span></div>}
    {state.kind === "ready" && response && response.node_total === 0 && <p className="empty-value reactome-status">No Reactome pathways are available for this protein.</p>}
    {state.kind === "ready" && response && response.node_total > 0 && index && <>
      <p className="reactome-summary">
        {countLabel(response.node_total, "pathway")} across {countLabel(response.root_total, "top-level system")}
        <span aria-hidden="true"> · </span>{countLabel(response.edge_total, "hierarchy relation")}
        {response.shared_node_total > 0 && <><span aria-hidden="true"> · </span>{countLabel(response.shared_node_total, "shared pathway")}</>}
      </p>
      {index.roots.length ? <ul className="reactome-root-list">
        {index.roots.map((root) => <PathwayBranch key={root.pathway_id} node={root} index={index} expanded={expanded} onToggle={toggle} onLocate={locateCanonical} root />)}
      </ul> : <p className="reactome-status reactome-error" role="alert">No top-level pathway was returned for this hierarchy.</p>}
    </>}
  </article>;
}
