import urwid
import sys
import asyncio

from widgets.sessions import Sessions
from widgets.messages import Messages

from api.channels import get_channels

class Handler:
    """Handler for channels and messages lists"""

    def __init__(self):
        # sort channels by name
        channels = sorted(
            get_channels(),
            key=lambda channel: channel['name']
        )

        # messages list
        self.messages = Messages(channels[0]['id'], 'channel')

        # channels list
        self.channels = Sessions(
            channels,
            self.messages.update
        )

        # handler box
        self.hbox = urwid.Columns(
            [
                self.channels,
                ('weight', 2, self.messages)
            ],
            dividechars=1
        )

        # color palette
        self.palette = [
            ('header', 'black,bold', 'dark magenta'),

            ('accent',      'dark blue',      'default'),
            ('accent_bold', 'dark blue,bold', 'default'),

            ('prompt', 'dark green', 'default')
        ]

    def keypress(self, key):
        """Handle exit keypress"""

        if key == 'q':
            # exit program
            sys.exit()

    def run(self):
        """Run terminal interface"""

        global loop, aloop

        aloop = asyncio.get_event_loop()

        # create main loop
        loop = urwid.MainLoop(
            self.hbox,
            self.palette,
            unhandled_input=self.keypress,
            event_loop=urwid.AsyncioEventLoop(loop=aloop)
        )

        loop.set_alarm_in(5, lambda *_: self.messages.list.refresh_loop())

        loop.run()
