"""Generate an installed-distribution licence inventory; unknown means unknown."""
import importlib.metadata
import json
from pathlib import Path

rows=[]
for distribution in importlib.metadata.distributions():
    meta=distribution.metadata
    classifiers=[v.removeprefix('License :: ') for v in meta.get_all('Classifier',[]) if v.startswith('License ::')]
    licence=meta.get('License-Expression') or meta.get('License') or '; '.join(classifiers) or 'unknown; inspect distribution licence files'
    rows.append({'name':meta['Name'],'version':distribution.version,'declared_license':licence[:500],
                 'license_files':[str(p) for p in distribution.files or [] if 'license' in str(p).lower() and '.dist-info/' in str(p)]})
Path('docs/dependency-licenses.json').write_text(json.dumps(sorted(rows,key=lambda x:x['name'].lower()),indent=2)+'\n')
print(f'Wrote metadata for {len(rows)} Python distributions. uv.lock remains the reproducibility authority.')
