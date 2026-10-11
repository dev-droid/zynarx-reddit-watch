#!/usr/bin/env python3
"""Reddit 需求监听：扫指定 sub 的新帖，关键词命中写 markdown 日报。零第三方依赖。"""
import json, os, re, sys, base64, urllib.request, urllib.parse, datetime

BASE = "/opt/reddit-watch"
ENV_FILE = os.path.join(BASE, ".env")
SEEN_FILE = os.path.join(BASE, "seen.json")
OUT_FILE = os.path.join(BASE, "daily.md")

SUBS = ["HVAC", "Plumbing", "electricians", "smallbusiness"]
KEYWORDS = [
    "missed call", "missed calls", "answering service", "after-hours",
    "after hours", "lose customers", "losing customers", "losing leads",
    "phone keeps ringing", "nobody answers", "no one answers",
    "receptionist", "front desk", "speed to lead", "lead response",
    "calls go unanswered", "miss calls", "missed leads",
]

def load_env():
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("\"").strip("\x27")
    return env

def get_token(cid, secret):
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request("https://www.reddit.com/api/v1/access_token", data=data)
    req.add_header("Authorization", "Basic " + base64.b64encode(("%s:%s" % (cid, secret)).encode()).decode())
    req.add_header("User-Agent", "zynarx-lead-watch/1.0")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)["access_token"]

def fetch_new(token):
    url = "https://oauth.reddit.com/r/%s/new.json?limit=100" % "+".join(SUBS)
    req = urllib.request.Request(url)
    req.add_header("Authorization", "bearer " + token)
    req.add_header("User-Agent", "zynarx-lead-watch/1.0")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)["data"]["children"]

def main():
    env = load_env()
    cid, secret = env.get("REDDIT_CLIENT_ID"), env.get("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        print("缺少 REDDIT_CLIENT_ID/SECRET：请先建好 " + ENV_FILE, file=sys.stderr)
        sys.exit(2)
    seen = set(json.load(open(SEEN_FILE))) if os.path.exists(SEEN_FILE) else set()
    token = get_token(cid, secret)
    hits = []
    for p in fetch_new(token):
        d = p["data"]
        pid = d["id"]
        text = (d.get("title", "") + "\n" + d.get("selftext", "")).lower()
        matched = [k for k in KEYWORDS if k in text]
        if matched and pid not in seen:
            snippet = (d.get("selftext", "") or "")[:300].replace("\n", " ")
            hits.append({
                "sub": d.get("subreddit"), "title": d.get("title"),
                "author": d.get("author"),
                "created": datetime.datetime.fromtimestamp(d.get("created_utc", 0), datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "keywords": matched,
                "url": "https://www.reddit.com" + d.get("permalink", ""),
                "snippet": snippet,
            })
        seen.add(pid)
    json.dump(sorted(seen), open(SEEN_FILE, "w"))
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    lines = ["# Reddit 需求监听日报 " + today, ""]
    if hits:
        lines.append("命中 %d 条：\n" % len(hits))
        for h in hits:
            lines.append("## r/%s — %s" % (h["sub"], h["title"]))
            lines.append("- 作者：u/%s ｜ 时间：%s" % (h["author"], h["created"]))
            lines.append("- 关键词：" + ", ".join(h["keywords"]))
            lines.append("- 链接：" + h["url"])
            if h["snippet"]:
                lines.append("- 摘要：" + h["snippet"])
            lines.append("")
    else:
        lines.append("今日无命中。")
    open(OUT_FILE, "w").write("\n".join(lines) + "\n")
    print("命中 %d 条，已写 %s" % (len(hits), OUT_FILE))

main()
