import os
import random

import requests
import pendulum
from zhconv import convert

# Configuration
TIMEZONE = "Asia/Shanghai"
# 使用 v2 API 获取完整诗词
SENTENCE_API = "https://v2.jinrishici.com/one.json"

DEFAULT_SENTENCE = """《苦笋》
赏花归去马如飞，
去马如飞酒力微，
酒力微醒时已暮，
醒时已暮赏花归。

—— 宋·苏轼"""

# 当无法获取历史事件时的备用有趣内容
FALLBACK_INTERESTING_FACTS = [
    "🎲 今天是个特别的日子，因为你又活过了新的一天！",
    "💡 有趣的事实：每天地球上大约会发生 50,000 次地震，但大多数我们感觉不到。",
    "🌍 你知道吗？地球每天会被大约 100 吨的宇宙尘埃撞击。",
    "⏰ 时间小知识：一天并不是精确的 24 小时，而是 23 小时 56 分 4 秒。",
    "🧠 大脑趣闻：你的大脑每天产生大约 50,000 个想法。",
    "📚 阅读启示：平均每人每天会说大约 16,000 个字。",
    "☕ 咖啡因事实：全世界每天要喝掉超过 20 亿杯咖啡。",
    "🌟 宇宙奥秘：光从太阳到达地球需要约 8 分 20 秒。",
    "💭 哲学思考：'今天'这个词在不同时区有 24 种不同的含义。",
    "🎯 激励语录：每一个伟大的成就，都始于决定去尝试。",
]

GET_UP_MESSAGE_TEMPLATE = """今天的起床时间是--{get_up_time}。

起床啦。

今天是今年的第 {day_of_year} 天。

{year_progress}

{history_today}

今天的一句诗:

{sentence}

#morning
"""

def get_one_sentence():
    """获取今天的一首诗

    使用今日诗词 v2 API 获取完整的诗词内容
    返回格式：《诗名》\n诗词内容\n\n—— 朝代·作者
    """
    try:
        r = requests.get(SENTENCE_API, timeout=10)
        if r.ok:
            data = r.json()

            # 获取诗词来源信息
            origin = data.get("data", {}).get("origin", {})
            title = origin.get("title", "")
            dynasty = origin.get("dynasty", "")
            author = origin.get("author", "")
            content_list = origin.get("content", [])

            if content_list and title and author:
                # 将诗词内容数组合并为字符串（每句一行）
                content = "\n".join(content_list)
                # 格式化输出：《诗名》\n内容\n\n—— 朝代·作者
                poem = f"《{title}》\n{content}\n\n—— {dynasty}·{author}"
                return poem

        return DEFAULT_SENTENCE
    except Exception as e:
        print(f"get SENTENCE_API wrong: {e}")
        return DEFAULT_SENTENCE

def get_day_of_year():
    now = pendulum.now(TIMEZONE)
    return now.day_of_year

def get_year_progress():
    """获取今年的进度条"""
    now = pendulum.now(TIMEZONE)
    day_of_year = now.day_of_year

    # 判断是否为闰年
    is_leap_year = now.year % 4 == 0 and (now.year % 100 != 0 or now.year % 400 == 0)
    total_days = 366 if is_leap_year else 365

    # 计算进度百分比
    progress_percent = (day_of_year / total_days) * 100

    # 生成进度条 (20个字符宽度)
    progress_bar_width = 20
    filled_blocks = int((day_of_year / total_days) * progress_bar_width)
    empty_blocks = progress_bar_width - filled_blocks

    progress_bar = "█" * filled_blocks + "░" * empty_blocks

    return f"{progress_bar} {progress_percent:.1f}% ({day_of_year}/{total_days})"

def get_history_today(limit=3):
    """获取历史上的今天发生的事件

    Args:
        limit: 返回事件数量限制

    Returns:
        str: 格式化的历史事件信息
    """
    try:
        now = pendulum.now(TIMEZONE)
        month = now.format("MM")
        day = now.format("DD")

        # 使用 Wikimedia On this day API
        url = f"https://api.wikimedia.org/feed/v1/wikipedia/zh/onthisday/events/{month}/{day}"

        headers = {"User-Agent": "GetUpBot/1.0 (https://github.com/iAlan66/get_up)"}

        response = requests.get(url, headers=headers, timeout=10)

        if not response.ok:
            print(f"Failed to get history today: {response.status_code}")
            return ""

        data = response.json()
        events = data.get("events", [])

        if not events:
            return ""

        # 过滤出 1900 至今的事件
        current_year = now.year
        filtered_events = [
            event
            for event in events
            if "year" in event and 1990 <= event["year"] <= current_year
        ]

        # 如果没有符合条件的事件，就取所有事件
        if not filtered_events:
            filtered_events = [e for e in events if "year" in e]

        if not filtered_events:
            return ""

        # 随机选择指定数量的事件
        selected_events = random.sample(
            filtered_events, min(limit, len(filtered_events))
        )
        # 按年份倒序排列选中的事件
        selected_events.sort(key=lambda x: x.get("year", 0), reverse=True)

        result_lines = ["历史上的今天：\n"]

        for event in selected_events:
            year = event.get("year")
            text = event.get("text", "")

            # 获取维基百科链接
            pages = event.get("pages", [])
            wiki_url = ""
            if pages and len(pages) > 0:
                # 使用第一个页面的链接
                content_urls = pages[0].get("content_urls", {})
                desktop = content_urls.get("desktop", {})
                wiki_url = desktop.get("page", "")

            # 清理文本中的换行符和多余空格，并转换为简体中文
            text = text.replace("\n", " ").strip()
            text = convert(text, "zh-cn")  # 繁体转简体

            # 构建带链接的文本
            if wiki_url:
                result_lines.append(f"• {year}年：[{text}]({wiki_url})")
            else:
                result_lines.append(f"• {year}年：{text}")

        return "\n".join(result_lines)

    except Exception as e:
        print(f"Error getting history today: {e}")
        # 返回随机的有趣内容作为备用
        return random.choice(FALLBACK_INTERESTING_FACTS)

def post_to_memos(content):
    memos_url = os.getenv("MEMOS_URL")
    memos_token = os.getenv("MEMOS_TOKEN")

    if not memos_url or not memos_token:
        print("MEMOS_URL or MEMOS_TOKEN not set")
        return

    # Ensure URL is correct
    if not memos_url.endswith("/api/v1/memos"):
        memos_url = memos_url.rstrip("/") + "/api/v1/memos"

    headers = {
        "Authorization": f"Bearer {memos_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "content": content,
    }

    try:
        response = requests.post(memos_url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Successfully posted to Memos")
        else:
            print(f"Failed to post to Memos: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error posting to Memos: {e}")

def main():
    get_up_time = pendulum.now(TIMEZONE).to_datetime_string()
    sentence = get_one_sentence()
    day_of_year = get_day_of_year()
    year_progress = get_year_progress()
    history_today = get_history_today()

    body = GET_UP_MESSAGE_TEMPLATE.format(
        get_up_time=get_up_time,
        sentence=sentence,
        day_of_year=day_of_year,
        year_progress=year_progress,
        history_today=history_today,
    )

    print("Generated Message:")
    print(body)

    post_to_memos(body)

if __name__ == "__main__":
    main()