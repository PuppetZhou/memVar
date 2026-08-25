type SearchFormProps = {
  initialQuery?: string;
  autoFocus?: boolean;
  className?: string;
};

export function SearchForm({ initialQuery = "", autoFocus = false, className = "" }: SearchFormProps) {
  return (
    <form action="/search" className={`search-form ${className}`} method="get" role="search">
      <label className="sr-only" htmlFor="protein-search">Search for a protein or identifier</label>
      <input
        id="protein-search"
        name="q"
        type="search"
        defaultValue={initialQuery}
        placeholder="EGFR, P00533, HGNC:3236, ENSG00000146648"
        autoFocus={autoFocus}
        required
      />
      <button type="submit">Search</button>
    </form>
  );
}
