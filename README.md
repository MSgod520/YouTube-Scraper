# YouTube Downloader (Mobile & Desktop)

![License](https://img.shields.io/github/license/MSgod520/YouTube-Scraper?style=flat-square)
![release](https://img.shields.io/github/v/release/MSgod520/YouTube-Scraper?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Windows-blue?style=flat-square)
![Python](https://img.shields.io/badge/Built%20with-Flet%20%7C%20Python-orange?style=flat-square)

## 📖 Description / 项目简介

**English:**
> A modern, cross-platform YouTube video downloader built with Flet and Python. Supported on **Android** and **Windows**, it features 4K video downloading, high-quality audio extraction (MP3), and a clean Material Design UI.
> 
> *Note: This project is open for modification and redistribution under the MIT License. Please retain the original copyright notice.*

**中文:** 
> 基于 Flet 和 Python 开发的现代化跨平台 YouTube 视频下载器。完美支持 **Android** 和 **Windows** 双端运行，提供 4K 视频下载、音频提取（自动转 MP3）及清爽的 Material Design 界面。
> 
> *注意：本项目遵循 MIT 开源协议，允许自由修改和二次分发，但请务必保留原作者版权声明。*

---

## 🛠 Features / 功能特点

*   📥 **High Quality Video**: Support downloading videos up to 4K/8K resolution. 支持最高 4K/8K 画质下载
*   🎵 **Audio Extraction**: Convert video to high-quality MP3 automatically. 自动提取并转换高音质 MP3
*   🖼️ **Thumbnail**: View and download video thumbnails. 一键获取高清封面
*   ⏸️ **Resume Capability**: Pause and resume downloads at any time. 支持断点续传
*   ⚡ **Single-Thread Stability**: Optimized for stability with auto-rename for duplicate files. 优化的下载线程，自动处理重名文件

---

## 📂 Project Structure / 项目结构

*   **`mobile_app/`**: Flet-based responsive UI for Android. (基于 Flet 的移动端代码)
*   **`main.py`**: CustomTkinter-based UI for Windows Desktop. (基于 CustomTkinter 的桌面端代码)
*   **`downloader_logic.py`**: Core download logic using `yt-dlp`. (基于 yt-dlp 的核心下载逻辑)

---

## 📦 Build & Deployment / 构建指南

We provide GitHub Actions workflows for automated building. 
本项目提供 GitHub Actions 自动化构建脚本

### Android APK
1.  Upload code to GitHub.
2.  Go to **Actions** -> **Build Android APK**.
3.  Click **Run workflow**. 
4.  Download the signed artifact `app-release.apk`.

### iOS IPA (Experimental)
1.  Go to **Actions** -> **Build iOS IPA**.
2.  Click **Run workflow**.
3.  Download `unsigned_app.ipa`.
4.  **Note**: This IPA is unsigned. You must use **AltStore** to sideload it onto your device. 
生成的 IPA 未签名，必须使用 AltStore 自签安装

---

## 🖥 Desktop Usage / 桌面端使用

1.  Install Python 3.10+.
2.  Install dependencies:
    ```bash
    pip install yt-dlp customtkinter flet
    ```
3.  **FFmpeg**: Ensure `ffmpeg.exe` is in the root directory or system PATH.
4.  Run `main.py`.

---

## 📄 License / 开源协议

This project is licensed under the **MIT License**.

> Permission is hereby granted, free of charge, to any person obtaining a copy of this software... to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software... **subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.**

See the [LICENSE](LICENSE) file for details.
