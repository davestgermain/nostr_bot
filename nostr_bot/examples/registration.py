from nostr_bot.bot import RegistrationBot
import os

class ShibbolethRegistrationBot(RegistrationBot):
    SHIBBOLETH = os.getenv("SHIBBOLETH")

    async def is_valid(self, event):
        return event.content == self.SHIBBOLETH


class PaymentRegistrationBot(RegistrationBot):
    AMOUNT = os.getenv("AMOUNT")

    async def is_valid(self, event):
        return event.content == 'here is {self.AMOUNT}'

