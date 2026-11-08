"""
YouTube 다운로더 핵심 모듈 (yt-dlp + FFmpeg 기반)
"""
import os
import sys
import re
import imageio_ffmpeg
import yt_dlp

# FFmpeg 경로 자동 감지
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

def sanitize_filename(name: str) -> str:
    """윈도우 파일 시스템에서 허용되지 않는 특수문자 제거/치환"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def get_video_info(url: str) -> dict:
    """
    유튜브 URL에서 영상 메타데이터와 다운로드 가능한 해상도 목록을 추출합니다.
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
    if not info:
        raise ValueError("영상 정보를 불러올 수 없습니다.")
        
    # 플레이리스트인 경우 첫 번째 항목 정보 처리
    if 'entries' in info:
        entries = list(info['entries'])
        is_playlist = True
        playlist_count = len(entries)
        first_video = entries[0] if entries else None
        title = info.get('title', '재생목록')
        thumbnail = first_video.get('thumbnail') if first_video else None
        duration = sum([e.get('duration', 0) or 0 for e in entries if e])
        channel = info.get('uploader') or (first_video.get('uploader') if first_video else '알 수 없음')
        available_resolutions = ['best', '1080p', '720p', 'audio']
    else:
        is_playlist = False
        playlist_count = 1
        title = info.get('title', '제목 없음')
        thumbnail = info.get('thumbnail', '')
        duration = info.get('duration', 0)
        channel = info.get('uploader', '알 수 없음')
        
        # 사용 가능한 해상도 탐색
        formats = info.get('formats', [])
        heights = set()
        for f in formats:
            h = f.get('height')
            if h and f.get('vcodec') != 'none':
                heights.add(h)
        
        sorted_heights = sorted(list(heights), reverse=True)
        available_resolutions = ['best']
        for h in sorted_heights:
            if h >= 2160:
                if '4k (2160p)' not in available_resolutions: available_resolutions.append('2160p')
            elif h >= 1440:
                if '2k (1440p)' not in available_resolutions: available_resolutions.append('1440p')
            elif h >= 1080:
                if '1080p' not in available_resolutions: available_resolutions.append('1080p')
            elif h >= 720:
                if '720p' not in available_resolutions: available_resolutions.append('720p')
            elif h >= 480:
                if '480p' not in available_resolutions: available_resolutions.append('480p')
        available_resolutions.append('audio')

    def format_duration(seconds):
        if not seconds:
            return "00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    return {
        'id': info.get('id', ''),
        'url': url,
        'title': title,
        'thumbnail': thumbnail,
        'duration': duration,
        'duration_str': format_duration(duration),
        'channel': channel,
        'is_playlist': is_playlist,
        'playlist_count': playlist_count,
        'resolutions': available_resolutions
    }

def download_video(
    url: str,
    output_dir: str,
    quality: str = "best",
    progress_callback = None
) -> dict:
    """
    유튜브 영상을 지정 폴더로 다운로드합니다.
    - quality: 'best', '2160p', '1440p', '1080p', '720p', '480p', 'audio'
    """
    os.makedirs(output_dir, exist_ok=True)
    
    downloaded_files = []

    def hook(d):
        status = d.get('status')
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded_bytes = d.get('downloaded_bytes') or 0
        speed = d.get('speed') or 0
        eta = d.get('eta') or 0
        filename = d.get('filename', '')

        percent = 0.0
        if total_bytes > 0:
            percent = round((downloaded_bytes / total_bytes) * 100, 1)

        speed_str = ""
        if speed:
            if speed > 1024 * 1024:
                speed_str = f"{speed / (1024 * 1024):.1f} MB/s"
            else:
                speed_str = f"{speed / 1024:.1f} KB/s"

        eta_str = ""
        if eta:
            eta_str = f"{eta}초 남음"

        if status == 'finished':
            if filename:
                downloaded_files.append(filename)

        if progress_callback:
            progress_callback({
                'status': status,
                'percent': percent,
                'downloaded_bytes': downloaded_bytes,
                'total_bytes': total_bytes,
                'speed': speed_str,
                'eta': eta_str,
                'filename': os.path.basename(filename) if filename else ''
            })

    # yt-dlp 옵션 구성
    outtmpl = os.path.join(output_dir, '%(title)s [%(id)s].%(ext)s')

    ydl_opts = {
        'ffmpeg_location': FFMPEG_PATH,
        'outtmpl': outtmpl,
        'progress_hooks': [hook],
        'windowsfilenames': True,
        'restrictfilenames': False,
        'no_warnings': True,
        'quiet': True,
    }

    if quality == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    elif quality == 'best':
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })
    else:
        # 특정 해상도 (예: 1080p -> height<=1080)
        h = quality.replace('p', '')
        if h.isdigit():
            ydl_opts.update({
                'format': f'bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best[height<={h}]/best',
                'merge_output_format': 'mp4',
            })
        else:
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', '영상')
        target_file = ydl.prepare_filename(info)
        
        # audio 변환 시 파일 확장자가 mp3로 바뀜
        if quality == 'audio':
            base, _ = os.path.splitext(target_file)
            target_file = base + '.mp3'

    return {
        'status': 'success',
        'title': title,
        'file_path': target_file,
        'file_name': os.path.basename(target_file),
        'output_dir': output_dir
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("사용법: python downloader.py <유튜브링크> [화질] [저장폴더]")
        print("예시: python downloader.py https://youtu.be/... best downloads")
        sys.exit(1)
        
    url_arg = sys.argv[1]
    quality_arg = sys.argv[2] if len(sys.argv) > 2 else "best"
    out_dir_arg = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(__file__), "downloads")
    
    print(f"영상 정보 조회 중: {url_arg}")
    try:
        video_meta = get_video_info(url_arg)
        print(f"제목: {video_meta['title']}")
        print(f"채널: {video_meta['channel']} | 길이: {video_meta['duration_str']}")
        print(f"다운로드 시작 (화질: {quality_arg})...")
        
        def print_prog(p):
            if p['status'] == 'downloading':
                print(f"\r진행률: {p['percent']}% | 속도: {p['speed']} | {p['eta']}", end='', flush=True)
            elif p['status'] == 'finished':
                print("\n다운로드 완료, 변환 및 병합 중...")

        result = download_video(url_arg, out_dir_arg, quality_arg, print_prog)
        print(f"\n성공! 저장 위치: {result['file_path']}")
    except Exception as e:
        print(f"\n오류 발생: {e}")
