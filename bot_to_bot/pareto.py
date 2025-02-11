from typing import Tuple

from offer import Offer, OfferList
from prompts import PROMPTS
from rnd_param import QUALITY_RANGE, PRICE_RANGE

# this is needed because user can suggest better than pareto efficient offer
def pareto_efficient(offer: Offer, all_offers: OfferList) -> bool:
    # Check if an offer is Pareto efficient among all offers.

    def coll_abs(o: Offer) -> Tuple[int, int]:
        # Calculate collective profit and absolute profit difference.
        return o.profit_user + o.profit_bot, abs(o.profit_user - o.profit_bot)

    collective_profit, abs_difference = coll_abs(offer)  # Current offer metrics

    for other_offer in all_offers:
        if offer == other_offer:  # Skip the current offer
            continue
        other_collective_profit, other_abs_difference = coll_abs(other_offer)

        # If another offer dominates in both metrics, the current offer is not Pareto efficient
        if other_collective_profit > collective_profit and \
                other_abs_difference <= abs_difference:
            return False
        if other_collective_profit >= collective_profit and \
                other_abs_difference < abs_difference:
            return False
    return True  # The offer is Pareto efficient


def get_efficient_offers(constraint_user: int,
                         constraint_bot: int,
                         bot_role: str) -> OfferList:
    # Generate all offers and filter Pareto-efficient ones.

    offer_list = OfferList()  # List to store all possible offers
    for price in PRICE_RANGE:  # Iterate over all possible prices
        for quality in QUALITY_RANGE:  # Iterate over all possible qualities
            offer = Offer(price=price, quality=quality, idx=0)
            offer.profits(bot_role, constraint_user, constraint_bot)  # Calculate profits
            offer_list.append(offer)

    efficient_offer_list = OfferList()  # List for Pareto-efficient offers
    for offer in offer_list:
        if pareto_efficient(offer, offer_list):  # Check if the offer is Pareto efficient
            efficient_offer_list.append(offer)

    return efficient_offer_list  # Return the filtered list


# determines the optimal Pareto-efficient profit for the bot, depending on its "greediness."
def pareto_efficient_offer(constraint_user: int,
                           constraint_bot: int,
                           bot_role: str,
                           max_greedy: bool) -> int:
    # Get the maximum or minimum profit from Pareto-efficient offers.

    efficient_offers_for_bot = \
        get_efficient_offers(constraint_user, constraint_bot, bot_role)

    if max_greedy:
        return efficient_offers_for_bot.max_profit  # Return the maximum profit
    else:
        return efficient_offers_for_bot.min_profit  # Return the minimum profit



def pareto_efficient_string(constraint_user: int,
                            constraint_bot: int,
                            bot_role: str) -> str:
    # Generate a string of Pareto-efficient offers.

    efficient_offers_for_bot = get_efficient_offers(
        constraint_user, constraint_bot, bot_role)

    profits_bot = [offer.profit_bot for offer in efficient_offers_for_bot]  # Bot profits
    max_profit_bot = max(profits_bot)  # Find the maximum bot profit

    # Get the best offers that yield the maximum profit
    best_offers = [o for o in efficient_offers_for_bot
                   if o.profit_bot == max_profit_bot]

    # Format the best offers into a string
    return ' | '.join(
        PROMPTS['offer_string'] % (o.price, o.quality) for o in best_offers)
