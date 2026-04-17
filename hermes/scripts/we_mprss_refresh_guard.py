#!/usr/bin/env python3
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = os.environ.get('WEMPRSS_BASE_URL', 'http://127.0.0.1:8001')
LOGIN_URL = f'{BASE_URL}/api/v1/wx/auth/login'
UPDATE_URL = f'{BASE_URL}/api/v1/wx/mps/update/{{feed_id}}?start_page=0&end_page=1'
DB_PATH = Path(os.environ.get('WEMPRSS_DB_PATH', '/Users/herenqing/we-mp-rss/data/db.db'))
APP_DIR = Path(os.environ.get('WEMPRSS_APP_DIR', '/Users/herenqing/we-mp-rss'))
APP_ENV = APP_DIR / '.env.local'
APP_PY = APP_DIR / '.venv/bin/python'
TARGET_FEEDS = [
    'MP_WXS_3016155866',
    'MP_WXS_3223096120',
    'MP_WXS_3934419561',
]
STALE_AFTER_SECONDS = int(os.environ.get('WEMPRSS_STALE_AFTER_SECONDS', str(12 * 3600)))
SLEEP_AFTER_UPDATE = float(os.environ.get('WEMPRSS_UPDATE_WAIT_SECONDS', '18'))
TIMEOUT_SECONDS = int(os.environ.get('WEMPRSS_TIMEOUT_SECONDS', '30'))
ADMIN_USERNAME = os.environ.get('WEMPRSS_ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('WEMPRSS_ADMIN_PASSWORD', 'admin@123')


def request(url, method='GET', data=None, headers=None):
    req = urllib.request.Request(url, method=method, headers=headers or {}, data=data)
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return resp.read().decode('utf-8', errors='replace')


def ensure_service():
    try:
        request(f'{BASE_URL}/')
        return 'already_running'
    except Exception:
        env = os.environ.copy()
        if APP_ENV.exists():
            for line in APP_ENV.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                env[k] = v
        subprocess.Popen(
            [str(APP_PY), 'main.py', '-job', 'False', '-init', 'False'],
            cwd=str(APP_DIR),
            env=env,
            stdout=open('/tmp/we-mp-rss.log', 'a'),
            stderr=open('/tmp/we-mp-rss.log', 'a'),
            start_new_session=True,
        )
        for _ in range(20):
            time.sleep(1)
            try:
                request(f'{BASE_URL}/')
                return 'started'
            except Exception:
                pass
        raise RuntimeError('we-mp-rss service did not start in time')


def login_token():
    body = f'username={ADMIN_USERNAME}&password={ADMIN_PASSWORD}'.encode()
    text = request(LOGIN_URL, method='POST', data=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    payload = json.loads(text)
    return payload['data']['access_token']


def fmt_ts(ts):
    if not ts:
        return 'N/A'
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')


def feed_stats(conn, feed_id):
    cur = conn.cursor()
    cur.execute('select mp_name, update_time, sync_time from feeds where id = ?', (feed_id,))
    row = cur.fetchone()
    cur.execute('select count(*), max(publish_time) from articles where mp_id = ?', (feed_id,))
    article_count, latest_publish = cur.fetchone()
    return {
        'name': row[0] if row else feed_id,
        'update_time': row[1] if row else 0,
        'sync_time': row[2] if row else 0,
        'article_count': article_count or 0,
        'latest_publish_time': latest_publish or 0,
    }


def main():
    checked_at = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
    try:
        service_state = ensure_service()
        token = login_token()
    except Exception as exc:
        print('WEMPRSS_REFRESH_STATUS: ERROR')
        print(f'WEMPRSS_REFRESH_ERROR: {exc}')
        return 0

    conn = sqlite3.connect(DB_PATH)
    now = int(time.time())
    refreshed, skipped, errors = [], [], []

    for feed_id in TARGET_FEEDS:
        before = feed_stats(conn, feed_id)
        lag = now - int(before['update_time'] or 0) if before['update_time'] else 10**9
        if lag < STALE_AFTER_SECONDS:
            skipped.append({'feed_id': feed_id, 'name': before['name'], 'lag_seconds': lag, 'before': before})
            continue
        try:
            request(UPDATE_URL.format(feed_id=feed_id), headers={'Authorization': f'Bearer {token}'})
            refreshed.append({'feed_id': feed_id, 'name': before['name'], 'lag_seconds_before': lag, 'before': before})
        except Exception as exc:
            errors.append({'feed_id': feed_id, 'name': before['name'], 'reason': str(exc)})

    if refreshed:
        time.sleep(SLEEP_AFTER_UPDATE)

    for group in (refreshed, skipped):
        for entry in group:
            entry['after'] = feed_stats(conn, entry['feed_id'])

    summary = {
        'checked_at': checked_at,
        'service_state': service_state,
        'stale_after_seconds': STALE_AFTER_SECONDS,
        'refreshed_count': len(refreshed),
        'skipped_count': len(skipped),
        'error_count': len(errors),
        'refreshed': refreshed,
        'skipped': skipped,
        'errors': errors,
    }
    print('WEMPRSS_REFRESH_STATUS: OK')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print('\n简表:')
    print(f'- service_state={service_state}')
    for entry in refreshed:
        after = entry['after']
        delta = after['article_count'] - entry['before']['article_count']
        print(f"- refreshed {entry['name']} | +{delta} articles | latest={fmt_ts(after['latest_publish_time'])}")
    for entry in skipped:
        after = entry['after']
        print(f"- skipped {entry['name']} | lag={entry['lag_seconds']}s | latest={fmt_ts(after['latest_publish_time'])}")
    for entry in errors:
        print(f"- error {entry['name']} | {entry['reason']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
