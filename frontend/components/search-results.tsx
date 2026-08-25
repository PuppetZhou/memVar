import { SearchCandidate, SearchResponse } from "../lib/api";
import { StatusMessage } from "./status-message";
import { formatTermLabel } from "../lib/display-labels";

function matchLabel(candidate: SearchCandidate) {
  const database = candidate.match.identifier_database ? ` · ${candidate.match.identifier_database}` : "";
  return `Matched ${formatTermLabel(candidate.match.kind).toLocaleLowerCase()} ${formatTermLabel(candidate.match.identifier_type)}${database}: ${candidate.match.text}`;
}

function CandidateCard({ candidate }: { candidate: SearchCandidate }) {
  return (
    <li className="candidate-card">
      <div className="candidate-main">
        <div className="candidate-title">
          <h2>{candidate.gene_symbol ?? candidate.uniprot_accession}</h2>
          <span className="accession">{candidate.uniprot_accession}</span>
        </div>
        <p className="protein-name">{candidate.protein_name ?? "Protein name unavailable"}</p>
        <dl className="candidate-facts">
          <div><dt>Entry</dt><dd>{candidate.entry_name ?? "Not available"}</dd></div>
          <div><dt>Membrane class</dt><dd>{candidate.membrane_class ? formatTermLabel(candidate.membrane_class) : "Not available"}</dd></div>
          <div><dt>Canonical length</dt><dd>{candidate.canonical_length === null ? "Not available" : `${candidate.canonical_length.toLocaleString()} aa`}</dd></div>
        </dl>
      </div>
      <div className="candidate-action">
        <p className="match-reason">{matchLabel(candidate)}</p>
        <a className="text-link" href={`/protein/${encodeURIComponent(candidate.uniprot_accession)}`}>Open protein page <span aria-hidden="true">→</span></a>
      </div>
    </li>
  );
}

export function SearchResults({ query, result, error }: { query: string; result: SearchResponse | null; error: string | null }) {
  if (!query.trim()) return <StatusMessage title="Enter a search term">Try a UniProt accession, gene symbol, or supported stable identifier.</StatusMessage>;
  if (error || !result) return <StatusMessage title="Search unavailable" tone="error">{error ?? "The protein search data could not be loaded."}</StatusMessage>;
  if (result.resolution === "no_match") {
    return <StatusMessage title="No matching reviewed protein entry">Search by UniProt accession, gene symbol, HGNC, Ensembl gene, transcript, or isoform ID. Similar names are not redirected automatically.</StatusMessage>;
  }

  return (
    <section className="search-results" aria-live="polite">
      <div className="result-summary">
        <div>
          <p className="eyebrow">Search results</p>
          <h2>{result.total_or_estimate.value} matching {result.total_or_estimate.value === 1 ? "entry" : "entries"}</h2>
        </div>
        <p>Query: <strong>{result.query}</strong><br />Showing {result.items.length.toLocaleString()} of {result.total_or_estimate.value.toLocaleString()}{result.items.length < result.total_or_estimate.value ? " suggestions" : " candidates"}</p>
      </div>
      {result.ambiguity && (
        <div className="ambiguity-note" role="note">
          <strong>Choose a protein entry.</strong> This input maps to multiple reviewed protein entries. Select the intended canonical UniProt accession; no result has been chosen automatically.
        </div>
      )}
      <ul className="candidate-list">
        {result.items.map((candidate) => <CandidateCard candidate={candidate} key={candidate.uniprot_accession} />)}
      </ul>
    </section>
  );
}
