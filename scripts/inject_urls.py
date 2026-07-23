# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "Pillow"]
# ///
"""
范画图片下载脚本
从飞书下载范画，压缩后存到 new-dashboard/fanhua_images/，
写入 GitHub Pages 公开静态链接，永久可访问。
"""
import requests, json, sys, io, os, pathlib, time, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from PIL import Image

APP_ID     = os.environ.get("FEISHU_APP_ID", "cli_aac4b1a47bf85bee")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")

GITHUB_PAGES_BASE = "https://laixiang-xu.github.io/beike-dashboard/new-dashboard/fanhua_images"
MAX_SIZE_PX  = 1200   # 长边最大像素
JPEG_QUALITY = 82     # JPEG 压缩质量，约 150-250KB/张

_SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
if (_SCRIPT_DIR / "new-dashboard").exists():
    _BASE = _SCRIPT_DIR / "new-dashboard"
elif (_SCRIPT_DIR.parent / "new-dashboard").exists():
    _BASE = _SCRIPT_DIR.parent / "new-dashboard"
else:
    raise FileNotFoundError(f"找不到 new-dashboard 目录，脚本位置: {_SCRIPT_DIR}")

DATA_PATH   = _BASE / "dashboard_data.json"
IMAGES_DIR  = _BASE / "fanhua_images"
CACHE_PATH  = _BASE / "fanhua_dl_cache.json"  # file_token -> 本地文件名

IMAGES_DIR.mkdir(exist_ok=True)

# ── 获取 tenant_access_token ──────────────────────────────────────
def get_token():
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=15
    )
    return resp.json()["tenant_access_token"]

# ── 下载附件内容 ─────────────────────────────────────────────────
def download_file(file_token, headers):
    resp = requests.get(
        f"https://open.feishu.cn/open-apis/drive/v1/medias/{file_token}/download",
        headers=headers, stream=True, timeout=30
    )
    if resp.status_code != 200:
        return None
    return resp.content

# ── 压缩图片，返回 bytes ─────────────────────────────────────────
def compress(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_SIZE_PX:
        ratio = MAX_SIZE_PX / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue()

# ════════════════════════════════════════════════════════════════
print("读取数据...")
with open(DATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

cache = {}
if CACHE_PATH.exists():
    with open(CACHE_PATH, encoding="utf-8") as f:
        cache = json.load(f)
print(f"缓存中已有 {len(cache)} 条记录")

# 收集所有需要处理的 file_token
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

new_tokens = [ft for ft in tokens if ft not in cache]
print(f"需要新下载：{len(new_tokens)} 张，已缓存：{len(tokens)-len(new_tokens)} 张")

# ── 下载并压缩新图片 ─────────────────────────────────────────────
if new_tokens:
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    ok, fail = 0, 0

    for i, ft in enumerate(new_tokens, 1):
        print(f"  [{i}/{len(new_tokens)}] 下载 {ft[:16]}...", end=" ")

        img_bytes = download_file(ft, headers)
        if img_bytes is None:
            print("下载失败")
            fail += 1
            continue

        try:
            compressed = compress(img_bytes)
        except Exception as e:
            print(f"压缩失败: {e}")
            fail += 1
            continue

        # 用 token 的 hash 作为文件名，避免重名
        fname = hashlib.md5(ft.encode()).hexdigest()[:16] + ".jpg"
        fpath = IMAGES_DIR / fname
        fpath.write_bytes(compressed)

        cache[ft] = fname
        kb = len(compressed) // 1024
        print(f"OK ({kb}KB) -> {fname}")
        ok += 1

        if i % 10 == 0:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)

        time.sleep(0.2)

    print(f"\n下载完成：OK {ok} 张，失败 {fail} 张")

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)

# ── 将 GitHub Pages 静态链接写入 JSON ────────────────────────────
def make_url(fname):
    return f"{GITHUB_PAGES_BASE}/{fname}"

url_map = {ft: make_url(fn) for ft, fn in cache.items()}

for group in data["by_group"].values():
    for t in group.get("teachers", []):
        ft = t.get("fanhua_token")
        t["fanhua_url"] = url_map.get(ft, "") if ft else ""

for course in data["by_course"].values():
    for t in course.get("teachers", []):
        ft = t.get("fanhua_token")
        t["fanhua_url"] = url_map.get(ft, "") if ft else ""

for t in data.get("all_teachers", []):
    ft = t.get("fanhua_token")
    t["fanhua_url"] = url_map.get(ft, "") if ft else ""

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n完成！{len(url_map)} 张范画链接已写入 dashboard_data.json")
print(f"图片存储位置：{IMAGES_DIR}")
