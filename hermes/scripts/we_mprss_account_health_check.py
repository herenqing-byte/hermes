#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_URL = os.environ.get('WEMPRSS_BASE_URL', 'http://127.0.0.1:8001')
LOGIN_URL = f'{BASE_URL}/api/v1/wx/auth/login'
SEARCH_URL = f'{BASE_URL}/api/v1/wx/mps/search/%E6%B7%B1%E6%80%9DSenseAI?offset=0&limit=1'
APP_DIR = Path(os.environ.get('WEMPRSS_APP_DIR', '/Users/herenqing/we-mp-rss'))
APP_ENV = APP_DIR / '.env.local'
APP_PY = APP_DIR / '.venv/bin/python'
WX_LIC = APP_DIR / 'data/wx.lic'
STATE_PATH = Path(os.path.expanduser('~/.hermes/state/we_mprss/account-health.json'))
HISTORY_PATH = Path(os.path.expanduser('~/.hermes/state/we_mprss/account-health-history.jsonl'))
TIMEOUT_SECONDS = int(os.environ.get('WEMPRSS_TIMEOUT_SECONDS', '30'))
ADMIN_USERNAME = os.environ.get('WEMPRSS_ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('WEMPRSS_ADMIN_PASSWORD', 'admin@123')
WARN_EXPIRE_SECONDS = int(os.environ.get('WEMPRSS_WARN_EXPIRE_SECONDS', str(24 * 3600)))


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
        import subprocess
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


def now_local():
    return datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')


def main():
    result = {
        'checked_at': now_local(),
        'ok': False,
        'service_state': None,
        'issues': [],
        'token_expiry': None,
        'search_ok': False,
    }
    try:
        result['service_state'] = ensure_service()
        if not WX_LIC.exists():
            result['issues'].append('wx.lic 缺失')
        else:
            content = WX_LIC.read_text()
            token = ''
            expiry_time = None
            expiry_ts = 0.0
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith('token:'):
                    token = stripped.split(':', 1)[1].strip().strip("'")
                elif stripped.startswith('expiry_time:'):
                    expiry_time = stripped.split(':', 1)[1].strip().strip("'")
                elif stripped.startswith('expiry_timestamp:'):
                    try:
                        expiry_ts = float(stripped.split(':', 1)[1].strip().strip("'"))
                    except ValueError:
                        expiry_ts = 0.0
            result['token_expiry'] = expiry_time
            if not token:
                result['issues'].append('token 缺失')
            if expiry_ts and expiry_ts - time.time() < WARN_EXPIRE_SECONDS:
                result['issues'].append('token 即将过期')
        token = login_token()
        payload = json.loads(request(SEARCH_URL, headers={'Authorization': f'Bearer {token}'}))
        result['search_ok'] = bool((payload.get('data') or {}).get('list'))
        if not result['search_ok']:
            result['issues'].append('搜索公众号失败')
        result['ok'] = not result['issues']
    except Exception as exc:
        result['issues'].append(f'检查失败: {exc}')

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    with HISTORY_PATH.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(result, ensure_ascii=False) + '\n')

    print('WEMPRSS_ACCOUNT_HEALTH_STATUS: ' + ('OK' if result['ok'] else 'WARN'))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print('\n简表:')
    print(f"- checked_at={result['checked_at']}")
    print(f"- service_state={result['service_state']}")
    print(f"- token_expiry={result['token_expiry']}")
    print(f"- search_ok={result['search_ok']}")
    if result['issues']:
        for issue in result['issues']:
            print(f'- issue {issue}')
    else:
        print('- account healthy')
    return 0


if __name__ == '__main__':
    sys.exit(main())
