import subprocess
import sys
import json
import os

CHANNEL_HANDLE = "@ffesportsbr"
SEARCH_QUERY = f"ytsearch3:{CHANNEL_HANDLE} live"
OUTPUT_M3U = "live_playlist.m3u"
COOKIES_PATH = os.path.expanduser("~/.cache/yt-dlp/youtube/cookies.txt")

def get_live_stream():
    print(f"[*] Fetching live stream using authenticated session...")
    try:
        command = [
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "--extractor-args", "youtube:player_client=android,web",
            "--dump-json",
            SEARCH_QUERY
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        
        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                stream_url = data.get("url", "")
                title = data.get("title", "Live Stream")
                thumbnail = data.get("thumbnail", "")
                
                if stream_url and "videoplayback" not in stream_url:
                    return stream_url, title, thumbnail
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print(f"[-] Error: {e}")
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
    print(f"[+] SUCCESS! M3U updated with active stream: '{safe_title}'")
    return True

if __name__ == "__main__":
    stream_url, title, thumbnail = get_live_stream()
    if stream_url:
        update_m3u_file(stream_url, title, thumbnail)
        sys.exit(0)
    else:
        print("[-] Channel is offline.")
        sys.exit(1)
