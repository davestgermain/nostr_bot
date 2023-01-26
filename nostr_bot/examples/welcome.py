"""
New User bot

This will listen for kind=0 events and send a dm to itself, welcoming the user

"""
from nostr_bot import CommunicatorBot
import json


class WelcomeBot(CommunicatorBot):
    LISTEN_KIND = 0
    LISTEN_PUBKEY = None

    async def handle_event(self, event):
        meta = json.loads(event.content)
        name = meta.get('display_name', '') or meta.get('name', '') or event.pubkey
        dm = self.make_dm(self.PUBLIC_KEY, content=f"Welcome, {name}!")
        self.log.info("Welcoming %s with %s", name, dm.id)
        await self.reply(dm)
