"""
Ping bot
"""

import os
import json
from nostr_bot import RPCBot


class PingBot(RPCBot):
    LISTEN_PUBKEY = os.getenv("PUBLIC_KEY")
    ENCRYPTED = False

    async def on_ping(self, event, *args):
        self.log.info("Got ping %s", event)
        self.log.info("Sending pong")
        return self.make_response(event, kind=event.kind, content=json.dumps({"method": "pong", "args": []}))

    async def on_pong(self, event, *args):
        self.log.info("Got pong %s", event)