import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN, CHANNELS
from pytube import YouTube
import instaloader

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь ссылку на TikTok, Instagram или YouTube, и я скачаю видео для тебя после подписки на каналы."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    # Проверка подписки на каналы
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user.id)
            if member.status in ["left", "kicked"]:
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(f"Подписаться на {channel}", url=f"https://t.me/{channel[1:]}")]]
                )
                await update.message.reply_text("Сначала подпишись на наши каналы", reply_markup=keyboard)
                return
        except:
            await update.message.reply_text(f"Ошибка проверки канала {channel}")
            return

    link = update.message.text

    # TikTok через сторонний сервис
    if "tiktok.com" in link:
        try:
            r = requests.get(f"https://api.tikmate.app/api/lookup?url={link}")
            data = r.json()
            video_url = data['video']['url']  # без водяного знака
            video_bytes = requests.get(video_url).content
            await update.message.reply_video(video_bytes)
        except:
            await update.message.reply_text("Не удалось скачать TikTok видео.")

    # YouTube
    elif "youtube.com" in link or "youtu.be" in link:
        try:
            yt = YouTube(link)
            stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
            stream.download(filename="video.mp4")
            with open("video.mp4", "rb") as f:
                await update.message.reply_video(f)
            os.remove("video.mp4")
        except:
            await update.message.reply_text("Не удалось скачать YouTube видео.")

    # Instagram
    elif "instagram.com" in link:
        try:
            L = instaloader.Instaloader(dirname_pattern="insta_video", filename_pattern="video")
            shortcode = link.rstrip("/").split("/")[-1]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target="insta_video")
            for file in os.listdir("insta_video"):
                if file.endswith(".mp4"):
                    path = os.path.join("insta_video", file)
                    with open(path, "rb") as f:
                        await update.message.reply_video(f)
                    os.remove(path)
        except:
            await update.message.reply_text("Не удалось скачать Instagram видео.")
    else:
        await update.message.reply_text("Не могу распознать ссылку!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.run_polling()
