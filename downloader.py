import yt_dlp
import tempfile
import os

async def extract_instagram_video(url: str) -> str | None:
    """
    Завантажує відео з Instagram через yt-dlp та повертає шлях до тимчасового файлу
    """
    temp_dir = tempfile.gettempdir()
    output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "mp4",
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            return filename
    except Exception as e:
        print(f"⚠️ yt-dlp помилка: {e}")
        return None
