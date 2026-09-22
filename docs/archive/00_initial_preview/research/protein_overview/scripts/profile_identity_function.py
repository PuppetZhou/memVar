"""Profile current identity fields and existing lossless FUNCTION parsing for discussion."""
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[7]
OUT=Path(__file__).resolve().parents[1]/'results'
c=json.loads((ROOT/'config/sources.yaml').read_text())
u=c['Function']['uniprot']
bridge=pq.read_table(ROOT/u['target_protein_gene']).to_pylist()
targets={r['accession'] for r in bridge}
base=ROOT/u['cleaned_tables']
entries=[r for r in pq.read_table(base/'protein_entry.parquet').to_pylist() if r['accession'] in targets]
isos=[r for r in pq.read_table(base/'protein_isoform.parquet').to_pylist() if r['accession'] in targets]
seqs=pq.read_table(base/'protein_sequence.parquet',columns=['sequence_id','accession','length','is_canonical']).to_pylist()
ids={x for r in isos for x in r['sequence_ids']}
selected=[r for r in seqs if r['accession'] in targets or r['sequence_id'] in ids]
source=ROOT/c['Function']['sequence_tracks']['source_run']/'prototype/uniprot_comment.parquet'
comments=[r for r in pq.read_table(source,columns=['accession','type','molecule','payload_json']).to_pylist() if r['accession'] in targets]
bytype=defaultdict(set); funcs=[]; counts=Counter(); chars=Counter(); ecos=Counter()
for r in comments:
    bytype[r['type']].add(r['accession'])
    if r['type']!='FUNCTION': continue
    obj=json.loads(r['payload_json']);texts=[t for t in obj.get('texts',[]) if t.get('value')]
    if not texts: continue
    counts[r['accession']]+=1
    chars[r['accession']]+=sum(len(t['value']) for t in texts)
    for t in texts: ecos.update(x['evidenceCode'] for x in t.get('evidences',[]))
    funcs.append({'accession':r['accession'],'molecule':r['molecule'],'texts':texts})
assert len(entries)==len(targets)==7715 and len({r['accession'] for r in entries})==7715
missing=targets-set(counts)
lengths=sorted(chars.values())
summary={
'checked_at':datetime.now(ZoneInfo('Asia/Hong_Kong')).isoformat(),'status':'research_only',
'inputs':{'target':u['target_protein_gene'],'identity_directory':u['cleaned_tables'],'comments':str(source.relative_to(ROOT))},
'identity':{'proteins':len(entries),'recommended_name_nonempty':sum(bool(r['recommended_protein_name']) for r in entries),'alternative_name_proteins':sum(bool(r['alternative_protein_names']) for r in entries),'secondary_accession_proteins':sum(bool(r['secondary_accessions']) for r in entries),'uniprot_single_primary_gene_name':sum(bool(r['primary_gene_name']) for r in entries),'uniprot_gene_name_list_sizes':dict(Counter(len(r['primary_gene_names']) for r in entries)),'canonical_lengths_min_max':[min(r['canonical_length'] for r in entries),max(r['canonical_length'] for r in entries)],'reviewed_counts':dict(Counter(str(r['reviewed']) for r in entries)),'protein_existence':dict(Counter(r['protein_existence'] for r in entries)),'canonical_sequence_links_found':sum(r['canonical_sequence_id'] in {x['sequence_id'] for x in selected} for r in entries),'isoform_declared_records':len(isos),'isoform_unavailable_records':sum(not r['sequence_available'] for r in isos),'available_sequence_records':len(selected),'canonical_sequence_records':sum(r['is_canonical'] for r in selected),'alternative_sequence_records':sum(not r['is_canonical'] for r in selected),'cross_entry_sequence_records':sum(r['accession'] not in targets for r in selected),'hgnc_relations':len(bridge),'hgnc_status_counts':dict(Counter(r['hgnc_status'] for r in bridge))},
'function':{'proteins_with_text':len(counts),'proteins_without_text':len(missing),'comment_records_with_text':len(funcs),'proteins_with_multiple_function_comments':sum(v>1 for v in counts.values()),'molecule_scoped_comment_records':sum(bool(r['molecule']) for r in funcs),'molecule_scoped_proteins':len({r['accession'] for r in funcs if r['molecule']}),'total_text_characters_per_protein':{'median':lengths[len(lengths)//2],'p90_nearest_rank':lengths[(9*len(lengths)+9)//10-1],'max':max(lengths),'over_1000':sum(n>1000 for n in lengths)},'evidence_occurrences':dict(ecos),'related_comment_protein_counts':{k:len(bytype[k]) for k in ['SIMILARITY','CATALYTIC ACTIVITY','COFACTOR','ACTIVITY REGULATION','CAUTION','SEQUENCE CAUTION']},'without_function_other_comments':{k:len(missing&bytype[k]) for k in ['SIMILARITY','CATALYTIC ACTIVITY','COFACTOR','ACTIVITY REGULATION','CAUTION','SEQUENCE CAUTION']}},
'limits':['Counts describe current target entries, not all raw proteins','FUNCTION character lengths aggregate source text, not proposed display limits','Isoform declarations and available FASTA sequence records are different denominators','ECO counts are source evidence occurrences, not independent experiments; no function summary generated']}
(OUT/'identity_function_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(OUT/'missing_function_accessions.txt').write_text('\n'.join(sorted(missing))+'\n')
# Bounded real examples illustrate short, long, object-scoped and uncertain descriptions.
example_ids=['P00533','A0A1B0GTW7']
for x in funcs:
    if x['molecule']:
        example_ids.append(x['accession']);break
(OUT/'function_examples.json').write_text(json.dumps([x for x in funcs if x['accession'] in example_ids],ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
