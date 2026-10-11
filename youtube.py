import subprocess
import sys
import json
from playwright.sync_api import sync_playwright

CHANNEL_HANDLE = "@ffesportsbr"
CHANNEL_LIVE_URL = f"https://www.youtube.com/{CHANNEL_HANDLE}/live"
OUTPUT_M3U = "live_playlist.m3u"

def get_live_stream_via_browser():
    print(f"[*] Launching Headless Chromium Browser...")
    with sync_playwright() as p:
        # Launch Chromium browser just like a real PC/phone browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        target_video_url = None
        
        # Intercept network requests or listen for the live page URL
        def handle_request(route, request):
            nonlocal target_video_url
            if "/watch?v=" in request.url and not target_video_url:
                # Catch the live watch URL when the browser loads it
                clean_url = request.url.split("&")[0]
                if "watch?v=" in clean_url:
                    target_video_url = clean_url
            route.continue_()

        page.route("**/*", handle_request)
        
        try:
            print(f"[*] Navigating to {CHANNEL_LIVE_URL}...")
            page.goto(CHANNEL_LIVE_URL, timeout=60000)
            page.wait_for_timeout(5000) # Wait for page scripts to execute
            
            # If network intercept didn't catch it, grab the current URL of the page
            current_url = page.url
            if "watch?v=" in current_url:
                target_video_url = current_url
                
        except Exception as e:
            print(f"[-] Browser navigation error: {e}")
            
        browser.close()
        return target_video_url

def extract_stream_data(video_url):
    if not video_url:
        return None, None, None
        
    print(f"[*] Extracting stream info from: {video_url}")
    try:
        command = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android,web",
            "--print", "url",
            "--print", "title",
            "--print", "thumbnail",
            video_url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        
        if len(lines) >= 3:
            stream_url = lines[0]
            title = lines[1]
            thumbnail = lines[2]
            
            if stream_url and "videoplayback" not in stream_url:
                return stream_url, title, thumbnail
    except Exception as e:
        print(f"[-] yt-dlp extraction failed: {e}")
        
    return None, None, None

def update_m3u_file(stream_url, title, thumbnail):
    if not stream_url:
        print("[-] No active live stream found.")
        return False
        
    safe_title = title.replace('"', '')
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="1" tvg-name="{safe_title}" tvg-logo="{thumbnail}" group-title="YouTube Live",{safe_title}
{stream_url}
"""
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
        
    print(f"[+] SUCCESS! M3U updated with: '{safe_title}'")
    return True

if __name__ == "__main__":
    video_url = get_live_stream_via_browser()
    if video_url:
        stream_url, title, thumbnail = extract_stream_data(video_url)
        if stream_url:
            update_m3u_file(stream_url, title, thumbnail)
            sys.exit(0)
            
    print("[-] Channel is offline or live stream could not be loaded via browser.")
    sys.exit(1)
