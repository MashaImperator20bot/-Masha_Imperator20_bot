import os
import re
import shutil
import tarfile
import telebot
import random
import threading
import time
import traceback
import requests
import subprocess
import asyncio
import edge_tts
from telebot import types
from datetime import datetime, timedelta
from urllib import request as urllib_request
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = os.environ.get('BOT_TOKEN')

# ============================================================
#  FFMPEG — ищем или скачиваем напрямую
# ============================================================
FFMPEG_PATH = "ffmpeg"

def _find_ffmpeg():
    which = shutil.which("ffmpeg")
    if which:
        return which

    for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg",
              "/app/ffmpeg", "/tmp/ffmpeg", os.path.expanduser("~/ffmpeg")]:
        if os.path.exists(p):
            return p

    try:
        from static_ffmpeg import run as _sff_run
        b, _ = _sff_run.get_or_fetch_platform_executables_else_raise()
        if b and os.path.exists(b):
            return b
    except Exception as e:
        print(f"[ffmpeg] static-ffmpeg не помог: {e}")

    try:
        url = ("https://github.com/BtbN/FFmpeg-Builds/releases/download/"
               "latest/ffmpeg-master-latest-linux64-gpl.tar.xz")
        tar_path = "/tmp/ffmpeg.tar.xz"
        extract_dir = "/tmp/ffmpeg_extract"

        print("[ffmpeg] скачиваю бинарник...")
        urllib_request.urlretrieve(url, tar_path)

        os.makedirs(extract_dir, exist_ok=True)
        with tarfile.open(tar_path, "r:xz") as tar:
            tar.extractall(extract_dir)

        for root, dirs, files in os.walk(extract_dir):
            if "ffmpeg" in files:
                found = os.path.join(root, "ffmpeg")
                os.chmod(found, 0o755)
                print(f"[ffmpeg] скачан: {found}")
                return found
    except Exception as e:
        print(f"[ffmpeg] скачать не удалось: {e}")

    return None

FFMPEG_PATH = _find_ffmpeg() or "ffmpeg"
print(f"[ffmpeg] итоговый путь: {FFMPEG_PATH}")

# ============================================================
#  LIBROSA
# ============================================================
try:
    import librosa
    import soundfile as sf
    LIBROSA_OK = True
    print("[librosa] OK")
except Exception as e:
    LIBROSA_OK = False
    print(f"[librosa] не загрузилась: {e}")

# ============================================================
#  OPENROUTER
# ============================================================
OPENROUTER_API_KEY = "sk-or-v1-вставь_свой_ключ_сюда"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

bot = telebot.TeleBot(TOKEN)

_original_reply_to = bot.reply_to

def _safe_reply_to(message, text, **kwargs):
    try:
        return _original_reply_to(message, text, **kwargs)
    except Exception:
        try:
            return bot.send_message(message.chat.id, text, **kwargs)
        except Exception:
            return None

bot.reply_to = _safe_reply_to

# ============================================================
#  СОСТОЯНИЕ
# ============================================================
voice_mode_enabled = {}
voice_pitch = {}
invis_users = {}
speak_users = {}
speak_voice = {}

muted_users = {}
banan_users = {}
chat_user_usernames = {}

EDGE_VOICES = {
    "1": ("ru-RU-SvetlanaNeural", "Светлана (женский)"),
    "2": ("ru-RU-DmitryNeural", "Дмитрий (мужской)"),
    "3": ("ru-RU-DmitryNeural", "💀 Демон (страшный)"),
}

# ============================================================
#  МАТ-ФИЛЬТР
# ============================================================
BAD_WORDS_RAW = [
    'хуй', 'пизда', 'ебать', 'блядь', 'блять', 'бля', 'сука',
    'нахуй', 'похуй', 'заебал', 'заебало', 'пиздец', 'ахуеть',
    'охуеть', 'хуево', 'пиздато', 'ебанутый', 'еблан', 'мудак',
    'уебок', 'уёбок', 'уебище', 'уёбище', 'долбоёб', 'долбоеб',
    'хуйня', 'херня', 'пиздеть', 'пиздишь', 'пиздит', 'хуев',
    'пизд', 'ебал', 'ебу', 'ебёт', 'ебет', 'выебон', 'залупа',
    'жопа', 'говно', 'срать', 'сраный', 'ссаный', 'сцаный',
    'шлюха', 'проститутка', 'дешёвка', 'дешевка', 'тварь',
    'урод', 'ублюдок', 'сволочь', 'падла', 'гандон', 'гондон',
    'мразь', 'сучара', 'черт', 'чёрт', 'хрен', 'фигня',
    'трахать', 'трахнуть', 'отсос', 'минет', 'член', 'вагина',
    'секс', 'порно', 'анальный', 'оральный', 'дрочить',
    'дрочила', 'дрочер', 'сперма', 'конча', 'кончить',
    'пидор', 'пидорас', 'пидр', 'гомосек', 'гомосесуалист',
    'лесбиянка', 'лесби', 'геи', 'гей', 'транс',
    'дебил', 'идиот', 'кретин', 'даун', 'аутист',
    'уродина', 'жирный', 'жиробас', 'толстый',
    'убогий', 'ничтожество', 'отброс', 'шваль',
    'лох', 'лошара', 'чмо', 'чмырь', 'чертила',
    'козёл', 'козел', 'баран', 'овца', 'свинья',
    'гнида', 'гандон', 'падло', 'сукин', 'сучий',
    'хренов', 'хреново', 'сучка', 'стерва', 'стерво',
    'сдохни', 'умри', 'убейся', 'повесься', 'застрелись',
    'мать', 'мамка', 'мамку', 'мать твою', 'твою мать',
    'ёбаный', 'ебаный', 'ёбанный', 'ебанный', 'ёпта', 'епта',
    'пиздануть', 'хуярить', 'хуярит', 'заебись', 'заебался',
    'охуенный', 'ахуенный', 'нихуя', 'нехуй', 'дохуя',
    'поебать', 'разъебать', 'разъебал', 'уебать', 'уебал',
    'отпиздить', 'изъебаться', 'наебать', 'наебал', 'проебать',
    'проебал', 'съебаться', 'съебал', 'ебанько', 'мудило',
    'мудачина', 'долбоебина', 'хуесос', 'хуесосина',
    'залупень', 'писюн', 'писька', 'жополиз', 'жополизство',
    'говнюк', 'говноед', 'говномес', 'дерьмо', 'дерьмовый',
    'срака', 'сракотан', 'пердун', 'пернуть', 'вонючка',
    'вонять', 'смердеть', 'смерд', 'мерзавец', 'мерзкий',
    'омерзительный', 'тошнотворный', 'рвота', 'блевота',
    'блевать', 'блевотный', 'ссанина', 'сцанина', 'обоссаный',
    'обосцаный', 'зассанец', 'зассаный', 'писюн', 'писюшка',
    'елда', 'елдак', 'хер', 'хренотень', 'хреновина',
    'хреновинка', 'фигня', 'фиговый', 'фигово',
    'петух', 'петушара', 'петушок', 'курица', 'курятник',
    'шалава', 'шалавка', 'шлюха', 'шлюшка', 'потаскуха',
    'блядина', 'блядища', 'блядство', 'блядовать',
    'разврат', 'развратник', 'развратный', 'похотливый',
    'кобель', 'кобелина', 'сука', 'сучонок', 'сучёныш',
    'щенок', 'шавка', 'моська', 'тварь', 'тварюга',
    'выродок', 'ублюдок', 'недоносок', 'недоумок',
    'тупица', 'тупой', 'тупарь', 'дурак', 'дура',
    'дурень', 'дурочка', 'глупый', 'глупец',
    'безмозглый', 'бездарь', 'бестолочь', 'балбес',
    'оболтус', 'олух', 'простофиля', 'растяпа',
    'недотёпа', 'недотепа', 'разиня', 'раззява',
    'лопух', 'шляпа', 'тюфяк', 'тряпка', 'слабак',
    'трус', 'трусливый', 'жалкий', 'низкий', 'подлый',
    'гад', 'гадюка', 'змея', 'змеюка', 'аспид', 'ехидна',
    'кровопийца', 'кровосос', 'паразит', 'нахлебник',
    'тунеядец', 'лентяй', 'лодырь', 'бездельник',
    'дармоед', 'обормот', 'оборванец', 'бродяга',
    'алкаш', 'алкоголик', 'пьянь', 'пьяница', 'пьянчуга',
    'наркоман', 'наркоша', 'торчок', 'обдолбыш',
    'курильщик', 'табачник', 'нищий', 'попрошайка',
    'побирушка', 'хам', 'хамло', 'хамьё', 'грубиян',
    'нахал', 'наглец', 'циник', 'циничный', 'эгоист',
    'себялюб', 'самовлюблённый', 'нарцисс', 'выскочка',
    'зазнайка', 'воображала', 'хвастун', 'бахвал',
    'лгун', 'лжец', 'обманщик', 'плут', 'мошенник',
    'вор', 'ворюга', 'бандит', 'громила', 'хулиган',
    'дебошир', 'скандалист', 'буян', 'драчун', 'задира',
    'забияка', 'грубиян', 'насильник', 'мучитель',
    'истязатель', 'садист', 'изверг', 'изувер', 'варвар',
    'дикарь', 'вандал', 'погромщик', 'разрушитель',
    'убийца', 'душегуб', 'головорез', 'живодёр',
    'потрошитель', 'палач', 'вешатель', 'расстрельщик',
    'террорист', 'экстремист', 'фашист', 'нацист',
    'расист', 'шовинист', 'сексист', 'женоненавистник',
    'мужененавистница', 'детоненавистник', 'человеконенавистник',
    'мизантроп', 'социопат', 'психопат', 'шизофреник',
    'маньяк', 'извращенец', 'перверт', 'фетишист',
    'вуайерист', 'эксгибиционист', 'педофил', 'зоофил',
    'некрофил', 'каннибал', 'людоед', 'кровожадный',
    'жестокий', 'беспощадный', 'безжалостный', 'бессердечный',
    'хладнокровный', 'равнодушный', 'бесчувственный',
    'чёрствый', 'твёрдолобый', 'твердолобый', 'упёртый',
    'упрямый', 'строптивый', 'своенравный', 'капризный',
    'взбалмошный', 'истеричный', 'нервный', 'психованный',
    'сумасшедший', 'безумный', 'ненормальный', 'чокнутый',
    'свихнувшийся', 'тронутый', 'помешанный', 'одержимый',
    'бесноватый', 'юродивый', 'блаженный', 'слабоумный'
]

def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[\s\.\,\;\:\!\?\-\_\=\+\*\/\\\|\(\)\[\]\{\}\@\#\$\%\^\&\~\`\"\'«»„"<>]', '', text)
    text = text.replace('0', 'о').replace('1', 'и').replace('3', 'е')
    text = text.replace('4', 'а').replace('5', 's').replace('6', 'б')
    text = text.replace('7', 'т').replace('8', 'в').replace('9', 'д')
    text = text.replace('a', 'а').replace('e', 'е').replace('o', 'о')
    text = text.replace('p', 'р').replace('c', 'с').replace('y', 'у')
    text = text.replace('k', 'к').replace('x', 'х').replace('b', 'в')
    text = text.replace('m', 'м').replace('h', 'н').replace('t', 'т')
    text = re.sub(r'(.)\1+', r'\1', text)
    return text

def contains_bad_word(text):
    normalized = normalize_text(text)
    for word in BAD_WORDS_RAW:
        normalized_word = normalize_text(word)
        if normalized_word and normalized_word in normalized:
            return True
    return False

def get_bot_identity_reply(text):
    normalized = (text or "").lower().replace("ё", "е")
    normalized = re.sub(r"[?!.,:;«»\"']", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if (re.search(r"\bкак зовут\b", normalized)
            or re.search(r"\bполное имя\b", normalized)
            or re.search(r"\bкак тебя зовут\b", normalized)):
        return "Моё полное имя — Жилимаша, а сокращённо меня зовут Маша."
    if (re.search(r"\bгде (ты )?жив", normalized)
            or re.search(r"\bоткуда ты\b", normalized)
            or re.search(r"\bв какой стране\b", normalized)):
        return "Я живу в России."
    if (re.search(r"\bкто (твой )?(хозяин|создатель|автор)\b", normalized)
            or re.search(r"\bкто тебя создал\b", normalized)
            or re.search(r"\bкто тебя придумал\b", normalized)):
        return "Мой создатель — крутой Макс."
    return None

def limit_sentences(text, n=3):
    parts = re.findall(r'[^.!?…]+[.!?…]+', text)
    if not parts:
        return text.strip()
    return " ".join(p.strip() for p in parts[:n]).strip()

# ============================================================
#  ПРОВЕРКА МУТА / БАНАНА
# ============================================================

def is_user_muted(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        now = datetime.now()

        if chat_id in muted_users and user_id in muted_users[chat_id]:
            until_time = muted_users[chat_id][user_id]
            if until_time is None or now < until_time:
                return True
            else:
                del muted_users[chat_id][user_id]
                if not muted_users[chat_id]:
                    del muted_users[chat_id]

        if chat_id in banan_users and user_id in banan_users[chat_id]:
            until_time = banan_users[chat_id][user_id]
            if now < until_time:
                return True
            else:
                del banan_users[chat_id][user_id]
                if not banan_users[chat_id]:
                    del banan_users[chat_id]
    except Exception:
        pass
    return False

# ============================================================
#  OPENROUTER
# ============================================================

def ask_openrouter(system_prompt, user_text, max_tokens=120):
    if not OPENROUTER_API_KEY or "вставь_свой_ключ" in OPENROUTER_API_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/",
        "X-Title": "Masha Bot",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            print(f"[openrouter error] {data['error']}")
            return None
        answer = data["choices"][0]["message"]["content"].strip()
        return answer if answer else None
    except requests.exceptions.RequestException as e:
        print(f"[openrouter error] {e}")
        return None

def send_ai_reply(message, system_prompt, user_text, max_tokens=120):
    def worker():
        try:
            bot.send_chat_action(message.chat.id, "typing")
        except Exception:
            pass
        answer = ask_openrouter(system_prompt, user_text, max_tokens=max_tokens)
        if not answer:
            return
        answer = limit_sentences(answer, 3)
        try:
            bot.reply_to(message, answer)
        except Exception as e:
            print(f"[send error] {e}")
    threading.Thread(target=worker, daemon=True).start()

# ============================================================
#  TTS
# ============================================================

def tts_generate(text, output_mp3, voice="ru-RU-SvetlanaNeural"):
    async def _run():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_mp3)
    asyncio.run(_run())

def speak_text_in_chat(chat_id, text, user_id, reply_to_id=None, voice="ru-RU-SvetlanaNeural", voice_key="1"):
    try:
        ts = int(time.time() * 1000)
        mp3_path = f"/tmp/tts_{chat_id}_{ts}.mp3"
        ogg_path = f"/tmp/tts_{chat_id}_{ts}.ogg"

        tts_generate(text[:500], mp3_path, voice)

        if voice_key == "3":
            voice_filter = (
                "aresample=44100,"
                "asetrate=44100*0.7,atempo=1.4286,"
                "aecho=0.8:0.88:60|180:0.4|0.35,"
                "aecho=0.7:0.8:400:0.35,"
                "aecho=0.6:0.7:900:0.25"
            )
            subprocess.run([
                FFMPEG_PATH, '-i', mp3_path,
                '-filter:a', voice_filter,
                '-c:a', 'libopus', '-b:a', '64k',
                ogg_path, '-y'
            ], capture_output=True, timeout=60)
        else:
            subprocess.run([
                FFMPEG_PATH, '-i', mp3_path,
                '-c:a', 'libopus', '-b:a', '64k',
                ogg_path, '-y'
            ], capture_output=True, timeout=60)

        with open(ogg_path, 'rb') as f:
            try:
                bot.send_voice(chat_id, f, reply_to_message_id=reply_to_id)
            except Exception:
                f.seek(0)
                bot.send_voice(chat_id, f)

        for p in [mp3_path, ogg_path]:
            try: os.remove(p)
            except Exception: pass
    except Exception as e:
        print(f"[tts error] {e}\n{traceback.format_exc()}")
        try:
            bot.send_message(chat_id, f"⚠️ Ошибка озвучки: {str(e)[:150]}")
        except Exception:
            pass

# ============================================================
#  ИЗМЕНЕНИЕ ТОНА
# ============================================================

def _download_telegram_file(file_id):
    last_err = None
    for attempt in range(3):
        try:
            file_info = bot.get_file(file_id)
            url = f'https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}'
            for dl_attempt in range(3):
                try:
                    r = requests.get(url, timeout=120, stream=True)
                    if r.status_code == 200:
                        content = r.content
                        if content and len(content) > 100:
                            return content, None
                        last_err = f"Empty file ({len(content)} bytes)"
                    else:
                        last_err = f"HTTP {r.status_code}"
                except Exception as e:
                    last_err = f"{type(e).__name__}: {str(e)[:120]}"
                    print(f"[dl attempt {dl_attempt+1}] {last_err}")
                    time.sleep(3)
            break
        except Exception as e:
            last_err = f"{type(e).__name__}: {str(e)[:120]}"
            print(f"[get_file attempt {attempt+1}] {last_err}")
            time.sleep(3)
    return None, last_err


def change_voice_pitch(message, semitones=4):
    if not LIBROSA_OK:
        try:
            bot.reply_to(message, "❌ Режим изменения голоса недоступен.")
        except Exception:
            pass
        return
    try:
        ts = int(time.time() * 1000)
        input_path = f"/tmp/in_{ts}.ogg"
        wav_path = f"/tmp/in_{ts}.wav"
        out_wav = f"/tmp/out_{ts}.wav"
        out_ogg = f"/tmp/out_{ts}.ogg"

        content, err = _download_telegram_file(message.voice.file_id)
        if content is None:
            try:
                bot.reply_to(
                    message,
                    f"❌ Не удалось скачать голосовое:\n{err}",
                    parse_mode=None
                )
            except Exception:
                pass
            return

        with open(input_path, 'wb') as f:
            f.write(content)

        subprocess.run([
            FFMPEG_PATH, '-i', input_path,
            '-ar', '22050', '-ac', '1', wav_path, '-y'
        ], capture_output=True, timeout=60)

        y, sr = librosa.load(wav_path, sr=22050)
        y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)
        sf.write(out_wav, y_shifted, sr)

        subprocess.run([
            FFMPEG_PATH, '-i', out_wav,
            '-c:a', 'libopus', '-b:a', '64k', out_ogg, '-y'
        ], capture_output=True, timeout=60)

        with open(out_ogg, 'rb') as f:
            try:
                bot.send_voice(message.chat.id, f, reply_to_message_id=message.message_id)
            except Exception:
                f.seek(0)
                bot.send_voice(message.chat.id, f)

        for p in [input_path, wav_path, out_wav, out_ogg]:
            try: os.remove(p)
            except Exception: pass
    except Exception as e:
        print(f"[pitch error] {e}")
        try:
            bot.reply_to(message, f"❌ Ошибка: {str(e)[:200]}")
        except Exception:
            pass

# ============================================================
#  КОМАНДЫ ГОЛОСА
# ============================================================

@bot.message_handler(commands=['voice'])
def enable_voice_mode(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    chat_id = message.chat.id
    voice_mode_enabled[chat_id] = True
    voice_pitch.setdefault(chat_id, 4)
    bot.reply_to(
        message,
        f"🎤 Режим изменения голоса *включён*.\n"
        f"Тон: *{voice_pitch[chat_id]:+d}* полутонов.\n\n"
        f"`/pitch N` — изменить тон (от -12 до +12)\n"
        f"`/voice_off` — выключить",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['voice_off'])
def disable_voice_mode(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    voice_mode_enabled[message.chat.id] = False
    bot.reply_to(message, "🔇 Режим изменения голоса выключен.")

@bot.message_handler(commands=['pitch'])
def set_pitch(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    try:
        parts = message.text.strip().split()
        chat_id = message.chat.id
        if len(parts) < 2:
            bot.reply_to(message, f"Текущий тон: *{voice_pitch.get(chat_id, 4):+d}*\n`/pitch N` (от -12 до +12)", parse_mode="Markdown")
            return
        n = max(-12, min(12, int(parts[1])))
        voice_pitch[chat_id] = n
        bot.reply_to(message, f"🎚️ Тон: *{n:+d}* полутонов.", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "❌ Использование: `/pitch N`")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    chat_id = message.chat.id
    if not voice_mode_enabled.get(chat_id, False):
        return
    bot.reply_to(message, "🎤 Обрабатываю...")
    semitones = voice_pitch.get(chat_id, 4)
    threading.Thread(target=change_voice_pitch, args=(message, semitones), daemon=True).start()

# ============================================================
#  /ИНВИЗ
# ============================================================

@bot.message_handler(commands=['инвиз'])
def toggle_invis(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.chat.type == "private":
        bot.reply_to(message, "❌ Только для групп.")
        return
    if chat_id not in invis_users:
        invis_users[chat_id] = set()
    if user_id in invis_users[chat_id]:
        invis_users[chat_id].discard(user_id)
        bot.reply_to(message, "👁 Видимость включена.")
    else:
        invis_users[chat_id].add(user_id)
        bot.reply_to(message, "🫥 Невидимка включён.")

# ============================================================
#  /ГОВОР
# ============================================================

@bot.message_handler(commands=['говор'])
def toggle_speak(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id not in speak_users:
        speak_users[chat_id] = set()
    if user_id in speak_users[chat_id]:
        speak_users[chat_id].discard(user_id)
        bot.reply_to(message, "🔇 Режим озвучки выключен.")
    else:
        speak_users[chat_id].add(user_id)
        cur = speak_voice.get(chat_id, "1")
        name = EDGE_VOICES[cur][1]
        bot.reply_to(
            message,
            f"🔊 Режим озвучки *включён*.\n"
            f"Голос: *{name}*\n\n"
            f"Смени голос: `/голос 1|2|3`\n"
            f"Выключить: `/говор`",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['голос'])
def set_voice(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 2 or parts[1] not in EDGE_VOICES:
            bot.reply_to(
                message,
                "Выбор голоса:\n"
                "`/голос 1` — Светлана (женский)\n"
                "`/голос 2` — Дмитрий (мужской)\n"
                "`/голос 3` — 💀 Демон (страшный)",
                parse_mode="Markdown"
            )
            return
        chat_id = message.chat.id
        speak_voice[chat_id] = parts[1]
        vk = parts[1]
        bot.reply_to(message, f"🎙️ Голос: *{EDGE_VOICES[vk][1]}*", parse_mode="Markdown")
    except Exception as e:
        print(f"[set voice error] {e}")
        bot.reply_to(message, "❌ Использование: `/голос 1|2|3`")

# ============================================================
#  БАНАН
# ============================================================

@bot.message_handler(commands=['банан'])
def handle_banan(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    try:
        if not is_chat_admin(message):
            bot.reply_to(message, "❌ Только для администраторов чата.")
            return

        chat_id = message.chat.id
        target_id = None
        target_name = None

        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name or str(target_id)

        if not target_id:
            parts = message.text.strip().split()
            username = None
            for p in parts[1:]:
                if p.startswith('@'):
                    username = p[1:].lower()
                    break
                elif not p.isdigit():
                    username = p.lower()
                    break

            if username:
                if chat_id in chat_user_usernames:
                    target_id = chat_user_usernames[chat_id].get(username)
                if not target_id:
                    try:
                        chat_info = bot.get_chat(f"@{username}")
                        target_id = chat_info.id
                        target_name = chat_info.first_name or username
                    except Exception:
                        pass

        if not target_id:
            bot.reply_to(message, "❌ Использование: `/банан @username` (или reply)", parse_mode="Markdown")
            return

        if not target_name:
            target_name = str(target_id)

        until = datetime.now() + timedelta(hours=24)
        if chat_id not in banan_users:
            banan_users[chat_id] = {}
        banan_users[chat_id][target_id] = until

        if message.reply_to_message:
            try:
                bot.delete_message(chat_id, message.reply_to_message.message_id)
            except Exception:
                pass

        bot.reply_to(
            message,
            f"🍌 *{target_name}* отправлен в банан на 24 часа.\n"
            f"Снять: `/антибананан`",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"[banan error] {e}")

@bot.message_handler(commands=['антибананан'])
def handle_antibanan(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    try:
        if not is_chat_admin(message):
            bot.reply_to(message, "❌ Только для администраторов чата.")
            return

        chat_id = message.chat.id

        if chat_id not in banan_users or not banan_users[chat_id]:
            bot.reply_to(message, "🍌 Некуда снимать банан.")
            return

        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            if target_id in banan_users[chat_id]:
                del banan_users[chat_id][target_id]
                bot.reply_to(message, "🍌 Банан снят.")
            else:
                bot.reply_to(message, "❌ У этого пользователя нет банана.")
            return

        banan_users[chat_id].clear()
        bot.reply_to(message, "🍌 Все бананы сняты.")
    except Exception as e:
        print(f"[antibanan error] {e}")

# ============================================================
#  МОДЕРАЦИЯ
# ============================================================

mat_filter_enabled = {}
last_messages = {}
last_message_names = {}
chat_contexts = {}
last_banned_users = {}
used_unban_words = {}
chat_modes = {}
lawyer_profiles = {}
lawyer_avatar_chats = set()
self_destruct_enabled = {}

GAV_VARIANTS = ["гав!", "гав?", "(довольный) гав", "Ррррр!", "ГАВ", "(веселый) гав", "гав..."]
PHOTO_IDS = ["https://i.postimg.cc/Rhc2J69R/IMG-20260609-205259-0969.jpg"]

NORMAL_AVATAR_PATH = os.path.join(os.path.dirname(__file__), "assets", "bark_avatar.png")
LAWYER_AVATAR_PATH = os.path.join(os.path.dirname(__file__), "assets", "lawyer_avatar.jpg")

def set_bot_avatar(path):
    try:
        bot.set_my_profile_photo(types.InputProfilePhotoStatic(photo=types.InputFile(path)))
        return True
    except Exception as e:
        print(f"[avatar error] {e}")
        return False

def update_lawyer_avatar():
    try:
        if lawyer_avatar_chats:
            set_bot_avatar(LAWYER_AVATAR_PATH)
        else:
            set_bot_avatar(NORMAL_AVATAR_PATH)
    except Exception as e:
        print(f"[avatar update error] {e}")

user_counters = {}

def is_filter_enabled(chat_id):
    return mat_filter_enabled.get(chat_id, False)

def is_chat_admin(message):
    if message.chat.type not in ("group", "supergroup"):
        return False
    try:
        member = bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ("administrator", "creator")
    except:
        return False

def is_moderation_command(message):
    if not message.text:
        return False
    command = message.text.lower().strip()
    return (
        re.fullmatch(r"/бан(?:1|5)?", command) is not None
        or re.fullmatch(r"/разбан[^\w\s]*", command) is not None
        or command == "/экстерминатус"
        or command == "/самоуничтожение еретика"
        or command in ("/прайм", "/антипрайм", "/юрист", "/.")
        or re.fullmatch(r'/юрист\s+"[^"]+"\s*,\s*"[^"]+"', command) is not None
        or command.startswith("/инвиз")
        or command.startswith("/говор")
        or command.startswith("/voice")
        or command.startswith("/pitch")
        or command.startswith("/голос")
        or command.startswith("/банан")
        or command.startswith("/антибананан")
    )

def set_manual_ban(message, duration_minutes):
    if message.chat.type not in ("group", "supergroup"):
        bot.reply_to(message, "❌ Эта команда работает только в группах.")
        return
    chat_id = message.chat.id
    last_message = last_messages.get(chat_id)
    if not last_message:
        bot.reply_to(message, "❌ Пока некому назначать удаление сообщений.")
        return
    target_user_id, target_message_id = last_message
    until_time = None if duration_minutes is None else datetime.now() + timedelta(minutes=duration_minutes)
    if chat_id not in muted_users:
        muted_users[chat_id] = {}
    muted_users[chat_id][target_user_id] = until_time
    last_banned_users[chat_id] = target_user_id
    try:
        bot.delete_message(chat_id, target_message_id)
    except:
        pass
    period = "навсегда" if duration_minutes is None else f"на {duration_minutes} мин."
    bot.reply_to(message, f"✅ Сообщения пользователя будут удаляться {period}.")

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/экстерминатус")
def exterminate_last_user(message):
    try:
        if is_user_muted(message):
            try: bot.delete_message(message.chat.id, message.message_id)
            except Exception: pass
            return
        if not is_chat_admin(message):
            bot.reply_to(message, "❌ Только для администраторов.")
            return
        chat_id = message.chat.id
        last_message = last_messages.get(chat_id)
        if not last_message:
            bot.reply_to(message, "❌ Пока некому назначать удаление.")
            return
        target_user_id, _ = last_message
        bot.ban_chat_member(chat_id, target_user_id, revoke_messages=True)
        try:
            bot.unban_chat_member(chat_id, target_user_id, only_if_banned=True)
        except:
            pass
        if chat_id in muted_users:
            muted_users[chat_id].pop(target_user_id, None)
            if not muted_users[chat_id]:
                del muted_users[chat_id]
        last_banned_users.pop(chat_id, None)
        bot.reply_to(message, "✅ Пользователь удалён из группы.")
    except Exception as e:
        print(f"[exterminate error] {e}")

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/.")
def toggle_self_destruct(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    chat_id = message.chat.id
    self_destruct_enabled[chat_id] = not self_destruct_enabled.get(chat_id, False)
    bot.reply_to(message, random.choice(GAV_VARIANTS))

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/самоуничтожение еретика")
def self_destruct_heretic(message):
    try:
        if is_user_muted(message):
            try: bot.delete_message(message.chat.id, message.message_id)
            except Exception: pass
            return
        if not self_destruct_enabled.get(message.chat.id, False):
            return
        if message.chat.type not in ("group", "supergroup"):
            bot.reply_to(message, "❌ Только для групп.")
            return
        context_entries = chat_contexts.get(message.chat.id, [])
        if context_entries:
            context_text = "\n".join(f"{e['name']}: {e['text']}" for e in context_entries[-6:])
        else:
            context_text = "Подробного контекста нет."
        farewell_prompt = (
            "Напиши короткую философскую речь-прощание от Маши. 3–4 предложения.\n\n"
            f"Контекст:\n{context_text[:1800]}"
        )
        farewell = ask_openrouter("Ты Маша — философский голос бота.", farewell_prompt, max_tokens=200)
        if not farewell:
            farewell = "Каждая группа однажды подходит к границе. Я ухожу, оставляя вам тишину."
        bot.send_message(message.chat.id, farewell)
        bot.leave_chat(message.chat.id)
    except Exception as e:
        print(f"[farewell error] {e}")

@bot.message_handler(func=lambda msg: msg.text and re.fullmatch(r"/бан(?:1|5)?", msg.text.lower().strip()))
def handle_manual_ban(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    try:
        command = message.text.lower().strip()
        duration_minutes = {"бан1": 1, "бан5": 5, "бан": None}[command[1:]]
        set_manual_ban(message, duration_minutes)
    except Exception as e:
        print(f"[ban error] {e}")

def perform_manual_unban(message):
    try:
        if not is_chat_admin(message):
            bot.reply_to(message, "❌ Только для админов.")
            return False
        chat_id = message.chat.id
        target_user_id = last_banned_users.get(chat_id)
        if target_user_id is None:
            bot.reply_to(message, "❌ Нет пользователя с активным удалением.")
            return False
        if chat_id in muted_users:
            muted_users[chat_id].pop(target_user_id, None)
            if not muted_users[chat_id]:
                del muted_users[chat_id]
        last_banned_users.pop(chat_id, None)
        bot.reply_to(message, "✅ Удаление сообщений снято.")
        return True
    except Exception as e:
        print(f"[unban error] {e}")
        return False

@bot.message_handler(func=lambda msg: msg.text and re.fullmatch(r"/разбан[^\w\s]*", msg.text.lower().strip()))
def handle_manual_unban(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    used_by_users = used_unban_words.setdefault(chat_id, set())
    if user_id in used_by_users:
        bot.reply_to(message, "это слово временно не работает, напишите писюнец.")
        return
    if perform_manual_unban(message):
        used_by_users.add(user_id)

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/йода")
def handle_hidden_unban(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    perform_manual_unban(message)

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "писюнец")
def handle_pisyunets(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    bot.reply_to(message, "хахаха повёлся")

def get_lawyer_names(message):
    command = message.text.strip()
    match = re.fullmatch(r'/юрист(?:\s+"([^"]+)"\s*,\s*"([^"]+)")?', command, re.IGNORECASE)
    if not match:
        return None
    return match.group(1), match.group(2)

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/прайм")
def enable_prime_mode(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    chat_id = message.chat.id
    chat_modes[chat_id] = "prime"
    lawyer_profiles.pop(chat_id, None)
    lawyer_avatar_chats.discard(chat_id)
    update_lawyer_avatar()
    bot.reply_to(message, "🧠 Прайм-режим включён.")

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/антипрайм")
def disable_prime_mode(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    chat_id = message.chat.id
    chat_modes.pop(chat_id, None)
    lawyer_profiles.pop(chat_id, None)
    lawyer_avatar_chats.discard(chat_id)
    update_lawyer_avatar()
    bot.reply_to(message, random.choice(GAV_VARIANTS))

@bot.message_handler(func=lambda msg: msg.text and get_lawyer_names(msg) is not None)
def toggle_lawyer_mode(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    chat_id = message.chat.id
    if chat_id in lawyer_profiles:
        chat_modes.pop(chat_id, None)
        lawyer_profiles.pop(chat_id, None)
        lawyer_avatar_chats.discard(chat_id)
        update_lawyer_avatar()
        bot.reply_to(message, random.choice(GAV_VARIANTS))
        return
    last_message = last_messages.get(chat_id)
    if not last_message:
        bot.reply_to(message, "❌ Не найден пользователь.")
        return
    protected_name, defender_name = get_lawyer_names(message)
    target_user_id, _ = last_message
    lawyer_profiles[chat_id] = {
        "protected_user_id": message.from_user.id,
        "defender_user_id": target_user_id,
        "protected_name": protected_name or message.from_user.first_name,
        "defender_name": defender_name or last_message_names.get(chat_id, "оппонент"),
    }
    chat_modes[chat_id] = "lawyer"
    lawyer_avatar_chats.add(chat_id)
    update_lawyer_avatar()
    bot.reply_to(message, "⚖️ Режим юриста включён.")

@bot.message_handler(commands=['мат+'])
def enable_mat_filter(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    mat_filter_enabled[message.chat.id] = True
    bot.reply_to(message, "✅ Мат-фильтр включён.")

@bot.message_handler(commands=['мат-'])
def disable_mat_filter(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    mat_filter_enabled[message.chat.id] = False
    bot.reply_to(message, "❌ Мат-фильтр отключён.")

# ============================================================
#  ГЛАВНЫЙ ОБРАБОТЧИК
# ============================================================

@bot.message_handler(func=lambda msg: True)
def count_messages(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        if message.from_user.username:
            chat_user_usernames.setdefault(chat_id, {})[message.from_user.username.lower()] = user_id

        if chat_id in invis_users and user_id in invis_users[chat_id]:
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass

        if not is_moderation_command(message):
            last_messages[chat_id] = (user_id, message.message_id)
            last_message_names[chat_id] = (message.from_user.first_name or message.from_user.username or str(user_id))
            message_text = (message.text or message.caption or "").strip()
            if message_text:
                context_entries = chat_contexts.setdefault(chat_id, [])
                context_entries.append({"name": last_message_names[chat_id], "text": message_text[:240]})
                del context_entries[:-8]

        if chat_id in muted_users and user_id in muted_users[chat_id]:
            until_time = muted_users[chat_id][user_id]
            if until_time is None or datetime.now() < until_time:
                try:
                    bot.delete_message(chat_id, message.message_id)
                except:
                    pass
                return
            else:
                del muted_users[chat_id][user_id]
                if not muted_users[chat_id]:
                    del muted_users[chat_id]

        if chat_id in banan_users and user_id in banan_users[chat_id]:
            until_time = banan_users[chat_id][user_id]
            if datetime.now() < until_time:
                try:
                    bot.delete_message(chat_id, message.message_id)
                except Exception:
                    pass
                return
            else:
                del banan_users[chat_id][user_id]
                if not banan_users[chat_id]:
                    del banan_users[chat_id]

        if is_filter_enabled(chat_id) and message.text:
            if contains_bad_word(message.text):
                try:
                    bot.delete_message(chat_id, message.message_id)
                except:
                    pass
                until_time = datetime.now() + timedelta(minutes=1)
                if chat_id not in muted_users:
                    muted_users[chat_id] = {}
                muted_users[chat_id][user_id] = until_time
                try:
                    warning = bot.send_message(chat_id, f"⚠️ {message.from_user.first_name} использовал запрещённое слово. Сообщения удаляются 1 минуту.")
                    def delete_warning():
                        time.sleep(5)
                        try:
                            bot.delete_message(chat_id, warning.message_id)
                        except:
                            pass
                    threading.Thread(target=delete_warning, daemon=True).start()
                except:
                    pass
                return

        if chat_id in speak_users and user_id in speak_users[chat_id] and message.text:
            text = message.text.strip()
            if text and not text.startswith('/'):
                vk = speak_voice.get(chat_id, "1")
                voice = EDGE_VOICES[vk][0]
                threading.Thread(
                    target=speak_text_in_chat,
                    args=(chat_id, text, user_id, message.message_id, voice, vk),
                    daemon=True
                ).start()
                return

        mode = chat_modes.get(chat_id)
        if mode == "prime":
            user_text = message.text or "Пользователь отправил сообщение без текста."
            identity_reply = get_bot_identity_reply(user_text)
            if identity_reply:
                bot.reply_to(message, identity_reply)
                return
            send_ai_reply(
                message,
                "Ты дружелюбная нейросеть. Отвечай на русском, максимум тремя короткими предложениями.",
                user_text,
                max_tokens=150,
            )
            return

        if mode == "lawyer":
            profile = lawyer_profiles.get(chat_id)
            if not profile:
                chat_modes.pop(chat_id, None)
                return
            if user_id == profile["defender_user_id"]:
                user_text = message.text or "Оппонент отправил сообщение без текста."
                send_ai_reply(
                    message,
                    (f"Ты жёсткий юридический защитник {profile['protected_name']} в споре с "
                     f"{profile['defender_name']}. Отвечай по-русски максимум тремя предложениями."),
                    user_text,
                    max_tokens=150,
                )
            return

        if user_id not in user_counters:
            user_counters[user_id] = 0
        user_counters[user_id] += 1

        if user_counters[user_id] % 5 == 0 and user_counters[user_id] < 20:
            bot.reply_to(message, random.choice(GAV_VARIANTS))

        if user_counters[user_id] >= 20:
            bot.reply_to(message, random.choice(GAV_VARIANTS))
            bot.send_photo(message.chat.id, random.choice(PHOTO_IDS))
            user_counters[user_id] = 0
    except Exception as e:
        print(f"[count_messages error] {e}\n{traceback.format_exc()}")

# ============================================================
#  HEALTH-CHECK
# ============================================================

def self_ping_loop():
    while True:
        try:
            urllib_request.urlopen("http://localhost:8099/", timeout=10)
        except Exception:
            pass
        time.sleep(180)

class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def run_health():
    port = int(os.environ.get("PORT", 8080))
    while True:
        try:
            HTTPServer(("0.0.0.0", port), Health).serve_forever()
        except Exception as error:
            print(f"[health error] {error}")
            time.sleep(5)

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as error:
            print(f"[polling error] {error}")
            time.sleep(15)

if __name__ == "__main__":
    if not OPENROUTER_API_KEY or "вставь_свой_ключ" in OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY не задан!")

    health_thread = threading.Thread(target=run_health, daemon=True)
    health_thread.start()
    ping_thread = threading.Thread(target=self_ping_loop, daemon=True)
    ping_thread.start()

    print("Бот запущен...")
    run_bot()
