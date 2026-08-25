"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { VariantTable } from "../../../../components/variant-table";

export default function ProteinVariantsPage() {
  const params = useParams<{ acc: string }>();
  return <main id="main-content" className="page-main shell">
    <div className="page-heading variant-page-heading">
      <p className="eyebrow">Protein-scoped evidence</p>
      <h1>{params.acc} variants</h1>
      <p>Browse bounded pages of canonical and isoform effects. Use the row-level evidence actions to open one independent source branch at a time.</p>
      <Link href={`/protein/${encodeURIComponent(params.acc)}#variants`}>← Back to protein overview</Link>
    </div>
    <VariantTable accession={params.acc} />
  </main>;
}
