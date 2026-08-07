#!/usr/bin/env python3
"""批量修复archive/下所有HTML文件的date-nav-bar——统一使用绝对路径"""

import os, re, glob

ARCHIVE_DIR = os.path.dirname(os.path.abspath(__file__)) + "/archive"

# 扫描所有归档日期
dates = []
for f in sorted(glob.glob(f"{ARCHIVE_DIR}/*.html")):
    d = os.path.basename(f).replace(".html", "")
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        dates.append(d)

# 按月分组
months = {}
for d in dates:
    y, m, day = d.split("-")
    key = f"{int(m)}月"
    months.setdefault(key, []).append(int(day))

# 生成date-nav-bar HTML (绝对路径)
nav_parts = []
for m_label in sorted(months.keys(), key=lambda x: int(x.replace("月",""))):
    if nav_parts:
        nav_parts.append('  <span class="month-sep"></span>')
    nav_parts.append(f'  <span class="month-label">{m_label}</span>')
    for day in sorted(set(months[m_label])):
        d_str = f"2026-{m_label.replace('月','').zfill(2)}-{str(day).zfill(2)}"
        nav_parts.append(f'<a href="/shangda-ras-daily/archive/{d_str}.html">{day}</a>')

NAV_HTML = '<div class="date-nav-bar">\n' + '\n'.join(nav_parts) + '\n</div>'

print(f"📅 生成导航条: {len(dates)}天, {len(months)}个月")
print(f"📏 HTML长度: {len(NAV_HTML)}字符\n")

# 处理每个文件
fixed, injected = 0, 0
for f in sorted(glob.glob(f"{ARCHIVE_DIR}/*.html")):
    fname = os.path.basename(f)
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()

    original = content

    if '<div class="date-nav-bar">' in content:
        # 替换已有的date-nav-bar块
        content = re.sub(
            r'<div class="date-nav-bar">.*?</div>\s*$',
            NAV_HTML,
            content,
            flags=re.DOTALL | re.MULTILINE
        )
        # 如果regex没匹配，用更宽松的
        if '<div class="date-nav-bar">' in content and '/shangda-ras-daily/' not in content:
            content = re.sub(
                r'<div class="date-nav-bar">.*?</div>',
                NAV_HTML,
                content,
                flags=re.DOTALL
            )
        if content != original:
            fixed += 1
            status = "🔧 replaced"
        else:
            status = "⚠️  need manual"
    else:
        # 无date-nav-bar，在</div>后、<div class="container">前插入
        # 先在container前找插入点
        marker = '<div class="container">'
        if marker in content:
            content = content.replace(marker, NAV_HTML + '\n\n' + marker, 1)
            injected += 1
            status = "✅ injected"
        else:
            status = "❌ no container"

    if content != original:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"  {status}  {fname}")
    else:
        print(f"  {status}  {fname}")

print(f"\n📊 结果: {fixed}个替换 + {injected}个注入 = {fixed+injected}个修复")
print(f"📊 总计: {len(dates)}个文件")
