#### Activation 
# import packages
import rnd_param
import logic
import json
import random
from typing import Any, List, Union
from system_info import Storage
from pareto import pareto_efficient_string
from offer import (Offer, OfferList, ACCEPT, OFFER_QUALITY, OFFER_PRICE,
                    NOT_OFFER, INVALID_OFFER, NOT_PROFITABLE)
from prompts import (PROMPTS, not_profitable_prompt, empty_offer_prompt,
                      offer_without_price_prompt, offer_without_quality_prompt,
                      offer_invalid)


# load the supplier-buyer chat history
with open('supplier_buyer.json', 'r') as f:
    supplier_buyer = json.load(f)

# modify the bot message based on the execution count
execution_count = 0  
def modify_bot_message(message):
    global execution_count 
    if execution_count == 0: 
        execution_count += 1
        return constraint_initial(message)
    elif execution_count == 1: 
        execution_count += 1
        return constraint_final(message)
    elif execution_count == 2:
        execution_count += 1
        test = interpretation(message)
        return test
    else:  
        return interpretation(message)



# sends the initial message to the conterpart based on the bot’s role (buyer or supplier)
def initial():
    if rnd_param.role == "buyer":
        message = PROMPTS['first_message_PC']
    else:
        message = PROMPTS['first_message_MP']
    
    return message

# asks the counterparts for their initial constraints (e.g., production cost or retail price)
def constraint_initial(message):

    constraint_user = logic.interpret_constraints(message, ai_number=2, ai_chat=supplier_buyer)
    context_constraint = PROMPTS['context_constraint'][rnd_param.role]

    if logic.constraint_in_range(constraint_user):
        params = (constraint_user, context_constraint) * 2
        message = PROMPTS['constraint_confirm'] % params
    else:
        message = PROMPTS['constraint_clarify'] % context_constraint

    return message


# store the final constraint
def constraint_final(inp_msg):
 
    if not inp_msg.isdigit():
        constraint_user = logic.interpret_constraints(inp_msg)
    else:
        constraint_user = inp_msg

    message = final_constraint = None
    if constraint_user is not None:
        if rnd_param.role == 'supplier':
            if logic.constraint_in_range(constraint_user):
                message = PROMPTS['constraint_final_buyer']
                final_constraint = constraint_user
        
        else:
            if logic.constraint_in_range(constraint_user):
                message = PROMPTS['constraint_final_supplier']
                final_constraint = constraint_user
    if message is None or final_constraint is None:
        message = PROMPTS['constraint_persisting']
        final_constraint = logic.constant_draw_constraint()


    Storage.other_constraint = int(final_constraint)
    return message


# interpret the counterpart's offer and determine the state of the conversation
def interpretation(message):
    global execution_count
    if execution_count == 3:
        state = "CONTINUE"
    else:
        state = determine_state()
    
    if state == "CONTINUE":    
        Storage.offer_user = logic.interpret_offer(message, ai_number=2, ai_chat=supplier_buyer)
        if Storage.offer_list is None:
            Storage.offer_list = OfferList()
        Storage.offer_list.append(Storage.offer_user)
        Storage.user_message = message
        return evaluate()

    elif state == "DEAL":
        Storage.end_convo = True
        return PROMPTS['end_negotiation'] % message


# evaluate the counterpart's offer and determine the bot’s response
def evaluate():
    print('evaluate')
 
    if Storage.offer_list is not None:
        for off in Storage.offer_list:
            logic.add_profits(off)


    greedy = logic.get_greediness(Storage.other_constraint, rnd_param.main_constraint)  
    print(f'greedy: {greedy}') 
    Storage.offers_pareto_efficient = pareto_efficient_string(
        Storage.other_constraint, Storage.main_bot_cons, rnd_param.role
    )
    
    evaluation = Storage.offer_user.evaluate(greedy)

    if evaluation == ACCEPT:
        return accept_offer()
    elif evaluation in (NOT_PROFITABLE, OFFER_PRICE, OFFER_QUALITY):
        return respond_to_offer(evaluation, greedy)
    elif evaluation in (INVALID_OFFER, NOT_OFFER):
        return respond_to_non_offer(evaluation, greedy)
    else:
        raise Exception


# respond to offer in case the offer is not profitable, the quality or price is not provided
def respond_to_offer(evaluation: str, greedy: int):
    print(f'respond_to_off with evalutation: {evaluation}')

    content1 = get_respond_prompt(evaluation)

    llm_offers = []
    last_offer = None

    while len(llm_offers) < 3 and evaluation != ACCEPT:
        response = logic.get_llm_response(content1, ai_number=2, ai_chat=supplier_buyer)
        last_offer = logic.interpret_offer(response, ai_number=2, ai_chat=supplier_buyer)

        if last_offer.is_complete:
            logic.add_profits(last_offer)
        else:
            last_offer.profit_bot = 0
            last_offer.profit_user = 0

        llm_offers.append([last_offer.profit_bot, response, last_offer])
        evaluation = last_offer.evaluate(greedy)
        print(f'Evalutation from the while loop: {evaluation}')
        print(f'Offer in offer.py: {OfferList}')
        
    return send_response(evaluation, last_offer, response, llm_offers)


# provide the RB bot's prompt for generating the response
def get_respond_prompt(evaluation: str) -> str:
    if evaluation == NOT_OFFER:
        return empty_offer_prompt(
            Storage.user_message, Storage.offers_pareto_efficient, str(Storage.interaction_list_bot2)
        )
    elif evaluation == OFFER_QUALITY:
        return offer_without_price_prompt(
            Storage.user_message, Storage.offers_pareto_efficient, str(Storage.interaction_list_bot2)
        )
    elif evaluation == OFFER_PRICE:
        return offer_without_quality_prompt(
            Storage.user_message, Storage.offers_pareto_efficient, str(Storage.interaction_list_bot2)
        )
    elif evaluation == INVALID_OFFER:
        return offer_invalid(Storage.user_message)
    else:
        return not_profitable_prompt(
            Storage.user_message, Storage.offers_pareto_efficient, str(Storage.interaction_list_bot2)
        )


# decide what to return to the RB bot
def send_response(evaluation: str, last_offer: Offer,
                  llm_output: str, llm_offers: List[List[Union[int, Any]]]):
    print('send_response')

    if evaluation != ACCEPT:
        max_profit = max(llm_offer[0] for llm_offer in llm_offers)
        best_offer = random.choice([llm_offer for llm_offer in llm_offers
                                    if llm_offer[0] == max_profit])
        _, llm_output, last_offer = best_offer


    if last_offer is not None and last_offer.is_valid:
        Storage.offer_list.append(last_offer)
    if llm_output is not None:
        test = PROMPTS['return_same_message'] % llm_output
        return test


# accept the bots offer
def accept_offer():
    print('accept')
    content = PROMPTS['accept_from_chat'] + Storage.user_message
    Storage.end_convo = True
    accept_final_chat()

    return content

# store the final offer in the storage
def accept_final_chat():
    bot_offer = Offer(
        idx=-1,
        price=Storage.offer_user.price,
        quality=Storage.offer_user.quality,
        test="accept_final_chat"
    )
    logic.add_profits(bot_offer)
    Storage.offer_list.append(bot_offer)


# respond to the counterpart's offer in case the offer is not valid or no offer is provided
def respond_to_non_offer(evaluation: str, greedy: int):
    print(f'respond_to_non_off with evalutation: {evaluation}')
    
    content1 = get_respond_prompt(evaluation)

    llm_offers = []
    last_offer = None

    while len(llm_offers) < 3 and evaluation != ACCEPT:
        response = logic.get_llm_response(content1, ai_number=2, ai_chat=supplier_buyer)
        last_offer = logic.interpret_offer(response, ai_number=2, ai_chat=supplier_buyer)

        if last_offer.is_complete:
            logic.add_profits(last_offer)
        else:
            last_offer.profit_bot = 0 
            last_offer.profit_user = 0

        llm_offers.append([last_offer.profit_bot, response, last_offer])
        evaluation = last_offer.evaluate(greedy)
        print(f'Evalutation from the while loop: {evaluation}')
        print(f'Offer in offer.py: {Offer}')
        
    return send_response(evaluation, last_offer, response, llm_offers)



# determine the state of the conversation
def determine_state():
    state = PROMPTS['evaluate_situation'] % Storage.interaction_list_bot2
    response = logic.get_llm_response(state, ai_number=2, ai_chat= supplier_buyer)

    return response
