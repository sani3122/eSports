import subprocess
import sys
import json
import urllib.request
import xml.etree.ElementTree as ET

# Target channel handle and its public RSS feed URL (bypasses all cloud/IP blocks)
CHANNEL_HANDLE = "@swmehreenlive"
CHANNEL_ID_OVERRIDE = None  # Will be resolved automatically if needed

def get_channel_feed_url(handle):
    # Fetch the channel page HTML to extract the channel ID safely
    try:
        url = f"https://www.youtube.com/{handle}"
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode("utf-8")
            # Look for channel_id inside meta tags
            for line in html.split("\n"):
                if "channel_id" in line or "externalId" in line:
                    # Extract ID using simple string partitioning
                    if '"channel_id":"' in line:
                        cid = line.split('"channel_id":"')[1].split('"')[0]
                        return f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
    except Exception as e:
        print(f"[-] Could not resolve channel feed: {e}")
    return None

def get_active_live_stream():
    # 1. Get RSS XML feed for the channel
    feed_url = get_channel_feed_url(CHANNEL_HANDLE)
    if not feed_url:
        print("[-] Failed to get channel RSS feed.")
        return None, None, None
        
    try:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        # Namespace used in YouTube RSS feeds
        ns = {"yt": "http://www.youtube.com/xml/schemas/2005", "atom": "http://www.w3.org/2005/Atom"}
        
        # Check recent videos in the feed
        for entry in root.findall("atom:entry", ns):
            video_id = entry.find("yt:videoId", ns).text
            title = entry.find("atom:title", ns).text
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            print(f"[*] Checking recent feed video: {title} ({video_url})")
            
            # Use yt-dlp to inspect if this specific video is currently live
            command = [
                "yt-dlp",
                "--extractor-args", "youtube:player_client=android",
                "--dump-json",
                video_url
            ]
            
            res = subprocess.run(command, capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip().split("\n")[0])
                stream_url = data.get("url", "")
                is_live = data.get("is_live") or data.get("live_status") == "is_live"
                thumbnail = data.get("thumbnail", "")
                
                # Verify it is genuinely live and NOT a videoplayback archive
                if is_live and stream_url and "videoplayback" not in stream_url:
                    return stream_url, title, thumbnail
                    
    except Exception as e:
        print(f"[-] Error parsing XML feed: {e}")
        
    return None, None, None

def update_m3u_file(stream_url, title, thumbnail):
    OUTPUT_M3U = "live_playlist.m3u"
    if not stream_url:
        print("[-] No active live stream found via RSS feed.")
        return False
        
    safe_title = title.replace('"', '')
    
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="1" tvg-name="{safe_title}" tvg-logo="{thumbnail}" group-title="YouTube Live",{safe_title}
{stream_url}
"""
    
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
        
    print(f"[+] FINAL BOSS SUCCESS! M3U updated with active stream: '{safe_title}'")
    return True

if __name__ == "__main__":
    print(f"[*] Querying YouTube RSS feed for {CHANNEL_HANDLE}...")
    stream_url, title, thumbnail = get_active_live_stream()
    
    if stream_url:
        update_m3u_file(stream_url, title, thumbnail)
    else:
        print("[-] Channel is offline. No update made.")
        sys.exit(1)
        
