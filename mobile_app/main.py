import flet as ft
import threading
import re
from downloader_logic import YouTubeDownloader

def main(page: ft.Page):
    page.title = "YouTube 视频下载器"
    page.theme_mode = "dark"
    page.scroll = "auto"
    page.window_width = 400
    page.window_height = 800

    # 逻辑实例
    downloader = YouTubeDownloader()
    video_info = {}
    format_map = {}
    
    # 状态
    download_tasks = {}
    cancel_flags = {}
    progress_map = {}
    is_paused = False

    # UI 组件
    title_label = ft.Text("YouTube 视频下载器", size=24, weight="bold")
    
    url_input = ft.TextField(label="在此粘贴 YouTube 链接...", width=None, expand=True)
    
    check_btn = ft.ElevatedButton("解析视频", icon="search")
    
    thumb_img = ft.Image(src="", width=320, height=180, fit="contain", visible=False)
    video_title_label = ft.Text("", size=16, weight="bold")
    
    res_dropdown = ft.Dropdown(label="选择画质", options=[], width=200, visible=False)
    
    # 动作按钮
    btn_thumb = ft.ElevatedButton("下载封面", icon="image", disabled=True)
    btn_download = ft.ElevatedButton("下载视频", icon="video_file", disabled=True)
    btn_audio = ft.ElevatedButton("下载音频 (MP3)", icon="audio_file", disabled=True, color="purple")
    
    actions_row = ft.Row([btn_thumb, btn_download, btn_audio], wrap=True, alignment="center", visible=False)
    
    # 控制按钮
    btn_control = ft.ElevatedButton("暂停下载", icon="pause", visible=False)
    
    progress_bar = ft.ProgressBar(width=None, value=0, visible=False)
    status_label = ft.Text("就绪")

    # 布局
    page.add(
        ft.Column(
            [
                ft.Container(title_label, alignment=ft.alignment.Alignment(0, 0), padding=20),
                ft.Row([url_input], alignment="center"),
                ft.Container(check_btn, alignment=ft.alignment.Alignment(0, 0), padding=10),
                ft.Container(thumb_img, alignment=ft.alignment.Alignment(0, 0)),
                ft.Container(video_title_label, alignment=ft.alignment.Alignment(0, 0), padding=5),
                ft.Container(res_dropdown, alignment=ft.alignment.Alignment(0, 0), padding=5),
                ft.Container(actions_row, alignment=ft.alignment.Alignment(0, 0), padding=10),
                ft.Container(btn_control, alignment=ft.alignment.Alignment(0, 0), padding=5),
                ft.Container(progress_bar, padding=20),
                ft.Container(status_label, alignment=ft.alignment.Alignment(0, 0)),
            ],
            horizontal_alignment="center",
        )
    )

    # 逻辑功能
    def update_ui_safe():
        page.update()

    def check_video(e):
        url = url_input.value
        if not url:
            status_label.value = "请输入链接"
            status_label.color = "red"
            page.update()
            return

        status_label.value = "正在获取视频信息..."
        status_label.color = "white"
        check_btn.disabled = True
        page.update()

        def task():
            nonlocal video_info
            info = downloader.get_video_info(url)
            if info:
                video_info = info
                # 更新 UI
                thumb_img.src = info.get('thumbnail')
                thumb_img.visible = True
                
                video_title_label.value = info.get('title', 'Unknown')
                
                # 格式处理
                formats = info.get('formats', [])
                resolutions = set()
                format_map.clear()
                
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('height'):
                        res_str = f"{f['height']}p - {f['ext']}"
                        if res_str not in resolutions:
                            resolutions.add(res_str)
                            format_map[res_str] = f['format_id']
                
                sorted_res = sorted(list(resolutions), key=lambda x: int(x.split('p')[0]), reverse=True)
                res_dropdown.options = [ft.dropdown.Option(r) for r in sorted_res]
                if sorted_res:
                    res_dropdown.value = sorted_res[0]
                
                res_dropdown.visible = True
                actions_row.visible = True
                btn_thumb.disabled = False
                btn_download.disabled = False
                btn_audio.disabled = False
                
                status_label.value = "视频已找到！"
            else:
                status_label.value = "获取信息失败"
                status_label.color = "red"
            
            check_btn.disabled = False
            update_ui_safe()

        threading.Thread(target=task).start()

    check_btn.on_click = check_video

    # 下载逻辑
    def prepare_download_ui(task_type, is_resume=False):
        if task_type == 'video':
            btn_download.disabled = True
        elif task_type == 'audio':
            btn_audio.disabled = True
        elif task_type == 'thumbnail':
            btn_thumb.disabled = True
            
        check_btn.disabled = True
        
        if not is_resume:
            progress_map[task_type] = 0.0
            status_label.value = f"开始下载 {task_type}..."
            
        progress_bar.visible = True
        btn_control.visible = True
        btn_control.text = "暂停下载"
        btn_control.icon = "pause"
        nonlocal is_paused
        is_paused = False
        update_ui_safe()

    def update_progress_bar():
        total = sum(progress_map.values())
        count = len(progress_map)
        avg_percent = total / count if count > 0 else 0
        progress_bar.value = avg_percent
        update_ui_safe()

    def download_wrapper(url, format_id, audio_only, task_type):
        def check_cancel():
            return cancel_flags.get(task_type, False)

        def progress(percent, status_msg):
            progress_map[task_type] = percent
            update_progress_bar()
            
            # 状态更新
            if "[download]" in status_msg:
                 # 去除 ANSI 字符
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                clean_msg = ansi_escape.sub('', status_msg)
                status_label.value = f"{clean_msg}"
                update_ui_safe()

        if audio_only:
            result = downloader.download_audio(url, progress, check_cancel)
        else:
            result = downloader.download_video(url, format_id, progress, check_cancel)
        
        finish_download(result, task_type)

    def finish_download(result, task_type):
        if result == "已暂停":
            status_label.value = "下载已暂停"
            update_ui_safe()
            return

        progress_map[task_type] = 1.0
        update_progress_bar()
        
        # 检查是否全部完成
        if all(p >= 0.99 for p in progress_map.values()):
            btn_download.disabled = False
            btn_audio.disabled = False
            btn_thumb.disabled = False
            check_btn.disabled = False
            btn_control.visible = False
            progress_map.clear()
            cancel_flags.clear()
            status_label.value = "所有任务已完成"
            
            page.snack_bar = ft.SnackBar(ft.Text(f"下载完成: {result}"))
            page.snack_bar.open = True
        else:
             status_label.value = f"{task_type}: {result}"
        
        update_ui_safe()

    def start_download_video(e=None, is_resume=False):
        url = url_input.value
        res = res_dropdown.value
        fid = format_map.get(res)
        
        prepare_download_ui('video', is_resume)
        cancel_flags['video'] = False
        t = threading.Thread(target=download_wrapper, args=(url, fid, False, 'video'))
        download_tasks['video'] = t
        t.start()

    def start_download_audio(e=None, is_resume=False):
        url = url_input.value
        prepare_download_ui('audio', is_resume)
        cancel_flags['audio'] = False
        t = threading.Thread(target=download_wrapper, args=(url, None, True, 'audio'))
        download_tasks['audio'] = t
        t.start()
        
    def start_download_thumb(e=None):
        url = url_input.value
        prepare_download_ui('thumbnail')
        
        def task():
            progress_map['thumbnail'] = 0.5
            update_progress_bar()
            res = downloader.download_thumbnail(url)
            finish_download(res, 'thumbnail')
            
        threading.Thread(target=task).start()

    def toggle_pause(e):
        nonlocal is_paused
        if is_paused:
            # 恢复
            is_paused = False
            btn_control.text = "暂停下载"
            btn_control.icon = "pause"
            if 'video' in progress_map and progress_map['video'] < 1.0:
                start_download_video(is_resume=True)
            if 'audio' in progress_map and progress_map['audio'] < 1.0:
                start_download_audio(is_resume=True)
        else:
            # 暂停
            is_paused = True
            btn_control.text = "继续下载"
            btn_control.icon = "play_arrow"
            for k in cancel_flags:
                cancel_flags[k] = True
        update_ui_safe()

    btn_download.on_click = start_download_video
    btn_audio.on_click = start_download_audio
    btn_thumb.on_click = start_download_thumb
    btn_control.on_click = toggle_pause

ft.app(target=main)
