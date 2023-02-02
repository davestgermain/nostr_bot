import logging
import os

from aionostr.relay import Manager
from aionostr.event import Event, loads, dumps

__all__ = ('NostrBot', 'RPCBot', 'CommunicatorBot')


class NostrBot:
    """
    Base bot class that listens for a query and logs the results

    Override `handle_event(event)` to do something interesting
    """
    LISTEN_KIND = 1
    LISTEN_PUBKEY = ''
    LIMIT = 1
    RELAYS = ['ws://localhost:6969']
    PRIVATE_KEY = os.getenv('NOSTR_KEY', 'd3b7207018ac76dfab82100a6c07a42c68b8efc4898b96d2882b8a7636dd0498')

    def __init__(self):
        self.log = logging.getLogger(self.get_origin())
        self._manager = None

    def get_origin(self):
        return self.__class__.__name__

    def get_manager(self):
        pk = self.private_key
        if pk:
            pk = pk.hex()
        return Manager(self.get_relays(), origin=self.get_origin(), private_key=pk)

    def get_relays(self):
        return self.RELAYS

    def get_query(self):
        filter_obj = {
            'limit': self.LIMIT
        }
        if self.LISTEN_PUBKEY:
            filter_obj['authors'] = [self.LISTEN_PUBKEY]
        if self.LISTEN_KIND is not None:
            filter_obj['kinds'] = [self.LISTEN_KIND]
        return filter_obj

    @property
    def private_key(self):
        if not self.PRIVATE_KEY:
            return None
        from aionostr.key import PrivateKey
        from aionostr.util import from_nip19
        if self.PRIVATE_KEY.startswith('nsec'):
            pk = from_nip19(self.PRIVATE_KEY)['object']
        else:
            pk = PrivateKey(bytes.fromhex(self.PRIVATE_KEY))
        return pk

    @property
    def manager(self):
        if not self._manager:
            self._manager = self.get_manager()
        return self._manager

    @manager.setter
    def manager(self, manager):
        self._manager = manager

    async def start(self):
        if self.private_key:
            self.manager.private_key = self.private_key.hex()
        await self.manager.connect()

        query = self.get_query()
        self.log.info("Running query %s on %s", query, self.get_relays())


        async for event in self.manager.get_events(query, only_stored=False):
            try:
                if not event.verify():
                    self.log.warning('Invalid event: %s', event.id)
                    continue
            except Exception as e:
                self.log.error(str(e))
                continue
            try:
                await self.handle_event(event)
            except Exception:
                self.log.exception('handle_event')

    async def handle_event(self, event: Event):
        """
        Override this to do useful things
        """
        self.log.info(str(event))


class CommunicatorBot(NostrBot):
    """
    A bot that can make DM's and reply
    """
    PUBLIC_KEY = ''
    
    def __init__(self):
        super().__init__()
        if not self.PUBLIC_KEY:
            self.PUBLIC_KEY = self.private_key.public_key.hex()
        elif self.PUBLIC_KEY.startswith('npub'):
            from aionostr.util import from_nip19
            self.PUBLIC_KEY = from_nip19(self.PUBLIC_KEY)['object'].hex()

    def make_event(self, encrypt_to=None, **event_args):
        if encrypt_to:
            event_args['content'] = self.private_key.encrypt_message(event_args['content'], encrypt_to)
        if not event_args.get('pubkey'):
            event_args['pubkey'] = self.PUBLIC_KEY
        event = Event(**event_args)

        event.sign(self.private_key.hex())
        return event

    def make_dm(self, encrypt_to, **event_args):
        tags = event_args.get('tags', [])
        tags.append(["p", encrypt_to])
        event_args['kind'] = 4
        event_args['tags'] = tags
        event = self.make_event(encrypt_to=encrypt_to, **event_args)
        return event

    async def reply(self, event):
        self.log.debug("Replying with %s", event)
        await self.manager.add_event(event, check_response=True)


class RPCBot(CommunicatorBot):
    """
    A bot that listens for (optionally encrypted) messages in the form:
    {
        "method": "name",
        "args": ["arg1", 1, "arg3"]
    }

    By default, these are kind 22222 -- ephemeral events
    """
    LISTEN_KIND = 22222
    ENCRYPTED = True

    def __init__(self):
        super().__init__()
        self.LISTEN_PUBKEY = self.PUBLIC_KEY

    async def handle_event(self, event: Event):
        content = event.content
        if self.ENCRYPTED:
            try:
                content = self.private_key.decrypt_message(content, event.pubkey)
            except Exception:
                self.log.exception("decrypt")
                return
        try:
            command = loads(content)
        except Exception:
            self.log.exception("json")
            return
        try:
            func = getattr(self, f"on_{command['method']}")
        except (KeyError, AttributeError, TypeError):
            self.log.error("%s", command)
            return
        try:
            args = command['args']
            response = await func(event, *args)
            self.log.debug("Command %s from %s", command, event)
        except Exception as e:
            self.log.exception(str(e))
        else:
            if response and 'event' in response:
                await self.reply(response['event'])

    def make_response(self, event, **kwargs):
        if self.ENCRYPTED:
            kwargs['encrypt_to'] = event.pubkey
        response = {
            'event': self.make_event(**kwargs)
        }
        return response


class RegistrationBot(CommunicatorBot):
    LISTEN_KIND = 11141
    LIMIT = 100

    async def handle_event(self, event: Event):
        if not event.verify():
            self.log("Bad event: %s", event.id)
            return
        self.log.info("Got registration request %s", event)

        if await self.is_valid(event):
            self.log.info("Valid registration from %s", event.pubkey)
            if await self.register(event):
                self.log.info("Registered pubkey %s", event.pubkey)

    async def is_valid(self, event: Event):
        valid = False
        for tag in event.tags:
            if tag[0] == 'relay':
                if tag[1] in self.RELAYS:
                    valid = True
        return valid

    async def register(self, event: Event):
        return False


async def start_multiple(bots, relays=None):
    """
    Start multiple bots in their own task
    """
    import asyncio

    if relays:
        first_manager = None
        for bot in bots:
            bot.RELAYS = relays
            if not first_manager:
                first_manager = bot.manager
            bot.manager = first_manager

    tasks = [asyncio.create_task(bot.start()) for bot in bots]
    try:
        await asyncio.wait(tasks)
    except asyncio.exceptions.CancelledError:
        return
