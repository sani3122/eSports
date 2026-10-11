import subprocess
import sys
import json

# Target channel URL directly
CHANNEL_HANDLE = "@swmehreenlive"
CHANNEL_URL = f"https://www.youtube.com/{CHANNEL_HANDLE}/streams"
OUTPUT_M3U = "live_playlist.m3u"

def get_live_stream_info(url):
    try:
        # Using web + android client arguments with flat-playlist to bypass cloud blocks
        command = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=web,android",
            "--dump-json",
            "--playlist-end", "5",
            url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        
        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                
                # Check if it's live or active
                live_status = data.get("live_status")
                is_live = data.get("is_live")
                stream_url = data.get("url", "")
                title = data.get("title", "Live Stream")
                thumbnail = data.get("thumbnail", "")
                
                # If we get a direct playable URL that isn't a recorded video playback
                if stream_url and "videoplayback" not in stream_url:
                    return stream_url, title, thumbnail
                
                # Fallback: If it lists a video ID from the streams page, grab its direct stream URL
                video_id = data.get("id")
                if video_id and (live_status == "is_live" or is_live):
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    sub_cmd = [
                        "yt-dlp",
                        "--extractor-args", "youtube:player_client=web,android",
                        "--print", "url",
                        "--print", "title",
                        "--print", "thumbnail",
                        video_url
                    ]
                    sub_res = subprocess.run(sub_cmd, capture_output=True, text=True)
                    if sub_res.returncode == 0:
                        out_lines = sub_res.stdout.strip().split("\n")
                        if len(out_lines) >= 3:
                            s_url = out_lines[0].strip()
                            s_title = out_lines[1].strip()
                            s_thumb = out_lines[2].strip()
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
        
    print(f"[+] SUCCESS! Updated {OUTPUT_M3U} with active stream: '{safe_title}'")
    return True

if __name__ == "__main__":
    print(f"[*] Scanning channel streams for {CHANNEL_HANDLE}...")
    stream_url, title, thumbnail = get_live_stream_info(CHANNEL_URL)
    
    if stream_url:
        update_m3u_file(stream_url, title, thumbnail)
    else:
        print("[-] Channel is currently offline.")
        sys.exit(1)
        
