import re
import httpx
from emoji import emojize

from widgets import handler
from api.tokens import get_token

def get_messages(session, session_type):
    """Get messages for session"""

    # get messages
    res = httpx.get(
        'https://api.zoom.us/v2/chat/users/me/messages',
        headers={'Authorization': f"Bearer {get_token('access_token')}"},
        params={
            'from': '2020-01-01T12:00:00Z',
            'page_size': 50,
            f'to_{session_type}': session
        }
    )

    # reverse messages
    return list(reversed(res.json()['messages']))

async def async_get_messages(session, session_type, callback):
    """Get messages for session asynchronously"""

    async with httpx.AsyncClient() as client:
        # get messages
        res = await client.get(
            'https://api.zoom.us/v2/chat/users/me/messages',
            headers={'Authorization': f"Bearer {get_token('access_token')}"},
            params={
                'from': '2020-01-01T12:00:00Z',
                'page_size': 50,
                f'to_{session_type}': session
            }
        )

        callback(list(reversed(res.json()['messages'])))

async def send_message(message, session, session_type, reply_id, callback):
    """Send message to session"""

    # interpret emoji codes
    message = emojize(message, language='alias')

    emails = re.findall(r'@\w+@\w+\.\w+', message)
    shorthands = [
        re.sub(r'(@\w+)@\w+\.\w+', r'\1', e)
        for e in emails
    ]

    # convert emails to shorthands
    for email, shorthand in zip(emails, shorthands):
        message = message.replace(email, shorthand)

    # message data
    json = {
        'message': message,
        f'to_{session_type}': session,
        'at_items': [{
            'at_type':    1,
            'at_contact': e[1:],

            'start_position': message.find(s),
            'end_position':   message.find(s) + len(s) - 1
        } for e, s in zip(emails, shorthands)]
    }

    if reply_id:
        # reply to message
        json['reply_main_message_id'] = reply_id

    async with httpx.AsyncClient() as client:
        # send message
        await client.post(
            'https://api.zoom.us/v2/chat/users/me/messages',
            headers={'Authorization': f"Bearer {get_token('access_token')}"},
            json=json
        )

        handler.loop.set_alarm_in(0.25, lambda *_: callback())
