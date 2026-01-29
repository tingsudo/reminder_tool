import requests
import json
import os

# 配置环境：先从系统环境找，找不到就用 .env 里的
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK")

# --- 本地测试增强代码 ---
# 如果在本地运行且没有环境变量，可以在这里手动硬编码测试（仅限临时调试）
if not SUPABASE_URL:
    print("检测到本地运行，正在加载测试配置...")
    SUPABASE_URL = "https://haknruuibpesnfmastws.supabase.co"
    SUPABASE_KEY = "sb_publishable_5MuzSf_1GiX94Zw8vzmITA_EzyWPBu2"
    WECHAT_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=7aa9180a-4c39-4611-9303-7bf4d0ef8846"
# -----------------------


def get_pending_tasks():
    url = f"{SUPABASE_URL}/rest/v1/tasks?status=eq.pending&select=*"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

def send_wechat_notification(content):
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }
    requests.post(WECHAT_WEBHOOK, headers=headers, data=json.dumps(data))

def main():
    tasks = get_pending_tasks()
    if not tasks:
        print("没有待办任务")
        return

    # 按老师分组
    grouped_tasks = {}
    for task in tasks:
        teacher = task['assignee']
        grouped_tasks.setdefault(teacher, []).append(task)

    # 构造并发送消息
    full_message = "## 📋 每日待办任务提醒\n"
    for teacher, teacher_tasks in grouped_tasks.items():
        full_message += f"\n**👤 老师：{teacher}**\n"
        for i, t in enumerate(teacher_tasks, 1):
            # 注意：这里的链接需要你之后配置 Pipedream 的 HTTP URL 来处理点击完成
            complete_url = f"https://your-pipedream-url.m.pipedream.net?id={t['id']}"
            full_message += f"{i}. {t['task_content']} [点此完成]({complete_url})\n"
    
    send_wechat_notification(full_message)

if __name__ == "__main__":
    main()