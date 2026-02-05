"""
Vercel Serverless：替代 Pipedream
处理 ?id=xxx（标记完成）和 ?assignee=xxx（待办列表）
"""
import html
import os
import urllib.parse
import requests
from http.server import BaseHTTPRequestHandler

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://haknruuibpesnfmastws.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_5MuzSf_1GiX94Zw8vzmITA_EzyWPBu2")


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def get_task_by_id(task_id: str):
    """获取单个任务详情"""
    url = f"{SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}&select=*"
    resp = requests.get(url, headers=supabase_headers())
    if resp.status_code != 200:
        return None
    data = resp.json()
    return data[0] if data else None


def mark_task_complete(task_id: str) -> bool:
    url = f"{SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    resp = requests.patch(url, headers=supabase_headers(), json={"status": "done"})
    return resp.status_code in (200, 204)


def get_tasks_by_assignee(assignee: str):
    url = f"{SUPABASE_URL}/rest/v1/tasks?assignee=eq.{assignee}&status=eq.pending&select=*&order=created_at.desc"
    resp = requests.get(url, headers=supabase_headers())
    return resp.json() if resp.status_code == 200 else []


def confirm_html(task_id: str, task_content: str = "", assignee: str = "") -> str:
    """确认页：显示任务内容，点击按钮后才标记完成"""
    task_block = ""
    if task_content:
        task_block += f'<div class="task-block"><h3>任务内容</h3><p class="task-content">{html.escape(task_content)}</p></div>'
    if assignee:
        task_block += f'<p class="assignee">负责人：{html.escape(assignee)}</p>'
    confirm_url = f"?id={html.escape(task_id)}&confirm=1"
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>确认完成</title>
<style>
body{{font-family:system-ui;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f5f5f5;}}
.box{{background:#fff;padding:2rem;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,.1);text-align:center;max-width:480px;}}
h2{{color:#333;margin:0 0 .5rem;}}p{{color:#666;margin:0;}}
.task-block{{text-align:left;margin:1rem 0;padding:1rem;background:#f9fafb;border-radius:8px;border-left:4px solid #667eea;}}
.task-block h3{{margin:0 0 .5rem;font-size:14px;color:#888;}}
.task-content{{font-size:16px;color:#333;line-height:1.6;white-space:pre-wrap;word-break:break-word;}}
.assignee{{margin-top:.5rem;font-size:14px;color:#888;}}
.confirm-btn{{margin-top:1rem;padding:12px 28px;background:#22c55e;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:16px;text-decoration:none;display:inline-block;}}
.confirm-btn:hover{{background:#1ea34f;}}
</style></head>
<body><div class="box"><h2>📋 确认任务</h2><p>请确认以下任务已完成</p>{task_block}
<a class="confirm-btn" href="{confirm_url}">确认完成</a></div></body></html>"""


DONE_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>已完成</title>
<style>body{font-family:system-ui;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f5f5f5;}
.box{background:#fff;padding:2rem;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,.1);text-align:center;}
h2{color:#22c55e;margin:0 0 .5rem;}p{color:#666;margin:0;}</style></head>
<body><div class="box"><h2>✅ 已完成</h2><p>任务已标记为完成</p></div></body></html>"""


def list_html(assignee: str, tasks: list) -> str:
    items = "".join(f"<li>{t['task_content']}</li>" for t in tasks)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{assignee} 的待办</title>
<style>body{{font-family:system-ui;margin:0;padding:20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;}}
.container{{max-width:500px;margin:0 auto;background:#fff;border-radius:16px;padding:24px;box-shadow:0 10px 40px rgba(0,0,0,.2);}}
h1{{color:#333;font-size:1.5rem;margin:0 0 1rem;}}ul{{list-style:none;padding:0;margin:0;}}
li{{padding:12px;border-bottom:1px solid #eee;}}li:last-child{{border:none;}}
.empty{{color:#888;text-align:center;padding:2rem;}}</style></head>
<body><div class="container"><h1>📋 {assignee} 的待办</h1>
{"<ul>" + items + "</ul>" if tasks else '<p class="empty">暂无待办任务</p>'}
</div></body></html>"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        task_id = params.get("id", [None])[0]
        confirm = params.get("confirm", [None])[0] == "1"
        assignee = params.get("assignee", [None])[0]

        if task_id:
            task = get_task_by_id(task_id)
            if not task:
                self._send_html(400, "<h2>任务不存在</h2>")
                return
            content = task.get("task_content", "")
            task_assignee = task.get("assignee", "")
            if confirm:
                # 用户点击了确认完成，更新状态为 completed
                if mark_task_complete(task_id):
                    self._send_html(200, DONE_HTML)
                else:
                    self._send_html(400, "<h2>操作失败</h2>")
            else:
                # 首次进入：只展示任务，等待用户确认
                self._send_html(200, confirm_html(task_id, content, task_assignee))
            return

        if assignee:
            tasks = get_tasks_by_assignee(assignee)
            self._send_html(200, list_html(assignee, tasks))
            return

        self._send_html(200, "<p>Xplorify 任务提醒服务</p>")

    def _send_html(self, code: int, body: str):
        self.send_response(code)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))
