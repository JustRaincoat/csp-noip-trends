#!/usr/bin/env python3
"""Figures for junior/senior group reports."""
import csv, os, collections, json
import matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); G=os.path.join(ROOT,'groups')
for cand in ['Noto Sans CJK SC','Noto Sans CJK JP','WenQuanYi Zen Hei']:
    if any(cand in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams['font.sans-serif']=[cand]; break
plt.rcParams['axes.unicode_minus']=False
V=json.load(open(os.path.join(ROOT,'taxonomy','vocab.json'),encoding='utf-8'))
MZH={x['id']:x['zh'] for x in V['main_model']}
BANDS=['1-2','3-4','5-6','7-8']; POS=['T1','T2','T3','T4']; COL=plt.cm.tab20.colors
def load(lvl):
    rows=[]
    for r in csv.DictReader(open(os.path.join(G,lvl+'.csv'),encoding='utf-8-sig')):
        r['atoms']=[x for x in (r['atoms'] or '').split('|') if x]
        rows.append(r)
    return rows
for lvl,name in [('junior','普及'),('senior','提高')]:
    rows=load(lvl); N=len(rows); out=os.path.join(G,'out'); os.makedirs(out,exist_ok=True)
    pc=collections.Counter(r['primary'] for r in rows)
    items=pc.most_common(14)[::-1]
    fig,ax=plt.subplots(figsize=(7.8,4.8),dpi=170)
    ax.barh([MZH.get(a,a) for a,_ in items],[c for _,c in items],color='#4C78A8')
    for i,(a,c) in enumerate(items): ax.text(c+0.15,i,'%d (%s)'%(c,'%.0f%%'%(100.0*c/N)),va='center',fontsize=8)
    ax.set_xlabel('题数（共 %d 题）'%N); ax.set_title('%s组主算法分布'%name); ax.set_xlim(0,max(c for _,c in items)*1.22)
    plt.tight_layout(); plt.savefig(os.path.join(out,lvl+'-primary.png')); plt.close()
    fams=[f for f,_ in collections.Counter(r['primary_family'] for r in rows).most_common()]
    bands=[b for b in BANDS if any(r['diff_band']==b for r in rows)]
    tot=collections.Counter(r['diff_band'] for r in rows)
    fig,ax=plt.subplots(figsize=(8.2,4.2),dpi=170)
    bottom=[0]*len(bands)
    for i,f in enumerate(fams):
        vals=[100.0*sum(1 for r in rows if r['diff_band']==b and r['primary_family']==f)/tot[b] for b in bands]
        ax.bar(['难度 %s（%d 题）'%(b,tot[b]) for b in bands],vals,bottom=bottom,label=f,color=COL[i%20]); bottom=[x+y for x,y in zip(bottom,vals)]
    ax.set_ylabel('占比 %'); ax.set_ylim(0,100); ax.set_title('%s组：算法族构成随难度变化'%name)
    ax.legend(ncol=4,fontsize=7.5,loc='upper center',bbox_to_anchor=(0.5,-0.12))
    plt.tight_layout(); plt.savefig(os.path.join(out,lvl+'-family-difficulty.png')); plt.close()
    pr=[r for r in rows if r['position']]
    if pr:
        top=[a for a,_ in collections.Counter(r['primary'] for r in pr).most_common(10)]
        mat=[]
        for p in POS:
            sub=[r for r in pr if r['position']==p]
            mat.append([100.0*sum(1 for r in sub if r['primary']==a)/len(sub) if sub else 0 for a in top])
        fig,ax=plt.subplots(figsize=(8.6,3.8),dpi=170)
        im=ax.imshow(mat,cmap='YlOrRd',aspect='auto',vmin=0,vmax=45)
        ax.set_xticks(range(len(top))); ax.set_xticklabels([MZH.get(a,a) for a in top],rotation=35,ha='right',fontsize=8)
        ax.set_yticks(range(len(POS))); ax.set_yticklabels(POS)
        for i in range(len(POS)):
            for j in range(len(top)):
                if mat[i][j]>=6: ax.text(j,i,'%.0f'%mat[i][j],ha='center',va='center',fontsize=6.5)
        ax.set_title('%s组：2022–2026 题号 × 主算法（%%）'%name); fig.colorbar(im,ax=ax,shrink=0.85)
        plt.tight_layout(); plt.savefig(os.path.join(out,lvl+'-position.png')); plt.close()
    s=json.load(open(os.path.join(out,'summary.json'),encoding='utf-8'))[lvl]
    ev=s.get('eval',{})
    if ev:
        labels=['主算法@1','主算法@3','主算法@5','算法族@1','算法族@3','算法族@5']
        vals=[100*ev['model'][k] for k in ['1','3','5']]+[100*ev['family'][k] for k in ['1','3','5']]
        fig,ax=plt.subplots(figsize=(8,3.8),dpi=170)
        ax.bar(labels,vals,color=['#4C78A8']*3+['#54A24B']*3)
        for i,v in enumerate(vals): ax.text(i,v+1,'%.0f'%v,ha='center',fontsize=8)
        ax.set_ylim(0,100); ax.set_ylabel('留一法命中率 %'); ax.set_title('%s组：题面信号→候选（留一法）'%name)
        plt.xticks(fontsize=8,rotation=12); plt.tight_layout(); plt.savefig(os.path.join(out,lvl+'-candidate.png')); plt.close()
    print(lvl,'figures done')
