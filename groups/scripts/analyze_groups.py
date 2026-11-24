#!/usr/bin/env python3
"""Per-level statistics + candidate-gating evaluation for junior/senior datasets."""
import json, csv, os, collections, math, itertools
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'groups')
V = json.load(open(os.path.join(ROOT,'taxonomy','vocab.json'), encoding='utf-8'))
MZH={x['id']:x['zh'] for x in V['main_model']}
OZH={x['id']:x['zh'] for x in V['objective']}
CZH={x['id']:x['zh'] for x in V['carrier']}
PZH={x['id']:x['zh'] for x in V['property']}
BANDS=['1-2','3-4','5-6','7-8']; ERAS=['2007-2012','2013-2018','2019-2026']; POS=['T1','T2','T3','T4']
def pct(a,b): return '%.1f%%'%(100.0*a/b) if b else '-'
def md(h,rows):
    o=['| '+' | '.join(h)+' |','|'+'|'.join(['---']*len(h))+'|']
    for r in rows: o.append('| '+' | '.join(str(x) for x in r)+' |')
    return '\n'.join(o)
def load(level):
    rows=[]
    for r in csv.DictReader(open(os.path.join(G,level+'.csv'),encoding='utf-8-sig')):
        r['atoms']=[x for x in (r['atoms'] or '').split('|') if x]
        r['property']=[x for x in (r['property'] or '').split('|') if x]
        r['multi']=len(r['atoms'])>=2
        r['atom_count']=len(r['atoms'])
        r['year']=int(r['year']); r['difficulty']=int(r['difficulty'])
        if r['ops_est']: r['ops_est']=float(r['ops_est'])
        rows.append(r)
    return rows
ATOMS=[x['id'] for x in V['main_model']]
def eval_loo(rows, target='primary'):
    """Naive Bayes LOO: context = difficulty band + carrier + object + n_order; fallback global."""
    def key(r): return (r['diff_band'], r['carrier'], r['object'], r['n_order'])
    glob=collections.Counter(r[target] for r in rows)
    ctxc=collections.defaultdict(collections.Counter)
    for r in rows: ctxc[key(r)][r[target]]+=1
    ctxn=collections.Counter(key(r) for r in rows)
    vocab=sorted(set(r[target] for r in rows))
    hits={1:0,3:0,5:0}; famhits={1:0,3:0,5:0}
    FAM={r['primary']:r['primary_family'] for r in rows}
    for i,r in enumerate(rows):
        k=key(r)
        def score(t):
            g=glob[t]-(1 if r[target]==t else 0)
            c=ctxc[k][t]-(1 if r[target]==t else 0)
            n=ctxn[k]-1
            pg=(g+0.5)/(sum(glob.values())-1+0.5*len(vocab))
            pc=(c+0.5)/(n+0.5*len(vocab)) if n else 0
            return 0.6*pc+0.4*pg
        rank=sorted(vocab,key=lambda t:-score(t))
        for kk in hits:
            if r[target] in rank[:kk]: hits[kk]+=1
    return {k:hits[k]/len(rows) for k in hits}
def main():
    os.makedirs(os.path.join(G,'out'),exist_ok=True)
    summary={}
    for lvl in ['junior','senior']:
        rows=load(lvl); N=len(rows)
        T=[]; S={'n':N,'level':lvl}
        T.append('# %s 组统计（%d 题）'%('普及' if lvl=='junior' else '提高', N)); T.append('')
        # 1 basic
        T.append('## 1 构成'); T.append('')
        rows2=[]
        for y in range(2007,2027):
            sub=[r for r in rows if r['year']==y]
            if sub: rows2.append([y,len(sub),collections.Counter(r['group'] for r in sub).most_common()])
        T.append(md(['年份','题数','组别'],rows2)); T.append('')
        T.append(md(['难度','题数','占比'],[[b,sum(1 for r in rows if r['diff_band']==b),pct(sum(1 for r in rows if r['diff_band']==b),N)] for b in BANDS if any(r['diff_band']==b for r in rows)])); T.append('')
        T.append(md(['年代','题数'],[[e,sum(1 for r in rows if r['era']==e)] for e in ERAS])); T.append('')
        # 2 primary algo
        T.append('## 2 主算法分布'); T.append('')
        pc=collections.Counter(r['primary'] for r in rows)
        T.append(md(['主算法','id','题数','占比'],[[MZH.get(a,a),a,c,pct(c,N)] for a,c in pc.most_common()])); T.append('')
        fc=collections.Counter(r['primary_family'] for r in rows)
        T.append(md(['算法族','题数','占比'],[[f,c,pct(c,N)] for f,c in fc.most_common()])); T.append('')
        # by band
        T.append('## 3 难度分层'); T.append('')
        hdr=['主算法']+[b for b in BANDS if any(r['diff_band']==b for r in rows)]+['合计']
        rows3=[]
        for a,c in pc.most_common(15):
            row=[MZH.get(a,a)]
            for b in hdr[1:-1]:
                row.append(sum(1 for r in rows if r['diff_band']==b and r['primary']==a))
            row.append(c); rows3.append(row)
        T.append(md(hdr,rows3)); T.append('')
        rows3=[]
        for b in hdr[1:-1]:
            sub=[r for r in rows if r['diff_band']==b]
            cc=collections.Counter(r['primary'] for r in sub)
            rows3.append([b,len(sub),'、'.join('%s×%d'%(MZH.get(a,a),c) for a,c in cc.most_common(3))])
        T.append(md(['难度段','题数','Top3 主算法'],rows3)); T.append('')
        # era
        T.append('## 4 年代趋势'); T.append('')
        rows4=[]
        for f,c in fc.most_common():
            row=[f]
            for e in ERAS:
                sub=[r for r in rows if r['era']==e]
                row.append('%d (%s)'%(sum(1 for r in sub if r['primary_family']==f), pct(sum(1 for r in sub if r['primary_family']==f), len(sub))))
            rows4.append(row)
        T.append(md(['算法族']+ERAS,rows4)); T.append('')
        # 4b 赛事组别 × 算法族
        T.append('### 赛事组别 × 算法族'); T.append('')
        gs=sorted(set(r['group'] for r in rows))
        fams=[f for f,_ in fc.most_common()]
        hdr2=['算法族']+gs+['合计']
        rows4b=[]
        for f in fams:
            row=[f]+[sum(1 for r in rows if r['group']==g and r['primary_family']==f) for g in gs]
            row.append(fc[f]); rows4b.append(row)
        T.append(md(hdr2,rows4b)); T.append('')
        # 5 combo (recent r2 + proxy old)
        T.append('## 5 多算法/组合'); T.append('')
        rec=[r for r in rows if r['source']=='r2']
        old=[r for r in rows if r['source']=='r1']
        T.append('近期（2022–2026，紧口径 atoms）：%d 题；多原子 %d（%s）。'%(len(rec),sum(1 for r in rec if r['multi']),pct(sum(1 for r in rec if r['multi']),len(rec))))
        T.append('')
        if rec:
            T.append(md(['难度段','题数','多原子','多原子率'],[[b,len([r for r in rec if r['diff_band']==b]),
                sum(1 for r in rec if r['diff_band']==b and r['multi']),pct(sum(1 for r in rec if r['diff_band']==b and r['multi']),len([r for r in rec if r['diff_band']==b]))] for b in BANDS if any(r['diff_band']==b for r in rec)])); T.append('')
            ct=collections.Counter(r['combo_type'] for r in rec)
            T.append(md(['组合类型','题数'],[[k,ct[k]] for k in ['single','pipeline','optimize','check','hybrid'] if ct[k]])); T.append('')
            ic=collections.Counter('+'.join(sorted(r['atoms'])) for r in rec if r['multi'])
            T.append(md(['多原子组合','题数'],[[ '+'.join(MZH.get(x,x) for x in i.split('+')), c] for i,c in ic.most_common(10)])); T.append('')
        if old:
            sec=sum(1 for r in old if len(r['atoms'])>=2)
            T.append('历史（2007–2021，第一轮主+次代理口径）：%d 题，标了次要算法的 %d（%s）——仅作「是否多解」参考。'%(len(old),sec,pct(sec,len(old))))
            T.append('')
        # 6 position (recent)
        T.append('## 6 题号先验（2022–2026）'); T.append('')
        pr=[r for r in rows if r['position']]
        if pr:
            T.append(md(['位置','题数','难度分布','平均难度','主算法 Top3','多原子率'],
                [[p,len([r for r in pr if r['position']==p]),
                  ' '.join('D%d×%d'%(d,c) for d,c in sorted(collections.Counter(r['difficulty'] for r in pr if r['position']==p).items())),
                  '%.2f'%(sum(r['difficulty'] for r in pr if r['position']==p)/max(1,len([r for r in pr if r['position']==p]))),
                  '、'.join('%s×%d'%(MZH.get(a,a),c) for a,c in collections.Counter(r['primary'] for r in pr if r['position']==p).most_common(3)),
                  pct(sum(1 for r in pr if r['position']==p and r['multi']),len([r for r in pr if r['position']==p]))] for p in POS if any(r['position']==p for r in pr)]))
            T.append('')
        else:
            T.append('（无题号数据）')
        T.append('')
        # 7 carrier/object
        T.append('## 7 载体与对象'); T.append('')
        T.append(md(['载体','题数','Top3 主算法'],[[CZH.get(c,c),n,'、'.join('%s×%d'%(MZH.get(a,a),k) for a,k in collections.Counter(r['primary'] for r in rows if r['carrier']==c).most_common(3))] for c,n in collections.Counter(r['carrier'] for r in rows).most_common(10)])); T.append('')
        T.append(md(['对象','题数','Top3 主算法'],[[OZH.get(o,o),n,'、'.join('%s×%d'%(MZH.get(a,a),k) for a,k in collections.Counter(r['primary'] for r in rows if r['object']==o).most_common(3))] for o,n in collections.Counter(r['object'] for r in rows).most_common()])); T.append('')
        # 8 complexity
        T.append('## 8 复杂度画像'); T.append('')
        def cclass(s):
            s=s or ''
            if '2^' in s or 'n!' in s: return '指数/阶乘'
            if 'n^3' in s: return '立方'
            if 'n^2' in s or 'n m' in s or 'nm' in s: return '平方级'
            if 'log' in s: return 'O(n log n)'
            if 'O(1)' in s or 'O(log' in s: return '常数/对数'
            return '线性'
        cc=collections.Counter(cclass(r['complexity']) for r in rows)
        T.append(md(['复杂度类别','题数','占比'],[[k,c,pct(c,N)] for k,c in cc.most_common()])); T.append('')
        no=collections.Counter(r['n_order'] for r in rows if r['n_order'])
        T.append(md(['n 规模','题数'],[[k,c] for k,c in no.most_common()])); T.append('')
        # 9 candidate eval
        T.append('## 9 候选锚定评估（留一法）'); T.append('')
        pm=eval_loo(rows,'primary'); pf=eval_loo(rows,'primary_family')
        T.append(md(['预测目标','hit@1','hit@3','hit@5'], [
            ['主算法（%d 类）'%len(set(r['primary'] for r in rows)), pct(pm[1]*100,100),pct(pm[3]*100,100),pct(pm[5]*100,100)],
            ['算法族（%d 类）'%len(set(r['primary_family'] for r in rows)), pct(pf[1]*100,100),pct(pf[3]*100,100),pct(pf[5]*100,100)]]))
        T.append('')
        T.append('上下文 = 难度段 + 载体 + 对象 + 规模；小样本，仅作方向参考。'); T.append('')
        S['primary']=dict(pc.most_common()); S['family']=dict(fc.most_common()); S['eval']={'model':pm,'family':pf}
        open(os.path.join(G,'out',lvl+'-tables.md'),'w',encoding='utf-8').write('\n'.join(T))
        summary[lvl]=S
        print('wrote', lvl, N)
    json.dump(summary,open(os.path.join(G,'out','summary.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1,default=str)
if __name__=='__main__': main()
