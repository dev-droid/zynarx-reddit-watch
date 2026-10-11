# zynarx-reddit-watch

Personal read-only Reddit keyword monitor. Runs once daily, fetches the newest
posts from a few subreddits via the Reddit API (script-type app, ~2 requests
per day), matches post titles against a keyword list, and writes matches to a
local Markdown digest.

It never posts, comments, votes, or sends messages.

## Setup

```bash
cp .env.example .env   # then fill in REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
python3 watch.py
```

## Files

- `watch.py` — the monitor (zero third-party dependencies, stdlib only)
- `.env` — `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` (not committed)
