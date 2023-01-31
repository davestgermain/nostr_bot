"""
Ping bot
"""

import os
import json
from nostr_bot import RPCBot


class PingBot(RPCBot):
    ENCRYPTED = False

    def __init__(self):
        super().__init__()
        self.LISTEN_PUBKEY = os.getenv("PUBLIC_KEY")

    async def on_ping(self, event, *args):
        self.log.info("Got ping %s", event)
        self.log.info("Sending pong")
        return self.make_response(event, kind=event.kind, content=json.dumps({"method": "pong", "args": []}))

    async def on_pong(self, event, *args):
        self.log.info("Got pong %s", event)