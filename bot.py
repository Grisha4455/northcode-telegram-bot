# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode
import config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(PROJECT_TYPE, DESCRIPTION, EXAMPLES, DEADLINE, BUDGET, CONTACT) = range(6)


class OrderBot:
    def __init__(self):
        self.application = None

    # --------- /start ---------
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("Оставить заявку", callback_data='start_order')],
            [InlineKeyboardButton("Подробнее", callback_data='details')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            config.WELCOME_TEXT.replace("NorthCode", "Wiradcode"),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    # --------- CALLBACK BUTTONS ---------
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == 'start_order':
            return await self.start_order(update, context)
        elif query.data == 'details':
            return await self.show_details(update, context)
        elif query.data == 'back_to_menu':
            return await self.back_to_menu(update, context)

    async def show_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query

        keyboard = [
            [InlineKeyboardButton("Оставить заявку", callback_data='start_order')],
            [InlineKeyboardButton("Назад в меню", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            config.DETAILS_TEXT.replace("NorthCode", "Wiradcode"),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    async def back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query

        keyboard = [
            [InlineKeyboardButton("Оставить заявку", callback_data='start_order')],
            [InlineKeyboardButton("Подробнее", callback_data='details')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            config.WELCOME_TEXT.replace("NorthCode", "Wiradcode"),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    # --------- ORDER FLOW ---------
    async def start_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query

        context.user_data['order'] = {
            'user_id': query.from_user.id,
            'username': query.from_user.username,
            'first_name': query.from_user.first_name,
            'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M")
        }

        keyboard = [[ptype] for ptype in config.PROJECT_TYPES]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await query.edit_message_text(
            config.ORDER_START_TEXT.replace("NorthCode", "Wiradcode"),
            parse_mode=ParseMode.HTML
        )
        await query.message.reply_text(
            "Выберите тип проекта или напишите свой вариант:",
            reply_markup=reply_markup
        )

        return PROJECT_TYPE

    async def get_project_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['order']['project_type'] = update.message.text

        await update.message.reply_text(
            f"<b>Вопрос 2/6:</b> {config.QUESTIONS['description']}",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )
        return DESCRIPTION

    async def get_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['order']['description'] = update.message.text

        await update.message.reply_text(
            f"<b>Вопрос 3/6:</b> {config.QUESTIONS['examples']}",
            parse_mode=ParseMode.HTML
        )
        return EXAMPLES

    async def get_examples(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['order']['examples'] = update.message.text

        await update.message.reply_text(
            f"<b>Вопрос 4/6:</b> {config.QUESTIONS['deadline']}",
            parse_mode=ParseMode.HTML
        )
        return DEADLINE

    async def get_deadline(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['order']['deadline'] = update.message.text

        await update.message.reply_text(
            f"<b>Вопрос 5/6:</b> {config.QUESTIONS['budget']}",
            parse_mode=ParseMode.HTML
        )
        return BUDGET

    async def get_budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['order']['budget'] = update.message.text

        await update.message.reply_text(
            f"<b>Вопрос 6/6:</b> {config.QUESTIONS['contact']}",
            parse_mode=ParseMode.HTML
        )
        return CONTACT

    async def get_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['order']['contact'] = update.message.text

        order_text = self.format_order(context.user_data['order'])

        await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID,
            text=order_text,
            parse_mode=ParseMode.HTML
        )

        keyboard = [[InlineKeyboardButton("Назад в меню", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "<b>Заявка успешно отправлена!</b>\n\n"
            "Команда <b>Wiradcode</b> свяжется с вами в ближайшее время.",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

        return ConversationHandler.END

    def format_order(self, order):
        return f"""
<b>Новая заявка — Wiradcode</b>

Дата: {order['timestamp']}

Имя: {order.get('first_name', 'Не указано')}
Username: @{order.get('username', 'нет')}
ID: {order['user_id']}

Тип проекта:
{order['project_type']}

Описание:
{order['description']}

Примеры:
{order['examples']}

Сроки:
{order['deadline']}

Бюджет:
{order['budget']}

Контакты:
{order['contact']}
""".strip()

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Заявка отменена. Для начала нажмите /start",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    # --------- RUN ---------
    def run(self):
        builder = Application.builder().token(config.BOT_TOKEN)

        if config.PROXY_URL:
            builder.proxy(config.PROXY_URL)

        self.application = builder.build()

        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_order, pattern='^start_order$')],
            states={
                PROJECT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_project_type)],
                DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_description)],
                EXAMPLES: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_examples)],
                DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_deadline)],
                BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_budget)],
                CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_contact)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
            per_message=False,
        )

        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(conv_handler)
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

        logger.info("Bot started")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    bot = OrderBot()
    bot.run()
