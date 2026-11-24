#!/usr/bin/env python3
"""Fetch statements for the 15 missing senior high-difficulty problems (2007-2021)."""
import json, os, re, time, urllib.request, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'groups', 'statements'); os.makedirs(OUT, exist_ok=True)
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36'
FENCE = chr(96) * 3
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
try: op.open(urllib.request.Request('https://www.luogu.com.cn/problem/list', headers={'User-Agent':UA}), timeout=30).read()
except Exception: pass
PIDS = ["P1084","P1600","P3959","P3960","P5023","P5024","P5659","P5665","P5666","P7078","P7115","P7116","P7916","P7962","P7963"]
def get(pid):
    url = 'https://www.luogu.com.cn/problem/' + pid + '?_contentOnly=1'
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':UA,'x-lentille-request':'content-only','Accept':'application/json'})
            with op.open(req, timeout=40) as r:
                return json.loads(r.read().decode())['data']['problem']
        except Exception:
            time.sleep(1.5*(i+1))
    raise RuntimeError(pid)
def strip(s):
    if not s: return ''
    s = re.sub(r'<script.*?</script>','',s,flags=re.S)
    s = re.sub(r'<br\s*/?>','\n',s); s = re.sub(r'</p>','\n',s); s = re.sub(r'<li>','\n- ',s)
    s = re.sub(r'<[^>]+>','',s)
    for a,b in [('&lt;','<'),('&gt;','>'),('&amp;','&'),('&quot;',chr(34)),('&#39;',chr(39)),('&nbsp;',' ')]: s=s.replace(a,b)
    return re.sub(r'\n{3,}','\n\n',s).strip()
index = []
for pid in PIDS:
    md = os.path.join(OUT, pid + '.md')
    if os.path.exists(md) and os.path.getsize(md) > 200:
        index.append(pid); continue
    p = get(pid)
    json.dump(p, open(os.path.join(OUT, pid + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    c = p.get('content') or {}
    lim = p.get('limits') or {}
    tmax = max(lim.get('time') or [0]); mmax = max(lim.get('memory') or [0])
    parts = ['# ' + p['pid'] + ' ' + p['name'], '', '- 时限/内存：%d ms / %d KB' % (tmax, mmax), '- 洛谷算法标签：（见下）', '']
    for key, label in [('background','题目背景'),('description','题目描述'),('formatI','输入格式'),('formatO','输出格式')]:
        t = strip(c.get(key))
        if t: parts += ['## ' + label, '', t, '']
    h = strip(c.get('hint'))
    if h: parts += ['## 提示', '', h[:6000], '']
    for i, pair in enumerate((p.get('samples') or [])[:2], 1):
        parts += ['输入 %d：' % i, FENCE, pair[0].strip(), FENCE, '输出 %d：' % i, FENCE, pair[1].strip(), FENCE]
    open(md, 'w', encoding='utf-8').write('\n'.join(parts))
    index.append(pid); time.sleep(0.4)
print('done', index)
