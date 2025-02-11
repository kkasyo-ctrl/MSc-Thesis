# random parameters
import random
import re 



# possible values
PRICE_RANGE = range(1, 15)
QUALITY_RANGE = range(0, 5)


# fomulas 
def profit_sup(PC, quality, neg_price ):
    profit_supplier = neg_price - PC - quality
    return profit_supplier

def profit_buy(MP, quality, neg_price):
    profit_buyer = MP + quality - neg_price
    return profit_buyer


# turn off greediness
greedy = 0 


role = 'buyer'
role_other = 'supplier'

if role == 'supplier':
    # supplier parameters
    #main_constraint = random.randint(1,3) 
    # comment it out
    main_constraint = 2
    # buyer parameters
    #other_constraint = random.randint(8,10)
    other_constraint = 9
else:  
    # buyer parameters
    #main_constraint = random.randint(8,10)
    main_constraint = 9
    # buyer parameters
    #other_constraint = random.randint(1,3)
    other_constraint = 2


PATTERN_CONSTRAINT = re.compile(r'\[.*?\]')
PATTERN_OFFER = re.compile(r'\[(?=[^\]]*(?:€|\$))([^\]]+)\]')
