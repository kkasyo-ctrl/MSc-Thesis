import time  # For getting the current timestamp
from typing import Any, Union  # Type annotations for type hinting

import rnd_param

# Constants for different offer evaluations
ACCEPT = 'accept'
NOT_PROFITABLE = 'not_profitable'
OFFER_QUALITY = 'offer_quality'
OFFER_PRICE = 'offer_price'
NOT_OFFER = 'not_offer'
INVALID_OFFER = 'invalid_offer'

class Offer(dict):  # Represents an individual offer
    def __init__(self,
                 idx: int = -1,  # Identifier for the offer
                 price: int = None,  # Price value
                 quality: int = None,  # Quality value
                 stamp: int = None,  # Timestamp of the offer
                 from_chat: bool = False,  # Whether the offer came from chat
                 enhanced: str = None,  # Fields enhanced during processing
                 profit_bot: int = None,  # Bot's profit from the offer
                 profit_user: int = None,  # User's profit from the offer
                 test: Any = None):  # Optional test data
        stamp = stamp or int(time.time())  # Set current timestamp if none provided
        dict.__init__(self, idx=idx, price=price, quality=quality,
                      stamp=stamp, from_chat=from_chat, enhanced=enhanced,
                      profit_bot=profit_bot, profit_user=profit_user,
                      test=test)
        self.idx = idx
        self.price = price
        self.quality = quality
        self.stamp = stamp
        self.from_chat = True ### set to true
        self.enhanced = enhanced
        self.profit_bot = profit_bot
        self.profit_user = profit_user

    def __getattr__(self, attr):  # Get attribute as dictionary value
        return self.get(attr)

    def __setattr__(self, key, value):  # Set dictionary key via attribute
        self.__setitem__(key, value)

    @property
    def specifics(self) -> str:  # Summary of offer details
        return f"P+Q = {str(self.price):4} + {str(self.quality):4} ; " \
               f"PROF = {str(self.profit_bot):3} + {str(self.profit_user):3} ;"

    @property
    def is_valid(self) -> bool:  # Check if the offer is valid
        return self.is_complete and self.price_in_range and self.quality_in_range

    @property
    def is_complete(self) -> bool:  # Check if price and quality are set
        return None not in (self.price, self.quality)

    @property
    def price_in_range(self) -> bool:  # Check if price is within valid range
        return self.price in rnd_param.PRICE_RANGE

    @property
    def quality_in_range(self) -> bool:  # Check if quality is within valid range
        return self.quality in rnd_param.QUALITY_RANGE

    def profits(self, bot_role: str, constraint_user: int, constraint_bot: int):
        """Calculate profits for the bot and the user."""
        if not self.is_valid or None in (constraint_user, constraint_bot):
            self.profit_bot = -10
            self.profit_user = -10
            return

        if bot_role == 'supplier':
            self.profit_bot = self.profit_supplier(self.price, self.quality, constraint_bot)
            self.profit_user = self.profit_buyer(self.price, self.quality, constraint_user)
        else:  # ROLE_BUYER
            self.profit_bot = self.profit_buyer(self.price, self.quality, constraint_bot)
            self.profit_user = self.profit_supplier(self.price, self.quality, constraint_user)

    def evaluate(self, greedy: int) -> str:
        """Evaluate the offer against bot's greediness."""
        if self.profit_bot >= greedy:
            return ACCEPT
        elif self.is_valid:
            return NOT_PROFITABLE
        elif self.price is None and self.quality_in_range:
            return OFFER_QUALITY
        elif self.quality is None and self.price_in_range:
            return OFFER_PRICE
        elif self.price is not None and not self.price_in_range:
            return INVALID_OFFER
        elif self.quality is not None and not self.quality_in_range:
            return INVALID_OFFER
        else:
            return NOT_OFFER

    @staticmethod
    def profit_supplier(price: int, quality: int, production_cost: int) -> int:
        """Calculate profit for supplier."""
        return price - production_cost - quality

    @staticmethod
    def profit_buyer(price: int, quality: int, retail_price: int) -> int:
        """Calculate profit for buyer."""
        return retail_price - price + quality

class OfferList(list):  # A list of offers with additional methods
    def __init__(self, *args):
        list.__init__(self, *args)  # Initialize as a regular list
        self.sort(key=lambda o: o.stamp)  # Sort offers by timestamp

    def last_valid_price(self, idx: int = None) -> int:
        """Get the last valid price."""
        for offer in sorted(self, key=lambda o: -o.stamp):  # Sort by latest timestamp
            if idx is not None and offer.idx != idx:  # Skip offers from other players
                continue
            if offer.price is not None:
                return offer.price
        return 5  # Hardcoded default price

    def last_valid_quality(self, idx: int = None) -> int:
        """Get the last valid quality."""
        for offer in sorted(self, key=lambda o: -o.stamp):  # Sort by latest timestamp
            if idx is not None and offer.idx != idx:  # Skip offers from other players
                continue
            if offer.quality is not None:
                return offer.quality
        return 2  # Hardcoded default quality

    @property
    def max_profit(self) -> int:
        """Get the maximum bot profit."""
        if len(self) == 0:
            return 0
        # Hardcoded filter for valid offers
        return max([offer.profit_bot for offer in self if offer.idx != -1])

    @property
    def min_profit(self) -> int:
        """Get the minimum bot profit."""
        if len(self) == 0:
            return 0
        # Hardcoded filter for valid offers
        return min([offer.profit_bot for offer in self if offer.idx != -1])



