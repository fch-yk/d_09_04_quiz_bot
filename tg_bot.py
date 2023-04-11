import functools
import random
from enum import Enum
from typing import Dict

from environs import Env
from redis import Redis
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from questions_loading import load_questions


class BotStates(Enum):
    NEW_QUESTION_REQUEST = 0
    SOLUTION_ATTEMPT = 1


def start(update: Update, context: CallbackContext) -> BotStates:
    """Send a message when the command /start is issued."""
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        'Привет! Я бот для викторин!',
        reply_markup=reply_markup
    )
    return BotStates.NEW_QUESTION_REQUEST


def handle_new_question_request(
    update: Update,
    context: CallbackContext,
    questions: Dict,
    redis_connection: Redis
) -> BotStates:
    question_text = random.choice(list(questions))
    redis_connection.set(f'tg{update.message.chat_id}', question_text)
    update.message.reply_text(question_text)
    return BotStates.SOLUTION_ATTEMPT


def handle_solution_attempt(
    update: Update,
    context: CallbackContext,
    questions: Dict,
    redis_connection: Redis
) -> BotStates:
    answer = update.message.text
    question_text = redis_connection.get(f'tg{update.message.chat_id}')
    correct_answer = questions[question_text]
    if '(' in correct_answer:
        parenthesis_index = correct_answer.find('(')
        correct_answer = correct_answer[:parenthesis_index]
    if '.' in correct_answer:
        dot_index = correct_answer.find('.')
        correct_answer = correct_answer[:dot_index]

    correct_answer = correct_answer.strip()

    if answer == correct_answer:
        reply_text = (
            'Правильно! Поздравляю! '
            'Для следующего вопроса нажми "Новый вопрос"'
        )
        update.message.reply_text(reply_text)
        return BotStates.NEW_QUESTION_REQUEST
    else:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?')
        return BotStates.SOLUTION_ATTEMPT


def give_up(
    update: Update,
    context: CallbackContext,
    questions: Dict,
    redis_connection: Redis
) -> BotStates:
    question_text = redis_connection.get(f'tg{update.message.chat_id}')
    correct_answer = questions[question_text]
    update.message.reply_text(f'Правильный ответ:\n{correct_answer}')

    question_text = random.choice(list(questions))
    redis_connection.set(f'tg{update.message.chat_id}', question_text)
    update.message.reply_text(f'Новый вопрос: \n{question_text}')

    return BotStates.SOLUTION_ATTEMPT


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text(
        'Bye!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    env = Env()
    env.read_env()
    folder_name = env('QUESTIONS_FOLDER', 'questions')
    questions = load_questions(folder_name)
    with env.prefixed('REDIS_'):
        redis_connection = Redis(
            host=env('HOST'),
            port=env('PORT'),
            password=env('PASSWORD'),
            decode_responses=True
        )

    updater = Updater(env('QUIZ_BOT_TOKEN'))
    dispatcher = updater.dispatcher

    new_question_request_handler = functools.partial(
        handle_new_question_request,
        questions=questions,
        redis_connection=redis_connection,
    )

    solution_attempt_handler = functools.partial(
        handle_solution_attempt,
        questions=questions,
        redis_connection=redis_connection,
    )

    give_up_handler = functools.partial(
        give_up,
        questions=questions,
        redis_connection=redis_connection,
    )

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BotStates.NEW_QUESTION_REQUEST: [
                MessageHandler(
                    Filters.text('Новый вопрос'),
                    new_question_request_handler
                )
            ],
            BotStates.SOLUTION_ATTEMPT: [
                MessageHandler(
                    Filters.text & ~Filters.text('Сдаться') & ~Filters.command,
                    solution_attempt_handler
                ),
                MessageHandler(
                    Filters.text('Сдаться'),
                    give_up_handler
                ),
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
