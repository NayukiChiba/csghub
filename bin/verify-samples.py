#!/usr/bin/env python3
import concurrent.futures,hashlib,json,pathlib,urllib.request,urllib.parse
root=pathlib.Path(__file__).resolve().parents[1];token=json.loads((root/'deploy/dev/credentials.json').read_text())['api_token']
base='http://127.0.0.1:18080/api/v1'
def read(url):
 req=urllib.request.Request(url)
 req.add_unredirected_header("Authorization", "Bearer "+token)
 with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=60) as r:return r.read()
def verify(item):
 key,digest=item
 parts=key.strip('/').split('/',3);kind,ns,name,file=parts
 url=base+f'/{kind}/{ns}/{name}/resolve/'+urllib.parse.quote(file)+'?ref=main&current_user=demo'
 data=read(url)
 if hashlib.sha256(data).hexdigest()!=digest:raise RuntimeError('Hash mismatch: '+key)
 return {'path':key,'bytes':len(data),'sha256':digest}
state=json.loads((root/'data/huggingface/import-state.json').read_text())
results=[];failures=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 futures={pool.submit(verify,item):item[0] for item in state.items()}
 for future in concurrent.futures.as_completed(futures):
  try:results.append(future.result())
  except Exception as e:failures.append({'path':futures[future],'error':str(e)})
counts={}
for kind in ['models','datasets']:
 data=json.loads(read(base+'/'+kind+'?per=100&page=1'))['data'];counts[kind]=len(data)
report={'repositories':counts,'verified_files':len(results),'verified_bytes':sum(r['bytes'] for r in results),'failures':failures}
(root/'data/huggingface/service-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(bool(failures))
