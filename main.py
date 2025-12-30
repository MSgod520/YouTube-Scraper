import customtkinter as ctk
import threading
from downloader_logic import YouTubeDownloader
from tkinter import messagebox
from PIL import Image
import requests
from io import BytesIO

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube 视频下载器")
        self.geometry("700x650") 
        self.grid_columnconfigure(0, weight=1)

        self.downloader = YouTubeDownloader()
        self.video_info = None
        
        # Download State Management
        self.download_tasks = {} # currently active tasks: {'video': thread_obj, 'audio': thread_obj}
        self.cancel_flags = {}   # cancellation flags: {'video': False, 'audio': False}
        self.progress_map = {}   # progress per task: {'video': 0.0, 'audio': 0.0}
        self.is_paused = False     # simple global pause for now, or per task? Let's do global for simplicity first or per task? User asked for "start/pause button". Let's assume global control for the active downloads initiated. 
        # Actually, user wants "Start/Pause" button displayed BELOW.


        # Title
        self.label_title = ctk.CTkLabel(self, text="YouTube 视频下载器", font=("Microsoft YaHei UI", 24, "bold"))
        self.label_title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # URL Entry
        self.entry_url = ctk.CTkEntry(self, placeholder_text="在此粘贴 YouTube链接...", width=500)
        self.entry_url.grid(row=1, column=0, padx=20, pady=10)

        # Check Button
        self.btn_check = ctk.CTkButton(self, text="解析视频", command=self.start_check_thread)
        self.btn_check.grid(row=2, column=0, padx=20, pady=10)

        # Thumbnail Image
        self.label_thumbnail = ctk.CTkLabel(self, text="") # Image holder
        self.label_thumbnail.grid(row=3, column=0, padx=20, pady=10)

        # Video Title
        self.label_video_title = ctk.CTkLabel(self, text="", font=("Microsoft YaHei UI", 14), wraplength=600)
        self.label_video_title.grid(row=4, column=0, padx=20, pady=5)

        # Options Frame
        self.frame_options = ctk.CTkFrame(self)
        self.frame_options.grid(row=5, column=0, padx=20, pady=10)
        
        # Options not visible initially
        self.frame_options.grid_remove()

        # Resolution Dropdown
        self.label_res = ctk.CTkLabel(self.frame_options, text="选择画质:")
        self.label_res.pack(side="left", padx=10)
        
        self.option_resolution = ctk.CTkComboBox(self.frame_options, values=["先解析视频"])
        self.option_resolution.pack(side="left", padx=10)

        # Action Buttons Frame
        self.frame_actions = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_actions.grid(row=6, column=0, padx=20, pady=20)
        
        # Download Thumbnail Button
        self.btn_thumb = ctk.CTkButton(self.frame_actions, text="下载封面", command=self.start_thumb_download_thread, state="disabled", fg_color="gray")
        self.btn_thumb.grid(row=0, column=0, padx=10)

        # Download Video Button
        self.btn_download = ctk.CTkButton(self.frame_actions, text="下载视频", command=self.start_download_video_thread, state="disabled")
        self.btn_download.grid(row=0, column=1, padx=10)

        # Download Audio Button
        self.btn_audio = ctk.CTkButton(self.frame_actions, text="下载音频 (MP3)", command=self.start_download_audio_thread, state="disabled", fg_color="#E0aaff", text_color="black") # Distinct color
        self.btn_audio.grid(row=0, column=2, padx=10)
        
        # Control Button (Pause/Resume) - Initially hidden
        self.btn_control = ctk.CTkButton(self, text="暂停下载", command=self.toggle_pause_resume, state="disabled")
        self.btn_control.grid(row=6, column=0, pady=(5, 0)) # Placed below actions, above progress
        self.btn_control.grid_remove()

        # Progress Bar
        self.progressbar = ctk.CTkProgressBar(self, width=500)
        self.progressbar.grid(row=7, column=0, padx=20, pady=10)
        self.progressbar.set(0)
        self.progressbar.grid_remove() # Default hidden

        # Status Label
        self.label_status = ctk.CTkLabel(self, text="就绪")
        self.label_status.grid(row=8, column=0, padx=20, pady=5)

    def start_check_thread(self):
        url = self.entry_url.get()
        if not url:
            messagebox.showerror("错误", "请输入链接")
            return
        
        self.label_status.configure(text="正在获取视频信息...")
        self.btn_check.configure(state="disabled")
        threading.Thread(target=self.check_video, args=(url,)).start()

    def check_video(self, url):
        info = self.downloader.get_video_info(url)
        if info:
            self.video_info = info
            self.load_thumbnail(info.get('thumbnail'))
            self.update_ui_after_check(info)
        else:
            self.update_status("获取信息失败", error=True)

    def load_thumbnail(self, url):
        if not url: return
        try:
            response = requests.get(url)
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            
            # Resize keeping aspect ratio
            base_width = 320
            w_percent = (base_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
            
            self.photo_image = ctk.CTkImage(light_image=img, dark_image=img, size=(base_width, h_size))
            self.after(0, lambda: self.label_thumbnail.configure(image=self.photo_image, text=""))
        except Exception as e:
            print(f"Thumbnail error: {e}")

    def update_ui_after_check(self, info):
        # Filter formats
        formats = info.get('formats', [])
        resolutions = set()
        self.format_map = {} 

        for f in formats:
            if f.get('vcodec') != 'none' and f.get('height'):
                res_str = f"{f['height']}p - {f['ext']}"
                if res_str not in resolutions:
                    resolutions.add(res_str)
                    self.format_map[res_str] = f['format_id']
        
        sorted_res = sorted(list(resolutions), key=lambda x: int(x.split('p')[0]), reverse=True)
        
        self.after(0, lambda: self._apply_ui_update(info.get('title', 'Unknown Title'), sorted_res))

    def _apply_ui_update(self, title, resolutions):
        self.label_video_title.configure(text=title)
        self.frame_options.grid() # Show options
        if resolutions:
            self.option_resolution.configure(values=resolutions)
            self.option_resolution.set(resolutions[0])
        self.btn_download.configure(state="normal")
        self.btn_audio.configure(state="normal")
        self.btn_thumb.configure(state="normal", fg_color="#2B2B2B") # Enable thumb button
        self.btn_check.configure(state="normal")
        self.label_status.configure(text="视频已找到！请选择画质。")

    def update_status(self, text, error=False):
        self.after(0, lambda: self.label_status.configure(text=text, text_color="#ff5555" if error else "white"))
        if error:
            self.after(0, lambda: self.btn_check.configure(state="normal"))

    def start_download_video_thread(self, is_resume=False):
        url = self.entry_url.get()
        selected_res = self.option_resolution.get()
        format_id = self.format_map.get(selected_res)

        self._prepare_download_ui('video', is_resume)
        # Reset cancel flag
        self.cancel_flags['video'] = False
        t = threading.Thread(target=self.download, args=(url, format_id, False, 'video'))
        self.download_tasks['video'] = t
        t.start()

    def start_download_audio_thread(self, is_resume=False):
        url = self.entry_url.get()
        self._prepare_download_ui('audio', is_resume)
        self.cancel_flags['audio'] = False
        t = threading.Thread(target=self.download, args=(url, None, True, 'audio'))
        self.download_tasks['audio'] = t
        t.start()

    def _prepare_download_ui(self, task_type, is_resume=False):
        if task_type == 'video':
            self.btn_download.configure(state="disabled")
        elif task_type == 'audio':
            self.btn_audio.configure(state="disabled")
        elif task_type == 'thumbnail':
            self.btn_thumb.configure(state="disabled")
            
        self.btn_check.configure(state="disabled")
        
        # Initialize progress for this task only if NOT resuming
        if not is_resume:
            self.progress_map[task_type] = 0.0
            # Also reset generic label if new start
            self.label_status.configure(text=f"开始下载 {task_type}...")
        
        self.progressbar.grid()
        
        # Show control button
        self.btn_control.grid()
        self.btn_control.configure(state="normal", text="暂停下载")
        self.is_paused = False

    def toggle_pause_resume(self):
        if self.is_paused:
            # Resume
            self.is_paused = False
            self.btn_control.configure(text="暂停下载") # Keep default or specific consistent color if needed, but removing dynamic color change
            # Restart tasks that were downloading
            if 'video' in self.progress_map and self.progress_map['video'] < 1.0:
                self.start_download_video_thread(is_resume=True) 
            if 'audio' in self.progress_map and self.progress_map['audio'] < 1.0:
                self.start_download_audio_thread(is_resume=True)
                 
        else:
            # Pause
            self.is_paused = True
            self.btn_control.configure(text="继续下载")
            # Set cancel flags for all active
            for k in self.cancel_flags:
                self.cancel_flags[k] = True

    def download(self, url, format_id, audio_only, task_type):
        def check_cancel():
            return self.cancel_flags.get(task_type, False)

        def progress(percent, eta):
            # Update specific task progress
            self.progress_map[task_type] = percent
            
            # Calculate average progress
            total = sum(self.progress_map.values())
            count = len(self.progress_map)
            avg_percent = total / count if count > 0 else 0
            
            self.after(0, lambda: self.progressbar.set(avg_percent))
            
            # Combine ETAs or status? Just show current one for now or generic
            # Updated to show detailed string if provided
            if "[download]" in eta:
                 self.after(0, lambda: self.label_status.configure(text=f"[{task_type}] {eta}"))
            elif "..." in eta or not any(c.isdigit() for c in eta):
                 self.after(0, lambda: self.label_status.configure(text=f"状态 ({task_type}): {eta}"))
            else:
                 self.after(0, lambda: self.label_status.configure(text=f"下载中... {int(avg_percent*100)}% (剩余时间: {eta})"))

        if audio_only:
            result = self.downloader.download_audio(url, progress, check_cancel)
        else:
            result = self.downloader.download_video(url, format_id, progress, check_cancel)
        
        self.after(0, lambda: self.finish_download(result, task_type))

    def finish_download(self, result, task_type):
        if result == "已暂停":
            self.label_status.configure(text="下载已暂停")
            return # Don't cleanup yet

        # Mark done
        self.progress_map[task_type] = 1.0
        # Re-calc progress to ensure 100% shown if all done
        total = sum(self.progress_map.values())
        count = len(self.progress_map)
        avg_percent = total / count if count > 0 else 0
        self.progressbar.set(avg_percent)

        if avg_percent >= 0.99: # All done
             self.btn_download.configure(state="normal")
             self.btn_audio.configure(state="normal")
             self.btn_check.configure(state="normal")
             self.btn_control.grid_remove() # Hide pause button
             self.progress_map.clear() # Reset
             self.cancel_flags.clear()
             messagebox.showinfo("下载完成", "所有任务已完成")
        
        self.label_status.configure(text=f"{task_type}: {result}")

    def start_thumb_download_thread(self):
        url = self.entry_url.get()
        self._prepare_download_ui('thumbnail')
        threading.Thread(target=self.download_thumb, args=(url,)).start()

    def download_thumb(self, url):
        self.after(0, lambda: self.label_status.configure(text="正在下载封面..."))
        # Mock progress for UI consistency
        self.progress_map['thumbnail'] = 0.1
        self._update_progress_bar_safe()
        
        result = self.downloader.download_thumbnail(url)
        self.after(0, lambda: self.finish_download(result, 'thumbnail'))

    # Removed finish_thumb as it is now integrated into finish_download structure
    
    def _update_progress_bar_safe(self):
        total = sum(self.progress_map.values())
        count = len(self.progress_map)
        avg_percent = total / count if count > 0 else 0
        self.after(0, lambda: self.progressbar.set(avg_percent))





if __name__ == "__main__":
    app = App()
    app.mainloop()
