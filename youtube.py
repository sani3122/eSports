import subprocess
import sys
import json
import urllib.request
import xml.etree.ElementTree as ET

CHANNEL_HANDLE = "@xteesproduction"
OUTPUT_M3U = "live_playlist.m3u"

def get_channel_feed_url(handle):
    try:
        url = f"https://www.youtube.com/{handle}"
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode("utf-8")
            for line in html.split("\n"):
                if '"channel_id":"' in line:
                    cid = line.split('"channel_id":"')[1].split('"')[0]
                    return f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
    except Exception as e:
        print(f"[-] RSS Feed Error: {e}")
    return None

def get_active_live_stream():
    feed_url = get_channel_feed_url(CHANNEL_HANDLE)
    if not feed_url:
        return None, None, None
        
    try:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        ns = {"yt": "http://www.youtube.com/xml/schemas/2005", "atom": "http://www.w3.org/2005/Atom"}
        
        for entry in root.findall("atom:entry", ns):
            video_id = entry.find("yt:videoId", ns).text
            title = entry.find("atom:title", ns).text
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Check if this video is currently live using yt-dlp
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
                
                if is_live and stream_url and "videoplayback" not in stream_url:
                    return stream_url, title, thumbnail
    except Exception as e:
        print(f"[-] Parse Error: {e}")
        
    return None, None, None

def update_m3u_file(stream_url, title, thumbnail):
    if not stream_url:
        return False
    safe_title = title.replace('"', '')
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="1" tvg-name="{safe_title}" tvg-logo="{thumbnail}" group-title="YouTube Live",{safe_title}
{stream_url}
"""
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    return True

if __name__ == "__main__":
    stream_url, title, thumbnail = get_active_live_stream()
    if stream_url:
        update_m3u_file(stream_url, title, thumbnail)
        sys.exit(0)
    sys.exit(1)
    
