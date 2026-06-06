import os
import json
import re
from datetime import datetime, date
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN", "8643925833:AAGlky5L6iytMziWdd65QTcGQjPPExuMiw0")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://finance-bot-production-7055.up.railway.app")
DATA_FILE = "data.json"

EXPENSE_CATEGORIES = [
    "Еда/рестораны","Бензин","Авто","Семья","Одежда","Коммуналка",
    "Кредиты","Личное","Развлечения","Здоровье","Работа/бизнес",
    "На будущее","На поездку","Подарки","Ремонт","Электроника",
    "Интернет/связь","Подписки","Дал в долг","Другое"
]
INCOME_CATEGORIES = ["Зарплата","От папы","Вернули долг","Другой доход"]

CATEGORY_MAP = {
    "eda":"Еда/рестораны","еда":"Еда/рестораны","food":"Еда/рестораны","restoran":"Еда/рестораны","kafe":"Еда/рестораны","ovqat":"Еда/рестораны","tushlik":"Еда/рестораны",
    "benzin":"Бензин","бензин":"Бензин","fuel":"Бензин","yoqilgi":"Бензин",
    "avto":"Авто","авто":"Авто","mashina":"Авто","radiator":"Авто","servis":"Авто",
    "mama":"Семья","mame":"Семья","маме":"Семья","папе":"Семья","papa":"Семья","oila":"Семья",
    "odezhda":"Одежда","одежда":"Одежда","odejda":"Одежда","kiyim":"Одежда",
    "kommunalka":"Коммуналка","коммуналка":"Коммуналка","gaz":"Коммуналка","tok":"Коммуналка","svet":"Коммуналка",
    "kredit":"Кредиты","кредит":"Кредиты","qarz":"Кредиты",
    "lichno":"Личное","личное":"Личное","себе":"Личное",
    "kino":"Развлечения","развлечения":"Развлечения","games":"Развлечения",
    "vrach":"Здоровье","doktor":"Здоровье","apteka":"Здоровье","здоровье":"Здоровье",
    "trip":"На поездку","sayohat":"На поездку","дорога":"На поездку",
    "podarok":"Подарки","подарок":"Подарки","sovga":"Подарки",
    "remont":"Ремонт","ремонт":"Ремонт",
    "telefon":"Электроника","noutbuk":"Электроника","электроника":"Электроника",
    "internet":"Интернет/связь","ucell":"Интернет/связь","beeline":"Интернет/связь","связь":"Интернет/связь",
    "netflix":"Подписки","spotify":"Подписки","подписка":"Подписки",
    "dal":"Дал в долг","дал":"Дал в долг",
    "zarplata":"Зарплата","зарплата":"Зарплата","maosh":"Зарплата","salary":"Зарплата",
    "otklad":"На будущее","коплю":"На будущее","jamgarma":"На будущее",
    "vernuli":"Вернули долг","вернули":"Вернули долг","qaytardi":"Вернули долг",
}

INCOME_KEYWORDS = ["получил","poluchil","пришло","зарплата","zarplata","salary","maosh","kirim","доход","вернули","vernuli"]
EXPENSE_KEYWORDS = ["потратил","potratil","купил","dal","дал","заплатил","zaplatil","rashod","расход","chiqim","otklad","коплю"]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

def get_user_data(data,user_id):
    uid=str(user_id)
    if uid not in data: data[uid]={}
    return data[uid]

def parse_amount(text):
    t = text.lower()
    patterns = [
        (r"(\d+(?:[.,]\d+)?)\s*млн", lambda m: float(m.group(1).replace(",",".")) * 1_000_000),
        (r"(\d+(?:[.,]\d+)?)\s*mln", lambda m: float(m.group(1).replace(",",".")) * 1_000_000),
        (r"(\d+(?:[.,]\d+)?)\s*м\b", lambda m: float(m.group(1).replace(",",".")) * 1_000_000),
        (r"(\d+(?:[.,]\d+)?)\s*тыс", lambda m: float(m.group(1).replace(",",".")) * 1_000),
        (r"(\d+(?:[.,]\d+)?)\s*tis", lambda m: float(m.group(1).replace(",",".")) * 1_000),
        (r"(\d+(?:[.,]\d+)?)\s*к", lambda m: float(m.group(1).replace(",",".")) * 1_000),
        (r"(\d+(?:[.,]\d+)?)\s*k", lambda m: float(m.group(1).replace(",",".")) * 1_000),
        (r"(\d[\d\s]*\d|\d+)", lambda m: float(m.group(1).replace(" ",""))),
    ]
    for pattern, converter in patterns:
        match = re.search(pattern, t)
        if match:
            try: return int(converter(match))
            except: pass
    return None

def detect_type(text):
    t=text.lower()
    for kw in INCOME_KEYWORDS:
        if kw in t: return "income"
    for kw in EXPENSE_KEYWORDS:
        if kw in t: return "expense"
    return "expense"

def detect_category(text,entry_type):
    t=text.lower()
    for keyword,category in CATEGORY_MAP.items():
        if keyword in t:
            if entry_type=="income" and category in INCOME_CATEGORIES: return category
            elif entry_type=="expense" and category in EXPENSE_CATEGORIES: return category
    return "Зарплата" if entry_type=="income" else "Другое"

def fmt(n): return f"{int(n):,}".replace(","," ")+" сум"
def get_month_key(): return date.today().strftime("%Y-%m")
def get_day_key(): return date.today().strftime("%Y-%m-%d")
def month_name(key):
    months={"01":"Январь","02":"Февраль","03":"Март","04":"Апрель","05":"Май","06":"Июнь","07":"Июль","08":"Август","09":"Сентябрь","10":"Октябрь","11":"Ноябрь","12":"Декабрь"}
    y,m=key.split("-")
    return f"{months[m]} {y}"

def get_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📊 Открыть приложение",web_app=WebAppInfo(url=WEBAPP_URL))],
        [KeyboardButton("📈 Итог месяца"),KeyboardButton("📅 По дням")],
        [KeyboardButton("💰 Доходы"),KeyboardButton("💸 Расходы")],
        [KeyboardButton("🗓 История"),KeyboardButton("❓ Помощь")],
    ],resize_keyboard=True)

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    name=update.effective_user.first_name
    await update.message.reply_text(
        f"Салом, {name}! 👋\n\nПросто пиши что потратил или получил:\n"
        "• *потратил 675к бензин*\n• *получил зарплату 26млн*\n• *дал маме 2.5млн*\n\n"
        "Или открой приложение кнопкой ниже 👇",
        parse_mode="Markdown",reply_markup=get_keyboard()
    )

async def handle_message(update:Update,context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text.strip()
    user_id=update.effective_user.id
    if text=="📈 Итог месяца": await show_summary(update,user_id); return
    if text=="📅 По дням": await show_days(update,user_id); return
    if text=="💰 Доходы": await show_type(update,user_id,"income"); return
    if text=="💸 Расходы": await show_type(update,user_id,"expense"); return
    if text=="🗓 История": await show_history(update,user_id); return
    if text=="❓ Помощь": await show_help(update); return
    amount=parse_amount(text)
    if not amount:
        await update.message.reply_text("Сумма топилмади 🤔\n\nМисол:\n• *потратил 675к бензин*\n• *получил зарплату 26млн*",parse_mode="Markdown",reply_markup=get_keyboard())
        return
    entry_type=detect_type(text)
    category=detect_category(text,entry_type)
    today=date.today()
    mk=get_month_key(); dk=get_day_key()
    data=load_data(); ud=get_user_data(data,user_id)
    if mk not in ud: ud[mk]={}
    if dk not in ud[mk]: ud[mk][dk]=[]
    ud[mk][dk].append({"id":int(datetime.now().timestamp()*1000),"amount":amount,"type":entry_type,"category":category,"note":text,"time":datetime.now().strftime("%H:%M"),"date":today.strftime("%d.%m.%Y")})
    save_data(data)
    emoji="💰" if entry_type=="income" else "💸"
    await update.message.reply_text(f"{emoji} Записал!\n\nТип: {'Доход' if entry_type=='income' else 'Расход'}\nСумма: {fmt(amount)}\nКатегория: {category}\nДата: {today.strftime('%d.%m.%Y')}",reply_markup=get_keyboard())

async def show_summary(update,user_id):
    data=load_data(); ud=get_user_data(data,user_id); mk=get_month_key()
    if mk not in ud or not ud[mk]: await update.message.reply_text("Бу ойда ҳали ёзувлар йўқ 📭"); return
    inc=exp=0; cats={}
    for d in ud[mk].values():
        for e in d:
            if e["type"]=="income": inc+=e["amount"]
            else: exp+=e["amount"]; cats[e["category"]]=cats.get(e["category"],0)+e["amount"]
    bal=inc-exp; be="🟢" if bal>=0 else "🔴"
    t=f"📊 *{month_name(mk)}*\n\n💰 Доходы: {fmt(inc)}\n💸 Расходы: {fmt(exp)}\n{be} Остаток: {fmt(bal)}\n\n📂 *По категориям:*\n"
    for c,a in sorted(cats.items(),key=lambda x:-x[1]):
        t+=f"  • {c}: {fmt(a)} ({a/exp*100:.0f}%)\n" if exp>0 else f"  • {c}: {fmt(a)}\n"
    await update.message.reply_text(t,parse_mode="Markdown")

async def show_days(update,user_id):
    data=load_data(); ud=get_user_data(data,user_id); mk=get_month_key()
    if mk not in ud or not ud[mk]: await update.message.reply_text("Бу ойда ҳали ёзувлар йўқ 📭"); return
    t=f"📅 *{month_name(mk)}:*\n\n"
    for dk in sorted(ud[mk].keys(),reverse=True):
        entries=ud[mk][dk]; ds=datetime.strptime(dk,"%Y-%m-%d").strftime("%d.%m")
        t+=f"*{ds}*\n"
        for e in entries:
            t+=f"  {'💰' if e['type']=='income' else '💸'} {e['category']}: {fmt(e['amount'])}\n"
        t+="\n"
    await update.message.reply_text(t,parse_mode="Markdown")

async def show_type(update,user_id,etype):
    data=load_data(); ud=get_user_data(data,user_id); mk=get_month_key()
    entries=[e for d in ud.get(mk,{}).values() for e in d if e["type"]==etype]
    if not entries: await update.message.reply_text("Ёзувлар йўқ 📭"); return
    total=sum(e["amount"] for e in entries)
    emoji="💰" if etype=="income" else "💸"
    label="Доходы" if etype=="income" else "Расходы"
    t=f"{emoji} *{label} — {month_name(mk)}:*\n\n"
    for e in entries: t+=f"• {e['category']}: {fmt(e['amount'])} ({e.get('date','')})\n"
    t+=f"\n*Итого: {fmt(total)}*"
    await update.message.reply_text(t,parse_mode="Markdown")

async def show_history(update,user_id):
    data=load_data(); ud=get_user_data(data,user_id)
    if not ud: await update.message.reply_text("Тарих ҳали йўқ 📭"); return
    t="🗓 *История:*\n\n"
    for mk in sorted(ud.keys(),reverse=True):
        inc=exp=0
        for d in ud[mk].values():
            for e in d:
                if e["type"]=="income": inc+=e["amount"]
                else: exp+=e["amount"]
        bal=inc-exp; be="🟢" if bal>=0 else "🔴"
        t+=f"*{month_name(mk)}*\n  💰{fmt(inc)}  💸{fmt(exp)}  {be}{fmt(bal)}\n\n"
    await update.message.reply_text(t,parse_mode="Markdown")

async def show_help(update):
    await update.message.reply_text(
        "❓ *Как пользоваться:*\n\n*Расходы:*\n• потратил 675к бензин\n• купил одежду 1.5млн\n• дал маме 2500000\n• отложил 1млн на поездку\n\n"
        "*Доходы:*\n• получил зарплату 26млн\n• вернули долг 500к\n\n"
        "*Форматы:*\n• 675к = 675,000\n• 2.5млн = 2,500,000",
        parse_mode="Markdown",reply_markup=get_keyboard()
    )

def main():
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__=="__main__":
    main()