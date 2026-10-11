import subprocess
import sys
import json

# Set the channel handle you want to scrape
CHANNEL_HANDLE = "@swmehreenlive"
CHANNEL_URL = f"https://www.youtube.com/{CHANNEL_HANDLE}/streams"
OUTPUT_M3U = "live_playlist.m3u"

def get_live_stream_info(url):
    try:
        # Command optimized for cloud runners (GitHub Actions / Linux / Windows)
        command = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android",
            "--dump-json",
            "--playlist-end", "10",
            url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        
        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                
                is_live = data.get("is_live") is True or data.get("live_status") == "is_live"
                stream_url = data.get("url", "")
                title = data.get("title", "Live Stream")
                thumbnail = data.get("thumbnail", "")
                
                # Verify active live stream (exclude recorded videoplayback files)
                if stream_url and "videoplayback" not in stream_url:
                    return stream_url, title, thumbnail
                elif is_live and stream_url:
                    return stream_url, title, thumbnail
            except json.JSONDecodeError:
                continue

    except Exception as e:
        print(f"[-] Extraction error: {e}")
        
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
    print(f"[*] Scraper running for {CHANNEL_HANDLE}...")
    stream_url, title, thumbnail = get_live_stream_info(CHANNEL_URL)
    
    if stream_url:
        update_m3u_file(stream_url, title, thumbnail)
    else:
        print("[-] No active live stream found.")
        sys.exit(1)
        
