import subprocess
import sys
import json
import os

CHANNEL_URL = "https://www.youtube.com/@ffesportsbr/streams"
OUTPUT_M3U = "live_playlist.m3u"
COOKIES_PATH = os.path.expanduser("~/.cache/yt-dlp/youtube/cookies.txt")

def get_live_stream():
    print(f"[*] Fetching live stream directly from channel streams tab...")
    try:
        # Using authenticated cookies directly on the channel streams tab
        command = [
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "--extractor-args", "youtube:player_client=android,web",
            "--dump-json",
            "--playlist-end", "5",
            CHANNEL_URL
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
                is_live = data.get("is_live")
                live_status = data.get("live_status")
                
                # Check if it's currently live or active
                if (is_live or live_status == "is_live") and stream_url and "videoplayback" not in stream_url:
                    return stream_url, title, thumbnail
                    
                # Fallback: If it's a video ID from the playlist, extract its direct stream URL
                video_id = data.get("id")
                if video_id and (is_live or live_status == "is_live"):
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    sub_cmd = [
                        "yt-dlp",
                        "--cookies", COOKIES_PATH,
                        "--extractor-args", "youtube:player_client=android,web",
                        "--print", "url",
                        "--print", "title",
                        "--print", "thumbnail",
                        video_url
                    ]
                    sub_res = subprocess.run(sub_cmd, capture_output=True, text=True)
                    if sub_res.returncode == 0:
                        out_lines = [l.strip() for l in sub_res.stdout.strip().split("\n") if l.strip()]
                        if len(out_lines) >= 3:
                            s_url = out_lines[0]
                            s_title = out_lines[1]
                            s_thumb = out_lines[2]
                            if s_url and "videoplayback" not in s_url:
                                return s_url, s_title, s_thumb
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
        print("[-] Channel is offline or stream is protected.")
        sys.exit(1)
