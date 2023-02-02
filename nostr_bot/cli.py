"""Console script for nostr_bot."""
import sys
import click
import asyncio
import os
from functools import wraps
try:
    import uvloop
    uvloop.install()
except ImportError:
    pass


DEFAULT_RELAYS = os.getenv('NOSTR_RELAYS', 'wss://nostr.mom,wss://relay.snort.social').split(',')

def stop():
    loop = asyncio.get_running_loop()
    try:
        loop.stop()
    except RuntimeError:
        return


def async_cmd(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
        async def _run(coro):
            from signal import SIGINT, SIGTERM

            loop = asyncio.get_running_loop()
            for signal_enum in [SIGINT, SIGTERM]:
                loop.add_signal_handler(signal_enum, stop)

            await coro
        coro = func(*args, **kwargs)
        try:
            asyncio.run(_run(coro))
        except RuntimeError:
            return
  return wrapper


@click.group()
def main(args=None):
    """Console script for nostr_bot."""
    return 0


@main.command()
@click.option('-c', '--cls', multiple=True, help='bot class(es) to run', default=['nostr_bot.NostrBot'])
@click.option('-r', 'relays', multiple=True, help='Relay address (can be added multiple times)', default=DEFAULT_RELAYS)
@click.option('-v', '--verbose', help='verbose results', is_flag=True, default=False)
@async_cmd
async def run(relays, cls, verbose):
    """
    Run a bot
    """
    import logging
    import importlib
    from .bot import start_multiple
    logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s – %(message)s', level=logging.DEBUG if verbose else logging.INFO)

    bots = []
    for classname in cls:
        try:
            bot_module, bot_class = classname.rsplit('.', 1)
            bot_class = getattr(importlib.import_module(bot_module), bot_class)
        except (ImportError, AttributeError):
            click.echo(f"Class {classname} not found")
            return -1
        bots.append(bot_class())
    await start_multiple(bots, relays=relays)




if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
