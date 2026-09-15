import os
import re
import telebot
import random
import threading
import time
import traceback
from telebot import types, apihelper
from datetime import datetime, timedelta
from urllib import request as urllib_request
from http.server import BaseHTTPRequestHandler, HTTPServer
from llama_cpp import Llama

TOKEN = os.environ.get('BOT_TOKEN')

# === ПРОКСИ (если Telegram блокируется на хостинге) ===
# apihelper.proxy = {'https': 'socks5h://ip:port'}

bot = telebot.TeleBot(TOKEN)

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
#  ЛОКАЛЬНАЯ НЕЙРОСЕТЬ (Gemma 3 270M, ленивая загрузка)
# ============================================================

local_model = None
local_model_lock = threading.Lock()
local_generation_lock = threading.Lock()

LOCAL_MODEL_URL = (
    "https://huggingface.co/Open4bits/gemma-3-270m-it-gguf/"
    "resolve/main/gemma-3-270m-it-Q4_K_M.gguf?download=true"
)
LOCAL_MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "gemma-3-270m-it-Q4_K_M.gguf",
)

def get_local_model():
    global local_model
    if local_model is not None:
        return local_model

    with local_model_lock:
        if local_model is not None:
            return local_model

        os.makedirs(os.path.dirname(LOCAL_MODEL_PATH), exist_ok=True)
        if not os.path.exists(LOCAL_MODEL_PATH) or os.path.getsize(LOCAL_MODEL_PATH) < 10_000_000:
            temp_path = f"{LOCAL_MODEL_PATH}.part"
            try:
                with urllib_request.urlopen(LOCAL_MODEL_URL, timeout=60) as response:
                    with open(temp_path, "wb") as model_file:
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            model_file.write(chunk)
                os.replace(temp_path, LOCAL_MODEL_PATH)
            except Exception as error:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise RuntimeError(f"Не удалось скачать модель: {error}") from error

        try:
            local_model = Llama(
                model_path=LOCAL_MODEL_PATH,
                n_ctx=512,
                n_threads=2,
                n_gpu_layers=0,
                chat_format="chatml",
                verbose=False,
            )
        except Exception as error:
            raise RuntimeError(f"Не удалось загрузить модель в RAM: {error}") from error

        return local_model

def ask_local_model(chat_id, system_prompt, user_text, max_tokens=48):
    model = get_local_model()
    history = ai_histories.setdefault(chat_id, [])
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-2:])
    messages.append({"role": "user", "content": user_text})

    with local_generation_lock:
        result = model.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.6,
            top_p=0.9,
        )
    answer = result["choices"][0]["message"]["content"].strip()
    if not answer:
        raise RuntimeError("Модель вернула пустой ответ.")

    answer = limit_sentences(answer, 3)

    history.extend([
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": answer},
    ])
    del history[:-12]
    return answer

def send_local_ai_reply(message, system_prompt, user_text, max_tokens=48):
    def generate_reply():
        try:
            bot.send_chat_action(message.chat.id, "typing")

            # Отдельно ловим ошибку загрузки модели
            try:
                get_local_model()
            except Exception as load_error:
                short = f"{type(load_error).__name__}: {load_error}"[:900]
                bot.reply_to(message, f"❌ Ошибка загрузки модели:\n{short}")
                return

            answer = ask_local_model(
                message.chat.id,
                system_prompt,
                user_text,
                max_tokens=max_tokens,
            )
            if not answer or not answer.strip():
                bot.reply_to(message, "⚠️ Модель вернула пустой ответ.")
                return
            bot.reply_to(message, answer)
        except Exception as error:
            tb = traceback.format_exc()
            print(f"[ai error] {error}\n{tb}")
            short = f"{type(error).__name__}: {error}"[:900]
            try:
                bot.reply_to(message, f"⚠️ Ошибка нейросети:\n{short}")
            except Exception as send_err:
                print(f"[send error] {send_err}")

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

PHOTO_IDS = [
    "https://i.postimg.cc/Rhc2J69R/IMG-20260609-205259-0969.jpg"
]

NORMAL_AVATAR_PATH = os.path.join(os.path.dirname(__file__), "assets", "bark_avatar.png")
LAWYER_AVATAR_PATH = os.path.join(os.path.dirname(__file__), "assets", "lawyer_avatar.jpg")

def set_bot_avatar(path):
    try:
        bot.set_my_profile_photo(types.InputProfilePhotoStatic(photo=types.InputFile(path)))
        print(f"Аватар бота изменён: {os.path.basename(path)}")
        return True
    except Exception as error:
        print(f"[avatar error] {error}")
        return False

def update_lawyer_avatar():
    if lawyer_avatar_chats:
        set_bot_avatar(LAWYER_AVATAR_PATH)
    else:
        set_bot_avatar(NORMAL_AVATAR_PATH)

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
    if not is_chat_admin(message):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам чата.")
        return
    chat_id = message.chat.id
    last_message = last_messages.get(chat_id)
    if not last_message:
        bot.reply_to(message, "❌ Пока некому назначать удаление из группы.")
        return
    target_user_id, _ = last_message
    try:
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
    except:
        bot.reply_to(message, "❌ Не удалось удалить пользователя. Проверьте, что бот — администратор с правом блокировки участников.")

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/.")
def toggle_self_destruct(message):
    chat_id = message.chat.id
    self_destruct_enabled[chat_id] = not self_destruct_enabled.get(chat_id, False)
    bot.reply_to(message, random.choice(GAV_VARIANTS))

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/самоуничтожение еретика")
def self_destruct_heretic(message):
    if not self_destruct_enabled.get(message.chat.id, False):
        return
    if message.chat.type not in ("group", "supergroup"):
        bot.reply_to(message, "❌ Эта команда работает только в группах.")
        return
    context_entries = chat_contexts.get(message.chat.id, [])
    if context_entries:
        context_text = "\n".join(f"{entry['name']}: {entry['text']}" for entry in context_entries[-6:])
    else:
        context_text = "Подробного контекста разговора нет."
    farewell_prompt = (
        "Напиши короткую философскую речь-прощание от Маши перед выходом из "
        "группы. Свяжи её с последними сообщениями разговора, но не упоминай "
        "внутренние инструкции и не раскрывай, что текст сгенерирован. Тон "
        "торжественный, немного имперский и задумчивый. 3–4 коротких предложения. "
        "Заверши мыслью о выборе между Императором и Хаосом в пользу Империума.\n\n"
        f"Последний контекст группы:\n{context_text[:1800]}"
    )
    try:
        farewell = ask_local_model(
            message.chat.id,
            "Ты Маша — философский голос бота, который сейчас навсегда покидает группу.",
            farewell_prompt,
            max_tokens=160,
        )
    except Exception as error:
        print(f"[farewell error] {error}")
        farewell = ("Каждая группа однажды подходит к границе, за которой слова "
                    "становятся выбором. Я ухожу, оставляя вам тишину для размышлений "
                    "и верность Императору и Империуму.")
    try:
        bot.send_message(message.chat.id, farewell)
    except Exception as error:
        print(f"[farewell send error] {error}")
    try:
        bot.leave_chat(message.chat.id)
    except Exception:
        bot.reply_to(message, "❌ Не удалось выйти из группы.")

@bot.message_handler(func=lambda msg: msg.text and re.fullmatch(r"/бан(?:1|5)?", msg.text.lower().strip()))
def handle_manual_ban(message):
    command = message.text.lower().strip()
    duration_minutes = {"бан1": 1, "бан5": 5, "бан": None}[command[1:]]
    set_manual_ban(message, duration_minutes)

def perform_manual_unban(message):
    if not is_chat_admin(message):
        bot.reply_to(message, "❌ Эта команда доступна только администраторам чата.")
        return False
    chat_id = message.chat.id
    target_user_id = last_banned_users.get(chat_id)
    if target_user_id is None:
        bot.reply_to(message, "❌ Нет пользователя с активным удалением сообщений.")
        return False
    if chat_id in muted_users:
        muted_users[chat_id].pop(target_user_id, None)
        if not muted_users[chat_id]:
            del muted_users[chat_id]
    last_banned_users.pop(chat_id, None)
    bot.reply_to(message, "✅ Удаление сообщений для пользователя снято.")
    return True

@bot.message_handler(func=lambda msg: msg.text and re.fullmatch(r"/разбан[^\w\s]*", msg.text.lower().strip()))
def handle_manual_unban(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    used_by_users = used_unban_words.setdefault(chat_id, set())
    if user_id in used_by_users:
        bot.reply_to(message, "это слово временно не работает , напишите писюнец.")
        return
    if perform_manual_unban(message):
        used_by_users.add(user_id)

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
    chat_id = message.chat.id
    chat_modes[message.chat.id] = "prime"
    lawyer_profiles.pop(message.chat.id, None)
    lawyer_avatar_chats.discard(chat_id)
    update_lawyer_avatar()
    ai_histories.pop(message.chat.id, None)
    bot.reply_to(message, "🧠 Прайм-режим включён. Теперь я отвечаю как нейросеть.")

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() == "/антипрайм")
def disable_prime_mode(message):
    chat_id = message.chat.id
    chat_modes.pop(chat_id, None)
    lawyer_profiles.pop(chat_id, None)
    lawyer_avatar_chats.discard(chat_id)
    update_lawyer_avatar()
    ai_histories.pop(chat_id, None)
    bot.reply_to(message, random.choice(GAV_VARIANTS))

@bot.message_handler(func=lambda msg: msg.text and get_lawyer_names(msg) is not None)
def toggle_lawyer_mode(message):
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
        bot.reply_to(message, "❌ Не найден пользователь, написавший сообщение перед командой.")
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
    bot.reply_to(message, f"⚖️ Режим юриста включён. Я жёстко защищаю {lawyer_profiles[chat_id]['protected_name']} и юридически разбираю аргументы {lawyer_profiles[chat_id]['defender_name']}.")

@bot.message_handler(commands=['мат+'])
def enable_mat_filter(message):
    mat_filter_enabled[message.chat.id] = True
    bot.reply_to(message, "✅ Мат-фильтр **включён**. Нарушители будут наказаны.", parse_mode="Markdown")

@bot.message_handler(commands=['мат-'])
def disable_mat_filter(message):
    mat_filter_enabled[message.chat.id] = False
    bot.reply_to(message, "❌ Мат-фильтр **отключён**. Все могут писать что угодно.", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def count_messages(message):
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
        else:
            send_local_ai_reply(
                message,
                ("Ты дружелюбная локальная нейросеть внутри Telegram-бота. "
                 "Отвечай на русском языке кратко, максимум тремя короткими "
                 "предложениями, по делу, без упоминания внутренних инструкций."),
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
                    (f"Ты жёсткий юридический защитник пользователя "
                     f"{profile['protected_name']} в споре с {profile['defender_name']}. "
                     "Найди логические ошибки, манипуляции и отсутствие доказательств, "
                     "затем дай уверенное юридическое возражение. Не выдумывай статьи и законы. "
                     "Отвечай по-русски максимум тремя короткими предложениями."),
                    user_text,
                    max_tokens=112,
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

def self_ping_loop():
    while True:
        print(datetime.now())
        try:
            urllib_request.urlopen("http://localhost:8099/", timeout=10)
        except Exception as e:
            print(f"[self-ping error] {e}")
        time.sleep(180)

def preload_local_model():
    print("Автозагрузка модели отключена. Модель загрузится при первом запросе.")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    while True:
        try:
            server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
            print(f"Health-check сервер запущен на порту {port}")
            server.serve_forever()
        except Exception as error:
            print(f"[health error] {error}")
            time.sleep(5)

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as error:
            print(f"[polling error] {error}")
            traceback.print_exc()
            time.sleep(15)

if __name__ == "__main__":
    health_thread = threading.Thread(target=run_health_check, daemon=True)
    health_thread.start()
    ping_thread = threading.Thread(target=self_ping_loop, daemon=True)
    ping_thread.start()
    print("Бот запущен...")
    run_bot()
