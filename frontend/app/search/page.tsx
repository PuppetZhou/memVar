import { redirect } from "next/navigation";
import { SearchForm } from "../../components/search-form";
import { SearchResults } from "../../components/search-results";
import { SearchResponse } from "../../lib/api";
import { getServerJson } from "../../lib/api-server";

type SearchPageProps = {
  searchParams: Promise<{ q?: string | string[] }>;
};

async function search(query: string): Promise<{ result: SearchResponse | null; error: string | null }> {
  if (!query) return { result: null, error: null };
  try {
    const result = await getServerJson<SearchResponse>(`/search?q=${encodeURIComponent(query)}&limit=20`);
    return { result, error: null };
  } catch {
    return { result: null, error: "The protein search data could not be loaded." };
  }
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const rawQuery = (await searchParams).q;
  const query = (Array.isArray(rawQuery) ? rawQuery[0] : rawQuery)?.trim() ?? "";
  const { result, error } = await search(query);
  const direct = result?.resolution === "direct_candidate" && !result.ambiguity && result.items.length === 1
    ? result.items[0]
    : null;

  if (direct) redirect(`/protein/${encodeURIComponent(direct.uniprot_accession)}`);

  return (
    <main id="main-content" className="page-main shell">
      <div className="page-heading">
        <p className="eyebrow">Protein search</p>
        <h1>Find the correct protein entry</h1>
      </div>
      <SearchForm initialQuery={query} />
      <SearchResults query={query} result={result} error={error} />
    </main>
  );
}
