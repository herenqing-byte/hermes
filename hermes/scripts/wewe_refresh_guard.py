#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE_URL = os.environ.get('WEWE_BASE_URL', 'http://127.0.0.1:4000')
AUTH_CODE = os.environ.get('WEWE_AUTH_CODE', '527931')
TARGET_FEEDS = [
    'MP_WXS_3016155866',
    'MP_WXS_3223096120',
    'MP_WXS_3934419561',
]
STALE_AFTER_SECONDS = int(os.environ.get('WEWE_STALE_AFTER_SECONDS', str(12 * 3600)))
SLEEP_BETWEEN_REFRESH = float(os.environ.get('WEWE_REFRESH_SLEEP_SECONDS', '6'))
TIMEOUT_SECONDS = int(os.environ.get('WEWE_TIMEOUT_SECONDS', '45'))


def request(url, method='GET', data=None, headers=None):
    req = urllib.request.Request(url, method=method, headers=headers or {}, data=data)
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return resp.read().decode('utf-8', errors='replace')


def fetch_feeds():
    text = request(f'{BASE_URL}/feeds', headers={'User-Agent': 'hermes-wewe-refresh/1.0'})
    return json.loads(text)


def call_refresh(feed_id):
    body = json.dumps({'mpId': feed_id}).encode('utf-8')
    text = request(
        f'{BASE_URL}/trpc/feed.refreshArticles',
        method='POST',
        data=body,
        headers={
            'User-Agent': 'hermes-wewe-refresh/1.0',
            'Authorization': AUTH_CODE,
            'Content-Type': 'application/json',
        },
    )
    return text


def fmt_ts(ts):
    if not ts:
        return 'N/A'
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')


def main():
    now = int(time.time())
    try:
        feeds = fetch_feeds()
    except Exception as exc:
        print('WEWE_REFRESH_STATUS: ERROR')
        print(f'WEWE_REFRESH_ERROR: failed_to_fetch_feed_list: {exc}')
        return 0

    by_id = {item.get('id'): item for item in feeds if item.get('id') in TARGET_FEEDS}
    refreshed = []
    skipped = []
    errors = []
    warnings = []

    for feed_id in TARGET_FEEDS:
        item = by_id.get(feed_id)
        if not item:
            errors.append({'feed_id': feed_id, 'reason': 'missing_from_feed_list'})
            continue

        sync_time = int(item.get('syncTime') or 0)
        lag = now - sync_time if sync_time else 10**9
        if lag < STALE_AFTER_SECONDS:
            skipped.append({
                'feed_id': feed_id,
                'name': item.get('name', feed_id),
                'lag_seconds': lag,
                'sync_time': sync_time,
            })
            continue

        try:
            response_text = call_refresh(feed_id)
            response_json = json.loads(response_text)
            if isinstance(response_json, dict) and response_json.get('error'):
                message = response_json['error'].get('message', 'unknown_error')
                if '暂无可用读书账号' in message:
                    warnings.append({
                        'feed_id': feed_id,
                        'name': item.get('name', feed_id),
                        'reason': message,
                    })
                else:
                    errors.append({
                        'feed_id': feed_id,
                        'name': item.get('name', feed_id),
                        'reason': message,
                    })
            else:
                refreshed.append({
                    'feed_id': feed_id,
                    'name': item.get('name', feed_id),
                    'lag_seconds_before': lag,
                    'sync_time_before': sync_time,
                })
            time.sleep(SLEEP_BETWEEN_REFRESH)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode('utf-8', errors='replace')
            reason = body or str(exc)
            if '暂无可用读书账号' in reason:
                warnings.append({
                    'feed_id': feed_id,
                    'name': item.get('name', feed_id),
                    'reason': '暂无可用读书账号',
                })
            else:
                errors.append({
                    'feed_id': feed_id,
                    'name': item.get('name', feed_id),
                    'reason': reason,
                })
        except Exception as exc:
            errors.append({
                'feed_id': feed_id,
                'name': item.get('name', feed_id),
                'reason': str(exc),
            })

    try:
        feeds_after = fetch_feeds()
        by_id_after = {item.get('id'): item for item in feeds_after if item.get('id') in TARGET_FEEDS}
    except Exception:
        by_id_after = {}

    for group in (refreshed, skipped):
        for entry in group:
            after = by_id_after.get(entry['feed_id'])
            if after:
                entry['sync_time_after'] = after.get('syncTime')
                entry['update_time_after'] = after.get('updateTime')

    summary = {
        'checked_at': datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),
        'stale_after_seconds': STALE_AFTER_SECONDS,
        'refreshed_count': len(refreshed),
        'skipped_count': len(skipped),
        'warning_count': len(warnings),
        'error_count': len(errors),
        'refreshed': refreshed,
        'skipped': skipped,
        'warnings': warnings,
        'errors': errors,
    }

    print('WEWE_REFRESH_STATUS: OK')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print('\n简表:')
    for entry in refreshed:
        print(f"- refreshed {entry['name']} | lag_before={entry['lag_seconds_before']}s | before={fmt_ts(entry.get('sync_time_before'))} | after={fmt_ts(entry.get('sync_time_after'))}")
    for entry in skipped:
        print(f"- skipped {entry['name']} | lag={entry['lag_seconds']}s | sync={fmt_ts(entry.get('sync_time_after') or entry.get('sync_time'))}")
    for entry in warnings:
        print(f"- warning {entry['name']} | {entry['reason']}")
    for entry in errors:
        print(f"- error {entry.get('name', entry['feed_id'])} | {entry['reason']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
