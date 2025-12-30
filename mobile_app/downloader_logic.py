import yt_dlp
import os
import re

def format_size(bytes_val):
    if not bytes_val:
        return "N/A"
    power = 1024
    n = 0
    power_labels = {0 : 'B', 1: 'KiB', 2: 'MiB', 3: 'GiB', 4: 'TiB'}
    while bytes_val > power:
        bytes_val /= power
        n += 1
    return f"{bytes_val:.2f}{power_labels.get(n, '')}"

class YouTubeDownloader:
    def __init__(self, download_path=None):
        if download_path:
             self.base_path = download_path
        else:
             # Intelligent path detection
             if os.path.exists('/storage/emulated/0/Download'):
                 self.base_path = '/storage/emulated/0/Download'
             else:
                 self.base_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        self.video_path = os.path.join(self.base_path, 'video')
        self.audio_path = os.path.join(self.base_path, 'audio')
        
        for p in [self.video_path, self.audio_path]:
            if not os.path.exists(p):
                try:
                    os.makedirs(p)
                except Exception as e:
                    print(f"Error creating dir {p}: {e}")

    def get_video_info(self, url):
        """获取视频信息和可用格式"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            print(f"Error fetching info: {e}")
            return None

    def download_video(self, url, format_id=None, progress_callback=None, cancel_check=None):
        """下载视频（指定格式或最佳画质）"""
        
        def progress_hook(d):
            if cancel_check and cancel_check():
                raise Exception("Download Cancelled")

            if d['status'] == 'downloading':
                if progress_callback:
                    # 1. 尝试解析百分比
                    p_str = d.get('_percent_str', '0%').strip()
                    try:
                        p_match = re.search(r"(\d+\.?\d*)", p_str)
                        if p_match:
                            val = float(p_match.group(1))
                            p = val / 100.0
                        else:
                            p = 0.0
                        
                        # 2. 尝试解析 ETA
                        raw_eta = d.get('_eta_str', '')
                        eta = raw_eta.strip()
                        if not re.match(r"^\d+:\d+", eta):
                             eta = "Unknown"
                        
                        # 3. 构建详细状态信息
                        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                        total_bytes_str = format_size(total_bytes)
                        
                        speed = d.get('speed')
                        speed_str = f"{format_size(speed)}/s" if speed else "Unknown speed"
                        
                        eta_str = d.get('_eta_str') or eta
                        # 如果没有格式化的时间，尝试从秒数转换
                        if (not eta_str or "Unknown" in eta_str) and d.get('eta'):
                             eta_s = d.get('eta')
                             eta_str = f"{int(eta_s//60):02d}:{int(eta_s%60):02d}"

                        # 格式化百分比
                        p_str = f"{p*100:.1f}%"
                        
                        status_msg = f"[download] {p_str} of {total_bytes_str} at {speed_str} ETA {eta_str}"
                        
                        progress_callback(p, status_msg)
                    except Exception as e:
                       print(f"Progress error: {e}")
            elif d['status'] == 'finished':
                if progress_callback:
                    progress_callback(1.0, "处理中...")

        # 检查本地或系统的 FFMPEG
        import shutil
        ffmpeg_local = os.path.join(os.getcwd(), 'ffmpeg.exe')
        has_ffmpeg = os.path.exists(ffmpeg_local) or shutil.which('ffmpeg') is not None
        ffmpeg_location = ffmpeg_local if os.path.exists(ffmpeg_local) else None

        ydl_opts = {
            'outtmpl': os.path.join(self.video_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4',
        }
        
        if ffmpeg_location:
            ydl_opts['ffmpeg_location'] = ffmpeg_location

        if format_id:
            ydl_opts['format'] = f"{format_id}+bestaudio/best"
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

        try:
            # 1. 先获取标题，计算唯一文件名，防止跳过
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl_temp:
                info = ydl_temp.extract_info(url, download=False)
                base_title = info.get('title', 'video')
                
                # 简单净化文件名
                safe_title = "".join([c for c in base_title if c.isalpha() or c.isdigit() or c in (' ', '-', '_', '.')]).rstrip()
                
                # 检测文件名冲突
                final_title = safe_title
                counter = 1
                while True:
                    # 假设最终是 mp4
                    check_path = os.path.join(self.video_path, f"{final_title}.mp4")
                    if os.path.exists(check_path):
                        final_title = f"{safe_title} ({counter})"
                        counter += 1
                    else:
                        break
            
            # 更新输出模板为唯一文件名
            ydl_opts['outtmpl'] = os.path.join(self.video_path, f"{final_title}.%(ext)s")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return "视频下载完成"
        except Exception as e:
            if "Download Cancelled" in str(e):
                return "已暂停"
            return f"错误: {e}"

    def download_audio(self, url, progress_callback=None, cancel_check=None):
        """下载音频（尝试转换为 MP3）"""
        import shutil
        
        ffmpeg_local = os.path.join(os.getcwd(), 'ffmpeg.exe')
        has_ffmpeg = os.path.exists(ffmpeg_local) or shutil.which('ffmpeg') is not None
        ffmpeg_location = ffmpeg_local if os.path.exists(ffmpeg_local) else None

        def progress_hook(d):
            if cancel_check and cancel_check():
                raise Exception("Download Cancelled")

            if d['status'] == 'downloading':
                if progress_callback:
                    p = 0.0
                    # 1. 尝试计算百分比
                    total = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded = d.get('downloaded_bytes')
                    
                    if total and downloaded:
                        p = float(downloaded) / float(total)
                    
                    # 2. ETA 处理
                    eta_seconds = d.get('eta')
                    if eta_seconds is not None:
                        m, s = divmod(eta_seconds, 60)
                        h, m = divmod(m, 60)
                        if h > 0:
                            eta_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
                        else:
                            eta_str = f"{int(m):02d}:{int(s):02d}"
                    else:
                        raw_eta = d.get('_eta_str', '')
                        eta_str = raw_eta.strip()

                        if not re.search(r"\d+:\d+", eta_str):
                            eta_str = "Unknown"
                    
                    # 3. 构建详细状态信息
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    total_bytes_str = format_size(total_bytes)
                    
                    speed = d.get('speed')
                    speed_str = f"{format_size(speed)}/s" if speed else "Unknown speed"
                    
                    percent_str = f"{p*100:.1f}%"
                    
                    raw_eta = d.get('_eta_str')
                    if raw_eta:
                         eta_str = raw_eta.strip()
                    
                    # 清理可能存在的 ANSI 字符
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    if eta_str: eta_str = ansi_escape.sub('', eta_str)

                    status_msg = f"[download] {percent_str} of {total_bytes_str} at {speed_str} ETA {eta_str}"
                    
                    progress_callback(p, status_msg)

            elif d['status'] == 'finished':
                if progress_callback:
                    step = "转换中..." if has_ffmpeg else "完成中..."
                    progress_callback(1.0, step)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.audio_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
        }
        
        if ffmpeg_location:
            ydl_opts['ffmpeg_location'] = ffmpeg_location

        if has_ffmpeg:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        try:
            # 1. 计算唯一文件名
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl_temp:
                info = ydl_temp.extract_info(url, download=False)
                base_title = info.get('title', 'audio')
                safe_title = "".join([c for c in base_title if c.isalpha() or c.isdigit() or c in (' ', '-', '_', '.')]).rstrip()
                
                final_title = safe_title
                counter = 1
                while True:
                    # 音频可能是 mp3
                    check_path = os.path.join(self.audio_path, f"{final_title}.mp3")
                    if os.path.exists(check_path):
                        final_title = f"{safe_title} ({counter})"
                        counter += 1
                    else:
                        break

            ydl_opts['outtmpl'] = os.path.join(self.audio_path, f"{final_title}.%(ext)s")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True) 
                ext = info.get('ext', 'audio')
                if has_ffmpeg:
                     return "Audio Download Complete (MP3)"
                else:
                     return f"Audio Download Complete (Saved as .{ext} - Install FFmpeg for MP3)"
        except Exception as e:
            if "Download Cancelled" in str(e):
                return "已暂停"
            return f"Error: {e}"

    def download_thumbnail(self, url):
        """下载封面图片"""
        import requests
        
        info = self.get_video_info(url)
        if not info:
             return "无法获取信息"
        
        thumbnail_url = info.get('thumbnail')
        title = info.get('title', 'thumbnail')
        
        if not thumbnail_url:
            return "未找到封面"

        try:
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                # 净化文件名
                safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ' or c=='_']).rstrip()
                filename = f"{safe_title}_thumbnail.jpg"
                path = os.path.join(self.video_path, filename)
                
                with open(path, 'wb') as f:
                    f.write(response.content)
                return f"封面已下载: {filename}"
            else:
                return "下载封面失败"
        except Exception as e:
            return f"错误: {e}"
