# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
飞书范画永久直链注入脚本
原理：把附件（file_token）上传为飞书「消息图片」，获得 image_key，
      拼成永久可公开访问的直链写入 dashboard_data.json。
图片不存本地，GitHub 仓库不增大。
"""
import requests, json, sys, io, os, pathlib, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

APP_ID     = os.environ.get("FEISHU_APP_ID", "cli_aac4b1a47bf85bee")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")

_SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
# 本地直接运行：脚本在 WorkBuddy/，new-dashboard 也在 WorkBuddy/
# GitHub Actions：脚本在 scripts/，new-dashboard 在仓库根目录
if (_SCRIPT_DIR / "new-dashboard").exists():
    _BASE = _SCRIPT_DIR / "new-dashboard"
elif (_SCRIPT_DIR.parent / "new-dashboard").exists():
    _BASE = _SCRIPT_DIR.parent / "new-dashboard"
else:
    raise FileNotFoundError(f"找不到 new-dashboard 目录，脚本位置: {_SCRIPT_DIR}")
DATA_PATH = _BASE / "dashboard_data.json"

# 本地缓存文件：记录 file_token → image_key 的映射，避免重复转存
CACHE_PATH = _BASE / "fanhua_image_keys.json"

# ── 获取 tenant_access_token ──────────────────────────────────────
def get_token():
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    return resp.json()["tenant_access_token"]

# ── 下载附件内容（bytes）─────────────────────────────────────────
def download_file(file_token, headers):
    resp = requests.get(
        f"https://open.feishu.cn/open-apis/drive/v1/medias/{file_token}/download",
        headers=headers, stream=True, timeout=30
    )
    if resp.status_code != 200:
        return None
    return resp.content

# ── 上传为飞书消息图片，获得永久 image_key ────────────────────────
def upload_as_image(img_bytes, headers):
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/images",
        headers=headers,
        data={"image_type": "message"},
        files={"image": ("fanhua.jpg", img_bytes, "image/jpeg")},
        timeout=30
    )
    data = resp.json()
    if data.get("code") == 0:
        return data["data"]["image_key"]
    print(f"    上传失败: {data.get('msg')}")
    return None

# ── 永久直链拼接 ─────────────────────────────────────────────────
def make_url(image_key):
    return f"https://open.feishu.cn/open-apis/im/v1/images/{image_key}"

# ════════════════════════════════════════════════════════════════
print("读取数据...")
with open(DATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

# 读取本地缓存
cache = {}
if CACHE_PATH.exists():
    with open(CACHE_PATH, encoding="utf-8") as f:
        cache = json.load(f)
print(f"缓存中已有 {len(cache)} 条 image_key")

# 收集所有需要处理的 file_token（去重）
tokens = set()
for group in data["by_group"].values():
    for t in group.get("teachers", []):
        if t.get("fanhua_token"):
            tokens.add(t["fanhua_token"])
for course in data["by_course"].values():
    for t in course.get("teachers", []):
        if t.get("fanhua_token"):
            tokens.add(t["fanhua_token"])

tokens = list(tokens)
print(f"共 {len(tokens)} 个范画附件")

# 需要新处理的（缓存里没有的）
new_tokens = [ft for ft in tokens if ft not in cache]
print(f"需要新转存：{len(new_tokens)} 张，已缓存：{len(tokens)-len(new_tokens)} 张")

# ── 转存新图片 ───────────────────────────────────────────────────
if new_tokens:
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    ok, fail = 0, 0

    for i, ft in enumerate(new_tokens, 1):
        print(f"  [{i}/{len(new_tokens)}] 转存 {ft[:16]}...", end=" ")

        img_bytes = download_file(ft, headers)
        if img_bytes is None:
            print("下载失败")
            fail += 1
            continue

        image_key = upload_as_image(img_bytes, headers)
        if image_key:
            cache[ft] = image_key
            print(f"✅ {image_key[:20]}...")
            ok += 1
        else:
            fail += 1

        # 每10张保存一次缓存，防止中途中断丢失
        if i % 10 == 0:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)

        # 轻微限速，避免触发飞书API限流
        time.sleep(0.3)

    print(f"\n转存完成：✅ {ok} 张成功，❌ {fail} 张失败")

    # 保存最终缓存
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)

# ── 将永久直链写入 JSON ──────────────────────────────────────────
url_map = {ft: make_url(ik) for ft, ik in cache.items()}

for group in data["by_group"].values():
    for t in group.get("teachers", []):
        ft = t.get("fanhua_token")
        t["fanhua_url"] = url_map.get(ft, "") if ft else ""

for course in data["by_course"].values():
    for t in course.get("teachers", []):
        ft = t.get("fanhua_token")
        t["fanhua_url"] = url_map.get(ft, "") if ft else ""

# all_teachers 列表同步更新
for t in data.get("all_teachers", []):
    ft = t.get("fanhua_token")
    t["fanhua_url"] = url_map.get(ft, "") if ft else ""

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 完成！{len(url_map)} 张范画永久直链已写入 dashboard_data.json")
print("GitHub 仓库不再存储图片文件。")
