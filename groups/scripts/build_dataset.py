#!/usr/bin/env python3
"""Build per-level datasets (junior=CSP-J+NOIP普及, senior=CSP-S+NOIP提高) from all annotations."""
import json, csv, os, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'groups')
cat = [r for r in csv.DictReader(open(os.path.join(ROOT,'data','catalog.csv'), encoding='utf-8-sig')) if r['is_variant']!='True']
r1 = {}
for l in open(os.path.join(ROOT,'data','annotations','merged.jsonl'), encoding='utf-8'):
    if l.strip():
        x=json.loads(l); r1[x['pid']]=x
r2 = {}
for l in open(os.path.join(ROOT,'data2','annotations','merged2b.jsonl'), encoding='utf-8'):
    if l.strip():
        x=json.loads(l); r2[x['pid']]=x
hi = {}
for f in glob.glob(os.path.join(G,'ann_high_*.jsonl')):
    for l in open(f, encoding='utf-8'):
        if l.strip():
            x=json.loads(l); hi[x['pid']]=x
FAMILY = {}
for m in ['simulation','enumeration','sorting']: FAMILY[m]='基础实现'
for m in ['greedy','greedy_heap']: FAMILY[m]='贪心'
for m in ['dp_linear','dp_knapsack','dp_interval','dp_tree','dp_dag','dp_bitmask','dp_digit','dp_count']: FAMILY[m]='动态规划'
for m in ['binary_answer','binary_search','two_pointers','prefix_diff','mono_stack_queue']: FAMILY[m]='二分/双指针/前缀'
for m in ['shortest_path','mst','toposort','tree_lca','tree_property']: FAMILY[m]='图论/树'
for m in ['dsu','ds_maintain']: FAMILY[m]='数据结构'
FAMILY['string_algo']='字符串'
for m in ['math_counting','math_nt','math_other']: FAMILY[m]='数学'
FAMILY['search']='搜索'; FAMILY['construction']='构造'; FAMILY['game']='博弈'; FAMILY['other']='其他'
def era(y):
    return '2007-2012' if y<=2012 else ('2013-2018' if y<=2018 else '2019-2026')
def band(d):
    if d<=2: return '1-2'
    if d<=4: return '3-4'
    if d<=6: return '5-6'
    return '7-8'
def norm_level(g):
    return 'junior' if g in ('CSP-J','普及组') else 'senior'
out = {'junior':[], 'senior':[]}
for c in cat:
    pid=c['pid']; level=norm_level(c['group']); y=int(c['year']); d=int(c['difficulty'])
    rec=None; source=''
    if pid in r2:
        x=r2[pid]; source='r2'
        primary=x['atoms'][0]; atoms=x['atoms']; ctype=x['combo_type']; pos=x['position']
        complexity=x['complexity']; ops=x.get('ops_est',''); nobs=x.get('n_order','')
        obj=(x.get('objective') or [''])[0]; car=(x.get('carrier') or [''])[0]
        prop=x.get('property') or []
    elif pid in hi:
        x=hi[pid]; source='high'
        primary=x['atoms'][0]; atoms=x['atoms']; ctype=x['combo_type']; pos=''
        complexity=x['complexity']; ops=x.get('ops_est',''); nobs=x.get('n_order','')
        obj=(x.get('objective') or [''])[0]; car=(x.get('carrier') or [''])[0]
        prop=x.get('property') or []
    elif pid in r1:
        x=r1[pid]; source='r1'
        primary=x['main_model']; atoms=[x['main_model']]+ (x.get('secondary_models') or [])
        atoms=atoms[:3]; ctype='single' if len(atoms)==1 else 'proxy'; pos=''
        complexity=x.get('complexity',''); ops=''; nobs=x.get('n_order','')
        obj=(x.get('objective') or [''])[0]; car=(x.get('carrier') or [''])[0]
        prop=x.get('property') or []
    else:
        continue
    out[level].append(dict(pid=pid, level=level, competition=c['competition'], year=y,
        group=c['group'], difficulty=d, title=c['title'], url=c['url'], source=source,
        primary=primary, primary_family=FAMILY.get(primary,'其他'),
        atoms=atoms, atom_count=len(atoms), multi=len(atoms)>=2, combo_type=ctype,
        position=pos, complexity=complexity, ops_est=ops, n_order=nobs,
        object=obj, carrier=car, property=prop,
        era=era(y), diff_band=band(d)))
for lvl in out:
    out[lvl].sort(key=lambda r:(r['year'], r['competition'], r['pid']))
    p=os.path.join(G, lvl+'.csv')
    with open(p,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(out[lvl][0].keys()))
        w.writeheader()
        for r in out[lvl]:
            rr=dict(r)
            for k in ['atoms','property']: rr[k]='|'.join(rr[k])
            w.writerow(rr)
    print(lvl, len(out[lvl]), collections.Counter(r['source'] for r in out[lvl]), 'missing:', 
          [c['pid'] for c in cat if norm_level(c['group'])==lvl and c['pid'] not in r1 and c['pid'] not in r2 and c['pid'] not in hi])
