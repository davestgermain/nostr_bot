import logging

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

    def __init__(self):
        self.log = logging.getLogger(self.get_origin())

    def get_origin(self):
        return self.__class__.__name__

    def get_manager(self):
        return Manager(self.get_relays(), origin=self.get_origin())

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

    async def start(self):
        query = self.get_query()
        self.manager = self.get_manager()
        self.log.info("Running query %s on %s", query, self.get_relays())
        async with self.manager as man:
            async for event in man.get_events(query, only_stored=False):
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

    async def handle_event(self, event):
        self.log.info(str(event))


class CommunicatorBot(NostrBot):
    """
    A bot that can make DM's and reply
    """
    PRIVATE_KEY = 'nsec16wmjquqc43mdl2uzzq9xcpay935t3m7y3x9ed55g9w98vdkaqjvqn76jcr'
    PUBLIC_KEY = 'npub10xtcn45hv7gkqzs53l74aws8mfmydt67x3hk3rya070sacgznk0qgtkc3v'
    
    def __init__(self):
        super().__init__()
        from nostr.key import PrivateKey
        from aionostr.util import from_nip19
        if self.PRIVATE_KEY.startswith('nsec'):
            self.PRIVATE_KEY = from_nip19(self.PRIVATE_KEY).hex()
        if self.PUBLIC_KEY.startswith('npub'):
            self.PUBLIC_KEY = from_nip19(self.PUBLIC_KEY).hex()
        self.prikey = PrivateKey(bytes.fromhex(self.PRIVATE_KEY))

    def make_event(self, encrypt_to=None, **event_args):
        if encrypt_to:
            event_args['content'] = self.prikey.encrypt_message(event_args['content'], encrypt_to)
        if not event_args.get('pubkey'):
            event_args['pubkey'] = self.PUBLIC_KEY
        event = Event(**event_args)

        event.sign(self.PRIVATE_KEY)
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
        await self.manager.add_event(event)


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
    PRIVATE_KEY = 'nsec16wmjquqc43mdl2uzzq9xcpay935t3m7y3x9ed55g9w98vdkaqjvqn76jcr'
    LISTEN_PUBKEY = PUBLIC_KEY = 'npub10xtcn45hv7gkqzs53l74aws8mfmydt67x3hk3rya070sacgznk0qgtkc3v'
    ENCRYPTED = True

    def __init__(self):
        super().__init__()

    async def handle_event(self, event):
        content = event.content
        if self.ENCRYPTED:
            try:
                content = self.prikey.decrypt_message(content, event.pubkey)
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
