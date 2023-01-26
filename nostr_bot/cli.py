"""Console script for nostr_bot."""
import sys
import click
import asyncio
import os
from functools import wraps

DEFAULT_RELAYS = os.getenv('NOSTR_RELAYS', 'wss://nostr.mom,wss://relay.damus.io').split(',')


def async_cmd(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    return asyncio.run(func(*args, **kwargs))
  return wrapper


@click.group()
def main(args=None):
    """Console script for nostr_bot."""
    return 0


@main.command()
@click.option('-c', '--cls', help='bot class to run', default='nostr_bot.NostrBot')
@click.option('-r', 'relays', multiple=True, help='Relay address (can be added multiple times)', default=DEFAULT_RELAYS)
@click.option('-v', '--verbose', help='verbose results', is_flag=True, default=False)
@async_cmd
async def run(relays, cls, verbose):
    """
    Run a bot
    """
    import logging
    import importlib
    try:
        bot_module, bot_class = cls.rsplit('.', 1)
        bot_class = getattr(importlib.import_module(bot_module), bot_class)
    except (ImportError, AttributeError):
        click.echo("Class not found")
        return -1
    logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s %(message)s', level=logging.DEBUG if verbose else logging.INFO)
    bot = bot_class()
    if relays:
        bot.RELAYS = relays
    await bot.start()



if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
