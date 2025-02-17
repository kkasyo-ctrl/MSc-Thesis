import re
from storage import rb_storage

def extract_other_constraint(text):
    # This pattern looks for the phrase "base production cost", then any characters
    # (non-greedy), followed by a Euro symbol (€) and optional whitespace, then captures
    # one or more digits (which can optionally include a decimal point).
    if rb_storage.bot_role == 'buyer':
        pattern = r"base production cost.*?€\s*([\d\.]+)"
    elif rb_storage.bot_role == 'seller':
        pattern = r"retail selling price.*?€\s*([\d\.]+)"
    
    # re.IGNORECASE: makes the search case-insensitive.
    # re.DOTALL: allows the dot (.) to match newline characters as well.
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    
    if match:
        cost_str = match.group(1)
        return float(cost_str) if '.' in cost_str else int(cost_str)
    return None

# Example message text
message = """ Hi! I'm excited to start our negotiation. As we begin, I'd like to get a sense of your needs and constraints. Can you share with me your Base Production Cost?"}, {'role': 'user', 'content': "As the supplier, my base production cost for the 10kg bag of wood pellets at quality level 0 is €2 per unit. This will serve as the foundation for our negotiation on wholesale price and quality. Now that we have this important information established, I'm ready to start discussing a mutually beneficial agreement with you!"""

# Extracting the base production cost
base_cost = extract_base_production_cost(message)
print("Base production cost:", base_cost)
