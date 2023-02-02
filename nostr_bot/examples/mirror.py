"""
MirrorBot will mirror events from authors you follow. 
The source relays are set with environment variable NOSTR_RELAYS or with -r on the command line

To run:

TARGET=ws://target-relay.biz PUBLIC_KEY=<YOURPUBKEY> nostr-bot run -c nostr_bot.examples.mirror.MirrorFollowersBot
"""
import os
import time
import shelve
from nostr_bot.bot import NostrBot
from aionostr import Manager


class MirrorFollowersBot(NostrBot):
    MY_PUBKEY = os.getenv('PUBLIC_KEY')
    TARGET_RELAY = os.getenv('TARGET')
    shelf = shelve.open(f'mirrorbot-{TARGET_RELAY.replace("://", "-")}')

    def get_query(self):
        return self.query

    def get_last_seen(self):
        return self.shelf.get('last_seen', 1)

    def set_last_seen(self, timestamp):
        if timestamp > self.get_last_seen():
            self.shelf['last_seen'] = timestamp

    async def get_following(self):
        find_query = {
            'kinds': [3],
            'authors': [self.MY_PUBKEY]
        }
        following = [self.MY_PUBKEY]
        self.log.info("Getting following for %s %s", self.MY_PUBKEY, find_query)
        async for event in self.manager.get_events(find_query):
            for tag in event.tags:
                if tag[0] == 'p':
                    following.append(tag[1])
        return following

    async def start(self):
        self.target_manager = Manager([self.TARGET_RELAY])
        await self.target_manager.connect()
        await self.manager.connect()
        self.query = {
            'authors': await self.get_following(),
            'since': self.get_last_seen()
        }
        return await super().start()

    async def handle_event(self, event):
        if event.id in self.shelf:
            return
        await self.target_manager.add_event(event)
        self.log.info("Mirrored %s from %s to %s", event.id[:8], event.pubkey, self.TARGET_RELAY)
        self.set_last_seen(event.created_at)
        self.shelf[event.id] = time.time()
