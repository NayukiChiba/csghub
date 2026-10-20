const fs = require('fs'), path = require('path'), {createRequire} = require('module');
const root = path.resolve(__dirname, '..');
const yaml = createRequire(path.join(root, 'frontend/package.json'))('yaml');
const base = path.join(root, 'data/huggingface/dataset');
for (const name of fs.readdirSync(base)) {
  const dir = path.join(base,name), sourcePath = path.join(dir,'SOURCE.json');
  if (!fs.existsSync(sourcePath)) continue;
  const source = JSON.parse(fs.readFileSync(sourcePath,'utf8'));
  const available = source.files.map(f=>f.path).filter(p=>/\.(parquet|csv|jsonl)$/.test(p));
  const data = available.some(p=>p.endsWith('.parquet')) ? available.filter(p=>p.endsWith('.parquet')) : available;
  if (!data.length) continue;
  const original = fs.readFileSync(path.join(dir,'README.md'),'utf8');
  const match = original.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  const metadata = match ? yaml.parse(match[1]) || {} : {};
  delete metadata.dataset_info;
  delete metadata.train_eval_index;
  delete metadata['model-index'];
  metadata.configs = [{config_name:'default',data_files:data.map(p=>({split: p.includes('validation')?'validation':p.includes('test')?'test':'train',path:p}))}];
  const body = match ? original.slice(match[0].length) : original;
  const note = `> 本仓库是本地演示样本。上游来源：[${source.repo}](${source.source})。已将数据配置调整为实际下载的文件；完整原始说明见 UPSTREAM_README.md。\n\n`;
  fs.writeFileSync(path.join(dir,'LOCAL_README.md'),'---\n'+yaml.stringify(metadata)+'---\n\n'+note+body);
}
console.log('Prepared local dataset cards matching downloaded files');
