import requests
import json
import os

# 1. 配置环境：优先从系统环境读取吧
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://haknruuibpesnfmastws.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_5MuzSf_1GiX94Zw8vzmITA_EzyWPBu2")
PIPEDREAM_URL = "https://eoixx30gpx9ym7f.m.pipedream.net" # 你的 Pipedream 地址

# 2. 定义负责人与其对应的微信 Webhook 映射
# 在 GitHub Secrets 中，你可以分别设置这些 URL
TEACHER_WEBHOOKS = {
    "Zhang": os.getenv("WEBHOOK_ZHANG", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=6fb04ff9-89c2-4178-a873-224ec4ec6d11"),
    "Flora": os.getenv("WEBHOOK_FLORA", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=002a0ed4-74ff-47b0-ab72-576f6fb8e24e"),
    "Ting": os.getenv("WEBHOOK_TING", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=7aa9180a-4c39-4611-9303-7bf4d0ef8846"),
    "Vivian": os.getenv("WEBHOOK_VIVIAN", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9211ef7c-3c53-428f-861d-7810e39be2f8"),
    "Mao": os.getenv("WEBHOOK_MAO", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=5763b54b-a3eb-491e-900f-abb593395575")
}

def get_pending_tasks():
    # 查询所有 pending 状态的任务
    url = f"{SUPABASE_URL}/rest/v1/tasks?status=eq.pending&select=*"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

def send_wechat_notification(webhook_url, content):
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }
    requests.post(webhook_url, headers=headers, data=json.dumps(data))

def main():
    tasks = get_pending_tasks()
    if not tasks or "error" in tasks:
        print("没有待办任务或获取失败")
        return

    # 按负责人分组任务
    grouped_tasks = {}
    for task in tasks:
        teacher = task.get('assignee')
        if teacher in TEACHER_WEBHOOKS:
            grouped_tasks.setdefault(teacher, []).append(task)

    # 遍历每个老师，发送专属推送
    for teacher, teacher_tasks in grouped_tasks.items():
        webhook_url = TEACHER_WEBHOOKS[teacher]
        
        full_message = f"## 📋 {teacher} 老师，您的每日待办提醒\n"
        for i, t in enumerate(teacher_tasks, 1):
            # 构造 Pipedream 确认链接
            complete_url = f"{PIPEDREAM_URL}?id={t['id']}"
            full_message += f"{i}. {t['task_content']} [点此核对并完成]({complete_url})\n"
        
        print(f"正在发送给 {teacher}...")
        send_wechat_notification(webhook_url, full_message)

if __name__ == "__main__":
    main()
