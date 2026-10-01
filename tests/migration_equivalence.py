"""Read-only HTTP migration acceptance. Outputs stay under ignored data/.
Capture before migration, then compare --candidate against the frozen baseline.
"""
from __future__ import annotations
import argparse, concurrent.futures, datetime, json, time, urllib.request, urllib.error
from pathlib import Path
from urllib.parse import urlencode, parse_qsl

ROOT=Path(__file__).resolve().parents[1]/'data/migration_validation'

def fetch(base,path):
    started=time.perf_counter()
    try:
        with urllib.request.urlopen(base+path,timeout=180) as response:
            status=response.status; raw=response.read(); content=response.headers.get('Content-Type','')
    except urllib.error.HTTPError as error:
        status=error.code; raw=error.read(); content=error.headers.get('Content-Type','')
    except Exception as error:
        return {'status':0,'body':str(error),'seconds':time.perf_counter()-started}
    body=json.loads(raw) if 'json' in content else raw.decode('utf-8',errors='replace')
    return {'status':status,'body':body,'seconds':time.perf_counter()-started}

def differences(a,b,path='$',limit=20):
    if type(a) is not type(b): return [f'{path}: type {type(a).__name__} != {type(b).__name__}']
    if isinstance(a,dict):
        out=[f'{path}: keys differ {sorted(set(a)^set(b))}'] if set(a)!=set(b) else []
        for key in a.keys()&b.keys(): out+=differences(a[key],b[key],path+'.'+key,limit)
        return out[:limit]
    if isinstance(a,list):
        out=[f'{path}: length {len(a)} != {len(b)}'] if len(a)!=len(b) else []
        for i,(x,y) in enumerate(zip(a,b)): out+=differences(x,y,f'{path}[{i}]',limit)
        return out[:limit]
    return [] if a==b else [f'{path}: {str(a)[:100]} != {str(b)[:100]}']

def initial_paths(spec):
    paths=['/api/proteins?query=egfr&limit=5','/api/proteins?query=IG&limit=5&offset=20','/api/proteins?query=3-7&limit=5','/api/proteins?membrane_class=peripheral_membrane&limit=5','/api/proteins?limit=5','/api/proteins?limit=5&offset=5','/api/proteins?query=EGFR&limit=5','/api/proteins?query=NO_SUCH_MEMVAR_PROTEIN']
    for accession in ('P00533','P13569','A0A075B6H7'):
        for path,methods in spec['paths'].items():
            op=methods.get('get')
            if not op or '/api/' not in path or path.count('{')>1:continue
            if '{' in path and '{accession}' not in path:continue
            if not '{' in path and accession!='P00533':continue
            params=op.get('parameters',[])
            if any(p.get('required') and p['in']=='query' for p in params):continue
            concrete=path.replace('{accession}',accession)
            optional={p['name'] for p in params if p['in']=='query'}
            if 'limit' in optional: concrete+='?limit=3'
            paths.append(concrete)
        paths.extend(f'/api/proteins/{accession}/'+suffix for suffix in ('variants?limit=3&offset=3','variants?limit=3&source=ClinVar','variants?limit=3&consequence=missense_variant','variants?limit=3&position=1','variants?limit=3&search=NO_SUCH_VARIANT','variants?limit=3&af_min=0&af_max=0','variants?limit=3&af_status=unavailable','variants?limit=3&predictors=none','variants?limit=3&canonical_start=1&canonical_end=20','qtl?limit=3&source=eQTLGen','qtl?limit=3&source=QTLbase','qtl?limit=3&qtl_type=eqtl','qtl?limit=3&offset=3','expression?limit=3&category=all','expression?limit=3&category=cancer','expression?limit=3&category=single_cell','expression?limit=3&offset=3','ppi?limit=3&source=IntAct','ppi?limit=3&offset=3'))
        paths.extend([f'/api/proteins/{accession}/sites/1',f'/api/proteins/{accession}/sites/0',f'/api/proteins/{accession}/interface/sites/1'])
    paths.extend('/api/proteins/P00533/qtl?'+urlencode({'source':'QTLbase','tissue':'Blood-Monocytes CD14+','qtl_type':'mQTL','offset':offset,'limit':1}) for offset in range(4061,4065))
    paths+=['/api/proteins/NO_SUCH_PROTEIN/overview','/api/proteins/P00533/overview/go','/api/proteins/P00533/overview/pathways','/api/proteins/P00533/overview/pharmacology']
    return list(dict.fromkeys(paths))

def followups(path,record):
    body=record['body']; result=[]
    if record['status']!=200 or not isinstance(body,dict):return result
    base=path.split('?')[0]
    if body.get('next_cursor'): result.append(base+'?'+urlencode({**dict(parse_qsl(path.partition('?')[2])), 'limit':3,'cursor':body['next_cursor']}))
    if '/proteins/' in base:
        accession=base.split('/proteins/')[1].split('/')[0]
        for row in body.get('items',[])[:2]:
            for key,route in [('variant_id','variants'),('record_id','ppi'),('disease_id','diseases')]:
                if row.get(key) and (key!='record_id' or base.endswith('/ppi')):result.append('/api/'+route+'/'+str(row[key])+'?'+urlencode({'accession':accession}))
        if base.endswith('/interface/summary'):
            for row in body.get('pesto_structures',[])[:1]:result.append(base.replace('/summary','/pesto')+'?'+urlencode({'structure_id':row['structure_id']}))
        if base.endswith('/interface/partners'):
            for row in body.get('items',[])[:1]:result.append(base.replace('/partners','/sppider')+'?'+urlencode({'partner':row['partner_sequence_key']}))
        if base.endswith('/diseases/clinvar-conditions'):
            for item in body.get('items',[])[:2]:result.append(base+'/'+item['condition_set_id']+'?limit=3')
        if base.endswith('/expression/alphagenome/avi'):
            for item in body.get('items',[])[:2]:result.append('/api/variants/'+item['variant_id']+'/avi?'+urlencode({'accession':accession}))
        if base.endswith('/structures'):
            for item in body.get('items',[])[:1]:result.append(base+'/'+str(item['id'])+'/model.pdb')
        if base.endswith('/qtl/tracks'):
            gene=dict(parse_qsl(path.partition('?')[2]))['gene']
            for item in body.get('items',[])[:2]:
                result.append(base.replace('/tracks','/track')+'?'+urlencode({'gene':gene,'dataset':item['dataset_id'],'chromosome':'chr2' if accession=='A0A075B6H7' else 'chr7','start':88000000 if accession=='A0A075B6H7' else 54000000,'end':90000000 if accession=='A0A075B6H7' else 120000000,'limit':3}))
        if base.endswith('/expression/alphagenome'):
            for gene in body.get('genes',[])[:1]:
                result.append('/api/proteins/'+accession+'/qtl/tracks?'+urlencode({'gene':gene['ensembl_gene_id']}))
                result.append(base+'/cds?'+urlencode({'gene':gene['ensembl_gene_id']}))
                for tile in gene.get('tiles',[])[:1]:
                    args={'gene':gene['ensembl_gene_id'],'tile':tile['tile_id']}
                    result.append(base+'/avi?'+urlencode({**args,'limit':3}))
                    modalities=set()
                    for track in body.get('tracks',[]):
                        if track['modality'] in modalities:continue
                        modalities.add(track['modality'])
                        result.append(base+'/track?'+urlencode({**args,'track_id':track['track_id'],'bins':32,'limit':3}))
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',default='http://127.0.0.1:8000');parser.add_argument('--candidate');parser.add_argument('--workers',type=int,default=4);parser.add_argument('--failed-only',action='store_true');parser.add_argument('--benchmark',action='store_true');parser.add_argument('--exclude',default='');parser.add_argument('--report',default='comparison.json');parser.add_argument('--recheck-variants',action='store_true');args=parser.parse_args();ROOT.mkdir(parents=True,exist_ok=True)
    saved=ROOT/'baseline.json'
    if not args.candidate:
        spec=fetch(args.baseline,'/openapi.json')['body'];records={}
        pending=initial_paths(spec)
        for iteration in range(2):
            for path in pending:
                records[path]=fetch(args.baseline,path)
                print(records[path]['status'],round(records[path]['seconds'],3),path,flush=True)
            pending=list(dict.fromkeys(p for path,r in records.items() for p in followups(path,r) if p not in records))
        saved.write_text(json.dumps({'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base':args.baseline,'responses':records},ensure_ascii=False,indent=2));return
    baseline=json.loads(saved.read_text());results={}
    if args.exclude:
        baseline['responses']={p:r for p,r in baseline['responses'].items() if not any(part in p for part in args.exclude.split(','))}
    if args.benchmark:
        paths=['/api/proteins?query=EGFR&limit=20','/api/proteins/P00533/sequence','/api/proteins/P00533/variants?limit=20','/api/proteins/P00533/variants?limit=20&source=ClinVar','/api/variants/GRCh38:7:117480095:A:G?accession=P13569','/api/proteins/P00533/variants/summary','/api/proteins/P13569/variants?limit=20','/api/proteins/P13569/variants/summary','/api/proteins/P13569/ppi?limit=20','/api/proteins/P00533/qtl?limit=20&offset=20','/api/proteins/P13569/expression?limit=20&category=all','/api/proteins/P00533/diseases/summary','/api/proteins/P00533/expression/alphagenome']
        timings={};originals={};mismatches={}
        for label,url in [('postgresql',args.baseline),('duckdb',args.candidate)]:
            first=[]
            for path in paths:
                response=fetch(url,path);first.append({'path':path,'status':response['status'],'seconds':response['seconds']})
                if label=='postgresql':originals[path]=response
                else:
                    diff=differences(originals[path]['body'],response['body'])
                    if response['status']!=originals[path]['status']:diff.insert(0,'HTTP status differs')
                    if diff:mismatches[path]=diff
                print(label,'first',round(response['seconds'],3),path,flush=True)
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
                started=time.perf_counter();responses=list(pool.map(lambda path:fetch(url,path),paths*2));elapsed=time.perf_counter()-started
            warm=[]
            for path,response in zip(paths*2,responses):
                warm.append({'path':path,'status':response['status'],'seconds':response['seconds']})
                diff=differences(originals[path]['body'],response['body'])
                if response['status']!=originals[path]['status']:diff.insert(0,'HTTP status differs')
                if diff:mismatches[label+':'+path]=diff
            timings[label]={'first_requests':first,'warm_elapsed_seconds':elapsed,'warm_requests':len(responses),'workers':args.workers,'warm_responses':warm}
        report={'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cache_condition':'First observed requests are recorded separately; existing PostgreSQL service is preserved, so neither engine filesystem cache nor PostgreSQL application caches are forcibly cleared. Warm batches have identical paths, order, repetition and concurrency.','engines':timings,'differences':mismatches}
        (ROOT/'benchmark.json').write_text(json.dumps(report,indent=2));print('benchmark differences',len(mismatches));raise SystemExit(bool(mismatches))
    if args.failed_only:
        previous=json.loads((ROOT/args.report).read_text())
        results={p:r for p,r in previous['results'].items() if not r.get('differences')}
        baseline['responses']={p:r for p,r in baseline['responses'].items() if p not in previous['results'] or previous['results'][p].get('differences') or (args.recheck_variants and '/variants' in p and '/avi' not in p)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(fetch,args.candidate,p):p for p in baseline['responses']}
        for future in concurrent.futures.as_completed(futures):
            path=futures[future];candidate=future.result();old=baseline['responses'][path]
            expected_changes=[]
            old_body=old['body'];candidate_body=candidate['body']
            if path=='/api/health' and isinstance(old_body,dict) and isinstance(candidate_body,dict) and old_body.get('database')=='PostgreSQL' and candidate_body.get('database')=='DuckDB':
                expected_changes=['database: PostgreSQL → DuckDB (requested backend migration)']
                candidate_body={**candidate_body,'database':'PostgreSQL'}
            diff=differences(old_body,candidate_body);
            if old['status']!=candidate['status']:diff.insert(0,f"status {old['status']} != {candidate['status']}")
            results[path]={'baseline_seconds':old['seconds'],'candidate_seconds':candidate['seconds'],'status':candidate['status'],'differences':diff,'expected_changes':expected_changes}
            print('FAIL' if diff else 'PASS',round(candidate['seconds'],3),path,flush=True)
            checkpoint={'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':args.candidate,'workers':args.workers,'status':'running','cases':len(results),'failed':sum(bool(r['differences']) for r in results.values()),'results':results}
            temporary=ROOT/(args.report+'.writing');temporary.write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2));temporary.replace(ROOT/args.report)
    report={'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':args.candidate,'workers':args.workers,'cases':len(results),'failed':sum(bool(r['differences']) for r in results.values()),'results':results}
    (ROOT/args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(bool(report['failed']))
if __name__=='__main__':main()
