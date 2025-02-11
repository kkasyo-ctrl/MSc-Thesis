# Role-based system storage
# import packages 
import sys
import os

folder_path = os.path.abspath('C:/Users/david/Desktop/MSc Thesis/Code_OG_Mine/bot_to_bot')  
if folder_path not in sys.path:
    sys.path.insert(0,folder_path)
import rnd_param 

import analyze_message

class rb_storage:
    bot_role = rnd_param.role_other
    bot_constraint = rnd_param.other_constraint
    other_constraint = 'Unknown'
    user_message = None
    interaction_list_bot1 = None
    offers_pareto_efficient = None
    end_convo = False
    
