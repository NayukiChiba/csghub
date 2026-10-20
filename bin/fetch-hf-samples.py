#!/usr/bin/env python3
"""Download pinned public HF cards and bounded sample files; never executes repo code."""
import concurrent.futures, json, pathlib, subprocess, hashlib
ROOT = pathlib.Path(__file__).resolve().parents[1] / 'data/huggingface'
CATALOG = [
 ('dataset','scikit-learn/iris','表格分类 / CSV'),
 ('dataset','stanfordnlp/imdb','影评情感分类 / Parquet'),
 ('dataset','rajpurkar/squad','阅读理解问答 / Parquet'),
 ('dataset','HuggingFaceH4/ultrachat_200k','多轮对话 / Parquet'),
 ('dataset','ylecun/mnist','手写数字图像 / Parquet'),
 ('dataset','ashraq/esc50','环境音频分类 / WAV'),
 ('dataset','fka/awesome-chatgpt-prompts','提示词 / CSV'),
 ('model','Qwen/Qwen2.5-0.5B-Instruct','中文指令生成'),
 ('model','sentence-transformers/all-MiniLM-L6-v2','文本向量检索'),
 ('model','openai/whisper-tiny','语音识别'),
 ('model','google/vit-base-patch16-224','图像分类'),
 ('model','Helsinki-NLP/opus-mt-en-zh','英中翻译'),
]
def hf(*args):
 p=subprocess.run(['hf',*args],capture_output=True,text=True,timeout=600)
 if p.returncode: raise RuntimeError(p.stderr[-1500:])
 return p.stdout

def fetch(item):
 kind,repo,category=item
 folder=ROOT/kind/repo.replace('/','--'); folder.mkdir(parents=True,exist_ok=True)
 group='datasets' if kind=='dataset' else 'models'
 meta=json.loads(hf(group,'info',repo,'--format','json'))
 rev=meta['sha']
 tree=json.loads(hf(group,'list',repo,'--recursive','--revision',rev,'--format','json'))
 files=[f for f in tree if 'size' in f]
 docs=[f for f in files if pathlib.PurePosixPath(f['path']).name.lower().startswith(('readme','license','notice')) and f['size']<2_000_000]
 chosen=list(docs)
 if kind=='model':
  chosen += [f for f in files if f not in chosen and f['size']<8_000_000 and f['path'].endswith(('.json','.txt','.model','.yaml')) and '/' not in f['path']]
 else:
  data=[f for f in files if f not in chosen and f['path'].endswith(('.csv','.jsonl','.json','.parquet','.wav','.flac','.png','.jpg','.zip')) and 0<f['size']<30_000_000]
  data.sort(key=lambda f:(0 if 'test' in f['path'] or 'validation' in f['path'] else 1,f['size']))
  budget=35_000_000
  for f in data:
   if f['size']<=budget and len(chosen)-len(docs)<5:
    chosen.append(f); budget-=f['size']
 if not any(f['path'].lower()=='readme.md' for f in chosen): raise RuntimeError('Missing root README')
 hf('download',repo,*[f['path'] for f in chosen],'--type',kind,'--revision',rev,'--local-dir',str(folder),'--max-workers','2','--quiet')
 record={'type':kind,'repo':repo,'category':category,'revision':rev,'source':'https://huggingface.co/'+('datasets/' if kind=='dataset' else '')+repo,'license':(meta.get('card_data') or {}).get('license'),'partial':True,'files':[{'path':f['path'],'bytes':(folder/f['path']).stat().st_size,'sha256':hashlib.sha256((folder/f['path']).read_bytes()).hexdigest()} for f in chosen]}
 (folder/'SOURCE.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 print('Downloaded '+repo+' ('+str(len(chosen))+' files)',flush=True)
 return record
if __name__=='__main__':
 ROOT.mkdir(parents=True,exist_ok=True); results=[]; errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(fetch,item):item for item in CATALOG}
  for future in concurrent.futures.as_completed(futures):
   try: results.append(future.result())
   except Exception as e:
    errors.append({'repo':futures[future][1],'error':str(e)}); print(errors[-1],flush=True)
 (ROOT/'manifest.json').write_text(json.dumps({'repositories':results,'errors':errors},ensure_ascii=False,indent=2)+'\n')
 print(f'Complete: {len(results)} repositories, {len(errors)} errors',flush=True)
 raise SystemExit(bool(errors))
