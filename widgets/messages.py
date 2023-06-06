import urwid
import mimetypes

from widgets import handler
from api.messages import get_messages, async_get_messages, send_message

def is_image(file):
    mime = mimetypes.guess_type(file)[0]
    return mime and mime.startswith('image/')

class Messages(urwid.Pile):
    """View for messages list and editing box"""

    def __init__(self, session, session_type):
        # current session
        self.session      = session
        self.session_type = session_type

        self.reply_id = None

        # messages widgets
        self.list = MessagesList(
            self.session,
            self.session_type,
            lambda _, message: self.reply_to(message['id'], focus=True)
        )
        self.prompt = MessagesPrompt(self.send_message)

        # render widget
        super().__init__([
            (1, urwid.AttrMap(urwid.Filler(urwid.Text('  Messages ')), 'header')),
            urwid.Padding(self.list),
            (1, urwid.Filler(self.prompt))
        ])

    def keypress(self, size, key):
        """Handle send keypress"""

        if key == 'ctrl x':
            # clear replying message
            self.reply_to(None)
        else:
            return super().keypress(size, key)

    def update(self, session, session_type):
        """Update session across widgets"""

        # update session
        self.session = session
        self.session_type = session_type

        # update list
        self.list.update(self.session, self.session_type)

    def reply_to(self, reply_id, focus=False):
        """Reply to sent message"""

        self.reply_id = reply_id

        # set prompt symbol
        self.prompt.set_caption((
            'prompt',
            ' ' if reply_id else ' '
        ))

        if focus:
            # focus prompt
            self.focus_position = 2

    def send_message(self):
        """Send message to session"""

        handler.aloop.create_task(
            send_message(
                self.prompt.edit_text,
                self.session,
                self.session_type,
                self.reply_id,
                self.list.refresh
            )
        )

        self.reply_to(None)

class MessagesList(urwid.ListBox):
    """A list of the messages for a session"""

    def __init__(self, session, session_type, on_select):
        # session data
        self.session      = session
        self.session_type = session_type

        self.on_select = on_select

        messages = get_messages(self.session, self.session_type)
        non_replies = [
            m for m in messages
            if 'reply_main_message_id' not in m
        ]

        # create list items
        body = [
            MessageItem(
                m,
                non_replies[i - 1] if i > 0 else None,
                messages,
                self.on_select
            )
            for i, m in enumerate(non_replies)
        ]

        self.walker = urwid.SimpleListWalker(body)

        super().__init__(self.walker)
        self.set_position()

    def set_position(self):
        """Go to first position in walker"""

        positions = self.walker.positions(reverse=True)

        if len(positions) > 0:
            self.focus_position = positions[0]

    def update(self, session, session_type):
        """Update session and messages"""

        # update session
        self.session      = session
        self.session_type = session_type

        def callback(messages):
            self.update_walker(messages)
            self.set_position()

        handler.aloop.create_task(
            async_get_messages(
                self.session,
                self.session_type,
                callback
            )
        )

    def refresh(self):
        """Refresh messages"""

        def callback(messages):
            self.update_walker(messages)

        handler.aloop.create_task(
            async_get_messages(
                self.session,
                self.session_type,
                callback
            )
        )

    def refresh_loop(self):
        """Refresh messages every five seconds"""

        self.refresh()
        handler.loop.set_alarm_in(5, lambda *_: self.refresh_loop())

    def update_walker(self, messages):
        """Update list walker"""

        non_replies = [
            m for m in messages
            if 'reply_main_message_id' not in m
        ]

        # create list items
        body = [
            MessageItem(
                m,
                non_replies[i - 1] if i > 0 else None,
                messages,
                self.on_select
            )
            for i, m in enumerate(non_replies)
        ]

        # refresh list items
        self.walker[:] = body

class MessageItem(urwid.Pile):
    """Sent message in list"""

    def __init__(self, message, last, messages, on_select):
        # message body
        body = MessageButton(message, last, on_select)

        if 'reply_main_message_id' not in message:
            # list of replies
            replies = [
                m for m in messages
                if 'reply_main_message_id' in m and m['reply_main_message_id'] == message['id']
            ]

            # add replies to message
            super().__init__([
                body,
                urwid.Padding(
                    urwid.Text([
                        self.reply(m, replies[i - 1] if i > 0 else None)
                        for i, m in enumerate(replies)
                    ]),
                    left=4
                )
            ] if replies else [body])
        else:
            super().__init__([body])

    def reply(self, message, last):
        """Sent reply in list"""

        # add icons corresponding to files
        if 'files' in message:
            message['message'] += f""" {
                ' '.join([
                    ''
                    if is_image(f['file_name'])
                    else ''
                    for f in message['files']
                 ])
            }"""

        # create reply
        return (
            f"\n{message['message']}"
            if last and last['sender_display_name'] == message['sender_display_name']
            else [
                (
                    'accent_bold',
                    f"\n{message['sender_display_name']}\n"
                    if last
                    else f"{message['sender_display_name']}\n"
                ),
                message['message']
            ]
        )

class MessageButton(urwid.Button):
    """Button for message in message list"""

    # brackets style
    button_left  = urwid.Text('│')
    button_right = urwid.Text('')

    def __init__(self, message, last, on_select):
        # add icons corresponding to files
        if 'files' in message:
            message['message'] += f""" {
                ' '.join([
                    ''
                    if is_image(f['file_name'])
                    else ''
                    for f in message['files']
                ])
            }"""

        # create button
        super().__init__(
            message['message']
            if last and last['sender_display_name'] == message['sender_display_name']
            else [
                ('accent_bold', f"{message['sender_display_name']}\n"),
                message['message']
            ],
            on_press=on_select,
            user_data=message
        )

class MessagesPrompt(urwid.Edit):
    """Prompt for sending a message"""

    def __init__(self, send_message):
        self.send_message = send_message
        super().__init__(('prompt', ' '), wrap='any')

    def keypress(self, size, key):
        """Handle send keypress"""

        if key == 'enter':
            # send message to session
            self.send_message()
            self.edit_text = ''
        else:
            return super().keypress(size, key)
