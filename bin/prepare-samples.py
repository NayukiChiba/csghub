#!/usr/bin/env python3
"""Validate Parquet samples and export a few real media files for UI previews."""
import json,pathlib,hashlib
import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.parquet as pq
root=pathlib.Path(__file__).resolve().parents[1]/'data/huggingface'
report=[]
for source in sorted(root.rglob('SOURCE.json')):
 meta=json.loads(source.read_text()); folder=source.parent
 for entry in list(meta['files']):
  original=folder/entry['path']
  if original.suffix not in ['.csv','.jsonl']: continue
  table=csv.read_csv(original,parse_options=csv.ParseOptions(newlines_in_values=True)) if original.suffix=='.csv' else pa.Table.from_pylist([json.loads(line) for line in original.read_text().splitlines() if line.strip()])
  derived=folder/'preview'/(original.stem+'.parquet');derived.parent.mkdir(exist_ok=True)
  pq.write_table(table,derived,version='1.0',data_page_version='1.0',write_statistics=False,use_dictionary=False,compression='snappy')
  record={'path':derived.relative_to(folder).as_posix(),'bytes':derived.stat().st_size,'sha256':hashlib.sha256(derived.read_bytes()).hexdigest(),'derived_from':entry['path'],'rows':table.num_rows}
  meta['files']=[item for item in meta['files'] if item['path']!=record['path']]+[record]
 for entry in meta['files']:
  p=folder/entry['path']
  assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],str(p)
  if p.suffix=='.parquet':
   parquet=pq.ParquetFile(p)
   report.append({'repo':meta['repo'],'file':entry['path'],'rows':parquet.metadata.num_rows,'columns':parquet.schema_arrow.names})
   if meta['repo'] in ['ylecun/mnist','hf-internal-testing/librispeech_asr_dummy']:
    rows=next(parquet.iter_batches(batch_size=5)).to_pylist()
    for i,row in enumerate(rows):
     col='image' if 'image' in row else 'audio'
     media=row.get(col)
     if not isinstance(media,dict) or not media.get('bytes'):continue
     suffix='.png' if col=='image' else pathlib.Path(media.get('path') or 'audio.flac').suffix
     target=folder/'samples'/f'{p.stem}-{i}{suffix}';target.parent.mkdir(exist_ok=True);target.write_bytes(media['bytes'])
     row[col]={'path':target.relative_to(folder).as_posix()}
    text=folder/'samples'/f'{p.stem}-metadata.json';text.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 for p in sorted((folder/'samples').glob('*')) if (folder/'samples').exists() else []:
  entry={'path':p.relative_to(folder).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  meta['files']=[f for f in meta['files'] if f['path']!=entry['path']]+[entry]
 source.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
(root/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
manifest=json.loads((root/'manifest.json').read_text());manifest['repositories']=[json.loads(p.read_text()) for p in sorted(root.rglob('SOURCE.json'))];(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
