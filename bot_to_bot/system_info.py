# storage of system variables
from typing import Optional
from offer import Offer, OfferList 
import rnd_param
import csv
import datetime

# system storage
class Storage:
    main_bot_cons = rnd_param.main_constraint
    other_constraint = 'Unknown'
    user_message = None
    offer_user: Optional[Offer] = None
    offer_list: Optional[OfferList] = None
    interaction_list_bot2 = None
    interaction_list_bot1 = None
    offers_pareto_efficient = None
    end_convo = False


# update system - each time modify message is called this will be added. Hence the buyer price is: will be there like million times
def update_system(history):
    #hist = history[0]['content']
    #hist= history[0]['content'] + f" The buyer price is: {Storage.other_constraint}"
    return history



def saving_convo():
    with open("output.csv", "a", newline="") as f:
        writer = csv.writer(f, delimiter=",")  # Use `;` as separator
        writer.writerow([datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), rnd_param.role, rnd_param.main_constraint, rnd_param.other_constraint, 
                         Storage.offer_list[-1].price, Storage.offer_list[-1].quality, Storage.main_bot_cons, Storage.other_constraint, 
                         Storage.offer_list[-1].profit_bot, Storage.offer_list[-1].profit_user, len(Storage.offer_list), 
                         len(Storage.interaction_list_bot1) - 1,Storage.interaction_list_bot2, Storage.offer_list])  
