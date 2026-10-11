import urllib.request
import json
import sys
import subprocess

# Target channel handle
CHANNEL_HANDLE = "@ffesportsbr"
OUTPUT_M3U = "live_playlist.m3u"

# Public, reliable Invidious API instances
INVIDIOUS_INSTANCES = [
    "https://invidious.privacyredirect.com",
    "https://vid.puffyan.us",
    "https://inv.nadeko.net",
    "https://invidious.perennialte.ch"
]

def get_live_stream_via_invidious():
    print(f"[*] Resolving channel ID for {CHANNEL_HANDLE}...")
    
    # 1. Clean the channel handle
    clean_handle = CHANNEL_HANDLE.replace("@", "")
    
    channel_id = None
    # Try fetching channel info from Invidious instances
    for instance in INVIDIOUS_INSTANCES:
        try:
            api_url = f"{instance}/api/v1/channels/search/{clean_handle}"
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data and len(data) > 0:
                    channel_id = data[0].get("authorId")
                    if channel_id:
                        print(f"[+] Found channel ID: {channel_id}")
                        break
        except Exception as e:
            continue
            
    if not channel_id:
        print("[-] Could not resolve channel ID from Invidious instances.")
        return None, None, None

    # 2. Fetch active live streams from the channel using Invidious API
    for instance in INVIDIOUS_INSTANCES:
        try:
            live_api_url = f"{instance}/api/v1/channels/{channel_id}/live"
            req = urllib.request.Request(
                live_api_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                live_data = json.loads(response.read().decode("utf-8"))
                
                # Invidious returns live videos if active
                if live_data and isinstance(live_data, list) and len(live_data) > 0:
                    video_id = live_data[0].get("videoId")
                    title = live_data[0].get("title", "Live Stream")
                    
                    if video_id:
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        print(f"[+] Found live video ID: {video_id} -> Fetching stream manifest...")
                        
                        # Use yt-dlp to grab the direct HLS stream link from the video ID
                        cmd = [
                            "yt-dlp",
                            "--extractor-args", "youtube:player_client=android,web",
                            "--print", "url",
                            "--print", "thumbnail",
                            video_url
                        ]
                        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                        if res.returncode == 0:
                            lines = [l.strip() for l in res.stdout.strip().split("\n") if l.strip()]
                            if len(lines) >= 2:
                                stream_url = lines[0]
                                thumbnail = lines[1]
                                if stream_url and "videoplayback" not in stream_url:
                                    return stream_url, title, thumbnail
        except Exception as e:
            continue
            
    return None, None, None

def update_m3u_file(stream_url, title, thumbnail):
    if not stream_url:
        print("[-] No active live stream found via Invidious proxy.")
        return False
        
    safe_title = title.replace('"', '')
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="1" tvg-name="{safe_title}" tvg-logo="{thumbnail}" group-title="YouTube Live",{safe_title}
{stream_url}
"""
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"[+] SUCCESS! M3U updated with stream: '{safe_title}'")
    return True

if __name__ == "__main__":
    stream_url, title, thumbnail = get_live_stream_via_invidious()
    if stream_url:
        update_m3u_file(stream_url, title, thumbnail)
        sys.exit(0)
    else:
        print("[-] Channel is currently offline or no live stream detected.")
        sys.exit(1)
