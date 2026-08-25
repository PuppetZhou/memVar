"use client";

import { useParams } from "next/navigation";
import { ProteinOverview } from "../../../components/protein-overview";

export default function ProteinPage() {
  const params = useParams<{ acc: string }>();
  return (
    <main id="main-content" className="page-main shell">
      <ProteinOverview accession={params.acc} />
    </main>
  );
}
