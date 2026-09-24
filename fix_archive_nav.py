#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【已废弃 2026-09-24】请勿使用本脚本。

原因：本脚本用非贪婪正则去替换导航条——匹配模式是
    <div class="date-nav-bar"> ... </div>
月份标签行内部含 <span> 嵌套时，正则会在第一个 </div> 处提前截断，
产生"部分匹配"事故。2026-09-24 全量体检发现：
  · 31 个归档文件的月份标签数与实际链接数对不上
  · 6/7 月共 39 个页面连导航 CSS 都丢失，渲染成裸链接列表
  · 上述缺陷全部源于本脚本的历次运行

正确做法：运行同目录下的 build_nav.py
    python build_nav.py            # 预演，不改任何文件
    python build_nav.py --apply    # 实际写入（幂等，可反复运行）

build_nav.py 生成 NAV-V2 结构：
    · 月份行：6/7/8/9 月标签（各指向该月最后一期）＋ 价格台账入口
    · 日期行：该页所属月份的全部日期，current 高亮，周一分隔
    · 自包含 nav-v2 样式注入 </head> 之前（字面色值，不依赖 :root 变量，
      因此 6/7 月那些没有变量定义的老页面也能正确渲染）
"""
import os
import sys
import subprocess

print(__doc__)
HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, 'build_nav.py')
if not os.path.exists(TARGET):
    sys.exit('未找到 build_nav.py，请确认仓库完整。')
if os.environ.get('NAV_CONFIRM') != '1':
    print('→ 未执行（安全阀）。确认请设置 NAV_CONFIRM=1 后重跑，或直接运行：')
    print('     python build_nav.py --apply')
    sys.exit(0)
sys.exit(subprocess.call([sys.executable, TARGET, '--apply']))
