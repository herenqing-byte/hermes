#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_URL = os.environ.get('WEWE_BASE_URL', 'http://127.0.0.1:4000')
AUTH_CODE = os.environ.get('WEWE_AUTH_CODE', '527931')
TIMEOUT_SECONDS = int(os.environ.get('WEWE_TIMEOUT_SECONDS', '30'))
STATE_PATH = Path(os.path.expanduser('~/.hermes/state/wewe/account-health.json'))
HISTORY_PATH = Path(os.path.expanduser('~/.hermes/state/wewe/account-health-history.jsonl'))

STATUS_LABELS = {
    0: '失效',
    1: '启用',
    2: '禁用',
}


def trpc_get(path: str):
    url = f"{BASE_URL}/trpc/{path}?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D"
    req = urllib.request.Request(url, headers={'Authorization': AUTH_CODE, 'User-Agent': 'hermes-wewe-account-check/1.0'})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode('utf-8'))


def now_local():
    return datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')


def main():
    checked_at = now_local()
    result = {
        'checked_at': checked_at,
        'ok': False,
        'healthy_account_count': 0,
        'blocked_ids': [],
        'accounts': [],
        'issues': [],
    }
    try:
        payload = trpc_get('account.list')
        data = payload[0]['result']['data']
        blocks = set(data.get('blocks') or [])
        items = data.get('items') or []
        result['blocked_ids'] = list(blocks)
        for item in items:
            account = {
                'id': item.get('id'),
                'name': item.get('name'),
                'status': item.get('status'),
                'status_label': STATUS_LABELS.get(item.get('status'), f"unknown:{item.get('status')}"),
                'blocked_today': item.get('id') in blocks,
                'updated_at': item.get('updatedAt'),
            }
            result['accounts'].append(account)
            if account['status'] == 1 and not account['blocked_today']:
                result['healthy_account_count'] += 1
            else:
                issue = f"{account['name']}({account['id']})={account['status_label']}"
                if account['blocked_today']:
                    issue += ' + 今日小黑屋'
                result['issues'].append(issue)
        if not items:
            result['issues'].append('没有配置任何读书账号')
        result['ok'] = result['healthy_account_count'] > 0
    except Exception as exc:
        result['issues'].append(f'检查失败: {exc}')

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    with HISTORY_PATH.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(result, ensure_ascii=False) + '\n')

    print('WEWE_ACCOUNT_HEALTH_STATUS: ' + ('OK' if result['ok'] else 'WARN'))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print('\n简表:')
    print(f"- checked_at={result['checked_at']}")
    print(f"- healthy_account_count={result['healthy_account_count']}")
    if result['issues']:
        for issue in result['issues']:
            print(f'- issue {issue}')
    else:
        print('- all accounts healthy')
    return 0


if __name__ == '__main__':
    sys.exit(main())
