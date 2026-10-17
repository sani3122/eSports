import subprocess
import sys
import json

PAGE_URL = "https://www.facebook.com/ffesportsbdofficial/videos"
OUTPUT_M3U = "live_playlist.m3u"

def get_active_facebook_lives():
    print(f"[*] Fetching active lives from {PAGE_URL}...")
    active_streams = []
    
    try:
        # yt-dlp দিয়ে ফেসবুক পেজের ভিডিওগুলো JSON ফরম্যাটে ডাম্প করা
        command = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            PAGE_URL
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        
        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                video_url = data.get("url") or f"https://www.facebook.com/watch/?v={data.get('id')}"
                title = data.get("title", "Facebook Live Stream")
                is_live = data.get("is_live")
                
                # যদি সরাসরি is_live ট্যাগ পাওয়া যায় অথবা টাইটেলে/স্ট্যাটাসে লাইভ বোঝায়
                if is_live or data.get("live_status") == "is_live":
                    print(f"[+] Found Live Candidate: {title}")
                    
                    # লাইভ ভিডিওর ডিরেক্ট স্ট্রিম এমথ্রিউইট লিংক বের করা
                    sub_cmd = ["yt-dlp", "--print", "url", "--print", "title", video_url]
                    sub_res = subprocess.run(sub_cmd, capture_output=True, text=True, timeout=30)
                    
                    if sub_res.returncode == 0:
                        out_lines = [l.strip() for l in sub_res.stdout.strip().split("\n") if l.strip()]
                        if len(out_lines) >= 2:
                            stream_url = out_lines[0]
                            stream_title = out_lines[1]
                            if stream_url and "m3u8" in stream_url or "akamaized" in stream_url or "fbcdn" in stream_url:
                                active_streams.append((stream_title, stream_url))
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print(f"[-] Error fetching Facebook streams: {e}")
        
    return active_streams

def update_m3u_file(streams):
    if not streams:
        print("[-] No active live streams found on the Facebook page right now.")
        # আপনি চাইলে পেজ অফলাইন থাকলে ফাঁকা বা আগের ফাইল রাখতে পারেন
        return False
        
    m3u_content = "#EXTM3U\n"
    for title, url in streams:
        safe_title = title.replace('"', '')
        m3u_content += f'#EXTINF:-1 tvg-id="1" tvg-name="{safe_title}" group-title="Facebook Live",{safe_title}\n'
        m3u_content += f"{url}\n"
        
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"[+] SUCCESS! M3U updated with {len(streams)} active live stream(s).")
    return True

if __name__ == "__main__":
    streams = get_active_facebook_lives()
    if update_m3u_file(streams):
        sys.exit(0)
    else:
        sys.exit(1)
        
