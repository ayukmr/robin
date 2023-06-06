import httpx
from api.tokens import get_token

def get_channels():
    """Get all channels for user"""

    # get channels
    res = httpx.get(
        'https://api.zoom.us/v2/chat/users/me/channels',
        headers={'Authorization': f"Bearer {get_token('access_token')}"},
        params={'page_size': 50}
    )

    return res.json()['channels']
