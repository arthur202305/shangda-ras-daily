#!/bin/bash
# ============================================================
# 商达.RAS行业高参 — GitHub Pages 永久部署脚本
# 解决问题：GitHub自动部署deploy环节频繁timeout/failure
# 方案：git push + API手动触发pages/builds（绕过不可靠的自动部署）
# 用法：./deploy.sh <HTML文件路径> <日期YYYY-MM-DD> <期数>
# ============================================================
set -e

HTML_FILE="$1"
DATE="$2"
ISSUE="$3"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$HTML_FILE" ] || [ -z "$DATE" ] || [ -z "$ISSUE" ]; then
    echo "用法: ./deploy.sh <HTML文件> <日期> <期数>"
    echo "示例: ./deploy.sh ../deploy_20260806/shangda_ras_industry_daily_2026-08-06_v7.html 2026-08-06 117"
    exit 1
fi

echo "============================================"
echo "  商达.RAS行业高参 第${ISSUE}期 部署"
echo "  日期: ${DATE}"
echo "============================================"

# Step 1: 复制HTML到仓库
echo "[1/5] 复制HTML文件..."
cp "$HTML_FILE" "$REPO_DIR/index.html"
mkdir -p "$REPO_DIR/archive"
cp "$HTML_FILE" "$REPO_DIR/archive/${DATE}.html"
echo "  ✅ index.html + archive/${DATE}.html"

# Step 2: Git提交
echo "[2/5] Git提交..."
cd "$REPO_DIR"
git add index.html "archive/${DATE}.html"
git commit -m "第${ISSUE}期: ${DATE}"

# Step 3: Git推送
echo "[3/5] Git推送..."
git push origin main
echo "  ✅ 推送成功"

# Step 4: API触发Pages构建（绕过不可靠的自动部署）
echo "[4/5] API触发Pages构建..."
GITHUB_TOKEN=$(git remote get-url origin | sed 's|https://||;s|@github.com.*||')
BUILD_RESPONSE=$(curl -s --connect-timeout 15 -X POST \
    "https://api.github.com/repos/arthur202305/shangda-ras-daily/pages/builds" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github+json")
BUILD_STATUS=$(echo "$BUILD_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','error'))" 2>/dev/null || echo "unknown")
echo "  ✅ Pages构建已排队 (status: $BUILD_STATUS)"

# Step 5: 等待并验证
echo "[5/5] 等待CDN分发（最多120秒）..."
for i in $(seq 1 12); do
    sleep 10
    HTTP_CODE=$(curl -s --connect-timeout 10 -o /dev/null -w "%{http_code}" "https://arthur202305.github.io/shangda-ras-daily/" 2>/dev/null)
    CURRENT=$(curl -sL --connect-timeout 10 "https://arthur202305.github.io/shangda-ras-daily/" 2>/dev/null | grep -oP "第\d+期" | head -1 || echo "")
    if [ "$CURRENT" = "第${ISSUE}期" ]; then
        echo "  ✅ 部署成功！第${ISSUE}期已上线 (HTTP $HTTP_CODE)"
        echo ""
        echo "============================================"
        echo "  部署完成"
        echo "  首页: https://arthur202305.github.io/shangda-ras-daily/"
        echo "  存档: https://arthur202305.github.io/shangda-ras-daily/archive/${DATE}.html"
        echo "============================================"
        exit 0
    fi
    echo "  ⏳ 等待中... (${i}0秒, 当前: ${CURRENT:-未获取})"
done

echo "  ⚠️ 超时未检测到更新，请手动验证"
echo "  https://arthur202305.github.io/shangda-ras-daily/"
exit 1
