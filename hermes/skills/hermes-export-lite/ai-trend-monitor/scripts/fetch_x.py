#!/usr/bin/env python3
"""Fetch recent tweets from key AI people via x.com API with browser Cookie auth.

Strategy (priority order):
1. Browser Cookie (primary) - uses logged-in x.com session via GraphQL API
2. Catclaw search (fallback) - when Cookie auth fails or is unavailable

Cookie extraction: reads from /root/.openclaw/workspace/tools/x_cookies.json
Auto-refresh: if cookie cache is stale (>6h) or auth fails, re-extract from CDP browser
"""

import json
import ssl
import sys
import os
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import urllib.error
import urllib.parse
# === TRACKED ACCOUNTS (70 accounts) ===
ACCOUNTS = [
    # --- AI Company Leaders ---
    ("sama", "leaders", "Sam Altman - OpenAI CEO"),
    ("DarioAmodei", "leaders", "Dario Amodei - Anthropic CEO"),
    ("ylecun", "leaders", "Yann LeCun - Meta Chief AI Scientist"),
    ("AndrewYNg", "leaders", "Andrew Ng - AI Fund / DeepLearning.AI"),
    ("JeffDean", "leaders", "Jeff Dean - Google DeepMind"),
    ("demis_hassabis", "leaders", "Demis Hassabis - Google DeepMind CEO"),
    ("satyanadella", "leaders", "Satya Nadella - Microsoft CEO"),
    ("AravSrinivas", "leaders", "Arav Srinivas - Perplexity CEO"),
    ("mustafasuleyman", "leaders", "Mustafa Suleyman - Microsoft AI CEO"),

    # --- Top Researchers ---
    ("karpathy", "researchers", "Andrej Karpathy - 前 Tesla AI / 独立"),
    ("DrJimFan", "researchers", "Jim Fan - NVIDIA 研究"),
    ("fchollet", "researchers", "François Chollet - Keras / ARC"),
    ("ilyasut", "researchers", "Ilya Sutskever - SSI"),
    ("jackclarkSF", "researchers", "Jack Clark - Anthropic 联合创始人"),
    ("woj_zaremba", "researchers", "Wojciech Zaremba - OpenAI 联合创始人"),
    ("tri_dao", "researchers", "Tri Dao - FlashAttention 作者"),
    ("Tim_Dettmers", "researchers", "Tim Dettmers - 量化/高效训练"),

    # --- AI Coding ---
    ("cursor_ai", "coding", "Cursor - AI Code Editor"),
    ("windsurf_ai", "coding", "Windsurf - AI Coding"),
    ("cognition_labs", "coding", "Cognition - Devin AI Engineer"),
    ("OpenClawAI", "coding", "OpenClaw - AI Agent Platform"),
    ("Replit", "coding", "Replit - AI Coding Platform"),
    ("cline_ai", "coding", "Cline - AI Coding Extension"),
    ("sourcegraph", "coding", "Sourcegraph - Code AI"),
    ("GitHubCopilot", "coding", "GitHub Copilot"),
    ("vercel", "coding", "Vercel - v0 AI"),
    ("stackblitz", "coding", "StackBlitz - bolt.new"),
    ("AnthropicAI", "coding", "Anthropic (Claude Code 相关)"),

    # --- AI Commentators / Podcasters ---
    ("simonw", "commentators", "Simon Willison - LLM 应用专家"),
    ("swyx", "commentators", "Swyx - AI Engineering / Latent Space"),
    ("lexfridman", "commentators", "Lex Fridman - 播客"),
    ("dwarkesh_sp", "commentators", "Dwarkesh Patel - 深度播客"),
    ("emollick", "commentators", "Ethan Mollick - AI 应用/商业"),
    ("TheAIGRID", "commentators", "The AI Grid - AI 新闻"),
    ("mattshumer_", "commentators", "Matt Shumer - AI Builder"),
    ("bindureddy", "commentators", "Bindu Reddy - AI CEO/评论"),
    ("_jasonwei", "commentators", "Jason Wei - OpenAI 研究员"),
    ("RichardSocher", "commentators", "Richard Socher - you.com"),

    # --- OpenAI Researchers ---
    ("lilianweng", "researchers", "Lilian Weng - 前 OpenAI VP, Thinking Machines Lab 联创, 顶级 AI 技术博主"),
    ("polynoamial", "researchers", "Noam Brown - OpenAI 研究员, o1 模型核心, 推理/规划领域顶尖"),
    ("gdb", "leaders", "Greg Brockman - OpenAI 联合创始人兼总裁"),
    ("miramurati", "researchers", "Mira Murati - 前 OpenAI CTO, ChatGPT 核心推动者"),
    ("SebastienBubeck", "researchers", "Sebastien Bubeck - OpenAI 研究员, 前微软杰出科学家, 深度学习理论"),
    ("npew", "researchers", "Peter Welinder - OpenAI 产品副总裁"),
    ("joannejang", "researchers", "Joanne Jang - OpenAI 模型行为负责人"),
    ("romainhuet", "researchers", "Romain Huet - OpenAI 开发者体验主管"),

    # --- Anthropic Researchers ---
    ("AmandaAskell", "researchers", "Amanda Askell - Anthropic Character 团队负责人, Claude 性格设计师"),
    ("ch402", "researchers", "Chris Olah - Anthropic 联合创始人, 可解释性研究开创者"),
    ("janleike", "researchers", "Jan Leike - Anthropic 对齐研究负责人, 前 OpenAI 超级对齐核心"),
    ("alexalbert__", "researchers", "Alex Albert - Anthropic 开发者关系负责人"),
    ("_sholtodouglas", "researchers", "Sholto Douglas - Anthropic 研究员, 前 DeepMind"),

    # --- Google DeepMind Researchers ---
    ("OriolVinyalsML", "researchers", "Oriol Vinyals - DeepMind 研究副总裁, Gemini 联席负责人"),
    ("goodfellow_ian", "researchers", "Ian Goodfellow - DeepMind, GANs 之父"),
    ("OfficialLoganK", "researchers", "Logan Kilpatrick - Google DeepMind 产品, 前 OpenAI 开发者关系"),
    ("ShaneLegg", "researchers", "Shane Legg - DeepMind 联合创始人, 首席 AGI 科学家"),

    # --- Meta AI / 独立 ---
    ("soumithchintala", "researchers", "Soumith Chintala - Meta AI, PyTorch 之父"),
    ("geoffreyhinton", "researchers", "Geoffrey Hinton - 图灵奖/诺贝尔奖, 深度学习之父"),
    ("drfeifei", "researchers", "Fei-Fei Li (李飞飞) - 斯坦福教授, ImageNet 创建者, AI 教母"),

    # --- AI 大 V / 意见领袖 ---
    ("_akhaliq", "commentators", "AK - Hugging Face, 全球最快 AI 论文速递"),
    ("ClementDelangue", "commentators", "Clem Delangue - Hugging Face CEO, 开源 AI 领军"),
    ("rasbt", "commentators", "Sebastian Raschka - Ahead of AI newsletter, LLM 技术内容"),
    ("nathanlambert", "commentators", "Nathan Lambert - AI2 研究员, RLHF 专家, Interconnects newsletter"),
    ("goodside", "commentators", "Riley Goodside - Scale AI 首席提示工程师, Prompt 工程宗师"),
    ("dylan522p", "commentators", "Dylan Patel - SemiAnalysis, AI 芯片/算力最权威分析师"),
    ("kaifulee", "commentators", "李开复 - 01.AI CEO, 创新工场, 中美 AI 双重视角"),

    # --- AI Coding 意见领袖 ---
    ("steipete", "coding", "Peter Steinberger - OpenAI (前 OpenClaw 创始人), AI Agent 实践者"),
    ("levelsio", "coding", "Pieter Levels - 独立开发者, vibe coding 先驱, 年入数百万"),
    ("mckaywrigley", "coding", "Mckay Wrigley - Takeoff AI, AI 编程实战教程第一人"),
    ("mntruell", "coding", "Michael Truell - Cursor CEO, AI 代码编辑器赛道领军"),

    # --- OpenClaw Ecosystem ---
    ("OpenClawAI", "openclaw", "OpenClaw Official"),
    ("nickscamara_", "openclaw", "Nick Scamara - OpenClaw"),
]

# Core accounts: always run Catclaw as supplement even when Nitter succeeds
CORE_ACCOUNTS = {
    "sama", "DarioAmodei", "karpathy", "ylecun", "JeffDean", "demis_hassabis",
    "ilyasut", "DrJimFan", "gdb", "miramurati", "fchollet", "jackclarkSF",
    "satyanadella", "mustafasuleyman", "geoffreyhinton", "drfeifei",
    "simonw", "swyx", "emollick",
}

# Deduplicate
seen = set()
UNIQUE_ACCOUNTS = []
for handle, cat, desc in ACCOUNTS:
    if handle not in seen:
        seen.add(handle)
        UNIQUE_ACCOUNTS.append((handle, cat, desc))

PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

CATEGORY_ORDER = ["leaders", "researchers", "coding", "commentators", "openclaw"]
CATEGORY_LABELS = {
    "leaders": "\U0001f3e2 AI \u516c\u53f8\u9886\u8896",
    "researchers": "\U0001f52c \u9876\u7ea7\u7814\u7a76\u5458",
    "coding": "\U0001f4bb AI Coding",
    "commentators": "\U0001f399\ufe0f \u8bc4\u8bba\u5458 / \u610f\u89c1\u9886\u8896",
    "openclaw": "\U0001f43e OpenClaw \u751f\u6001",
}

COOKIE_TIMEOUT = 10
CATCLAW_TIMEOUT = 12
MAX_WORKERS_COOKIE = 8
MAX_WORKERS_CATCLAW = 10
GLOBAL_TIMEOUT = 180
COOKIE_CACHE_PATH = "/root/.openclaw/workspace/tools/x_cookies.json"
COOKIE_MAX_AGE_HOURS = 6

BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
GRAPHQL_USER_BY_SCREEN_NAME = "qW5u-DAuXpMEG0zA1F7UGQ"
GRAPHQL_USER_TWEETS = "V7H0Ap3_Hh2FyS75OCDO3Q"


# =====================================================================
# Cookie management
# =====================================================================

def load_cookies_from_cache():
    if not os.path.exists(COOKIE_CACHE_PATH):
        return None, None
    try:
        with open(COOKIE_CACHE_PATH) as f:
            data = json.load(f)
        extracted_at = data.get("extracted_at", "")
        if extracted_at:
            age = datetime.now() - datetime.fromisoformat(extracted_at)
            if age.total_seconds() > COOKIE_MAX_AGE_HOURS * 3600:
                print(f"[fetch_x] Cookie cache is {age.total_seconds()/3600:.1f}h old, will refresh.", file=sys.stderr)
                return None, None
        cookie_list = data.get("cookies", [])
        cookie_dict = {c["name"]: c["value"] for c in cookie_list}
        if "auth_token" not in cookie_dict or "ct0" not in cookie_dict:
            print("[fetch_x] Cookie cache missing auth_token/ct0.", file=sys.stderr)
            return None, None
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
        return cookie_dict, cookie_str
    except Exception as e:
        print(f"[fetch_x] Failed to load cookie cache: {e}", file=sys.stderr)
        return None, None


def extract_cookies_from_browser():
    try:
        from playwright.sync_api import sync_playwright
        print("[fetch_x] Extracting cookies from browser CDP...", file=sys.stderr)
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            ctx = browser.contexts[0]
            all_cookies = ctx.cookies("https://x.com")
            cookie_dict = {c["name"]: c["value"] for c in all_cookies}
            if "auth_token" not in cookie_dict or "ct0" not in cookie_dict:
                print("[fetch_x] Browser cookies missing auth_token/ct0. Not logged in?", file=sys.stderr)
                return None, None
            os.makedirs(os.path.dirname(COOKIE_CACHE_PATH), exist_ok=True)
            with open(COOKIE_CACHE_PATH, "w") as f:
                json.dump({
                    "cookies": all_cookies,
                    "extracted_at": datetime.now().isoformat(),
                }, f, indent=2)
            print(f"[fetch_x] Saved {len(all_cookies)} cookies to cache.", file=sys.stderr)
            cookie_str = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
            return cookie_dict, cookie_str
    except ImportError:
        print("[fetch_x] playwright not available, cannot extract cookies.", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"[fetch_x] Failed to extract cookies from browser: {e}", file=sys.stderr)
        return None, None


def get_cookies(force_refresh=False):
    if not force_refresh:
        cookie_dict, cookie_str = load_cookies_from_cache()
        if cookie_dict:
            return cookie_dict, cookie_str
    return extract_cookies_from_browser()


# =====================================================================
# X.com API helpers
# =====================================================================

def make_x_request(url, cookie_dict, cookie_str):
    ct0 = cookie_dict.get("ct0", "")
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {BEARER_TOKEN}")
    req.add_header("Cookie", cookie_str)
    req.add_header("x-csrf-token", ct0)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    req.add_header("x-twitter-active-user", "yes")
    req.add_header("x-twitter-auth-type", "OAuth2Session")
    req.add_header("x-twitter-client-language", "zh-cn")
    req.add_header("Accept", "application/json")
    req.add_header("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
    req.add_header("Referer", "https://x.com/")
    if PROXY:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        )
    else:
        opener = urllib.request.build_opener()
    resp = opener.open(req, timeout=COOKIE_TIMEOUT)
    return json.loads(resp.read())


def get_user_id(screen_name, cookie_dict, cookie_str):
    variables = json.dumps({
        "screen_name": screen_name,
        "withSafetyModeUserFields": True,
    })
    features = json.dumps({
        "hidden_profile_likes_enabled": True,
        "hidden_profile_subscriptions_enabled": True,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "subscriptions_verification_info_is_identity_verified_enabled": True,
        "subscriptions_verification_info_verified_since_enabled": True,
        "highlights_tweets_tab_ui_enabled": True,
        "responsive_web_twitter_article_notes_tab_enabled": False,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "responsive_web_graphql_timeline_navigation_enabled": True,
    })
    _params1 = {"variables": variables, "features": features}
    url = (f"https://api.x.com/graphql/{GRAPHQL_USER_BY_SCREEN_NAME}/UserByScreenName"
           f"?{urllib.parse.urlencode(_params1)}")
    result = make_x_request(url, cookie_dict, cookie_str)
    user = result.get("data", {}).get("user", {}).get("result", {})
    return user.get("rest_id")


def extract_tweets_from_timeline(timeline_data):
    tweets = []
    instructions = (timeline_data.get("data", {})
                    .get("user", {})
                    .get("result", {})
                    .get("timeline_v2", {})
                    .get("timeline", {})
                    .get("instructions", []))
    for instr in instructions:
        if instr.get("type") == "TimelineAddEntries":
            for entry in instr.get("entries", []):
                content = entry.get("content", {})
                items_to_check = []
                if content.get("itemContent"):
                    items_to_check.append(content["itemContent"])
                for item in content.get("items", []):
                    if item.get("item", {}).get("itemContent"):
                        items_to_check.append(item["item"]["itemContent"])
                for item_content in items_to_check:
                    tweet_result = item_content.get("tweet_results", {}).get("result", {})
                    if tweet_result.get("__typename") == "TweetWithVisibilityResults":
                        tweet_result = tweet_result.get("tweet", tweet_result)
                    legacy = tweet_result.get("legacy", {})
                    if not legacy.get("full_text"):
                        continue
                    tweets.append({
                        "id": legacy.get("id_str", ""),
                        "text": legacy.get("full_text", ""),
                        "date": legacy.get("created_at", ""),
                        "retweet": legacy.get("retweeted_status_id_str") is not None,
                        "reply": legacy.get("in_reply_to_status_id_str") is not None,
                        "lang": legacy.get("lang", ""),
                    })
    return tweets


def fetch_user_tweets_by_id(user_id, cookie_dict, cookie_str, count=20):
    variables = json.dumps({
        "userId": user_id,
        "count": count,
        "includePromotedContent": False,
        "withQuickPromoteEligibilityTweetFields": True,
        "withVoice": True,
        "withV2Timeline": True,
    })
    features = json.dumps({
        "rweb_lists_timeline_redesign_enabled": True,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "tweetypie_unmention_optimization_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": False,
        "tweet_awards_web_tipping_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "responsive_web_enhance_cards_enabled": False,
    })
    _params2 = {"variables": variables, "features": features}
    url = (f"https://api.x.com/graphql/{GRAPHQL_USER_TWEETS}/UserTweets"
           f"?{urllib.parse.urlencode(_params2)}")
    return make_x_request(url, cookie_dict, cookie_str)


def parse_twitter_date(date_str):
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception:
        try:
            return datetime.strptime(date_str, "%a %b %d %H:%M:%S +0000 %Y").replace(tzinfo=timezone.utc)
        except Exception:
            return None


_user_id_cache = {}


def fetch_via_browser_cookie(handle, cookie_dict, cookie_str, hours=24, max_tweets=10):
    """Fetch recent tweets for a handle using browser Cookie auth (x.com GraphQL API)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    tweets = []

    if handle not in _user_id_cache:
        user_id = get_user_id(handle, cookie_dict, cookie_str)
        if not user_id:
            raise ValueError(f"Could not resolve user ID for @{handle}")
        _user_id_cache[handle] = user_id
    user_id = _user_id_cache[handle]

    timeline_data = fetch_user_tweets_by_id(user_id, cookie_dict, cookie_str, count=20)
    raw_tweets = extract_tweets_from_timeline(timeline_data)

    for t in raw_tweets:
        tweet_time = parse_twitter_date(t["date"])
        if tweet_time and tweet_time < cutoff:
            continue
        text = t.get("text", "")
        tweet_id = t.get("id", "")
        link = f"https://x.com/{handle}/status/{tweet_id}" if tweet_id else ""
        tweets.append({
            "title": text[:100],
            "text": text[:800],
            "link": link,
            "date": t.get("date", ""),
            "source": "browser_cookie",
            "lang": t.get("lang", ""),
        })
        if len(tweets) >= max_tweets:
            break

    return tweets


# =====================================================================
# Catclaw fallback
# =====================================================================

def search_catclaw(query, num=10, engine="google-search"):
    payload = {
        "query": query,
        "sources": [engine],
        "topK": num,
        "isFast": True,
        "timeout": CATCLAW_TIMEOUT,
    }
    data = json.dumps(payload).encode()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        "https://mmc.sankuai.com/openclaw/v1/universal-search",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=CATCLAW_TIMEOUT, context=ctx)
        result = json.loads(resp.read())
        return result.get("data", {}).get("results", [])
    except Exception:
        return []


def fetch_via_catclaw(handle, description, hours=24):
    yesterday = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%d")
    tweets = []
    queries = [
        f"from:{handle} site:x.com since:{yesterday}",
        f'"{handle}" site:x.com',
        f"@{handle} site:twitter.com",
    ]
    for query in queries:
        results = search_catclaw(query, num=5)
        if results:
            for r in results:
                url = r.get("url", "")
                title = r.get("title", "")
                snippet = r.get("snippet", r.get("content", ""))
                if "x.com" in url or "twitter.com" in url:
                    tweets.append({
                        "title": title[:300],
                        "text": snippet[:800] if snippet else title[:800],
                        "link": url,
                        "date": r.get("publishedDate", r.get("date", "")),
                        "source": "catclaw",
                    })
            if tweets:
                break
    return tweets


# =====================================================================
# Per-account fetching
# =====================================================================

def fetch_single_account(handle, cat, desc, cookie_state, hours, max_per_account):
    """Fetch tweets for one account: browser_cookie first, catclaw fallback."""
    result_tweets = []
    stats = {"cookie_ok": 0, "cookie_fail": 0, "catclaw_ok": 0, "catclaw_fail": 0, "error": False}

    if cookie_state:
        try:
            cookie_tweets = fetch_via_browser_cookie(
                handle, cookie_state["dict"], cookie_state["str"], hours=hours, max_tweets=max_per_account
            )
            for t in cookie_tweets:
                t["account"] = handle
                t["category"] = cat
                t["who"] = desc
                result_tweets.append(t)
            stats["cookie_ok"] = 1
            return result_tweets, stats
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                stats["cookie_fail"] = 1
                raise RuntimeError(f"Auth error {e.code} for @{handle}")
            stats["cookie_fail"] = 1
            print(f"  [cookie] @{handle}: HTTP {e.code}", file=sys.stderr)
        except Exception as e:
            stats["cookie_fail"] = 1
            print(f"  [cookie] @{handle}: {type(e).__name__}: {e}", file=sys.stderr)

    catclaw_tweets = fetch_via_catclaw(handle, desc, hours=hours)
    if catclaw_tweets:
        stats["catclaw_ok"] = 1
        for t in catclaw_tweets[:max_per_account]:
            t["account"] = handle
            t["category"] = cat
            t["who"] = desc
            result_tweets.append(t)
    else:
        stats["catclaw_fail"] = 1
        if not cookie_state:
            stats["error"] = True

    return result_tweets, stats


# =====================================================================
# Main fetch orchestration
# =====================================================================

def fetch_all(hours=24, max_per_account=10):
    global_start = time.time()
    all_tweets = []
    errors = []
    cookie_ok = 0
    cookie_fail = 0
    catclaw_ok = 0
    catclaw_fail = 0
    cookie_refresh_attempted = False
    auth_errors = []

    print(f"[fetch_x] Scanning {len(UNIQUE_ACCOUNTS)} accounts (last {hours}h)...", file=sys.stderr)

    print("[fetch_x] Loading x.com cookies...", file=sys.stderr)
    cookie_dict, cookie_str = get_cookies()
    if cookie_dict:
        print(f"[fetch_x] Cookies loaded (auth_token + ct0 present)", file=sys.stderr)
        cookie_state = {"dict": cookie_dict, "str": cookie_str}
    else:
        print("[fetch_x] No valid cookies, will use Catclaw only.", file=sys.stderr)
        cookie_state = None

    core_list = [(h, c, d) for h, c, d in UNIQUE_ACCOUNTS if h in CORE_ACCOUNTS]
    other_list = [(h, c, d) for h, c, d in UNIQUE_ACCOUNTS if h not in CORE_ACCOUNTS]
    ordered_accounts = core_list + other_list

    workers = MAX_WORKERS_COOKIE if cookie_state else MAX_WORKERS_CATCLAW
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {}
        for handle, cat, desc in ordered_accounts:
            if time.time() - global_start > GLOBAL_TIMEOUT - 10:
                print(f"[fetch_x] Global timeout approaching, skipping remaining.", file=sys.stderr)
                break
            f = pool.submit(fetch_single_account, handle, cat, desc, cookie_state, hours, max_per_account)
            future_map[f] = (handle, cat, desc)

        remaining_time = max(GLOBAL_TIMEOUT - (time.time() - global_start), 15)

        for future in as_completed(future_map, timeout=remaining_time):
            handle, cat, desc = future_map[future]
            try:
                tweets, stats = future.result(timeout=5)
                all_tweets.extend(tweets)
                cookie_ok += stats["cookie_ok"]
                cookie_fail += stats["cookie_fail"]
                catclaw_ok += stats["catclaw_ok"]
                catclaw_fail += stats["catclaw_fail"]
                if stats["error"]:
                    errors.append(handle)
                completed += 1
                src = "cookie" if stats["cookie_ok"] else ("catclaw" if stats["catclaw_ok"] else "failed")
                cnt = len(tweets)
                if cnt > 0:
                    print(f"  ✓ @{handle}: {cnt} tweets ({src})", file=sys.stderr)
                elif not stats["error"]:
                    print(f"  · @{handle}: 0 recent ({src})", file=sys.stderr)
                else:
                    print(f"  ✗ @{handle}: failed", file=sys.stderr)
            except RuntimeError as e:
                if "Auth error" in str(e) and not cookie_refresh_attempted:
                    print(f"[fetch_x] Auth failure, refreshing cookies...", file=sys.stderr)
                    auth_errors.append((handle, cat, desc))
                    cookie_refresh_attempted = True
                else:
                    errors.append(handle)
                    cookie_fail += 1
            except Exception as e:
                errors.append(handle)
                cookie_fail += 1
                print(f"  ✗ @{handle}: exception ({e})", file=sys.stderr)

    if auth_errors and cookie_refresh_attempted:
        print(f"[fetch_x] Re-fetching {len(auth_errors)} accounts with refreshed cookies...", file=sys.stderr)
        new_cd, new_cs = get_cookies(force_refresh=True)
        if new_cd:
            new_state = {"dict": new_cd, "str": new_cs}
            for handle, cat, desc in auth_errors:
                try:
                    tweets, stats = fetch_single_account(handle, cat, desc, new_state, hours, max_per_account)
                    all_tweets.extend(tweets)
                    cookie_ok += stats["cookie_ok"]
                except Exception as e:
                    errors.append(handle)
                    print(f"  ✗ @{handle}: retry failed ({e})", file=sys.stderr)
        else:
            for handle, _, _ in auth_errors:
                errors.append(handle)

    total_time = time.time() - global_start
    by_category = defaultdict(list)
    for t in all_tweets:
        by_category[t["category"]].append(t)

    print(f"\n[fetch_x] Done in {total_time:.1f}s.", file=sys.stderr)
    print(f"[fetch_x] Completed {completed}/{len(ordered_accounts)} accounts.", file=sys.stderr)
    print(f"[fetch_x] Cookie: {cookie_ok}✓/{cookie_fail}✗ | Catclaw: {catclaw_ok}✓/{catclaw_fail}✗ | Total tweets: {len(all_tweets)}", file=sys.stderr)

    return {
        "tweets": all_tweets,
        "by_category": {k: v for k, v in by_category.items()},
        "category_counts": {k: len(v) for k, v in by_category.items()},
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "hours": hours,
        "total": len(all_tweets),
        "accounts_tracked": len(UNIQUE_ACCOUNTS),
        "cookie_ok": cookie_ok,
        "cookie_fail": cookie_fail,
        "catclaw_ok": catclaw_ok,
        "catclaw_fail": catclaw_fail,
        "errors": errors,
        "elapsed_seconds": round(total_time, 1),
        "nitter_ok": 0,
        "nitter_fail": 0,
    }


# =====================================================================
# Output formatting
# =====================================================================

def format_categorized_output(result):
    lines = []
    lines.append(f"# X/Twitter AI \u52a8\u6001 \u2014 \u6700\u8fd1 {result['hours']} \u5c0f\u65f6")
    lines.append("")
    lines.append(f"**\u91c7\u96c6\u65f6\u95f4**: {result['fetched_at']}")
    lines.append(f"**\u8ffd\u8e2a\u8d26\u53f7\u6570**: {result['accounts_tracked']} (\u53bb\u91cd\u540e)")
    lines.append(f"**\u83b7\u53d6\u63a8\u6587\u6570**: {result['total']}")
    lines.append(f"**\u8017\u65f6**: {result.get('elapsed_seconds', '?')}s")
    lines.append(f"**\u6570\u636e\u6e90**: Cookie API {result['cookie_ok']}\u2713/{result['cookie_fail']}\u2717 | Catclaw {result['catclaw_ok']}\u2713/{result['catclaw_fail']}\u2717")
    if result["errors"]:
        lines.append(f"**\u5931\u8d25\u8d26\u53f7**: {', '.join(result['errors'][:20])}")
    lines.append("")
    lines.append("---")
    lines.append("")
    by_category = result.get("by_category", {})
    for cat_key in CATEGORY_ORDER:
        tweets = by_category.get(cat_key, [])
        if not tweets:
            continue
        label = CATEGORY_LABELS.get(cat_key, cat_key)
        lines.append(f"## {label}")
        lines.append("")
        by_account = defaultdict(list)
        for t in tweets:
            by_account[t["account"]].append(t)
        for account, account_tweets in by_account.items():
            who = account_tweets[0].get("who", account)
            lines.append(f"### @{account} ({who})")
            for t in account_tweets:
                date_str = t.get("date", "")
                link = t.get("link", "")
                text = t.get("text", t.get("title", ""))
                source = t.get("source", "")
                if text:
                    display_text = text[:500] + "..." if len(text) > 500 else text
                    lines.append(f"- {display_text}")
                if link:
                    lines.append(f"  \u6765\u6e90: [{link}]({link})")
                if date_str:
                    lines.append(f"  \u65e5\u671f: {date_str}")
                if source:
                    lines.append(f"  via: {source}")
                lines.append("")
        lines.append("")
    return "\n".join(lines)


# =====================================================================
# CLI
# =====================================================================

if __name__ == "__main__":
    test_mode = "--test" in sys.argv
    if test_mode:
        sys.argv.remove("--test")

    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    output_format = sys.argv[2] if len(sys.argv) > 2 else "json"

    if test_mode:
        print("[test] Quick test for @sama, @karpathy, @AnthropicAI", file=sys.stderr)
        cookie_dict, cookie_str = get_cookies()
        if not cookie_dict:
            print("[test] FAILED: No cookies available", file=sys.stderr)
            sys.exit(1)
        print(f"[test] Cookies: auth_token={'ok' if 'auth_token' in cookie_dict else 'MISSING'}, ct0={'ok' if 'ct0' in cookie_dict else 'MISSING'}", file=sys.stderr)
        test_accounts = [
            ("sama", "leaders", "Sam Altman - OpenAI CEO"),
            ("karpathy", "researchers", "Andrej Karpathy"),
            ("AnthropicAI", "coding", "Anthropic"),
        ]
        total_found = 0
        for handle, cat, desc in test_accounts:
            try:
                tweets = fetch_via_browser_cookie(handle, cookie_dict, cookie_str, hours=48, max_tweets=5)
                print(f"  @{handle}: {len(tweets)} tweets (last 48h)", file=sys.stderr)
                for t in tweets[:2]:
                    print(f"    - [{t['date'][:16]}] {t['text'][:100]}", file=sys.stderr)
                total_found += len(tweets)
            except Exception as e:
                print(f"  @{handle}: ERROR - {e}", file=sys.stderr)
        print(f"\n[test] Total: {total_found} tweets from 3 accounts", file=sys.stderr)
        result = {"test": "ok", "total_tweets": total_found}
        print(json.dumps(result))
        sys.exit(0)

    result = fetch_all(hours=hours)
    if output_format in ("md", "markdown"):
        print(format_categorized_output(result))
    else:
        output = {k: v for k, v in result.items() if k != "by_category"}
        print(json.dumps(output, ensure_ascii=False, indent=2))
