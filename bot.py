import os
import json
import re
from datetime import datetime, date
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN", "8643925833:AAGlky5L6iytMziWdd65QTcGQjPPExuMiw0")
DATA_FILE = "data.json"

CATEGORIES = {
    "benzin": "Бензин",
    "бензин": "Бензин",
    "fuel": "Бензин",
    "vinetka": "Виnetка",
    "виnetка": "Виnetка",
    "vinетка": "Виnetка",
    "kredit": "Кредит",
    "кредит": "Кредит",
    "drug": "Кредит друга",
    "друг": "Кредит друга",
    "mama": "Маме",
    "mame": "Маме",
    "маме": "Маме",
    "маме": "Маме",
    "маме дал": "Маме",
    "eda": "Еда",
    "еда": "Еда",
    "food": "Еда",
    "restoran": "Еда",
    "kafe": "Еда",
    "одежда": "Одежда",
    "odezhda": "Одежда",
    "odejda": "Одежда",
    "коммуналка": "Коммуналка",
    "kommunalka": "Коммуналка",
    "gaz": "Коммуналка",
    "tok": "Коммуналка",
    "svet": "Коммуналка",
    "avto": "Авто",
    "авто": "Авто",
    "radiator": "Авто",
    "mashina": "Авто",
    "medicina": "Медицина",
    "doktor": "Медицина",
    "apteka": "Медицина",
    "salary": "Зарплата",
    "zarplata": "Зарплата",
    "зарплата": "Зарплата",
    "maosh": "Зарплата",
    "получил": "Доход",
    "poluchil": "Доход",
    "дал": "Перевод",
    "dal": "Перевод",
}

INCOME_KEYWORDS = ["получил", "poluchil", "пришло", "prishlo", "зарплата", "zarplata", "salary", "maosh", "kirim", "доход", "income"]
EXPENSE_KEYWORDS = ["потратил", "potratil", "купил", "купил", "kupit", "dal", "дал", "заплатил", "zaplatil", "rashod", "расход", "chiqim"]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_data(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {}
    return data[uid]

def parse_amount(text):
    text_lower = text.lower().replace(" ", "")
    patterns = [
        (r"(\d+(?:\.\d+)?)млн", lambda m: float(m.group(1)) * 1_000_000),
        (r"(\d+(?:\.\d+)?)mln", lambda m: float(m.group(1)) * 1_000_000),
        (r"(\d+(?:\.\d+)?)м\b", lambda m: float(m.group(1)) * 1_000_000),
        (r"(\d+(?:\.\d+)?)к\b", lambda m: float(m.group(1)) * 1_000),
        (r"(\d+(?:\.\d+)?)k\b", lambda m: float(m.group(1)) * 1_000),
        (r"(\d+(?:\.\d+)?)тыс", lambda m: float(m.group(1)) * 1_000),
        (r"(\d+(?:\.\d+)?)tis", lambda m: float(m.group(1)) * 1_000),
        (r"(\d[\d\s,]*\d|\d+)", lambda m: float(m.group(1).replace(",", "").replace(" ", ""))),
    ]
    for pattern, converter in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                return int(converter(match))
            except:
                pass
    return None

def detect_category(text):
    text_lower = text.lower()
    for keyword, category in CATEGORIES.items():
        if keyword in text_lower:
            return category
    return "Другое"

def detect_type(text):
    text_lower = text.lower()
    for kw in INCOME_KEYWORDS:
        if kw in text_lower:
            return "income"
    for kw in EXPENSE_KEYWORDS:
        if kw in text_lower:
            return "expense"
    return "expense"

def fmt(n):
    return f"{int(n):,}".replace(",", " ") + " сум"

def get_month_key(dt=None):
    if dt is None:
        dt = date.today()
    return dt.strftime("%Y-%m")

def get_day_key(dt=None):
    if dt is None:
        dt = date.today()
    return dt.strftime("%Y-%m-%d")

def month_name(key):
    months = {
        "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель",
        "05": "Май", "06": "Июнь", "07": "Июль", "08": "Август",
        "09": "Сентябрь", "10": "Октябрь", "11": "Ноябрь", "12": "Декабрь"
    }
    y, m = key.split("-")
    return f"{months[m]} {y}"

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("📊 Итог месяца"), KeyboardButton("📅 По дням")],
    [KeyboardButton("📈 Доходы"), KeyboardButton("📉 Расходы")],
    [KeyboardButton("🗓 История"), KeyboardButton("❓ Помощь")],
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"Привет, {name}! 👋\n\n"
        "Я твой личный финансовый бот.\n\n"
        "Просто пиши мне что потратил или получил:\n"
        "• *потратил 675к на бензин*\n"
        "• *получил зарплату 26млн*\n"
        "• *дал маме 2.5млн*\n"
        "• *купил одежду за 1.5млн*\n\n"
        "Я всё запишу и посчитаю 📝",
        parse_mode="Markdown",
        reply_markup=main_keyboard
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == "📊 Итог месяца":
        await show_month_summary(update, user_id)
        return
    if text == "📅 По дням":
        await show_by_days(update, user_id)
        return
    if text == "📈 Доходы":
        await show_incomes(update, user_id)
        return
    if text == "📉 Расходы":
        await show_expenses(update, user_id)
        return
    if text == "🗓 История":
        await show_history(update, user_id)
        return
    if text == "❓ Помощь":
        await show_help(update)
        return

    amount = parse_amount(text)
    if not amount:
        await update.message.reply_text(
            "Не нашёл сумму 🤔\n\n"
            "Попробуй так:\n"
            "• *потратил 675к на бензин*\n"
            "• *получил 26млн зарплата*\n"
            "• *купил еду за 150000*",
            parse_mode="Markdown"
        )
        return

    entry_type = detect_type(text)
    category = detect_category(text)
    today = date.today()
    day_key = get_day_key(today)
    month_key = get_month_key(today)

    data = load_data()
    user_data = get_user_data(data, user_id)

    if month_key not in user_data:
        user_data[month_key] = {}
    if day_key not in user_data[month_key]:
        user_data[month_key][day_key] = []

    entry = {
        "amount": amount,
        "type": entry_type,
        "category": category,
        "note": text,
        "time": datetime.now().strftime("%H:%M")
    }
    user_data[month_key][day_key].append(entry)
    save_data(data)

    emoji = "💰" if entry_type == "income" else "💸"
    type_text = "Доход" if entry_type == "income" else "Расход"

    await update.message.reply_text(
        f"{emoji} Записал!\n\n"
        f"Тип: {type_text}\n"
        f"Сумма: {fmt(amount)}\n"
        f"Категория: {category}\n"
        f"Дата: {today.strftime('%d.%m.%Y')}",
        reply_markup=main_keyboard
    )

async def show_month_summary(update, user_id):
    data = load_data()
    user_data = get_user_data(data, user_id)
    month_key = get_month_key()

    if month_key not in user_data or not user_data[month_key]:
        await update.message.reply_text("За этот месяц пока нет записей 📭", reply_markup=main_keyboard)
        return

    total_income = 0
    total_expense = 0
    cat_expenses = {}

    for day_entries in user_data[month_key].values():
        for e in day_entries:
            if e["type"] == "income":
                total_income += e["amount"]
            else:
                total_expense += e["amount"]
                cat = e["category"]
                cat_expenses[cat] = cat_expenses.get(cat, 0) + e["amount"]

    balance = total_income - total_expense
    bal_emoji = "🟢" if balance >= 0 else "🔴"

    text = f"📊 *{month_name(month_key)}*\n\n"
    text += f"💰 Доходы: {fmt(total_income)}\n"
    text += f"💸 Расходы: {fmt(total_expense)}\n"
    text += f"{bal_emoji} Остаток: {fmt(balance)}\n\n"

    if cat_expenses:
        text += "📂 *По категориям:*\n"
        for cat, amt in sorted(cat_expenses.items(), key=lambda x: -x[1]):
            pct = (amt / total_expense * 100) if total_expense > 0 else 0
            text += f"  • {cat}: {fmt(amt)} ({pct:.0f}%)\n"

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard)

async def show_by_days(update, user_id):
    data = load_data()
    user_data = get_user_data(data, user_id)
    month_key = get_month_key()

    if month_key not in user_data or not user_data[month_key]:
        await update.message.reply_text("За этот месяц пока нет записей 📭", reply_markup=main_keyboard)
        return

    text = f"📅 *{month_name(month_key)} — по дням:*\n\n"

    for day_key in sorted(user_data[month_key].keys(), reverse=True):
        entries = user_data[month_key][day_key]
        day_income = sum(e["amount"] for e in entries if e["type"] == "income")
        day_expense = sum(e["amount"] for e in entries if e["type"] == "expense")
        day_dt = datetime.strptime(day_key, "%Y-%m-%d")
        day_str = day_dt.strftime("%d.%m")

        text += f"*{day_str}*\n"
        for e in entries:
            emoji = "💰" if e["type"] == "income" else "💸"
            text += f"  {emoji} {e['category']}: {fmt(e['amount'])}\n"
        if day_income > 0:
            text += f"  ↑ Итого доход: {fmt(day_income)}\n"
        if day_expense > 0:
            text += f"  ↓ Итого расход: {fmt(day_expense)}\n"
        text += "\n"

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard)

async def show_incomes(update, user_id):
    data = load_data()
    user_data = get_user_data(data, user_id)
    month_key = get_month_key()

    entries = []
    if month_key in user_data:
        for day_entries in user_data[month_key].values():
            entries += [e for e in day_entries if e["type"] == "income"]

    if not entries:
        await update.message.reply_text("Доходов за этот месяц нет 📭", reply_markup=main_keyboard)
        return

    total = sum(e["amount"] for e in entries)
    text = f"📈 *Доходы — {month_name(month_key)}:*\n\n"
    for e in entries:
        text += f"💰 {e['category']}: {fmt(e['amount'])}\n"
    text += f"\n*Итого: {fmt(total)}*"

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard)

async def show_expenses(update, user_id):
    data = load_data()
    user_data = get_user_data(data, user_id)
    month_key = get_month_key()

    entries = []
    if month_key in user_data:
        for day_entries in user_data[month_key].values():
            entries += [e for e in day_entries if e["type"] == "expense"]

    if not entries:
        await update.message.reply_text("Расходов за этот месяц нет 📭", reply_markup=main_keyboard)
        return

    total = sum(e["amount"] for e in entries)
    text = f"📉 *Расходы — {month_name(month_key)}:*\n\n"
    for e in entries:
        text += f"💸 {e['category']}: {fmt(e['amount'])}\n"
    text += f"\n*Итого: {fmt(total)}*"

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard)

async def show_history(update, user_id):
    data = load_data()
    user_data = get_user_data(data, user_id)

    if not user_data:
        await update.message.reply_text("Истории пока нет 📭", reply_markup=main_keyboard)
        return

    text = "🗓 *История по месяцам:*\n\n"
    for month_key in sorted(user_data.keys(), reverse=True):
        total_income = 0
        total_expense = 0
        for day_entries in user_data[month_key].values():
            for e in day_entries:
                if e["type"] == "income":
                    total_income += e["amount"]
                else:
                    total_expense += e["amount"]
        balance = total_income - total_expense
        bal_emoji = "🟢" if balance >= 0 else "🔴"
        text += f"*{month_name(month_key)}*\n"
        text += f"  💰 {fmt(total_income)}  💸 {fmt(total_expense)}  {bal_emoji} {fmt(balance)}\n\n"

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard)

async def show_help(update):
    await update.message.reply_text(
        "❓ *Как пользоваться:*\n\n"
        "*Расходы:*\n"
        "• потратил 675к на бензин\n"
        "• купил одежду за 1.5млн\n"
        "• дал маме 2500000\n"
        "• заплатил за коммуналку 265к\n\n"
        "*Доходы:*\n"
        "• получил зарплату 26млн\n"
        "• пришло 5млн от папы\n\n"
        "*Форматы суммы:*\n"
        "• 675к = 675,000\n"
        "• 2.5млн = 2,500,000\n"
        "• 26000000 = 26,000,000\n\n"
        "*Кнопки меню:*\n"
        "📊 Итог месяца — общая сводка\n"
        "📅 По дням — детализация по дням\n"
        "📈 Доходы — все доходы\n"
        "📉 Расходы — все расходы\n"
        "🗓 История — прошлые месяцы",
        parse_mode="Markdown",
        reply_markup=main_keyboard
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
