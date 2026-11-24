"""Check prepared migration; pass --apply only after agreeing the session change."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import stat
import tempfile

base=Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def replace(path, data, mode):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=path.name+'.')
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.chmod(tmp,mode);os.replace(tmp,path)
        directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    plan=json.loads((base/'plan.json').read_text());prepared=[]
    for row in plan:
        target=Path(row['target']);candidate=base/row['candidate']
        if digest(target)!=row['beforeSha256']:raise SystemExit(f'Changed since preparation: {target}; no files installed')
        data=candidate.read_bytes();old=target.read_bytes() if target.exists() else None
        prepared.append((target,data,old,stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644))
        print(('CHANGE ' if data!=old else 'KEEP   ')+str(target))
    if not args.apply:
        print('Check only; no files installed.')
    else:
        backup=base/('backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir(mode=0o700)
        manifest=[]
        for index,(target,data,old,mode) in enumerate(prepared):
            if old is not None:replace(backup/str(index),old,mode)
            manifest.append({'target':str(target),'backup':str(index) if old is not None else None,'mode':mode})
        replace(backup/'manifest.json',json.dumps(manifest,indent=2).encode(),0o600)
        changed=[]
        try:
            for target,data,old,mode in prepared:
                if data!=old:
                    # Refuse to replace an intervening edit, including a newly generated palette.
                    if (target.read_bytes() if target.exists() else None)!=old:raise RuntimeError(f'Concurrent edit: {target}')
                    replace(target,data,mode);changed.append((target,old,mode))
        except BaseException:
            for target,old,mode in reversed(changed):
                if old is None:target.unlink(missing_ok=True)
                else:replace(target,old,mode)
            raise
        print('Installed. Backup:',backup)
