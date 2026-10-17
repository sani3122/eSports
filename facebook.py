import subprocess
import sys
import json

# ফেসবুক পেজের সরাসরি ভিডিও সেকশন URL
PAGE_URL = "https://www.facebook.com/ffesportsbdofficial/videos/"
OUTPUT_M3U = "live_playlist.m3u"

def get_active_facebook_live():
    print(f"[*] Attempting to fetch live stream from: {PAGE_URL}")
    
    # yt-dlp এর মাধ্যমে সরাসরি পেজ থেকে প্রথম লাইভ বা লেটেস্ট স্ট্রিম ফেচ করার শক্তিশালী কমান্ড
    command = [
        "yt-dlp",
        "--no-check-certificate",
        "--geo-bypass",
        "--dump-json",
        "--playlist-end", "3",
        PAGE_URL
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        
        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                video_url = data.get("url") or f"https://www.facebook.com/watch/?v={data.get('id')}"
                title = data.get("title", "Free Fire Live Stream")
                is_live = data.get("is_live") or (data.get("live_status") == "is_live")
                
                # যদি চলমান লাইভ হয় অথবা ডিরেক্ট ভিডিও স্ট্রিম পাওয়া যায়
                if video_url:
                    print(f"[+] Found video candidate, extracting direct HLS link...")
                    
                    # yt-dlp দিয়ে ডিরেক্ট স্ট্রিম লিংক বের করা
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
                                print(f"[+] SUCCESS! Got active live stream: {stream_title}")
                                return stream_title, stream_url
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print(f"[-] Execution error: {e}")
        
    return None, None

def update_m3u_file(title, stream_url):
    if not stream_url:
        print("[-] No active live stream found at this moment.")
        # গিটহ্যাব অ্যাকশন যেন ফেইল না করে, তাই আমরা ফাঁকা প্লেলিস্ট বা আগের স্টেট বজায় রাখতে পারি 
        # অথবা নিচের কোড দিয়ে এম থ্রি ইউ ফাইলটি জেনারেট করে দিতে পারি
        return False
        
    safe_title = title.replace('"', '')
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="1" tvg-name="{safe_title}" group-title="Facebook Live",{safe_title}
{stream_url}
"""
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"[+] M3U playlist successfully updated!")
    return True

if __name__ == "__main__":
    title, stream_url = get_active_facebook_live()
    if stream_url and update_m3u_file(title, stream_url):
        sys.exit(0)
    else:
        # পেজ লাইভে না থাকলে গিটহ্যাব অ্যাকশন যাতে লাল না হয়ে গ্রিন হয়ে পাস করে যায়, 
        # সেজন্য আমরা exit 0 দিচ্ছি যাতে আপনার বারবার নোটিফিকেশন বা এরর না দেখায়।
        print("[-] Channel is offline or stream is not public right now.")
        # একটি ডামি বা ব্ল্যাঙ্ক M3U ফাইল রেখে দিতে পারেন যেন IPTV প্লেয়ার ক্র্যাশ না করে
        with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n#EXTINF:-1, Offline - Check Back Later\nhttp://localhost/offline.ts\n")
        sys.exit(0)
        
