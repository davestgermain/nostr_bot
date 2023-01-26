"""
Announce when you receive a DM

Set environment variable PUBLIC_KEY to your public key

Set env var KINDS to a comma-separated list of kinds to listen for

This works on MacOS by calling the 'say' command

You can set env var VOICE to use a different voice
"""
from nostr_bot import NostrBot
import os
import subprocess
import json


class GotMailBot(NostrBot):
    VOICE = os.getenv("VOICE", "Fred")
    KINDS = [int(k) for k in os.getenv("KINDS", "4").split(',')]
    seen_pubkeys = {}

    def get_query(self):
        my_pubkey = os.getenv('PUBLIC_KEY')
        assert my_pubkey, "Set PUBLIC_KEY environment variable"
        return {
            'limit': 1,
            '#p': [my_pubkey],
            'kinds': self.KINDS,
        }

    async def handle_event(self, event):
        if event.pubkey not in self.seen_pubkeys:
            self.seen_pubkeys[event.pubkey] = event.pubkey[:4]
            async for profile in self.manager.get_events({"authors": [event.pubkey], "kinds": [0]}, single_event=True):
                meta = json.loads(profile.content)
                self.seen_pubkeys[event.pubkey] = meta.get('display_name', '') or meta.get('name', '') or event.pubkey[:4]

        name = self.seen_pubkeys[event.pubkey]
        kind = "mail"
        if event.kind == 7:
            kind = "a reaction"
        elif event.kind == 1:
            kind = "a reply"
        announcement = f"You've got {kind} from {name}"
        self.log.info(announcement)
        command = ["say", announcement, f"-v", self.VOICE]
        try:
            subprocess.run(command)
        except FileNotFoundError:
            self.log.error("Cannot speak the announcement")
