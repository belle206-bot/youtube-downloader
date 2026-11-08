# 🎬 YouTube Video Downloader (유튜브 영상 다운로더)

유튜브 링크(일반 동영상, 쇼츠 Shorts, 재생목록)를 입력하면 원하는 폴더에 초고화질(최대 4K) MP4 영상 또는 고음질 MP3 음원으로 다운로드해 주는 서비스입니다.

---

## 🚀 빠른 시작 (가장 쉬운 실행 방법)

1. 폴더 안의 **`run.bat`** 파일을 **더블클릭**합니다.
2. 검은색 콘솔 창이 열리며 서비스가 자동으로 시작되고, **웹 브라우저가 자동으로 열립니다** (`http://127.0.0.1:5000`).
3. 다운로드하고 싶은 유튜브 링크를 입력하고 **[영상 정보 확인]** 버튼을 누릅니다.
4. 원하는 화질(최고 화질 4K/1080p 또는 MP3 오디오)을 선택하고 **[다운로드 시작]** 버튼을 클릭합니다.
5. 다운로드가 완료되면 **[다운로드 폴더에서 보기]**를 눌러 영상을 확인합니다!

---

## ✨ 주요 기능

1. **초고화질 비디오 다운로드**:
   - 원본 최고화질(4K, 2K, 1080p FHD, 720p HD 등) 자동 감지 및 선택 가능
   - 영상(Video)과 음성(Audio)을 무손실로 완벽하게 합쳐 MP4 파일로 저장 (FFmpeg 내장)
2. **MP3 음원 추출**:
   - 영상 없이 음악/오디오만 192kbps 고음질 MP3로 추출 가능
3. **유튜브 Shorts 및 재생목록 지원**:
   - `youtube.com/shorts/...` 숏폼 링크도 완벽 다운로드
   - 재생목록 링크 지원
4. **실시간 다운로드 진행률 표시**:
   - 다운로드 진행률(%), 속도(MB/s), 남은 시간 실시간 표시
5. **편리한 폴더 관리**:
   - 기본 저장 위치: `e:\13.김정아\숏폼제작\Youtube\downloads`
   - 웹 화면에서 **[폴더 변경]** 클릭 시 윈도우 폴더 선택 창이 열려 자유롭게 저장 위치 변경 가능
   - **[저장 폴더 열기]** 클릭 시 윈도우 파일 탐색기 즉시 실행
6. **최근 다운로드 기록**:
   - 웹 화면 하단에서 최근 다운로드된 파일 목록과 용량을 한눈에 확인 가능

---

## 💻 터미널 / CLI 사용법 (개발자용)

웹 브라우저 없이 명령 프롬프트(CMD)나 PowerShell에서도 바로 다운로드할 수 있습니다.

```powershell
# 기본 최고화질 다운로드
python downloader.py "https://www.youtube.com/watch?v=영상ID"

# 1080p 화질 다운로드
python downloader.py "https://www.youtube.com/watch?v=영상ID" 1080p

# MP3 음원만 추출
python downloader.py "https://www.youtube.com/watch?v=영상ID" audio

# 특정 폴더에 다운로드
python downloader.py "https://www.youtube.com/watch?v=영상ID" best "C:\Users\User\Videos"
```

---

## 📁 디렉토리 구조

```
e:\13.김정아\숏폼제작\Youtube\
│
├── run.bat              # 더블클릭으로 원클릭 실행 (브라우저 자동 오픈)
├── app.py               # FastAPI 웹 서버 백엔드
├── downloader.py        # yt-dlp + FFmpeg 다운로드 엔진
├── templates/
│   └── index.html       # 모던 웹 대시보드 UI (Tailwind CSS)
├── downloads/           # 기본 영상 저장 폴더
├── requirements.txt     # 의존 패키지 목록
└── README.md            # 본 설명서
```
