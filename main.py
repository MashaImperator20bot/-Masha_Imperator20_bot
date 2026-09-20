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
import tempfile
from telebot import types
from datetime import datetime, timedelta
from urllib import request as urllib_request
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = os.environ.get('BOT_TOKEN')
TMP = tempfile.gettempdir()

# Пауза при старте: даём сети контейнера время подключиться (совет поддержки RelaxDev)
MOUTH_INVERT = False  # False: пока говорят - рот открыт. Если наоборот - поставь True
_START_DELAY = int(os.environ.get("START_DELAY", "15"))
print(f"[start] жду {_START_DELAY} c, пока поднимется сеть...")
time.sleep(_START_DELAY)
# ===== КАРТИНКИ ДЛЯ /video (встроены в код) =====
import base64

_VIDEO_IMG_1_B64 = (
    "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"
)

_VIDEO_IMG_2_B64 = (
    "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"
)

VIDEO_IMG_1 = f"{TMP}/video_1.jpg"
VIDEO_IMG_2 = f"{TMP}/video_2.jpg"

def _write_video_images():
    for path, data in ((VIDEO_IMG_1, _VIDEO_IMG_1_B64), (VIDEO_IMG_2, _VIDEO_IMG_2_B64)):
        try:
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
        except Exception as e:
            print(f"[video img] не удалось записать {path}: {e}")

_write_video_images()
# ===== FFMPEG — ищем или скачиваем напрямую =====
FFMPEG_PATH = "ffmpeg"

def _find_ffmpeg():
    which = shutil.which("ffmpeg")
    if which:
        return which

    for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg",
              "/app/ffmpeg", f"{TMP}/ffmpeg", os.path.expanduser("~/ffmpeg")]:
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
        tar_path = f"{TMP}/ffmpeg.tar.xz"
        extract_dir = f"{TMP}/ffmpeg_extract"

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

# ============================================================
#  ТЯЖЁЛАЯ ЗАГРУЗКА (ffmpeg + librosa) В ФОНЕ,
#  чтобы бот отвечал на команды сразу после старта
# ============================================================
LIBROSA_OK = False
librosa = None
sf = None

def _init_heavy():
    global FFMPEG_PATH, LIBROSA_OK, librosa, sf
    try:
        FFMPEG_PATH = _find_ffmpeg() or "ffmpeg"
        print(f"[ffmpeg] итоговый путь: {FFMPEG_PATH}")
    except Exception as e:
        print(f"[ffmpeg] ошибка поиска: {e}")
    if os.environ.get("USE_LIBROSA") == "1":
        try:
            import librosa as _librosa
            import soundfile as _sf
            librosa = _librosa
            sf = _sf
            LIBROSA_OK = True
            print("[librosa] OK")
        except Exception as e:
            LIBROSA_OK = False
            print(f"[librosa] не загрузилась: {e}")
    else:
        print("[librosa] выключен (экономим память), голос меняется через ffmpeg")

threading.Thread(target=_init_heavy, daemon=True).start()

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

def _log_updates(messages):
    for m in messages:
        try:
            txt = m.text or ""
            info = txt.split()[0][:30] if txt.startswith("/") else m.content_type
            print(f"[msg] chat={m.chat.id} user={m.from_user.id} {info}")
        except Exception:
            pass

bot.set_update_listener(_log_updates)
# ===== СОСТОЯНИЕ =====
voice_mode_enabled = {}
voice_pitch = {}
video_mode_enabled = {}

muted_users = {}
banan_users = {}
chat_user_usernames = {}
# ===== МАТ-ФИЛЬТР =====
BAD_WORDS_RAW = [
    'хуй', 'пизда', 'ебать', 'блядь', 'блять', 'бля', 'сука', 'нахуй', 'похуй', 'заебал', 'заебало', 'пиздец',
    'ахуеть', 'охуеть', 'хуево', 'пиздато', 'ебанутый', 'еблан', 'мудак', 'уебок', 'уёбок', 'уебище', 'уёбище',
    'долбоёб', 'долбоеб', 'хуйня', 'херня', 'пиздеть', 'пиздишь', 'пиздит', 'хуев', 'пизд', 'ебал', 'ебу', 'ебёт',
    'ебет', 'выебон', 'залупа', 'жопа', 'говно', 'срать', 'сраный', 'ссаный', 'сцаный', 'шлюха', 'проститутка',
    'дешёвка', 'дешевка', 'тварь', 'урод', 'ублюдок', 'сволочь', 'падла', 'гандон', 'гондон', 'мразь', 'сучара',
    'черт', 'чёрт', 'хрен', 'фигня', 'трахать', 'трахнуть', 'отсос', 'минет', 'член', 'вагина', 'секс', 'порно',
    'анальный', 'оральный', 'дрочить', 'дрочила', 'дрочер', 'сперма', 'конча', 'кончить', 'пидор', 'пидорас', 'пидр',
    'гомосек', 'гомосесуалист', 'лесбиянка', 'лесби', 'геи', 'гей', 'транс', 'дебил', 'идиот', 'кретин', 'даун',
    'аутист', 'уродина', 'жирный', 'жиробас', 'толстый', 'убогий', 'ничтожество', 'отброс', 'шваль', 'лох', 'лошара',
    'чмо', 'чмырь', 'чертила', 'козёл', 'козел', 'баран', 'овца', 'свинья', 'гнида', 'гандон', 'падло', 'сукин',
    'сучий', 'хренов', 'хреново', 'сучка', 'стерва', 'стерво', 'сдохни', 'умри', 'убейся', 'повесься', 'застрелись',
    'мать', 'мамка', 'мамку', 'мать твою', 'твою мать', 'ёбаный', 'ебаный', 'ёбанный', 'ебанный', 'ёпта', 'епта',
    'пиздануть', 'хуярить', 'хуярит', 'заебись', 'заебался', 'охуенный', 'ахуенный', 'нихуя', 'нехуй', 'дохуя',
    'поебать', 'разъебать', 'разъебал', 'уебать', 'уебал', 'отпиздить', 'изъебаться', 'наебать', 'наебал', 'проебать',
    'проебал', 'съебаться', 'съебал', 'ебанько', 'мудило', 'мудачина', 'долбоебина', 'хуесос', 'хуесосина',
    'залупень', 'писюн', 'писька', 'жополиз', 'жополизство', 'говнюк', 'говноед', 'говномес', 'дерьмо', 'дерьмовый',
    'срака', 'сракотан', 'пердун', 'пернуть', 'вонючка', 'вонять', 'смердеть', 'смерд', 'мерзавец', 'мерзкий',
    'омерзительный', 'тошнотворный', 'рвота', 'блевота', 'блевать', 'блевотный', 'ссанина', 'сцанина', 'обоссаный',
    'обосцаный', 'зассанец', 'зассаный', 'писюн', 'писюшка', 'елда', 'елдак', 'хер', 'хренотень', 'хреновина',
    'хреновинка', 'фигня', 'фиговый', 'фигово', 'петух', 'петушара', 'петушок', 'курица', 'курятник', 'шалава',
    'шалавка', 'шлюха', 'шлюшка', 'потаскуха', 'блядина', 'блядища', 'блядство', 'блядовать', 'разврат', 'развратник',
    'развратный', 'похотливый', 'кобель', 'кобелина', 'сука', 'сучонок', 'сучёныш', 'щенок', 'шавка', 'моська',
    'тварь', 'тварюга', 'выродок', 'ублюдок', 'недоносок', 'недоумок', 'тупица', 'тупой', 'тупарь', 'дурак', 'дура',
    'дурень', 'дурочка', 'глупый', 'глупец', 'безмозглый', 'бездарь', 'бестолочь', 'балбес', 'оболтус', 'олух',
    'простофиля', 'растяпа', 'недотёпа', 'недотепа', 'разиня', 'раззява', 'лопух', 'шляпа', 'тюфяк', 'тряпка',
    'слабак', 'трус', 'трусливый', 'жалкий', 'низкий', 'подлый', 'гад', 'гадюка', 'змея', 'змеюка', 'аспид', 'ехидна',
    'кровопийца', 'кровосос', 'паразит', 'нахлебник', 'тунеядец', 'лентяй', 'лодырь', 'бездельник', 'дармоед',
    'обормот', 'оборванец', 'бродяга', 'алкаш', 'алкоголик', 'пьянь', 'пьяница', 'пьянчуга', 'наркоман', 'наркоша',
    'торчок', 'обдолбыш', 'курильщик', 'табачник', 'нищий', 'попрошайка', 'побирушка', 'хам', 'хамло', 'хамьё',
    'грубиян', 'нахал', 'наглец', 'циник', 'циничный', 'эгоист', 'себялюб', 'самовлюблённый', 'нарцисс', 'выскочка',
    'зазнайка', 'воображала', 'хвастун', 'бахвал', 'лгун', 'лжец', 'обманщик', 'плут', 'мошенник', 'вор', 'ворюга',
    'бандит', 'громила', 'хулиган', 'дебошир', 'скандалист', 'буян', 'драчун', 'задира', 'забияка', 'грубиян',
    'насильник', 'мучитель', 'истязатель', 'садист', 'изверг', 'изувер', 'варвар', 'дикарь', 'вандал', 'погромщик',
    'разрушитель', 'убийца', 'душегуб', 'головорез', 'живодёр', 'потрошитель', 'палач', 'вешатель', 'расстрельщик',
    'террорист', 'экстремист', 'фашист', 'нацист', 'расист', 'шовинист', 'сексист', 'женоненавистник',
    'мужененавистница', 'детоненавистник', 'человеконенавистник', 'мизантроп', 'социопат', 'психопат', 'шизофреник',
    'маньяк', 'извращенец', 'перверт', 'фетишист', 'вуайерист', 'эксгибиционист', 'педофил', 'зоофил', 'некрофил',
    'каннибал', 'людоед', 'кровожадный', 'жестокий', 'беспощадный', 'безжалостный', 'бессердечный', 'хладнокровный',
    'равнодушный', 'бесчувственный', 'чёрствый', 'твёрдолобый', 'твердолобый', 'упёртый', 'упрямый', 'строптивый',
    'своенравный', 'капризный', 'взбалмошный', 'истеричный', 'нервный', 'психованный', 'сумасшедший', 'безумный',
    'ненормальный', 'чокнутый', 'свихнувшийся', 'тронутый', 'помешанный', 'одержимый', 'бесноватый', 'юродивый',
    'блаженный', 'слабоумный',
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
# ===== ПРОВЕРКА МУТА / БАНАНА =====

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
# ===== ИЗМЕНЕНИЕ ТОНА =====

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

def shift_pitch_wav(in_wav, out_wav, semitones):
    """Сдвиг тона. Если librosa нет — обходимся только ffmpeg."""
    if LIBROSA_OK:
        y, sr = librosa.load(in_wav, sr=22050)
        y2 = librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)
        sf.write(out_wav, y2, sr)
    else:
        f = 2 ** (semitones / 12.0)
        subprocess.run([
            FFMPEG_PATH, '-i', in_wav,
            '-af', f'asetrate={22050 * f:.2f},aresample=22050,atempo={1 / f:.5f}',
            out_wav, '-y'
        ], capture_output=True, timeout=60)
    if not os.path.exists(out_wav):
        raise RuntimeError("не удалось изменить голос (проверь ffmpeg)")

def mouth_states(wav_path, step=0.04):
    """Список кадров по 40 мс: True = голос громкий (рот открыт)."""
    import wave, array, math
    with wave.open(wav_path, 'rb') as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        raw = w.readframes(w.getnframes())
    a = array.array('h')
    a.frombytes(raw[:len(raw) // 2 * 2])
    if ch > 1:
        a = a[::ch]
    duration = min(len(a) / sr, 60)
    hop = max(1, int(sr * step))
    rms = []
    for i in range(0, int(duration * sr), hop):
        chunk = a[i:i + hop]
        if not chunk:
            break
        rms.append(math.sqrt(sum(x * x for x in chunk) / len(chunk)))
    thr = max(max(rms) * 0.15 if rms else 0, 30)
    states = [v > thr for v in rms]
    i = 0
    while i < len(states):
        j = i
        while j < len(states) and states[j] == states[i]:
            j += 1
        if j - i < 2 and i > 0:
            for k in range(i, j):
                states[k] = states[i - 1]
        i = j
    return states, duration

def change_voice_pitch(message, semitones=4):
    try:
        ts = int(time.time() * 1000)
        input_path = f"{TMP}/in_{ts}.ogg"
        wav_path = f"{TMP}/in_{ts}.wav"
        out_wav = f"{TMP}/out_{ts}.wav"
        out_ogg = f"{TMP}/out_{ts}.ogg"

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

        shift_pitch_wav(wav_path, out_wav, semitones)

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
# ===== КРУЖОК (видео-заметка) С ИЗМЕНЁННЫМ ГОЛОСОМ =====

def make_video_note(message, semitones=4):
    if not (os.path.exists(VIDEO_IMG_1) and os.path.exists(VIDEO_IMG_2)):
        _write_video_images()
    try:
        ts = int(time.time() * 1000)
        input_path = f"{TMP}/vin_{ts}.ogg"
        wav_path = f"{TMP}/vin_{ts}.wav"
        out_wav = f"{TMP}/vout_{ts}.wav"
        list_path = f"{TMP}/vlist_{ts}.txt"
        out_mp4 = f"{TMP}/vout_{ts}.mp4"

        content, err = _download_telegram_file(message.voice.file_id)
        if content is None:
            try: bot.reply_to(message, f"❌ Не удалось скачать голосовое:\n{err}", parse_mode=None)
            except Exception: pass
            return
        with open(input_path, 'wb') as f:
            f.write(content)

        subprocess.run([FFMPEG_PATH, '-i', input_path, '-ar', '22050', '-ac', '1', wav_path, '-y'],
                       capture_output=True, timeout=60)
        shift_pitch_wav(wav_path, out_wav, semitones)
        states, duration = mouth_states(out_wav)
        STEP = 0.04

        # кадры по 40 мс (25 к/с): рот открыт -> картинка 1, закрыт -> картинка 2
        frames_dir = f"{TMP}/vf_{ts}"
        os.makedirs(frames_dir, exist_ok=True)
        for idx, opened in enumerate(states or [False]):
            shutil.copyfile(VIDEO_IMG_1 if (opened != MOUTH_INVERT) else VIDEO_IMG_2, f"{frames_dir}/f_{idx:05d}.jpg")

        r = subprocess.run([
            FFMPEG_PATH, '-framerate', '25', '-i', f"{frames_dir}/f_%05d.jpg",
            '-i', out_wav,
            '-vf', 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,format=yuv420p',
            '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.1',
            '-preset', 'veryfast', '-bf', '0', '-g', '25', '-r', '25',
            '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-b:a', '64k',
            '-t', str(duration), '-shortest', '-movflags', '+faststart',
            out_mp4, '-y'
        ], capture_output=True, timeout=120)
        shutil.rmtree(frames_dir, ignore_errors=True)
        if r.returncode != 0 or not os.path.exists(out_mp4):
            raise RuntimeError("ffmpeg: " + r.stderr.decode(errors="ignore")[-200:])

        with open(out_mp4, 'rb') as f:
            try:
                bot.send_video_note(message.chat.id, f, reply_to_message_id=message.message_id, length=480)
            except Exception:
                f.seek(0)
                bot.send_video_note(message.chat.id, f, length=480)

        for p in [input_path, wav_path, out_wav, list_path, out_mp4]:
            try: os.remove(p)
            except Exception: pass
    except Exception as e:
        print(f"[video error] {e}\n{traceback.format_exc()}")
        try: bot.reply_to(message, f"❌ Ошибка: {str(e)[:200]}")
        except Exception: pass
# ===== КОМАНДЫ ГОЛОСА =====

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

@bot.message_handler(commands=['video'])
def enable_video_mode(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    chat_id = message.chat.id
    video_mode_enabled[chat_id] = True
    voice_pitch.setdefault(chat_id, 4)
    bot.reply_to(
        message,
        f"🎥 Режим кружков *включён*.\n"
        f"Тон: *{voice_pitch[chat_id]:+d}* полутонов.\n\n"
        f"`/pitch N` — изменить тон (от -12 до +12)\n"
        f"`/video_off` — выключить",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['video_off'])
def disable_video_mode(message):
    if is_user_muted(message):
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception: pass
        return
    video_mode_enabled[message.chat.id] = False
    bot.reply_to(message, "🔇 Режим кружков выключен.")

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
    video_on = video_mode_enabled.get(chat_id, False)
    if not video_on and not voice_mode_enabled.get(chat_id, False):
        return
    bot.reply_to(message, "🎤 Обрабатываю...")
    semitones = voice_pitch.get(chat_id, 4)
    target = make_video_note if video_on else change_voice_pitch
    threading.Thread(target=target, args=(message, semitones), daemon=True).start()
# ===== БАНАН =====

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
# ===== МОДЕРАЦИЯ =====

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
        or command.startswith("/voice")
        or command.startswith("/video")
        or command.startswith("/pitch")
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
# ===== ГЛАВНЫЙ ОБРАБОТЧИК =====

@bot.message_handler(func=lambda msg: True)
def count_messages(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        if message.from_user.username:
            chat_user_usernames.setdefault(chat_id, {})[message.from_user.username.lower()] = user_id

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

        mode = chat_modes.get(chat_id)
        if mode == "prime":
            user_text = message.text or "Пользователь отправил сообщение без текста."
            identity_reply = get_bot_identity_reply(user_text)
            if identity_reply:
                bot.reply_to(message, identity_reply)
                return
            return

        if mode == "lawyer":
            profile = lawyer_profiles.get(chat_id)
            if not profile:
                chat_modes.pop(chat_id, None)
                return
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
# ===== HEALTH-CHECK =====

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
            try:
                me = bot.get_me()
                print(f"[bot] @{me.username} подключён, слушаю сообщения")
            except Exception as error:
                print(f"[bot] get_me не удался (проверь BOT_TOKEN): {error}")
            bot.polling(none_stop=True, timeout=60)
        except Exception as error:
            print(f"[polling error] {error}")
            time.sleep(15)

if __name__ == "__main__":
    health_thread = threading.Thread(target=run_health, daemon=True)
    health_thread.start()
    ping_thread = threading.Thread(target=self_ping_loop, daemon=True)
    ping_thread.start()

    print("Бот запущен...")
    run_bot()
