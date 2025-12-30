import os
import requests
import pendulum

# Configuration
TIMEZONE = "Asia/Shanghai"
SENTENCE_API = "https://v1.jinrishici.com/all"
DEFAULT_SENTENCE = "赏花归去马如飞\r\n去马如飞酒力微\r\n酒力微醒时已暮\r\n醒时已暮赏花归\r\n"

GET_UP_MESSAGE_TEMPLATE = """今天的起床时间是--{get_up_time}。

起床啦。

今天是今年的第 {day_of_year} 天。

{year_progress}

今天的一句诗:

{sentence}
"""

def get_one_sentence():
    try:
        r = requests.get(SENTENCE_API)
        if r.ok:
            return r.json()["content"]
        return DEFAULT_SENTENCE
    except Exception:
        print("get SENTENCE_API wrong")
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

    body = GET_UP_MESSAGE_TEMPLATE.format(
        get_up_time=get_up_time,
        sentence=sentence,
        day_of_year=day_of_year,
        year_progress=year_progress,
    )

    print("Generated Message:")
    print(body)

    post_to_memos(body)

if __name__ == "__main__":
    main()