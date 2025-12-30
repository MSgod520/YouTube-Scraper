from downloader_logic import YouTubeDownloader
import os

def test_logic():
    print("Testing YouTubeDownloader Logic...")
    dl = YouTubeDownloader()
    
    # Test Info Fetching (using a very short/dummy video if possible, or a standard test video)
    # Using a reliable test video (e.g., from YouTube creators channel or similar)
    # "Me at the zoo" is a classic test: https://www.youtube.com/watch?v=jNQXAC9IVRw
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw" 
    
    print(f"Fetching info for: {test_url}")
    info = dl.get_video_info(test_url)
    
    if info:
        print(f"Successfully fetched info: {info.get('title')}")
    else:
        print("Failed to fetch info.")
        return

    # Test Download (Audio Only to be quick)
    print("Testing Audio Download...")
    result = dl.download_audio(test_url, progress_callback=lambda p, e: print(f"Progress: {p:.2f}, ETA: {e}"))
    print(f"Download Result: {result}")
    
    if "Complete" in result:
        print("Verification Successful!")
    else:
        print("Verification Failed.")

if __name__ == "__main__":
    test_logic()
