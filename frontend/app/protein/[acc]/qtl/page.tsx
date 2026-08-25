"use client";

import { Suspense } from "react";
import { useParams } from "next/navigation";
import { QtlBrowser } from "../../../../components/qtl-browser";

export default function ProteinQtlPage() {
  const params = useParams<{ acc: string }>();
  return <main id="main-content" className="page-main shell qtl-detail-page">
    <div className="page-heading qtl-page-heading">
      <p className="eyebrow">Protein-scoped molecular QTL evidence</p>
      <h1>{params.acc} QTL records</h1>
      <p>Browse source-specific records without merging genome builds or evidence semantics. Source and QTL type are required for every bounded query.</p>
    </div>
    <Suspense fallback={<p role="status">Preparing QTL filters…</p>}><QtlBrowser accession={params.acc} /></Suspense>
  </main>;
}
