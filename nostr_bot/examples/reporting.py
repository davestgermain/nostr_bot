"""
TattleBot will listen for kind=1984 reports and notify the subject of the report that they've been tattled on.

You can subclass TattleBot and override handle_message(event, tattle_subject, message) to do something more interesting with the generated message
Override create_message(event, report_type, tattled_event_id, impersonation) to generate a different response

To run:
TATTLE_WATCH=<mypubkey> NOSTR_KEY=<bot_private_key> nostr-bot run -c nostr_bot.examples.reporting.TattleBot -r wss://my.relay.biz

"""

from nostr_bot.bot import CommunicatorBot
from aionostr.util import to_nip19
import shelve
import os
import time


class TattleBot(CommunicatorBot):
    SEND_MESSAGE = False

    shelf = shelve.open('tattlebot')

    def get_query(self):
        query = {
            'kinds': [1984]
        }
        last_seen = self.get_last_seen()
        if last_seen:
            query['since'] = last_seen
        pubkeys = self.get_watch_for_pubkeys()
        if pubkeys:
            query['#p'] = pubkeys
        return query

    def get_last_seen(self):
        return self.shelf.get('last_seen', 0)

    def set_last_seen(self, event):
        self.shelf['last_seen'] = max(event.created_at, self.get_last_seen())

    def get_watch_for_pubkeys(self):
        pubkeys = os.getenv('TATTLE_WATCH', '').split(',')
        if all(pubkeys):
            return pubkeys

    async def handle_event(self, event):
        if event.id in self.shelf:
            self.log.info("Skipping %s", event.id)
            return
        report_type = ''
        tattled_event_id = ''
        tattle_subject = ''
        impersonation = ''
        for tag in event.tags:
            if tag[0] == 'report':
                report_type = tag[1]
            elif tag[0] == 'e':
                tattled_event_id = tag[1]
            elif tag[0] == 'p':
                if len(tag) == 3 and tag[2] == 'impersonation':
                    impersonation = tag[1]
                else:
                    tattle_subject = tag[1]

        message = self.create_message(event, report_type, tattled_event_id, impersonation)

        response = await self.handle_message(event, tattle_subject, message)
        self.set_last_seen(event)
        self.shelf[event.id] = {'seen': time.time(), 'response': response}

    def create_message(self, event, report_type, tattled_event_id, impersonation):
        reporter = to_nip19('npub', event.pubkey)
        if tattled_event_id:
            tattle_note = to_nip19('note', tattled_event_id)
        else:
            tattle_note = '<somewhere>'
        if report_type == 'spam':
            reason = 'spamming'
        elif report_type == 'illegal':
            reason = 'doing something illegal'
        elif report_type == 'impersonation':
            reason = f'impersonating {to_nip19("npub", impersonation)}'
        else:
            reason = report_type
        response = f'''YOU'RE IN TROUBLE
{reporter} tattled on you for {reason} in {tattle_note}.
They said you were "{event.content}"

Just letting you know.

Sent by TattleBot.
'''
        return response

    async def handle_message(self, event, tattle_subject, message):
        if tattle_subject and message:
            if self.SEND_MESSAGE:
                dm = self.make_dm(tattle_subject, content=message)
                self.log.debug(str(dm))
                await self.reply(dm)
                self.log.info("Alerted %s about tattling on %s with dm %s", tattle_subject, event.id, dm.id)
                return dm.id
            else:
                self.log.info("%s tattled on %s. Sending:\n%s", event.pubkey, tattle_subject, message)
