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
# ===== КАРТИНКИ ДЛЯ /video (скачиваются по ссылкам) =====
VIDEO_URL_OPEN = "https://i.postimg.cc/mr09BbQN/Polish-20260920-191700739.jpg"    # рот открыт
VIDEO_URL_CLOSED = "https://i.postimg.cc/fb6dDwxt/Polish-20260920-191729556.jpg"  # рот закрыт
VIDEO_IMG_1 = f"{TMP}/video_1.jpg"  # открыт
VIDEO_IMG_2 = f"{TMP}/video_2.jpg"  # закрыт

def _write_video_images():
    """Скачивает две картинки один раз и хранит во временной папке."""
    for url, path in ((VIDEO_URL_OPEN, VIDEO_IMG_1), (VIDEO_URL_CLOSED, VIDEO_IMG_2)):
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            continue
        try:
            r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            if len(r.content) < 1000 or not r.content.startswith(b"\xff\xd8"):
                raise ValueError("по ссылке не JPEG-картинка")
            with open(path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"[video img] не удалось скачать {url}: {e}")
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
    """Сдвиг тона. Если librosa нет - ffmpeg. Если и он не справился - голос без сдвига."""
    try:
        if LIBROSA_OK:
            y, sr = librosa.load(in_wav, sr=22050)
            y2 = librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)
            sf.write(out_wav, y2, sr)
        else:
            f = 2 ** (semitones / 12.0)
            r = subprocess.run([
                FFMPEG_PATH, '-i', in_wav,
                '-af', f'asetrate={22050 * f:.2f},aresample=22050,atempo={1 / f:.5f}',
                '-acodec', 'pcm_s16le', out_wav, '-y'
            ], capture_output=True, timeout=60)
            if r.returncode != 0:
                print(f"[pitch] ffmpeg rc={r.returncode}: {r.stderr.decode(errors='ignore')[-300:]}")
    except Exception as e:
        print(f"[pitch] ошибка: {e}")
    if not os.path.exists(out_wav) or os.path.getsize(out_wav) < 2000:
        print("[pitch] сдвиг тона не получился, беру голос без изменений")
        shutil.copyfile(in_wav, out_wav)

def mouth_states(wav_path, step=0.04):
    """Список кадров по 40 мс: True = голос громкий (рот открыт)."""
    import wave, array, math
    try:
        with wave.open(wav_path, 'rb') as w:
            sr = w.getframerate()
            ch = w.getnchannels()
            raw = w.readframes(w.getnframes())
    except Exception as e:
        print(f"[mouth] wave не прочитал ({e}), читаю сырые данные")
        sr, ch = 22050, 1
        with open(wav_path, 'rb') as fh:
            raw = fh.read()[44:]
    a = array.array('h')
    a.frombytes(raw[:len(raw) // 2 * 2])
    if ch > 1:
        a = a[::ch]
    duration = min(len(a) / sr, 60)
    if duration < 0.3:
        raise RuntimeError("голос получился пустой (слишком короткий или не прочитался)")
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
    _write_video_images()
    for _i, _p in enumerate((VIDEO_IMG_1, VIDEO_IMG_2), 1):
        if not os.path.exists(_p):
            bot.reply_to(message, f"❌ Не удалось скачать картинку {_i} по ссылке. Проверь, что ссылка на postimg открывается.")
            return
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
            '-shortest', '-movflags', '+faststart',
            out_mp4, '-y'
        ], capture_output=True, timeout=120)
        shutil.rmtree(frames_dir, ignore_errors=True)
        if r.returncode != 0 or not os.path.exists(out_mp4):
            raise RuntimeError("ffmpeg: " + r.stderr.decode(errors="ignore")[-200:])
        info = subprocess.run([FFMPEG_PATH, '-i', out_mp4], capture_output=True, timeout=30).stderr.decode(errors="ignore")
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
        if not m or int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) < 0.3 or "Audio" not in info:
            raise RuntimeError("видео получилось пустым: " + info[-200:])

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
