"""Read current UniProt annotations for overview research; no formal classification."""
import csv
import gzip
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[7]
OUT = Path(__file__).resolve().parents[1] / 'results'
config = json.loads((ROOT / 'config/sources.yaml').read_text())
source = config['foundation']['uniprot']
target_path = config['membrane']['sources']['MemProtMD']['target_table']
targets = set(pq.read_table(ROOT / target_path, columns=['accession']).column(0).to_pylist())
rows = []
topologies = Counter()
for path in sorted((ROOT / source['directory'] / 'pages').glob('*.json.gz')):
    entries = json.load(gzip.open(path, 'rt'))['results']
    for e in entries:
        acc = e['primaryAccession']
        if acc not in targets:
            continue
        features = e.get('features', [])
        comments = e.get('comments', [])
        locations = [c for c in comments if c['commentType'] == 'SUBCELLULAR LOCATION']
        topology = {x.get('topology', {}).get('value', '') for c in locations for x in c.get('subcellularLocations', [])} - {''}
        topologies.update(topology)
        counts = Counter(x['type'] for x in features)
        rows.append({
            'accession': acc,
            'protein_name': e.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', ''),
            'has_function_text': any(c['commentType'] == 'FUNCTION' and any(t.get('value') for t in c.get('texts', [])) for c in comments),
            'has_location_comment': bool(locations),
            'has_tm_feature': counts['Transmembrane'] > 0,
            'has_intramembrane_feature': counts['Intramembrane'] > 0,
            'has_lipidation_feature': counts['Lipidation'] > 0,
            'has_lipid_anchor_topology': any('Lipid-anchor' in t.split(', ') for t in topology),
            'has_peripheral_topology': 'Peripheral membrane protein' in topology,
            'has_tm_topology': any(t.startswith(('Single-pass', 'Multi-pass')) for t in topology),
            'has_membrane_keyword': any(k['id'] == 'KW-0472' for k in e.get('keywords', [])),
            'topology_values': '; '.join(sorted(topology)),
            'lipidation_descriptions': '; '.join(sorted({f.get('description', '') for f in features if f['type']=='Lipidation'})),
        })
assert len(rows) == len(targets) == len({r['accession'] for r in rows})
fields = list(rows[0])
with (OUT / 'protein_annotation_flags.tsv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(sorted(rows,key=lambda r:r['accession']))
flags = {k:sum(r[k] for r in rows) for k in fields if k.startswith('has_')}
non_tm=[r for r in rows if not r['has_tm_feature']]
residual=[r for r in rows if not r['has_tm_feature'] and not r['has_lipid_anchor_topology']]
no_lipid_feature=[r for r in non_tm if not r['has_lipidation_feature']]
stats={
 'checked_at':datetime.now(ZoneInfo('Asia/Hong_Kong')).isoformat(),
 'source_directory':source['directory'],'source_version':source['version'],'source_query':source['query'],
 'target_table':target_path,'total':len(rows),'protein_flags':flags,'topology_protein_counts':dict(topologies),
 'non_tm_count':len(non_tm),
 'non_tm_flags':{k:sum(r[k] for r in non_tm) for k in flags},
 'neither_tm_nor_explicit_anchor':{'total':len(residual),'explicit_peripheral':sum(r['has_peripheral_topology'] for r in residual),'intramembrane_feature':sum(r['has_intramembrane_feature'] for r in residual)},
 'neither_tm_nor_any_lipidation':{'total':len(no_lipid_feature),'explicit_peripheral':sum(r['has_peripheral_topology'] for r in no_lipid_feature),'intramembrane_feature':sum(r['has_intramembrane_feature'] for r in no_lipid_feature)},
 'tm_and_anchor':sum(r['has_tm_feature'] and r['has_lipid_anchor_topology'] for r in rows),
 'intramembrane_without_tm_examples':[r for r in non_tm if r['has_intramembrane_feature']][:6],
 'limits':['Accession-level source annotation presence; isoform/processed-chain and evidence contexts are not resolved','Flags overlap; lipidation presence does not itself establish membrane anchoring','Not a formal project membrane classification; no changes to curated or source files']}
(OUT / 'summary.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(stats,ensure_ascii=False,indent=2))
