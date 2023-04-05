import json
import os

from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        'Привет! Я бот для викторин!',
        reply_markup=reply_markup
    )


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def main():
    env = Env()
    env.read_env()
    folder_name = 'questions'
    files_names = os.listdir(path=folder_name)
    questions = {}
    for file_name in files_names:
        file_path = os.path.join(folder_name, file_name)
        with open(file_path, mode='r', encoding='KOI8-R') as file:
            question_lines = False
            question_text = ''
            answer_lines = False
            answer_text = ''
            for line in file:
                if not line.strip():
                    if answer_lines:
                        question_text = question_text.replace(
                            '\n',
                            ' '
                        ).strip()
                        answer_text = answer_text.replace(
                            '\n',
                            ' '
                        ).strip()
                        questions[question_text] = answer_text
                        question_lines = False
                        question_text = ''
                        answer_lines = False
                        answer_text = ''
                    continue

                if line.startswith('Вопрос'):
                    question_lines = True
                    continue

                if line.startswith('Ответ:'):
                    answer_lines = True
                    question_lines = False
                    continue

                if question_lines:
                    question_text += line

                if answer_lines:
                    answer_text += line

    with open('tmp.txt', 'w', encoding='UTF-8') as tmp_file:
        json.dump(questions, tmp_file, indent=4, ensure_ascii=False)

    updater = Updater(env('QUIZ_BOT_TOKEN'))

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
