import vk_api as vk
from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id


def reply(event, vk_api):

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)
    vk_api.messages.send(
        user_id=event.user_id,
        message=event.text,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard()
    )


def main() -> None:
    env = Env()
    env.read_env()
    vk_group_token = env.str('VK_GROUP_TOKEN')
    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            reply(event, vk_api)


if __name__ == '__main__':
    main()
