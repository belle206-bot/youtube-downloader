"""
외부 접속 전용 원클릭 실행 스크립트 (FastAPI 서버 + Cloudflare Tunnel)
"""
import os
import sys
import re
import time
import subprocess
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_EXE = os.path.join(BASE_DIR, "cloudflared.exe")

if not os.path.exists(CLOUDFLARED_EXE):
    print("[오류] cloudflared.exe 파일을 찾을 수 없습니다.")
    input("엔터 키를 누르면 종료합니다...")
    sys.exit(1)

print("=" * 65)
print("     YouTube Downloader 온라인 외부 접속 서비스 시작")
print("=" * 65)
print("[1/2] 로컬 서버 시작 중...")

# 1. FastAPI 서버 시작
server_cmd = [
    sys.executable, "-m", "uvicorn", "app:app",
    "--host", "127.0.0.1",
    "--port", "5000",
    "--log-level", "warning"
]
server_proc = subprocess.Popen(
    server_cmd,
    cwd=BASE_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(1.5)

print("[2/2] 보안 암호화(HTTPS) 외부 전용 링크 생성 중...")

# 2. Cloudflare Tunnel 시작
tunnel_cmd = [CLOUDFLARED_EXE, "tunnel", "--url", "http://127.0.0.1:5000"]
tunnel_proc = subprocess.Popen(
    tunnel_cmd,
    cwd=BASE_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace"
)

public_url = None
url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

# 터널 로그에서 생성된 URL 파싱
for line in iter(tunnel_proc.stdout.readline, ''):
    match = url_pattern.search(line)
    if match:
        public_url = match.group(0)
        break

if public_url:
    print("\n" + "=" * 65)
    print(" ★ 외부 접속 링크가 성공적으로 발급되었습니다! ★")
    print(f" 👉 {public_url}")
    print("=" * 65)
    print("※ 스마트폰이나 다른 컴퓨터에서 위 링크로 바로 접속하실 수 있습니다.")
    print("※ 이 검은 창을 끄면 사이트 접속이 중단됩니다. (창을 최소화해 두세요)\n")

    # 클립보드 복사 시도
    try:
        subprocess.run(["clip"], input=public_url.encode('utf-8'), check=False)
        print("✔ 링크가 클립보드에 자동으로 복사되었습니다! (Ctrl+V로 붙여넣기 가능)")
    except Exception:
        pass

    # 브라우저 자동 오픈
    webbrowser.open(public_url)
else:
    print("\n[오류] 외부 링크를 생성하지 못했습니다. 인터넷 연결을 확인해주세요.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n서비스를 종료합니다...")
finally:
    server_proc.terminate()
    tunnel_proc.terminate()
