import argparse
import json
from pathlib import Path
from knowledge import build

ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Index ESMF 8.9.1 sections and complete Fortran routines')
    parser.add_argument('--manifest',type=Path,default=ROOT/'corpus.json')
    parser.add_argument('--db',type=Path,default=ROOT/'data'/'nuopc.sqlite3')
    args=parser.parse_args()
    try:print(json.dumps(build(args.manifest,args.db),indent=2))
    except Exception as error:parser.exit(1,f'Ingestion failed; prior index preserved: {error}\n')
