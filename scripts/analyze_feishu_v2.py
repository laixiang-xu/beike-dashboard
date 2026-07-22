# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///

import requests
import sys
import io
import json
import os
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

APP_ID     = os.environ.get("FEISHU_APP_ID", "cli_aac4b1a47bf85bee")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
APP_TOKEN = "KOqOb8TwraoiC2suczkc3H8vn0b"
TABLE_ID = "tbl3rhMeTKYd59id"

def get_token():
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    return resp.json()["tenant_access_token"]

def get_all_records(token):
    headers = {"Authorization": f"Bearer {token}"}
    all_records = []
    page_token = None
    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        resp = requests.get(
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records",
            headers=headers, params=params
        ).json()
        all_records.extend(resp["data"]["items"])
        if not resp["data"]["has_more"]:
            break
        page_token = resp["data"]["page_token"]
    return all_records

def get_week_sunday(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    days_until_sunday = 6 - date.weekday()
    sunday = date + timedelta(days=days_until_sunday)
    return sunday.replace(hour=23, minute=59, second=0)

def get_week_label(date_str):
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        year, week, _ = date.isocalendar()
        return f"{year}-W{week:02d}"
    except:
        return "未知周次"

def classify_record(fields):
    has_doc = bool(fields.get("备课文档"))
    has_fanhua = bool(fields.get("备课范画"))
    is_exempt = fields.get("是否免检") == "是"

    if is_exempt:
        return "免检", False

    deadline = None
    if fields.get("上课日期"):
        try:
            deadline = get_week_sunday(fields["上课日期"])
        except:
            pass

    is_late = False
    submit_time = fields.get("提交时间")
    if submit_time and deadline:
        try:
            submit_dt = datetime.strptime(submit_time, "%Y-%m-%d")
            is_late = submit_dt > deadline
        except:
            pass

    if has_doc and has_fanhua:
        return ("迟交完成" if is_late else "已完成"), is_late
    elif has_doc or has_fanhua:
        return "部分提交", is_late
    else:
        return "未提交", False

def analyze(records):
    stats = {
        "meta": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_records": len(records),
            "week": ""
        },
        "overall": {"已完成": 0, "迟交完成": 0, "部分提交": 0, "未提交": 0, "免检": 0, "total": len(records)},
        "by_district": {},
        "by_group": {},
        "by_course": {},
        "all_teachers": []
    }

    # 取最新上课日期推断周次
    dates = [r["fields"].get("上课日期", "") for r in records if r["fields"].get("上课日期")]
    if dates:
        stats["meta"]["week"] = get_week_label(max(dates))

    for r in records:
        fields = r["fields"]
        status, is_late = classify_record(fields)

        district = fields.get("老师学区", "").strip() or "未知"
        group    = fields.get("老师小组", "").strip() or "未知"
        course   = fields.get("课程名", "").strip() or "未知课程"
        teacher  = fields.get("老师艺名", "").strip() or "未知"
        real_name= fields.get("老师真名", "").strip() or ""
        work_id  = fields.get("老师工号", "").strip() or ""
        date     = fields.get("上课日期", "")
        weekday  = fields.get("星期", "")
        submit_t = fields.get("提交时间", "")
        has_doc  = bool(fields.get("备课文档"))
        has_fanhua = bool(fields.get("备课范画"))
        fanhua_token = None
        fanhua_name  = None
        if has_fanhua and fields["备课范画"]:
            fanhua_token = fields["备课范画"][0].get("file_token")
            fanhua_name  = fields["备课范画"][0].get("name")
        doc_token = None
        if has_doc and fields["备课文档"]:
            doc_token = fields["备课文档"][0].get("file_token")

        # overall
        stats["overall"][status] = stats["overall"].get(status, 0) + 1

        # by_district
        if district not in stats["by_district"]:
            stats["by_district"][district] = {
                "已完成": 0, "迟交完成": 0, "部分提交": 0, "未提交": 0, "免检": 0, "total": 0,
                "groups": []
            }
        stats["by_district"][district][status] += 1
        stats["by_district"][district]["total"] += 1

        # by_group
        if group not in stats["by_group"]:
            stats["by_group"][group] = {
                "已完成": 0, "迟交完成": 0, "部分提交": 0, "未提交": 0, "免检": 0, "total": 0,
                "district": district, "teachers": []
            }
        stats["by_group"][group][status] += 1
        stats["by_group"][group]["total"] += 1

        # by_course
        if course not in stats["by_course"]:
            stats["by_course"][course] = {
                "已完成": 0, "未完成": 0, "total": 0, "fanhua_count": 0, "teachers": []
            }
        stats["by_course"][course]["total"] += 1
        if status in ("已完成", "迟交完成", "免检"):
            stats["by_course"][course]["已完成"] += 1
        else:
            stats["by_course"][course]["未完成"] += 1
        if has_fanhua:
            stats["by_course"][course]["fanhua_count"] += 1

        # 老师记录（用于下钻）
        teacher_rec = {
            "name": teacher, "real_name": real_name, "work_id": work_id,
            "district": district, "group": group,
            "course": course, "date": date, "weekday": weekday,
            "has_doc": has_doc, "has_fanhua": has_fanhua,
            "status": status, "is_late": is_late,
            "submit_time": submit_t,
            "fanhua_token": fanhua_token,
            "fanhua_name": fanhua_name,
            "doc_token": doc_token
        }
        stats["by_group"][group]["teachers"].append(teacher_rec)
        stats["by_course"][course]["teachers"].append({
            "name": teacher, "district": district, "group": group,
            "status": status, "has_fanhua": has_fanhua,
            "fanhua_token": fanhua_token, "fanhua_name": fanhua_name,
            "date": date, "submit_time": submit_t
        })
        stats["all_teachers"].append(teacher_rec)

    # 汇总各学区的小组列表
    for group, gdata in stats["by_group"].items():
        d = gdata["district"]
        if d in stats["by_district"] and group not in stats["by_district"][d]["groups"]:
            stats["by_district"][d]["groups"].append(group)

    return stats

if __name__ == "__main__":
    print("读取飞书数据...")
    token = get_token()
    records = get_all_records(token)
    print(f"共读取 {len(records)} 条记录")

    stats = analyze(records)

    week = stats["meta"]["week"]
    total = stats["meta"]["total_records"]
    done = stats["overall"]["已完成"] + stats["overall"]["迟交完成"] + stats["overall"]["免检"]
    rate = done / total * 100 if total else 0

    print(f"周次: {week}")
    print(f"完成率: {rate:.1f}%  ({done}/{total})")
    for d, data in stats["by_district"].items():
        d_done = data["已完成"] + data["迟交完成"] + data["免检"]
        d_rate = d_done / data["total"] * 100 if data["total"] else 0
        print(f"  {d}: {d_rate:.1f}%  ({d_done}/{data['total']})")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "new-dashboard", "dashboard_data.json")
    out = os.path.normpath(out)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\n数据已保存到 {out}")
