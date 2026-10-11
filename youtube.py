import subprocess
import sys
import json

# Search query via yt-dlp search index (bypasses direct channel IP blocks)
CHANNEL_HANDLE = "@swmehreenlive"
SEARCH_QUERY = f"ytsearch5:{CHANNEL_HANDLE} live"
OUTPUT_M3U = "live_playlist.m3u"

def get_live_stream_info(search_query):
    try:
        # Using ytsearch with android client which works reliably on cloud servers
        command = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android",
            "--dump-json",
            search_query
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
                
                # CRITICAL RULE: Must have a URL and MUST NOT contain "videoplayback"
                if stream_url and "videoplayback" not in stream_url:
                    return stream_url, title, thumbnail
            except json.JSONDecodeError:
                continue

    except Exception as e:
        print(f"[-] Search extraction error: {e}")
        
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
    print(f"[*] Running search scraper for {CHANNEL_HANDLE}...")
    stream_url, title, thumbnail = get_live_stream_info(SEARCH_QUERY)
    
    if stream_url:
        update_m3u_file(stream_url, title, thumbnail)
    else:
        print("[-] Channel is currently offline or no active live stream found.")
        sys.exit(1)
        
