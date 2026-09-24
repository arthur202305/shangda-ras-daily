# -*- coding: utf-8 -*-
"""
NAV-V2 改革：统一 gh-pages-repo 全归档导航

问题（2026-09-24 体检）：
  - 81 个归档文件中，11 个正常、39 个（6/7月）连导航 CSS 都不存在 → 渲染成裸链接列表
  - 31 个文件的月份标签数与实际链接数对不上（fix_archive_nav.py 的正则部分匹配事故）
  - date-nav 只覆盖"当月滚动窗口" → 6/7/8 月归档在页面上完全不可达

方案（NAV-V2）：
  1. 月份行：6月 / 7月 / 8月 / 9月 四个标签（各指向该月最后一期）＋「价格台账」入口
  2. 日期行：该页所属月份的全部日期，current 高亮，周一分隔
  3. CSS 自包含（字面色值，不用 var()）→ 老页面无 :root 也能正确渲染
  4. 幂等：nav-v2 <style> 与 nav 块按标记定位替换，可反复运行
"""
import io, os, re, sys, glob, shutil, datetime

BASE = os.environ.get('NAV_ROOT') or os.path.dirname(os.path.abspath(__file__))
# 脚本既可放在工作区根（Claw/），也可放在仓库根（gh-pages-repo/），自动识别
GH = BASE if os.path.basename(BASE) == 'gh-pages-repo' else os.path.join(BASE, 'gh-pages-repo')
ARCH = GH + '/archive'
ABS = '/shangda-ras-daily'
LEDGER_HREF = ABS + '/ledger/'

# ---------------------------------------------------------------- NAV-V2 CSS
NAV_CSS = '''<style id="nav-v2">
/* ==== NAV-V2 自包含样式（字面色值 · 覆盖全部归档页） ==== */
.date-nav-bar{
  display:flex; flex-wrap:wrap; align-items:center; gap:6px;
  background:#ffffff; border:1px solid #e6e9ef; border-radius:10px;
  padding:12px 18px; margin-bottom:24px;
  font-size:12px; box-shadow:0 1px 3px rgba(0,0,0,0.03);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
}
.date-nav-bar .nav-months{
  display:flex; flex-wrap:wrap; align-items:center; gap:6px;
  width:100%; padding-bottom:10px; margin-bottom:8px;
  border-bottom:1px dashed #e6e9ef;
}
.date-nav-bar .nav-months a{
  display:inline-block; padding:3px 11px; border-radius:12px;
  border:1px solid #e6e9ef; background:#f7f8fa;
  color:#5a6472; text-decoration:none;
  font-weight:600; font-size:12px; line-height:1.5;
  transition:all .15s ease;
}
.date-nav-bar .nav-months a:hover{
  border-color:#c9a84c; background:#fff8e1; color:#0a1f3f;
}
.date-nav-bar .nav-months a.active{
  background:#0a1f3f; border-color:#0a1f3f; color:#ffffff;
}
.date-nav-bar .nav-months a.nav-ledger{
  margin-left:auto; border-color:rgba(201,168,76,.55);
  background:#fff8e1; color:#8a6d20;
}
.date-nav-bar .nav-months a.nav-ledger:hover{
  background:#c9a84c; border-color:#c9a84c; color:#0a1f3f;
}
.date-nav-bar .month-label{
  font-weight:700; color:#0a1f3f; margin-right:4px;
  font-size:12px; letter-spacing:.5px;
}
.date-nav-bar .month-sep{
  display:inline-block; width:1px; height:14px;
  background:#e6e9ef; margin:0 8px;
}
.date-nav-bar a{
  display:inline-block; padding:3px 9px; border-radius:4px;
  color:#5a6472; text-decoration:none; font-weight:500;
  transition:all .15s ease;
}
.date-nav-bar a:hover{ background:#eef1f6; color:#0a1f3f; }
.date-nav-bar a.current{
  background:#c9a84c; color:#0a1f3f; font-weight:700;
}
@media (max-width:480px){
  .date-nav-bar{ padding:10px 12px; gap:5px; }
  .date-nav-bar a{ padding:3px 7px; }
  .date-nav-bar .nav-months a.nav-ledger{ margin-left:0; }
}
/* ==== NAV-V2 END ==== */
</style>
'''

BEGIN = '<!-- NAV-V2 BEGIN -->'
END = '<!-- NAV-V2 END -->'


def collect_dates():
    ds = []
    for f in sorted(glob.glob(ARCH + '/*.html')):
        d = os.path.basename(f)[:-5]
        if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            ds.append(d)
    return sorted(ds)


def ym(d):
    return d[:7]


def build_months(dates):
    """{'2026-06': ['2026-06-04', ...], ...}"""
    m = {}
    for d in dates:
        m.setdefault(ym(d), []).append(d)
    return {k: sorted(v) for k, v in sorted(m.items())}


def week_key(ds):
    y, m, dd = (int(x) for x in ds.split('-'))
    return datetime.date(y, m, dd).isocalendar()[:2]


def build_nav(cur_date, months, is_index=False):
    """cur_date: 该页代表的日期（index 用最新日期）"""
    cur_m = ym(cur_date)
    # ---- 月份行 ----
    parts = [BEGIN, '<div class="date-nav-bar">', '  <span class="nav-months">']
    for k in sorted(months.keys()):
        last = months[k][-1]
        mi = int(k[5:7])
        cls = ' class="active"' if k == cur_m else ''
        parts.append('    <a href="%s/archive/%s.html"%s>%d月 <span class="mn-cnt">%d</span></a>'
                     % (ABS, last, cls, mi, len(months[k])))
    parts.append('    <a class="nav-ledger" href="%s">📈 价格台账</a>' % LEDGER_HREF)
    parts.append('  </span>')
    # ---- 日期行 ----
    mi = int(cur_m[5:7])
    parts.append('  <span class="month-label">%d月</span>' % mi)
    day_dates = months[cur_m]
    prev_wk = None
    for d in day_dates:
        wk = week_key(d)
        if prev_wk is not None and wk != prev_wk:
            parts.append('  <span class="month-sep"></span>')
        prev_wk = wk
        cur = ' class="current"' if d == cur_date else ''
        parts.append('  <a href="%s/archive/%s.html"%s>%s</a>' % (ABS, d, cur, d[8:10]))
    parts.append('</div>')
    parts.append(END)
    return '\n'.join(parts)


def strip_old_nav(s):
    """移除旧 NAV-V2 块与全部遗留 date-nav-bar 块（可重复，有的页面有 2 个）"""
    n = 0
    # 1) NAV-V2 标记块
    s, k = re.subn(re.escape(BEGIN) + r'.*?' + re.escape(END), '', s, flags=re.S)
    n += k
    # 2) 遗留 date-nav-bar（内部只嵌套 span，不嵌套 div）
    while True:
        m = re.search(r'<div class="date-nav-bar">', s)
        if not m:
            break
        i = m.start()
        # 用 div 深度匹配取真实结束位置，避免内部嵌套
        j = s.find('>', i) + 1
        depth = 1
        k = j
        while depth > 0:
            no = s.find('<div', k)
            nc = s.find('</div>', k)
            if nc < 0:
                break
            if 0 <= no < nc:
                depth += 1
                k = no + 4
            else:
                depth -= 1
                k = nc + 6
        s = s[:i] + s[k:]
        n += 1
    return s, n > 0


def split_nav(block):
    """把 nav 块拆成 (月份行, 日期行)"""
    mon, _, day = block.partition('<span class="month-label">')
    return mon, day


def count_nav(block):
    mon, day = split_nav(block)
    n_month = len(re.findall(r'/archive/\d{4}-\d{2}-\d{2}\.html', mon))
    n_day = len(re.findall(r'<a href="/shangda-ras-daily/archive/[^"]+"', day))
    return n_month, n_day


def ensure_css(s):
    """注入/替换 nav-v2 样式，置于 </head> 前（后置 → 级联覆盖遗留规则）"""
    s = re.sub(r'<style id="nav-v2">.*?</style>\s*', '', s, flags=re.S)
    if '</head>' in s:
        return s.replace('</head>', NAV_CSS + '</head>', 1), True
    return s, False


def main():
    dry = '--apply' not in sys.argv
    dates = collect_dates()
    months = build_months(dates)
    latest = dates[-1]
    print('归档文件 %d 个 / %d 个月：%s' % (len(dates), len(months),
          '  '.join('%s(%d)' % (k, len(v)) for k, v in months.items())))

    if not dry:
        bk = os.environ.get('NAV_BACKUP') or os.path.join(BASE, '_backup_nav')
        if os.path.basename(BASE) == 'gh-pages-repo':
            bk = None  # 仓库内运行时以 git 历史作为备份
        if bk and not os.path.isdir(bk):
            shutil.copytree(ARCH, bk)
            print('✅ 备份 archive → %s（%d 文件）' % (bk, len(os.listdir(bk))))
        elif bk:
            print('ℹ️ 备份已存在，跳过：%s' % bk)

    targets = [(ARCH + '/%s.html' % d, d) for d in dates]
    targets.append((GH + '/index.html', latest))

    ok = fail = 0
    for path, cur in targets:
        s = io.open(path, encoding='utf-8').read()
        before = s
        s, removed = strip_old_nav(s)
        s, css_ok = ensure_css(s)
        nav = build_nav(cur, months, is_index=path.endswith('index.html'))
        # 插到 <body> 之后
        if '<body>' in s:
            s = s.replace('<body>', '<body>\n' + nav + '\n', 1)
        else:
            fail += 1
            print('  ❌ 无 <body> 开标签:', path)
            continue
        # 断言
        errs = []
        # 先记录"本文件固有"的结构失衡（改革前就存在的老毛病），单独统计
        legacy_span = before.count('<span') - before.count('</span>')
        legacy_div = len(re.findall(r'<div\b', before)) - before.count('</div>')
        if s.count('class="date-nav-bar"') != 1:
            errs.append('nav 块数 %d' % s.count('class="date-nav-bar"'))
        if s.count('class="current"') != 1:
            errs.append('current 数 %d' % s.count('class="current"'))
        if not css_ok:
            errs.append('CSS 注入失败')
        if len(re.findall(r'<span\b', s)) - s.count('</span>') != legacy_span:
            errs.append('span 失配(%+d vs 固有%+d)'
                        % (len(re.findall(r'<span\b', s)) - s.count('</span>'), legacy_span))
        if len(re.findall(r'<div\b', s)) - s.count('</div>') != legacy_div:
            errs.append('div 失配(%+d vs 固有%+d)'
                        % (len(re.findall(r'<div\b', s)) - s.count('</div>'), legacy_div))
        nb = s.split('<div class="date-nav-bar">')[1].split('</div>')[0]
        n_month, n_day = count_nav(nb)
        if n_month != len(months):
            errs.append('月份标签 %d != %d' % (n_month, len(months)))
        if n_day != len(months[ym(cur)]):
            errs.append('日期链接 %d != %d' % (n_day, len(months[ym(cur)])))
        if errs:
            fail += 1
            print('  ❌ %s : %s' % (os.path.basename(path), '; '.join(errs)))
            continue
        if not dry:
            with io.open(path, 'w', encoding='utf-8') as f:
                f.write(s); f.flush(); os.fsync(f.fileno())
            # 回读
            assert io.open(path, encoding='utf-8').read() == s, '回读不一致 ' + path
        ok += 1

    print('%s：%d 成功 / %d 失败' % ('DRY-RUN' if dry else 'APPLIED', ok, fail))
    if dry:
        print('   （加 --apply 实际写入）')
    else:
        # 抽样自检
        for d in ['2026-06-04', '2026-08-31', latest]:
            p = ARCH + '/%s.html' % d
            s = io.open(p, encoding='utf-8').read()
            nb = s.split('<div class="date-nav-bar">')[1].split('</div>')[0]
            nm, nd = count_nav(nb)
            print('   %s : months=%d days=%d current=%d css=%s'
                  % (d, nm, nd, s.count('class="current"'), 'nav-v2' in s))
        # 遗留结构失衡清单（只报告，供后续修）
        legacy = []
        for d in dates:
            s = io.open(ARCH + '/%s.html' % d, encoding='utf-8').read()
            a = len(re.findall(r'<span\b', s)) - s.count('</span>')
            b = len(re.findall(r'<div\b', s)) - s.count('</div>')
            if a or b:
                legacy.append((d, a, b))
        if legacy:
            print('   ⚠️ 固有结构失衡 %d 个文件（非本次引入）: %s'
                  % (len(legacy), legacy[:12]))
        else:
            print('   ✅ 无固有结构失衡')


if __name__ == '__main__':
    main()
