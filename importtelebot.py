import json
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime

import os
TOKEN = os.getenv("BOT_TOKEN")

COINS = {
    'TON': 'the-open-network',
    'ETH-ETH': 'ethereum',
    'ETHlinea': 'ethereum',
    'ETHbase': 'ethereum',
    'SOL': 'solana',
    'BNB': 'binancecoin',
    'SUI': 'sui',
    'TRX': 'tron'
}
ADMIN_ID = 5660784227
user_data = {}

def calculate_fee(nominal):
    if nominal <= 50000:
        return 0.12
    elif nominal <= 110000:
        return 0.10
    else:
        return 0.07

def get_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=idr"
    response = requests.get(url)
    data = response.json()
    return data[coin_id]['idr']

def start(update: Update, context):
    text_help = "Halo, Selamat datang di crypto reffi. Ketik /beli untuk coin crypto eceran"
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_help)

def beli(update: Update, context: CallbackContext):
    keyboard = []
    row = []
    for i, coin in enumerate(COINS.keys()):
        row.append(InlineKeyboardButton(coin, callback_data=f"coin_{coin}"))
        if i % 2 == 1:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🙌Selamat Datang Teman Refi🙌, Langsung Saja kamu ingin beli crpyto kan, NIH ada pilihan Koin mulai dari 15k aja loh⤵️:", reply_markup=reply_markup)

def help(update: Update, context):
    text_help = "Hubungi admin @refi_disini"
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_help)

def coin_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    coin = query.data.split("_")[1]
    user_id = query.from_user.id
    user_data[user_id] = {'coin': coin, 'state': None}
    query.edit_message_text(f"Oh kamu butuh koin {coin}👈Silahkan masukkan nominal pembelian {coin}.\nMinimal Pembelian adalah sebesar Rp 15,000")

def send_payment_instruction(update: Update, context: CallbackContext, user_id):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Lanjut ke Pembayaran", callback_data="confirm_payment")]])
    context.bot.send_message(
        chat_id=user_id,
        text="Jika kamu setuju, klik tombol di bawah untuk melanjutkan ke pembayaran.",
        reply_markup=keyboard
    )

def confirm_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    if user_id not in user_data:
        context.bot.send_message(chat_id=user_id, text="Data tidak ditemukan. Mulai dari /start.")
        return

    context.bot.send_message(
        chat_id=user_id,
        text=(
            "💸 Silakan transfer sejumlah Rp {:,.0f}\n"
            "Baik 👌, untuk pembayaran bisa kakak pilih :\n\n"
            "**BCA - 1131820271 A/N YUSRIL PRASETIYO**\n"
            "**SEABANK - 9013 1654 5332 A/N YUSRIL PRASETIYO**\n"
            "**DANA - 089643668209 A/N YUSRIL PRASETIYO**\n\n"
            "Setelah transfer, kirim bukti transfer berupa foto."
        ).format(user_data[user_id]['nominal']),
        parse_mode='Markdown'
    )

def handle_proof(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        update.message.reply_text("Silakan mulai dari /start.")
        return

    photo_file = update.message.photo[-1].file_id
    user_data[user_id]['proof'] = photo_file
    user_data[user_id]['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    coin = user_data[user_id]['coin']
    nominal = user_data[user_id]['nominal']
    estimation = user_data[user_id]['estimation']

    caption = (
        f"🧾 *Bukti Transfer Masuk*\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"🪙 Koin: {coin}\n"
        f"💵 Nominal: Rp {nominal:,.0f}\n"
        f"📊 Estimasi: {estimation} {coin}\n"
        f"⏰ Waktu: {user_data[user_id]['timestamp']}\n\n"
        f"Klik tombol di bawah jika bukti sudah valid."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Konfirmasi Pembayaran", callback_data=f"admin_confirm_{user_id}")]
    ])

    context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file,
        caption=caption,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    update.message.reply_text("📨 Bukti sudah dikirim ke admin. Mohon tunggu konfirmasi.  Hubungi @refi_disini jika belum di konfirmasi")

def admin_confirm_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = int(query.data.split("_")[2])

    coin = user_data[user_id]['coin']
    message = (
        f"Silahkan masukkan alamat dompet tujuan {coin} yang menggunakan jaringan {coin}.\n\n"
        f"<b>Catatan:</b>\n"
        f"- Mengirim ke jaringan yang berbeda akan mengakibatkan coin hangus.\n"
        f"- Tidak mendukung pengiriman ke Smart Contract.\n"
        f"- Transaksi blockchain tidak dapat dibatalkan."
    )

    context.bot.send_message(
        chat_id=user_id,
        text=message,
        parse_mode=ParseMode.HTML
    )

    user_data[user_id]['state'] = 'awaiting_wallet_address'

def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text
    state = user_data.get(user_id, {}).get('state')

    if user_id not in user_data:
        update.message.reply_text("Silakan mulai dengan /start.")
        return

    if state == 'awaiting_wallet_address':
        user_data[user_id]['wallet_address'] = text
        user_data[user_id]['state'] = 'awaiting_memo'
        update.message.reply_text(
            "Silahkan masukkan memo/tag/comment address kamu.\n"
            "Jika address tidak memiliki memo, silahkan masukkan angka 1"
        )
        return

    elif state == 'awaiting_memo':
        user_data[user_id]['wallet_memo'] = text
        user_data[user_id]['state'] = None
        wallet = user_data[user_id]['wallet_address']
        memo = user_data[user_id]['wallet_memo']
        combined = f"{wallet} (Memo: {memo})"
        user_data[user_id]['address_memo'] = combined

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Konfirmasi Pengiriman", callback_data=f"confirm_send_{user_id}")]
        ])

        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(f"📥 Address wallet user {user_id}:\n{combined}\n\n"
                  f"Koin: {user_data[user_id]['coin']}\n"
                  f"Nominal: Rp {user_data[user_id]['nominal']:,}\n"
                  f"Estimasi: {user_data[user_id]['estimation']}"),
            reply_markup=keyboard
        )

        update.message.reply_text("✅ Address dan memo kamu sudah kami terima. Admin akan segera mengirimkan koin.")
        return

    if 'coin' not in user_data[user_id]:
        update.message.reply_text("Silakan mulai dengan /start dan pilih koin terlebih dahulu.")
        return

    try:
        nominal = int(text)
    except ValueError:
        update.message.reply_text("Nominal harus berupa angka.")
        return

    if nominal < 15000:
        update.message.reply_text("Minimal pembelian  Rp 15.000 Bos maaf banget😥.")
        return

    if nominal > 500001:
        update.message.reply_text("Maximal pembelian  Rp 500.000 Bos maaf banget😥.")
        return

    coin_symbol = user_data[user_id]['coin']
    coin_id = COINS[coin_symbol]
    price = get_price(coin_id)
    fee_percent = calculate_fee(nominal)
    after_fee = nominal * (1 - fee_percent)
    estimated_coin = after_fee / price

    user_data[user_id].update({
        'nominal': nominal,
        'fee': fee_percent,
        'estimation': round(estimated_coin, 6),
        'price': price
    })

    update.message.reply_text(
        f"💰 Harga {coin_symbol} saat ini: Rp {price:,.0f}\n"
        f"🔍 Estimasi {coin_symbol} yang kamu dapat: {estimated_coin:.6f}"
    )
    send_payment_instruction(update, context, user_id)

def confirm_sent(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = int(query.data.split("_")[2])

    context.bot.send_message(
        chat_id=user_id,
        text=(
            "✅ Koin kamu telah berhasil dikirim! Berikut adalah nota transaksi:\n\n"
            f"🪙 Koin: {user_data[user_id]['coin']}\n"
            f"💵 Nominal: Rp {user_data[user_id]['nominal']:,}\n"
            f"📊 Jumlah coin: {user_data[user_id]['estimation']}\n"
            f"💼 Address Wallet: {user_data[user_id]['address_memo']}\n"
            f"⏰ Waktu Pengiriman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "Terima kasih telah bertransaksi dengan kami😍!\n"
            "Admin juga jual STARS/REFFERAL lohh 💁‍♂️@refi_disini"
        )
    )
    context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"✅ Transaksi ke {user_id} selesai."
    )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("beli", beli))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CallbackQueryHandler(confirm_payment, pattern="^confirm_payment$"))
    dp.add_handler(CallbackQueryHandler(coin_selected, pattern=r'^coin_'))
    dp.add_handler(CallbackQueryHandler(admin_confirm_payment, pattern=r'^admin_confirm_'))
    dp.add_handler(CallbackQueryHandler(confirm_sent, pattern=r'^confirm_send_'))
    dp.add_handler(MessageHandler(Filters.photo, handle_proof))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
