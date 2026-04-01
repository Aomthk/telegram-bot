import io
import os
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from PIL import Image
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.environ["BOT_TOKEN"]
bot = Bot(token=TOKEN)

app = FastAPI()

# เก็บรูปชั่วคราวต่อ user
user_images = defaultdict(list)

ptb_app = Application.builder().token(TOKEN).build()


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return

    user_id = update.message.from_user.id
    photo = update.message.photo[-1]

    tg_file = await context.bot.get_file(photo.file_id)
    img_bytes = await tg_file.download_as_bytearray()
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    user_images[user_id].append(img)

    if len(user_images[user_id]) < 2:
        await update.message.reply_text("ส่งมาอีก 1 รูปครับ")
        return

    img1, img2 = user_images[user_id][:2]

    # ต่อแบบซ้าย-ขวา
    new_width = img1.width + img2.width
    new_height = max(img1.height, img2.height)

    merged = Image.new("RGB", (new_width, new_height), (255, 255, 255))
    merged.paste(img1, (0, 0))
    merged.paste(img2, (img1.width, 0))

    output = io.BytesIO()
    output.name = "merged.jpg"
    merged.save(output, format="JPEG", quality=95)
    output.seek(0)

    await update.message.reply_photo(photo=output)

    user_images[user_id].clear()


ptb_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))


@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await ptb_app.initialize()
    await ptb_app.process_update(update)
    return JSONResponse({"ok": True})