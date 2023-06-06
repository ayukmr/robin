import urwid
from widgets import messages

class Sessions(urwid.Pile):
    """View for channels"""

    def __init__(self, channels, update):
        self.update = update

        # channels widgets
        self.list = ChannelsList(
            channels,
            lambda _, session: self.update(
                session, 'channel'
            )
        )
        self.prompt = ContactPrompt(self.update)

        # render widget
        super().__init__([
            (1, urwid.AttrMap(urwid.Filler(urwid.Text('  Sessions ')), 'header')),
            urwid.Padding(self.list),
            (1, urwid.Filler(self.prompt))
        ])

class ChannelsList(urwid.ListBox):
    """A list of the available channels"""

    def __init__(self, channels, on_select):
        # list of channels
        self.channels = channels

        # create list of buttons
        body = [ChannelButton(c, on_select) for c in channels]
        super().__init__(urwid.SimpleListWalker(body))

class ChannelButton(urwid.Button):
    """Button for channel in channel list"""

    # brackets style
    button_left  = urwid.Text(('accent', '•'))
    button_right = urwid.Text('')

    def __init__(self, channel, on_select):
        # create button
        super().__init__(
            channel['name'],
            on_press=on_select,
            user_data=channel['id']
        )

class ContactPrompt(urwid.Edit):
    """Prompt for selecting a contact"""

    def __init__(self, update):
        self.update = update
        super().__init__(('prompt', ' '), wrap='any')

    def keypress(self, size, key):
        """Handle send keypress"""

        if key == 'enter':
            # select entered contact
            self.update(self.edit_text, 'contact')
        else:
            return super().keypress(size, key)
