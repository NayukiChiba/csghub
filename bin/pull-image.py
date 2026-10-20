#!/usr/bin/env python3
"""Fetch a public registry image concurrently, verify digests, then docker load."""
import concurrent.futures,gzip,hashlib,json,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,urllib.parse,urllib.error,time
image=sys.argv[1]; registry,repo=image.split('/',1); repo,tag=repo.rsplit(':',1)
root=pathlib.Path(__file__).resolve().parents[1]/'data/image-cache'/hashlib.sha256(image.encode()).hexdigest()[:12];root.mkdir(parents=True,exist_ok=True)
base='https://'+registry+'/v2/'+repo
accept='application/vnd.docker.distribution.manifest.v2+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.oci.image.index.v1+json'
token=None
try:urllib.request.urlopen(urllib.request.Request(base+'/manifests/'+tag,headers={'Accept':accept}),timeout=40)
except urllib.error.HTTPError as e:
 if e.code!=401:raise
 auth=e.headers['WWW-Authenticate']; realm=re.search('realm="([^"]+)"',auth)[1];service=re.search('service="([^"]+)"',auth)[1];scope=re.search('scope="([^"]+)"',auth)[1]
 with urllib.request.urlopen(realm+'?'+urllib.parse.urlencode({'service':service,'scope':scope}),timeout=40) as r:token=json.load(r)['token']
def get(path, extra=None):
 return urllib.request.urlopen(urllib.request.Request(base+path,headers={'Accept':accept,**({'Authorization':'Bearer '+token} if token else {}),**(extra or {})}),timeout=300)
def manifest(ref):
 with get('/manifests/'+ref) as r:return json.load(r)
m=manifest(tag)
if 'manifests' in m:
 ref=next(x['digest'] for x in m['manifests'] if x.get('platform',{}).get('os')=='linux' and x.get('platform',{}).get('architecture')=='amd64');m=manifest(ref)
if '--inspect' in sys.argv:
 print([(f['digest'][:19],round(f['size']/1e6,1)) for f in m['layers']]);sys.exit(0)
def fetch(entry):
 digest=entry['digest'].split(':')[1];p=root/digest
 if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==digest:return p
 for attempt in range(3):
  try:
   partial=root/(digest+'.part')
   if entry['size'] >= 20_000_000:
    start=partial.stat().st_size if partial.exists() else 0
    ranges=[(i,min(i+4_000_000,entry['size'])-1) for i in range(start,entry['size'],4_000_000)]
    def chunk(bounds):
     a,b=bounds;target=root/(digest+'.chunk-'+str(a))
     if target.exists() and target.stat().st_size==b-a+1:return target
     with get('/blobs/'+entry['digest'],{'Range':f'bytes={a}-{b}'}) as r,target.open('wb') as out:
      if r.status!=206:raise RuntimeError('Registry does not support ranged downloads')
      shutil.copyfileobj(r,out,1024*1024)
     if target.stat().st_size!=b-a+1:raise RuntimeError('Truncated range')
     return target
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:chunks=list(pool.map(chunk,ranges))
    with partial.open('ab') as out:
     for part in chunks:
      with part.open('rb') as src:shutil.copyfileobj(src,out,1024*1024)
   else:
    with get('/blobs/'+entry['digest']) as r,partial.open('wb') as f:shutil.copyfileobj(r,f,1024*1024)
   if hashlib.sha256((root/(digest+'.part')).read_bytes()).hexdigest()!=digest:raise RuntimeError('digest mismatch')
   (root/(digest+'.part')).rename(p);print('Fetched',image,digest[:12],entry['size'],flush=True);return p
  except Exception:
   if attempt==2:raise
 return p
entries=[m['config']]+m['layers']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:paths=list(pool.map(fetch,entries))
config_name=m['config']['digest'].split(':')[1]+'.json';shutil.copy2(paths[0],root/config_name)
layers=[]
for i,p in enumerate(paths[1:]):
 out=root/(str(i)+'.tar')
 if not out.exists():
  with gzip.open(p,'rb') as src,out.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
 layers.append(out.name)
(root/'manifest.json').write_text(json.dumps([{'Config':config_name,'RepoTags':[image],'Layers':layers}]))
archive=root/'image.tar'
with tarfile.open(archive,'w') as tar:
 for name in ['manifest.json',config_name]+layers:tar.add(root/name,arcname=name)
subprocess.run(['docker','load','-i',str(archive)],check=True)
print('LOADED',image,flush=True)
