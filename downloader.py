import yt_dlp

async def extract_instagram_video(url: str) -> str | None:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'cookies': 'cookies.txt',  # 👈 важливо
        'format': 'best[ext=mp4]/best',
        'skip_download': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("url")
    except Exception as e:
        print(f"Помилка: {e}")
        return None
