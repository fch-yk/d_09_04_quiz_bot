import functools
import json
import os
import random
from typing import Dict

from redis import Redis
from environs import Env
from telegram import ReplyKeyboardMarkup, Update
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


def reply(
    update: Update,
    context: CallbackContext,
    questions: Dict,
    redis_connection: Redis
) -> None:
    """Reply to the user message."""
    if update.message.text == 'Новый вопрос':
        question_text = random.choice(list(questions))
        redis_connection.set(str(update.message.chat_id), question_text)
        update.message.reply_text(question_text)
    else:
        answer = update.message.text
        question_text = redis_connection.get(str(update.message.chat_id))
        correct_answer = questions[question_text]
        if '(' in correct_answer:
            parenthesis_index = correct_answer.find('(')
            correct_answer = correct_answer[:parenthesis_index]
        if '.' in correct_answer:
            dot_index = correct_answer.find('.')
            correct_answer = correct_answer[:dot_index].strip()

        correct_answer = correct_answer.strip()

        if answer == correct_answer:
            reply_text = (
                'Правильно! Поздравляю! '
                'Для следующего вопроса нажми "Новый вопрос"'
            )
        else:
            reply_text = 'Неправильно… Попробуешь ещё раз?'

        update.message.reply_text(reply_text)


def main():
    env = Env()
    env.read_env()
    folder_name = env('QUESTIONS_FOLDER', 'questions')
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

    with env.prefixed('REDIS_'):
        redis_connection = Redis(
            host=env('HOST'),
            port=env('PORT'),
            password=env('PASSWORD'),
            decode_responses=True
        )

    updater = Updater(env('QUIZ_BOT_TOKEN'))
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    reply_handler = functools.partial(
        reply,
        questions=questions,
        redis_connection=redis_connection,
    )
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, reply_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
