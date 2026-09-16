import os
import re
import telebot
import random
import threading
import time
import traceback
import multiprocessing as mp
from queue import Empty
from telebot import types
from datetime import datetime, timedelta
from urllib import request as urllib_request
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

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
#  ВОРКЕР МОДЕЛИ (отдельный процесс)
# ============================================================

LOCAL_MODEL_URL = (
    "https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct-GGUF/"
    "resolve/main/smollm2-135m-instruct-q4_k_m.gguf?download=true"
)
LOCAL_MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "smollm2-135m-instruct-q4_k_m.gguf",
)

def model_worker(req_q, resp_q):
    try:
        os.makedirs(os.path.dirname(LOCAL_MODEL_PATH), exist_ok=True)
        if not os.path.exists(LOCAL_MODEL_PATH) or os.path.getsize(LOCAL_MODEL_PATH) < 10_000_000:
            temp_path = f"{LOCAL_MODEL_PATH}.part"
            with urllib_request.urlopen(LOCAL_MODEL_URL, timeout=60) as response:
                with open(temp_path, "wb") as f:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
            os.replace(temp_path, LOCAL_MODEL_PATH)

        from llama_cpp import Llama
        llm = Llama(
            model_path=LOCAL_MODEL_PATH,
            n_ctx=128,
            n_threads=2,
            n_gpu_layers=0,
            chat_format="chatml",
            verbose=False,
        )
    except Exception as e:
        resp_q.put(("init_error", str(e)))
        return

    resp_q.put(("ready", None))

    while True:
        try:
            req = req_q.get()
        except (EOFError, OSError):
            break
        if req is None:
            break
        try:
            system_prompt, user_text, max_tokens = req
            messages = [
                {"role": "system", "content": (system_prompt or "")[:120]},
                {"role": "user", "content": (user_text or "")[:120]},
            ]
            result = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.6,
                top_p=0.9,
            )
            answer = result["choices"][0]["message"]["content"].strip()
            resp_q.put(("ok", answer))
        except Exception as e:
            resp_q.put(("gen_error", str(e)))

# ============================================================
#  МЕНЕДЖЕР ВОРКЕРА
# ============================================================

model_process = None
model_req_q = None
model_resp_q = None
model_status = "not_started"
model_lock = threading.Lock()

chats_waiting_model = set()

def start_model_worker():
    global model_process, model_req_q, model_resp_q, model_status
    with model_lock:
        if model_status in ("loading", "ready"):
            return
        if model_status == "failed":
            return
        model_status = "loading"

    try:
        model_req_q = mp.Queue()
        model_resp_q = mp.Queue()
        model_process = mp.Process(
            target=model_worker,
            args=(model_req_q, model_resp_q),
            daemon=True,
        )
        model_process.start()
        print("[model] Процесс модели запущен.")
        threading.Thread(target=_watch_model, daemon=True).start()
    except Exception as e:
        print(f"[model] Не удалось запустить процесс: {e}")
        with model_lock:
            model_status = "failed"

def _watch_model():
    global model_status
    try:
        status, payload = model_resp_q.get(timeout=300)
    except Empty:
        print("[model] Таймаут загрузки модели.")
        _kill_model_process()
        with model_lock:
            model_status = "failed"
        _notify_failed()
        return
    except Exception as e:
        print(f"[model] Ошибка ожидания: {e}")
        with model_lock:
            model_status = "failed"
        _notify_failed()
        return

    if status == "ready":
        with model_lock:
            model_status = "ready"
        print("[model] Модель загружена.")
        _notify_ready()
    else:
        print(f"[model] Ошибка инициализации: {payload}")
        _kill_model_process()
        with model_lock:
            model_status = "failed"
        _notify_failed()

def _notify_ready():
    for chat_id in list(chats_waiting_model):
        try:
            bot.send_message(
                chat_id,
                "✅ Маша проснулась! Нейросеть загружена — теперь отвечаю по-настоящему. "
                "Напиши что-нибудь."
            )
        except Exception as e:
            print(f"[notify error] {e}")
    chats_waiting_model.clear()

def _notify_failed():
    for chat_id in list(chats_waiting_model):
        try:
            bot.send_message(
                chat_id,
                "⚠️ Не удалось загрузить нейросеть. Попробуй позже."
            )
        except Exception:
            pass
    chats_waiting_model.clear()

def _kill_model_process():
    global model_process
    try:
        if model_process is not None and model_process.is_alive():
            model_process.terminate()
            model_process.join(timeout=2)
    except Exception:
        pass

def ask_local_model(chat_id, system_prompt, user_text, max_tokens=20):
    global model_status, model_process
    if model_status != "ready":
        if model_status == "not_started":
            threading.Thread(target=start_model_worker, daemon=True).start()
        return None

    if model_process is None or not model_process.is_alive():
        print("[model] Процесс модели умер.")
        with model_lock:
            model_status = "failed"
        return None

    try:
        model_req_q.put((system_prompt, user_text, max_tokens))
        status, payload = model_resp_q.get(timeout=90)
    except Empty:
        print("[model] Таймаут генерации.")
        _kill_model_process()
        with model_lock:
            model_status = "failed"
        return None
    except Exception as e:
        print(f"[model] Ошибка запроса: {e}")
        return None

    if status != "ok":
        print(f"[model] Ошибка генерации: {payload}")
        return None

    answer = (payload or "").strip()
    if not answer:
        return None
    return limit_sentences(answer, 2)

def send_local_ai_reply(message, system_prompt, user_text, max_tokens=20):
    def generate_reply():
        try:
            bot.send_chat_action(message.chat.id, "typing")
        except Exception:
            pass
        try:
            answer = ask_local_model(
                message.chat.id, system_prompt, user_text, max_tokens=max_tokens
            )
            if not answer or not answer.strip():
                try:
                    bot.reply_to(message, "⏳ Маша ещё думает. Попробуй чуть позже.")
                except Exception:
                    pass
                return
            try:
                bot.reply_to(message, answer)
            except Exception as e:
                print(f"[send error] {e}")
        except Exception as e:
            print(f"[ai error] {e}")
            try:
                bot.reply_to(message, "⏳ Маша ещё думает. Попробуй чуть позже.")
            except Exception:
                pass
    threading.Thread(target=generate_reply, daemon=True).start()

muted_users = {}
mat_filter_enabled = {}
last_messages = {}
last_message_names = {}
chat_contexts = {}
last_banned_users = {}
used_unban_words = {}
chat_modes = {}
lawyer_profiles = {}
lawyer_avatar_chats = set()
ai_histories = {}
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
        if not is_chat_admin(message):
            bot.reply_to(message, "❌ Эта команда доступна только администраторам чата.")
            return
        chat_id = message.chat.id
        last_message = last_messages.get(chat_id)
        if not last_message:
            bot.reply_to(message, "❌ Пока некому назначать удаление из группы.")
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
    try:
        chat_id = message.chat.id
        self_destruct_enabled[chat_id] = not self_destruct_enabled.get(chat_id, False)
        bot.reply_to(message, random.choice(GAV_VARIANTS))
    except Exception as e:
        print(f"[toggle error] {e}")

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/самоуничтожение еретика")
def self_destruct_heretic(message):
    try:
        if not self_destruct_enabled.get(message.chat.id, False):
            return
        if message.chat.type not in ("group", "supergroup"):
            bot.reply_to(message, "❌ Эта команда работает только в группах.")
            return
        context_entries = chat_contexts.get(message.chat.id, [])
        if context_entries:
            context_text = "\n".join(f"{e['name']}: {e['text']}" for e in context_entries[-6:])
        else:
            context_text = "Подробного контекста разговора нет."
        farewell_prompt = (
            "Напиши короткую философскую речь-прощание от Маши. 3–4 предложения.\n\n"
            f"Контекст:\n{context_text[:1800]}"
        )
        try:
            farewell = ask_local_model(
                message.chat.id,
                "Ты Маша — философский голос бота.",
                farewell_prompt,
                max_tokens=60,
            )
        except Exception:
            farewell = None
        if not farewell:
            farewell = ("Каждая группа однажды подходит к границе, за которой слова "
                        "становятся выбором. Я ухожу, оставляя вам тишину.")
        bot.send_message(message.chat.id, farewell)
        bot.leave_chat(message.chat.id)
    except Exception as e:
        print(f"[farewell error] {e}")

@bot.message_handler(func=lambda msg: msg.text and re.fullmatch(r"/бан(?:1|5)?", msg.text.lower().strip()))
def handle_manual_ban(message):
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
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        used_by_users = used_unban_words.setdefault(chat_id, set())
        if user_id in used_by_users:
            bot.reply_to(message, "это слово временно не работает, напишите писюнец.")
            return
        if perform_manual_unban(message):
            used_by_users.add(user_id)
    except Exception as e:
        print(f"[unban error] {e}")

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/йода")
def handle_hidden_unban(message):
    perform_manual_unban(message)

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "писюнец")
def handle_pisyunets(message):
    bot.reply_to(message, "хахаха повёлся")

def get_lawyer_names(message):
    command = message.text.strip()
    match = re.fullmatch(r'/юрист(?:\s+"([^"]+)"\s*,\s*"([^"]+)")?', command, re.IGNORECASE)
    if not match:
        return None
    return match.group(1), match.group(2)

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/прайм")
def enable_prime_mode(message):
    try:
        chat_id = message.chat.id
        chat_modes[chat_id] = "prime"
        lawyer_profiles.pop(chat_id, None)
        lawyer_avatar_chats.discard(chat_id)
        update_lawyer_avatar()
        ai_histories.pop(chat_id, None)

        if model_status == "not_started":
            chats_waiting_model.add(chat_id)
            threading.Thread(target=start_model_worker, daemon=True).start()
        elif model_status == "ready":
            bot.reply_to(
                message,
                "🧠 Прайм-режим включён. Нейросеть уже загружена — можешь писать."
            )
            return

        bot.reply_to(
            message,
            "🧠 Прайм-режим включён.\n\n"
            "⏳ Первый ответ придёт через 2–3 минуты — Маша собирается с мыслями "
            "(загружает нейросеть). Дальше будет отвечать быстрее."
        )
    except Exception as e:
        print(f"[prime error] {e}")

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/антипрайм")
def disable_prime_mode(message):
    try:
        chat_id = message.chat.id
        chat_modes.pop(chat_id, None)
        lawyer_profiles.pop(chat_id, None)
        lawyer_avatar_chats.discard(chat_id)
        update_lawyer_avatar()
        ai_histories.pop(chat_id, None)
        chats_waiting_model.discard(chat_id)
        bot.reply_to(message, random.choice(GAV_VARIANTS))
    except Exception as e:
        print(f"[anti-prime error] {e}")

@bot.message_handler(func=lambda msg: msg.text and get_lawyer_names(msg) is not None)
def toggle_lawyer_mode(message):
    try:
        chat_id = message.chat.id
        if chat_id in lawyer_profiles:
            chat_modes.pop(chat_id, None)
            lawyer_profiles.pop(chat_id, None)
            lawyer_avatar_chats.discard(chat_id)
            update_lawyer_avatar()
            ai_histories.pop(chat_id, None)
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
        ai_histories.pop(chat_id, None)
        if model_status == "not_started":
            threading.Thread(target=start_model_worker, daemon=True).start()
        bot.reply_to(message, f"⚖️ Режим юриста включён.")
    except Exception as e:
        print(f"[lawyer error] {e}")

@bot.message_handler(commands=['мат+'])
def enable_mat_filter(message):
    try:
        mat_filter_enabled[message.chat.id] = True
        bot.reply_to(message, "✅ Мат-фильтр **включён**.", parse_mode="Markdown")
    except Exception as e:
        print(f"[mat+ error] {e}")

@bot.message_handler(commands=['мат-'])
def disable_mat_filter(message):
    try:
        mat_filter_enabled[message.chat.id] = False
        bot.reply_to(message, "❌ Мат-фильтр **отключён**.", parse_mode="Markdown")
    except Exception as e:
        print(f"[mat- error] {e}")

@bot.message_handler(func=lambda msg: True)
def count_messages(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
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
                    warning = bot.send_message(chat_id, f"⚠️ Пользователь {message.from_user.first_name} использовал запрещённое слово. Все его сообщения будут удаляться в течение 1 минуты.")
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

            if model_status != "ready":
                bot.reply_to(message, "⏳ Маша ещё собирается с мыслями (загружает нейросеть). Попробуй через пару минут.")
                return

            send_local_ai_reply(
                message,
                ("Ты дружелюбная нейросеть. Отвечай на русском, максимум двумя короткими предложениями."),
                user_text,
            )
            return

        if mode == "lawyer":
            profile = lawyer_profiles.get(chat_id)
            if not profile:
                chat_modes.pop(chat_id, None)
                return
            if user_id == profile["defender_user_id"]:
                user_text = message.text or "Оппонент отправил сообщение без текста."
                identity_reply = get_bot_identity_reply(user_text)
                if identity_reply:
                    bot.reply_to(message, identity_reply)
                else:
                    send_local_ai_reply(
                        message,
                        (f"Ты жёсткий юридический защитник. Отвечай по-русски максимум двумя предложениями."),
                        user_text,
                        max_tokens=30,
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
    mp.set_start_method("spawn", force=True)

    health_thread = threading.Thread(target=run_health, daemon=True)
    health_thread.start()
    ping_thread = threading.Thread(target=self_ping_loop, daemon=True)
    ping_thread.start()

    print("Бот запущен...")
    run_bot()
