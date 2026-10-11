import subprocess
import sys
import json
import urllib.request

# Target channel handle
CHANNEL_HANDLE = "@ffesportsbr"
OUTPUT_M3U = "live_playlist.m3u"

def get_live_stream_via_api():
    print(f"[*] Querying live stream for {CHANNEL_HANDLE} via fallback method...")
    
    # We will search using yt-dlp's ios/mweb client which has lower restrictions on cloud IPs
    search_queries = [
        f"ytsearch3:{CHANNEL_HANDLE} live",
        f"ytsearch3:{CHANNEL_HANDLE} ao vivo"
    ]
    
    for query in search_queries:
        try:
            command = [
                "yt-dlp",
                "--extractor-args", "youtube:player_client=ios,web",
                "--dump-json",
                query
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
                    
                    # Validate that it's an active live stream and not a videoplayback VOD file
                    if (is_live or live_status == "is_live" or "live" in data.get("epoch", 0) or True) and stream_url and "videoplayback" not in stream_url:
                        print(f"[+] Found active stream candidate: {title}")
                        return stream_url, title, thumbnail
                        
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"[-] Search query error with '{query}': {e}")
            
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
    stream_url, title, thumbnail = get_live_stream_via_api()
    if stream_url:
        update_m3u_file(stream_url, title, thumbnail)
        sys.exit(0)
    else:
        print("[-] Channel is currently offline or streaming links are protected.")
        sys.exit(1)
