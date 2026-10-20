#!/usr/bin/env python3
"""Import downloaded HF samples through CSGHub APIs, preserving provenance."""
import json,pathlib,urllib.request,urllib.parse,urllib.error,uuid,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:18080/api/v1'
TOKEN=json.loads((ROOT/'deploy/dev/credentials.json').read_text())['api_token']
QUERY='?current_user=demo'
OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}))

def request(method,path,data=None,content_type='application/json'):
 if isinstance(data,dict): data=json.dumps(data).encode()
 req=urllib.request.Request(BASE+path+QUERY,data=data,method=method,headers={'Authorization':'Bearer '+TOKEN,'Content-Type':content_type})
 try:
  with OPENER.open(req,timeout=180) as r: return r.read()
 except urllib.error.HTTPError as e:
  raise RuntimeError(f'{method} {path}: HTTP {e.code}: {e.read().decode()[:800]}') from e

def upload(path,name,data):
 boundary='csghub-'+uuid.uuid4().hex
 body=bytearray()
 for key,value in [('file_path',name),('branch','main'),('message','Import attributed Hugging Face sample')]:
  body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
 body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{pathlib.PurePosixPath(name).name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode())
 body.extend(data); body.extend(f'\r\n--{boundary}--\r\n'.encode())
 return request('POST',path+'/upload_file',bytes(body),'multipart/form-data; boundary='+boundary)

def main():
 global QUERY
 user=json.loads(request('GET','/user/demo'))['data']
 QUERY += '&current_user_uuid='+urllib.parse.quote(user['uuid'])
 state_path=ROOT/'data/huggingface/import-state.json'
 state=json.loads(state_path.read_text()) if state_path.exists() else {}
 for source in sorted((ROOT/'data/huggingface').rglob('SOURCE.json')):
  meta=json.loads(source.read_text()); folder=source.parent
  kind=meta['type']; name=meta['repo'].replace('/','-'); path=f'/{kind}s/demo/{name}'
  if kind=='dataset' and not any(f['path'].endswith(('.parquet','.csv','.jsonl')) for f in meta['files']):
   print('SKIP metadata-only dataset '+meta['repo'],flush=True); continue
  try: request('GET',path)
  except RuntimeError as e:
   if 'HTTP 404' not in str(e) and 'SYS-ERR-3' not in str(e): raise
   payload={'name':name,'namespace':'demo','nickname':meta['repo'],'description':meta['category']+'; Hugging Face 原始说明与精选文件，非完整权重/全量数据。','private':False,'default_branch':'main','license':meta.get('license') if isinstance(meta.get('license'),str) else 'unknown'}
   request('POST','/'+kind+'s',payload)
   state={k:v for k,v in state.items() if not k.startswith(path+'/')}
  note=f"# 本地演示样本\n\n原始仓库：{meta['source']}\n\n固定版本：`{meta['revision']}`\n\n这是用于 CSGHub 浏览、预览和下载测试的精选文件集合，不是完整模型或完整数据集。数据集 README.md 的文件配置适配了本地样本，原文保存在 UPSTREAM_README.md；模型 README 保留原文。原始授权以 README 和 LICENSE 为准。模型未下载权重，不代表可以直接推理。\n\n文件及 SHA256 见 SOURCE.json。通过 Dataset Viewer 提取的 samples.jsonl 为少量真实记录，详见 SOURCE.json 中 sample_api 字段。\n"
  (folder/'LOCAL_SAMPLE.md').write_text(note)
  files=[p for p in folder.rglob('*') if p.is_file() and '.cache' not in p.parts and p.name!='.gitattributes']
  files.sort(key=lambda p:(0 if p.name=='.gitattributes.local' else 1 if p.name=='README.md' else 2,str(p)))
  for file in files:
   relative=file.relative_to(folder).as_posix()
   if relative=='.gitattributes.local': relative='.gitattributes'
   if (folder/'LOCAL_README.md').exists():
    if relative=='README.md': relative='UPSTREAM_README.md'
    elif relative=='LOCAL_README.md': relative='README.md'
   key=path+'/'+relative; data=file.read_bytes(); digest=hashlib.sha256(data).hexdigest()
   if state.get(key)==digest: continue
   upload(path,relative,data)
   state[key]=digest; state_path.write_text(json.dumps(state,indent=2)+'\n')
   print(f'Imported {kind}/{name}/{relative} ({len(data)} bytes)',flush=True)
  print('READY '+path,flush=True)
if __name__=='__main__':main()
