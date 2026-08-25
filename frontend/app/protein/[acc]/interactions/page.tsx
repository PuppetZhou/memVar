"use client";

import { Suspense } from "react";
import { useParams } from "next/navigation";
import { InteractionBrowser, InteractionDetailPageHeading } from "../../../../components/interaction-browser";

export default function ProteinInteractionsPage() {
  const params = useParams<{ acc: string }>();
  return <main id="main-content" className="page-main shell interaction-detail-page"><InteractionDetailPageHeading accession={params.acc} /><Suspense fallback={<p role="status">Preparing interaction filters…</p>}><InteractionBrowser accession={params.acc} /></Suspense></main>;
}
