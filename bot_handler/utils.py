import requests


def broadcast_message(bot_token, user_ids, broadcast_message_text):
    for user_id in user_ids:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={user_id}&text={broadcast_message_text}"
        resp = requests.get(url)
