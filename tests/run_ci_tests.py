#!/usr/bin/env python3
"""Run one disjoint CI shard of the complete unittest discovery suite."""
import argparse,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
def cases(suite):
    for case in suite:
        if isinstance(case,unittest.TestSuite): yield from cases(case)
        else: yield case

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shard',required=True,choices=('hooks','other'))
    parser.add_argument('--list-only',action='store_true')
    args=parser.parse_args()
    complete=list(cases(unittest.defaultTestLoader.discover(str(ROOT),pattern='test_*.py')))
    ids=[case.id() for case in complete]
    if not ids or len(ids)!=len(set(ids)):
        parser.error('discovery is empty or has duplicate test IDs')
    selected=[case for case in complete if (case.__class__.__module__=='test_hook_safety')==(args.shard=='hooks')]
    if not selected: parser.error('selected shard is empty')
    if args.list_only:
        print(json.dumps([case.id() for case in selected]));return 0
    print(f'CI shard {args.shard}: {len(selected)}/{len(complete)} discovered cases',flush=True)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(selected))
    return 0 if result.wasSuccessful() else 1
if __name__=='__main__':sys.exit(main())
