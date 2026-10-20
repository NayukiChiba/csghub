#!/usr/bin/env python3
"""Package native binaries and their exact shared libraries for local Docker use."""
import pathlib,subprocess,re,shutil
root=pathlib.Path(__file__).resolve().parents[1]
out=root/'data/runtime-root'
def copy(path):
 src=pathlib.Path(path); dst=out/src.relative_to('/')
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists(): dst.chmod(0o600)
 shutil.copy2(src,dst)
for name in ['csghub-server','csghub-portal']:
 binary=root/'bin'/name
 if not binary.is_file(): raise SystemExit(f'Missing {binary}; build first')
 proc=subprocess.run(['ldd',str(binary)],capture_output=True,text=True)
 for path in re.findall(r'(/[^\s()]+)',proc.stdout):
  if pathlib.Path(path).is_file(): copy(path)
for lib in ['/usr/lib/libpthread.so.0','/usr/lib/libdl.so.2','/usr/lib/librt.so.1']:
 copy(lib)
copy('/etc/ssl/certs/ca-certificates.crt')
copy('/usr/share/zoneinfo/Asia/Shanghai')
copy('/usr/share/zoneinfo/UTC')
for dirname in ['tmp','app/data','etc','root']:(out/dirname).mkdir(parents=True,exist_ok=True)
(out/'tmp').chmod(0o1777)
(out/'etc/passwd').write_text('root:x:0:0:root:/root:/bin/false\n')
(out/'etc/group').write_text('root:x:0:\n')
print('Runtime files ready at',out)
