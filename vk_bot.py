import random

import vk_api as vk
from environs import Env
from redis import Redis
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from common import load_questions


def reply(event, vk_api, questions, redis_connection):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)
    if event.text == 'Привет':
        vk_api.messages.send(
            user_id=event.user_id,
            message='Привет! Я бот для викторин!',
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )
        return
    if event.text == 'Новый вопрос':
        question_text = random.choice(list(questions))
        redis_connection.set(f'vk{event.user_id}', question_text)
        vk_api.messages.send(
            user_id=event.user_id,
            message=question_text,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )
        return
    if event.text == 'Сдаться':
        question_text = redis_connection.get(f'vk{event.user_id}')
        correct_answer = questions[question_text]
        vk_api.messages.send(
            user_id=event.user_id,
            message=f'Правильный ответ:\n{correct_answer}',
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )

        question_text = random.choice(list(questions))
        redis_connection.set(f'vk{event.user_id}', question_text)
        vk_api.messages.send(
            user_id=event.user_id,
            message=f'Новый вопрос: \n{question_text}',
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )
        return

    answer = event.text
    question_text = redis_connection.get(f'vk{event.user_id}')
    if not question_text:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Привет! Я бот для викторин!',
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )
        return

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
        vk_api.messages.send(
            user_id=event.user_id,
            message=reply_text,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )
    else:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Неправильно… Попробуешь ещё раз?',
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard()
        )


def main() -> None:
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

    vk_group_token = env.str('VK_GROUP_TOKEN')
    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            reply(event, vk_api, questions, redis_connection)


if __name__ == '__main__':
    main()
