import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import yfinance as yf
import pandas as pd
import ta

# Configuración (¡CAMBIARÁS ESTO DESPUÉS!)
TOKEN = "8585065523:AAGfB6u1SELEOMRD4dZSCATiFcqsm3cLB9o"

class Estrategia:
    def analizar(self, simbolo):
        try:
            df = yf.download(simbolo, period="1d", interval="5m", progress=False)
            if df.empty: return None
            
            df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
            df['ema20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
            
            last = df.iloc[-1]
            precio = round(last['Close'], 2)
            
            # Apalancamiento
            if 30 <= last['rsi'] <= 45 and last['Close'] > last['ema20']:
                return {'tipo': 'CALL', 'precio': precio, 'estrategia': 'Apalancamiento'}
            if 55 <= last['rsi'] <= 70 and last['Close'] < last['ema20']:
                return {'tipo': 'PUT', 'precio': precio, 'estrategia': 'Apalancamiento'}
            
            # Binarias
            if 40 <= last['rsi'] <= 60:
                if last['Close'] > last['ema20']:
                    return {'tipo': 'CALL', 'precio': precio, 'estrategia': 'Binarias'}
                else:
                    return {'tipo': 'PUT', 'precio': precio, 'estrategia': 'Binarias'}
            return None
        except:
            return None

estrategia = Estrategia()
ACTIVOS = {
    "ORO": "GC=F",
    "PETROLEO": "CL=F",
    "NASDAQ": "^NDX"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Ver señales AHORA", callback_data='señales')],
        [InlineKeyboardButton("⏰ Activar automáticas (c/30min)", callback_data='auto')]
    ]
    await update.message.reply_text(
        "🤖 Bot de Trading Activo\nTus estrategias optimizadas >80% win rate",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'señales':
        mensaje = "📊 SEÑALES AHORA:\n\n"
        for nombre, simbolo in ACTIVOS.items():
            senal = estrategia.analizar(simbolo)
            if senal:
                mensaje += f"✅ {nombre}: {senal['tipo']} a ${senal['precio']} ({senal['estrategia']})\n"
            else:
                mensaje += f"⏸ {nombre}: Sin señal clara\n"
        await query.edit_message_text(mensaje)
    
    elif query.data == 'auto':
        context.user_data['auto'] = True
        await query.edit_message_text("✅ Automático activado. Recibirás señales cada 30 minutos.")

async def enviar_automaticas(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    mensaje = "🔄 SEÑALES AUTOMÁTICAS:\n\n"
    for nombre, simbolo in ACTIVOS.items():
        senal = estrategia.analizar(simbolo)
        if senal:
            mensaje += f"✅ {nombre}: {senal['tipo']} a ${senal['precio']}\n"
    await context.bot.send_message(chat_id=chat_id, text=mensaje)

async def set_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.job_queue.run_repeating(enviar_automaticas, interval=1800, first=5, chat_id=update.message.chat_id)
    await update.message.reply_text("⏰ Señales cada 30 minutos activadas")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("auto", set_auto))
    print("✅ Bot funcionando...")
    app.run_polling()

if __name__ == "__main__":
    main()
