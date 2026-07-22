# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
import requests, json, sys, io, os, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

APP_ID     = os.environ.get("FEISHU_APP_ID", "cli_aac4b1a47bf85bee")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")

# 路径：相对于脚本所在目录的 ../new-dashboard/
_BASE = pathlib.Path(__file__).parent.parent / "new-dashboard"
DATA_PATH = _BASE / "dashboard_data.json"

token = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": APP_ID, "app_secret": APP_SECRET}
).json()["tenant_access_token"]
headers = {"Authorization": f"Bearer {token}"}

with open(DATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

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

# 正确方式：直接下载图片，保存到本地
img_dir = _BASE / "fanhua_images"
img_dir.mkdir(exist_ok=True)

saved = 0
for ft in tokens:
    out_path = img_dir / f"{ft}.jpg"
    if out_path.exists():
        saved += 1
        continue
    resp = requests.get(
        f"https://open.feishu.cn/open-apis/drive/v1/medias/{ft}/download",
        headers=headers, stream=True
    )
    if resp.status_code == 200:
        with open(out_path, "wb") as f_img:
            for chunk in resp.iter_content(8192):
                f_img.write(chunk)
        saved += 1
        print(f"  ✅ 下载 {ft[:16]}...")
    else:
        print(f"  ❌ 失败 {ft[:16]} status={resp.status_code}")

print(f"\n下载完成：{saved}/{len(tokens)} 张")

# 将本地路径注入 JSON（相对路径，供 HTTP 服务器使用）
url_map = {ft: f"fanhua_images/{ft}.jpg" for ft in tokens
           if (img_dir / f"{ft}.jpg").exists()}

for group in data["by_group"].values():
    for t in group.get("teachers", []):
        ft = t.get("fanhua_token")
        t["fanhua_url"] = url_map.get(ft, "") if ft else ""

for course in data["by_course"].values():
    for t in course.get("teachers", []):
        ft = t.get("fanhua_token")
        t["fanhua_url"] = url_map.get(ft, "") if ft else ""

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("完成！图片路径已写入 dashboard_data.json")
