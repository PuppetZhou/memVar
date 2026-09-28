"""Project approved PaxDB tables without changing scientific records."""
from pathlib import Path
import json,shutil
import yaml
WEB=Path(__file__).resolve().parents[2]
def main():
 cfg=yaml.safe_load((WEB/'config/paxdb.yaml').read_text());src=WEB.parent/cfg['source_directory']
 manifest=json.loads((src/'manifest.json').read_text());assert manifest['status']=='published'
 dst=WEB/'data/tables/paxdb';dst.mkdir(parents=True,exist_ok=True)
 for name in ['datasets.parquet','mapped_observations.parquet','protein_mapping.parquet']:
  shutil.copy2(src/name,dst/(name+'.next'));(dst/(name+'.next')).replace(dst/name)
 (dst/'manifest.json').write_text(json.dumps({'data_version':cfg['data_version'],'source':manifest,'status':'built'},indent=2))
if __name__=='__main__':main()
