=========
nostr bot
=========


.. image:: https://img.shields.io/pypi/v/nostr-bot.svg
        :target: https://pypi.python.org/pypi/nostr-bot

.. image:: https://img.shields.io/travis/davestgermain/nostr_bot.svg
        :target: https://travis-ci.com/davestgermain/nostr_bot

.. image:: https://readthedocs.org/projects/nostr-bot/badge/?version=latest
        :target: https://nostr-bot.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status




A Python nostr bot framework

To install:

``pip install nostr-bot``

To run:

``nostr-bot run``

For instance:
``PUBLIC_KEY=84dee6e676e5bb67b4ad4e042cf70cbd8681155db535942fcc6a0533858a7240 KINDS=1,4,5,7 nostr-bot run -c nostr_bot.examples.gotmail.GotMailBot``

See the examples_ for more ideas of what you can do!



* Free software: BSD license
* Documentation: https://nostr-bot.readthedocs.io.


Features
--------

* RPC using ephemeral events
* automatic reconnect
* simple API

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _examples: https://github.com/davestgermain/nostr_bot/tree/master/nostr_bot/examples
