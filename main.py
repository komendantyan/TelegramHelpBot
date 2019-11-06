#!/usr/bin/env python
# -*- coding: utf-8 -*-

import traceback
import json
import os

import requests

TOKEN = os.environ['TELEGRAM_TOKEN']
EMERGENCY_CHAT_ID = os.environ.get("EMERGENCY_CHAT_ID")
ALLOWED_USERNAMES = os.environ.get("ALLOWED_USERNAMES", "").split()

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
AWS_ENDPOINT = 'https://storage.yandexcloud.net'


USE_TOR = os.environ.get('USE_TOR')


BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)


def post(method, **params):
    def encode(obj):
        if isinstance(obj, dict) and obj.get("@") == "json.dumps":
            obj.pop("@")
            return json.dumps(obj)
        elif isinstance(obj, dict):
            return {k: encode(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [encode(v) for v in obj]
        else:
            return obj

    with requests.Session() as session:
        if USE_TOR:
            session.proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }
        response = session.post(BASE_URL + "/" + method, encode(params))
        return response.json()


def send_message(**params):
    post("sendMessage", **params)


def alert(text):
    if EMERGENCY_CHAT_ID is not None:
        send_message(chat_id=EMERGENCY_CHAT_ID, text='❌ ' + text)
    else:
        raise RuntimeError("Trying alert, but no EMERGENCY_CHAT_ID set")


class Bot:
    def __init__(self):
        self._commands = {}

    def _reply_dump(self, chat_id, body):
        formated_body = json.dumps(body, indent=2)

        for message in ['message', 'edited_message']:
            if message in body:
                send_message(
                    chat_id=chat_id,
                    text=formated_body,
                    reply_to_message_id=body[message]['message_id']
                )
                break
        else:
            send_message(chat_id=chat_id, text=formated_body)

    def register_command(self, name):
        def _register(callback):
            self._commands[name] = callback
            return callback

        return _register

    def __call__(self, body):
        chat_id = find_message(body)['chat']['id']

        entities = body.get('message', {}).get('entities', [])
        for entity in entities:
            if entity['type'] == 'bot_command':
                offset, length = entity['offset'], entity['length']
                if offset != 0:
                    send_message(chat_id=chat_id, text="Not allowed any text before command!")
                else:
                    bot_command = body['message']['text'][offset: offset + length]
                    if bot_command in self._commands:
                        self._commands[bot_command](body)
                    else:
                        send_message(chat_id=chat_id, text=f"Unknown command: {bot_command}\ntry /help")

                break
        else:
            self._reply_dump(chat_id, body)


bot = Bot()


@bot.register_command("/help")
@bot.register_command("/start")
def process_help_command(body):
    text = """
        Using:
            /start, /help - print this message
            /chat_id - print current chat_id
            /post <method> <params>
                ask bot to make request with given method and params (params is json)
                example: `/post getMe {}`
            /setobject key json_value - store value in object storage
            /getobject key - get value from object storage
    """
    chat_id = body['message']['chat']['id']
    send_message(
        chat_id=chat_id,
        text=text
    )


@bot.register_command("/post")
def process_post_command(body):
    chat_id = body['message']['chat']['id']

    _, method, params = body['message']['text'].split(' ', 2)
    params = json.loads(params)
    response = post(method, **params)
    send_message(chat_id=chat_id, text=json.dumps(response, indent=2))


@bot.register_command("/chat_id")
def process_chat_id_command(body):
    chat_id = body['message']['chat']['id']
    send_message(
        chat_id=chat_id,
        reply_to_message_id=body['message']['message_id'],
        text=str(chat_id)
    )


@bot.register_command("/setobject")
def process_setobject_command(body):
    chat_id = body['message']['chat']['id']

    _, key, value = body['message']['text'].split(' ', 2)
    value = json.loads(value)

    from boto3.session import Session
    session = Session(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    client = session.client(service_name='s3', endpoint_url=AWS_ENDPOINT)

    client.put_object(Bucket=AWS_BUCKET_NAME,
                      Key=f'{key}.json',
                      Body=json.dumps(value, separators=',:'))

    send_message(chat_id=chat_id, text=f'Key {key} successfuly saved')


@bot.register_command("/getobject")
def process_getobject_command(body):
    chat_id = body['message']['chat']['id']

    _, key = body['message']['text'].split(' ', 1)

    from boto3.session import Session
    session = Session(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    client = session.client(service_name='s3', endpoint_url=AWS_ENDPOINT)

    response = client.get_object(Bucket=AWS_BUCKET_NAME,
                                 Key=f'{key}.json')
    value = json.loads(response['Body'].read())

    send_message(
        chat_id=chat_id,
        reply_to_message_id=body['message']['message_id'],
        text=json.dumps(value, indent=2)
    )


def find_message(body):
    for message in ["message", "edited_message", "channel_post", "edited_channel_post"]:
        if message in body:
            return body[message]

    try:
        return body['callback_query']['message']
    except KeyError:
        pass

    return None


def assert_username_allowed(body):
    if not ALLOWED_USERNAMES:
        raise RuntimeError("ALLOWED_USERNAMES list is empty!")

    message = find_message(body)
    from_ = message['from'] if message is not None else None

    if from_ is None or 'username' not in from_:
        raise RuntimeError("Cant detect username!")
    elif from_['username'] not in ALLOWED_USERNAMES:
        raise RuntimeError(f"Username @{from_['username']} not allowed")


def handler(event, context):
    body = json.loads(event['body'])
    try:
        assert_username_allowed(body)
        bot(body)

    except Exception:
        alert(traceback.format_exc() + "\n\nbody:\n" + json.dumps(body, indent=2))
    return {"statusCode": 200}
