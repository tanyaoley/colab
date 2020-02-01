# -*- coding: utf-8 -*-
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.upload import VkUpload
from sklearn.cluster import KMeans
import numpy as np
import skimage
from PIL import Image

import random
import argparse
import traceback
from skimage import io

VK_TOKEN = 'your_vk_token'
GROUP_ID = 0 #your group id


def clustering(img, number):
    img = skimage.img_as_float(img)
    X = np.vstack(img)
    clf = KMeans(n_clusters=number)
    clf.fit(X)
    X_compressed = clf.cluster_centers_[clf.labels_]
    X_compressed = np.clip(X_compressed.astype('float'), 0, 1)
    X_compressed = np.reshape(X_compressed, (img.shape[0], img.shape[1], img.shape[2]))
    print(img.shape)
    print(X_compressed.shape)
    print()
    return X_compressed


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vk_token', type=str, default=VK_TOKEN)
    parser.add_argument('--vk_group_id', type=int, default=GROUP_ID)
    return parser.parse_args()


def isint(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def get_number(colors):
    number = 0
    params = parse_args()

    vk_session = vk_api.VkApi(token=params.vk_token)
    long_poll = VkBotLongPoll(vk_session, params.vk_group_id)

    for event in long_poll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            print(type(event.obj))
            print(event.obj)
            print()

            message = event.obj.message
            peer_id = message['peer_id']
            from_id = message['from_id']
            text = message['text']

            if len(text) > 0:
                if isint(text) and 1 <= int(text) <= colors:
                    number = int(text)
                    answer = {
                        'peer_id': peer_id,
                        'random_id': random.randint(0, 100000),
                        }
                    answer.update({'message': "Количество новых цветов получено"})
                    vk_session.method('messages.send', answer)
                elif text == "стоп":
                    return -1
                else:
                    answer = {
                        'peer_id': peer_id,
                        'random_id': random.randint(0, 100000),
                    }
                    answer.update({'message': "Введено неверное число. Попробуйте снова"})
                    vk_session.method('messages.send', answer)

                return number


def main(user_dict):
    params = parse_args()

    vk_session = vk_api.VkApi(token=params.vk_token)
    uploader = VkUpload(vk_session)
    long_poll = VkBotLongPoll(vk_session, params.vk_group_id)

    for event in long_poll.listen():

        if event.type == VkBotEventType.MESSAGE_NEW:
            print(type(event.obj))
            print(event.obj)
            print()

            message = event.obj.message
            peer_id = message['peer_id']
            from_id = message['from_id']
            text = message['text']

            attachments = message['attachments']
            print(type(attachments))
            print(attachments)
            print()
            if len(text) > 0 and peer_id not in user_dict and len(attachments) == 0:
                answer = {
                    'peer_id': peer_id,
                    'random_id': random.randint(0, 100000),
                }
                answer.update({'message': "Ошибочка. Это не изображение"})
                vk_session.method('messages.send', answer)
            if len(text) > 0 and peer_id in user_dict:
                if isint(text) and 1 <= int(text) <= colors:
                    user_dict[peer_id] = int(text)
                    answer = {
                        'peer_id': peer_id,
                        'random_id': random.randint(0, 100000),
                        }
                    answer.update({'message': "Количество новых цветов получено"})
                    vk_session.method('messages.send', answer)
                elif text == "стоп":
                    user_dict.pop(peer_id)
                    answer = {
                            'peer_id': peer_id,
                            'random_id': random.randint(0, 100000),
                    }
                    answer.update({'message': "Можете отправить изображение заново"})
                    vk_session.method('messages.send', answer)
                else:
                    answer = {
                        'peer_id': peer_id,
                        'random_id': random.randint(0, 100000),
                    }
                    answer.update({'message': "Введено неверное число. Попробуйте снова"})
                    vk_session.method('messages.send', answer)

            if len(attachments) > 0 and attachments[0]['type'] == 'photo' and peer_id not in user_dict:
                photo = attachments[0]['photo']
                print(type(photo))
                print(photo)
                print()
                photos = sorted(photo['sizes'], key=lambda a: a['height'], reverse=True)
                best_photo = photos[0]
                best_photo_url = best_photo['url']
                img = io.imread(best_photo_url)
                np.random.seed(0)

                im_colors = Image.fromarray(img)
                colors = len(set(im_colors.getcolors(img.shape[0]*img.shape[1])))
                answer = {
                    'peer_id': peer_id,
                    'random_id': random.randint(0, 100000),
                }
                answer.update({'message': "Количество цветов в изображении {}. Введите новое количество(должно быть меньше, чем текущее) или стоп, чтобы отправить новое изображение ".format(colors)})
                vk_session.method('messages.send', answer)

                user_dict[peer_id] = 0
                io.imsave("{}.png".format(peer_id), img)

            if peer_id in user_dict and user_dict[peer_id] != 0:

                img = io.imread("./{}.png".format(peer_id))
                img = clustering(img, user_dict[peer_id])
                io.imsave("{}.png".format(peer_id), img)
                uploaded_photos = uploader.photo_messages("./{}.png".format(peer_id))
                uploaded_photo = uploaded_photos[0]
                user_dict.pop(peer_id)
                answer_with_img = {
                    'peer_id': peer_id,
                    'random_id': random.randint(0, 100000),
                }
                photo_attachment = f'photo{uploaded_photo["owner_id"]}_{uploaded_photo["id"]}'

                answer_with_img.update({'attachment': photo_attachment})
                vk_session.method('messages.send', answer_with_img)

                print(answer_with_img)
                print()




if __name__ == '__main__':
    while True:
        try:
            print("(RE)START")
            user_dict = dict()
            main(user_dict)
        except Exception as err:
            full_stack_trace = traceback.format_exc()

            print("BLIN {}".format(full_stack_trace))