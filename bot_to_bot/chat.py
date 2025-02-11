import datetime # used to generate timestamps
import requests # making HTTP requests to ollama api
import json # reading javescript object notation
import sys # for command-line arguments and I/O encoding.
import activation 
import system_info
import rnd_param
import copy
from prompts import system_final_prompt

# ensure encoding is utf-8
sys.stdout.reconfigure(encoding='utf-8')

# this list will store the formatted conversation
formatted_conversation_list = []

init_chist = 0

# appends a chat_message string to the formatted_conversation_list
def _record_conversation(chat_message, suppress_print=False):
    formatted_conversation_list.append(chat_message)
    if not suppress_print:
        print(chat_message)


# check available models; if error list available models
def _get_List_of_downloaded_models():
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get('http://localhost:11434/api/tags', headers=headers)
        if response.status_code == 200:
            models = response.json()
            # check if models is a dictionary
            if isinstance(models, dict):
                model_name_List = []
                for model in models['models']:
                    model_name_List.append(model['name'])
                return model_name_List
            else:
                print('Failed to get list of models.')
                print('Response:', response.text)
                return []
        else:
            print('Failed to get list of models.')
            print('Status Code:', response.status_code)
            print('Response:', response.text)

    except requests.exceptions.RequestException as e:
        print('Failed to get list of models.')
        print('Error:', e)
        return []


# checks if a given model_name is present in downloaded models
def _is_model_available(model_name):
    models = _get_List_of_downloaded_models()
    if model_name in models:
        return True
    return False


# sends a conversation prompt/history to the Ollama endpoint (/api/chat) and streams the response
def _chat_to_ai(conversation_history, ai_number, mod_used, temperature=0.1):
    
    # update system if the parameters have been determined -> do that later
    ####!!!!


    response_chat = {
        "role": "assistant",
        "content": "",
        "options": {
            "temperature": temperature,
        }
    }

    headers = {
        'Content-Type': 'application/json'
    }

    # determine the model type
    if mod_used == 'llama3':
        llm_mod = 'llama3:latest'
    elif mod_used == 'llm_reader':
        llm_mod = 'reader:latest'
    elif mod_used == 'llm_constraint':
        llm_mod = 'constrain_reader:latest'
    elif mod_used == 'rb':
        if rnd_param.role == 'supplier':
            llm_mod = 'rb_supplier:latest'
        else:
            llm_mod = 'rb_buyer:latest'
    else:
        llm_mod = 'llama3:latest'

    # Send the chat request with history
    ollama_payload = {
        "model": llm_mod,
        "messages": conversation_history
    }

    try:
        response = requests.post('http://localhost:11434/api/chat', data=json.dumps(ollama_payload), headers=headers,
                                 stream=True)
        if response.status_code == 200:

            # Handle the stream of responses
            formatted_chat_text = ''
            for line in response.iter_lines():
                # Filter out keep-alive new lines
                if line:
                    decoded_line = line.decode('utf-8')
                    chat_response = json.loads(decoded_line)
                    chat_message = chat_response['message']['content']
                    response_chat['content'] += chat_message

                    print(chat_message, end='', flush=True)
                    formatted_chat_text += chat_message

                    # Check if the conversation is done
                    if chat_response.get('done', False):
                        # printing is suppressed because the code above has already streamed the chat to the screen
                        _record_conversation('{}\n\n'.format(formatted_chat_text.strip()), suppress_print=True)
                        break
        else:
            print('Failed to send chat request.')
            print('Status Code:', response.status_code)
            print('Response:', response.text)

    except requests.exceptions.RequestException as e:
        print('Failed to send chat request.')
        print('Error:', e)
        response_chat['content'] = 'Failed to send chat request.'

    return response_chat



# Call this function to save conversation history
def _save_conversation_json(path, conversation, display_save_message=False):
    if display_save_message:
        print('Conversation saved to {}'.format(path))
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=4)


# takes formatted_conversation_list (which is human-readable strings of the chat) and saves it to a text file.
def _save_formatted_conversation(path):
    print('Formatted Conversation saved to {}'.format(path))
    with open(path, 'w') as f:
        for line in formatted_conversation_list:
            f.write(line + '\n')
        f.write('\n\n** The End **')



def _chat_run(conversation_history, ai_number, ai_display_name, ai_other_number, counter, ai_chat):
    _record_conversation('({} of {}) {}:'.format(counter + 1, ai_chat['number_of_chat_turns'], ai_display_name))
    

    # hard coded messages bot 2 to improve performance
    if ai_number == 2 and (counter == 1 or counter == 3):
        print('\n\n')
        custom_message = {
            "role": "assistant",
            "content": conversation_history[2][-1]['content']
        }
        _record_conversation('{}\n\n'.format(custom_message['content']))
        conversation_history[2] = copy.deepcopy(system_info.Storage.interaction_list_bot2)

        # Append the custom message to Bot 2's conversation history.
        conversation_history[ai_number].append(custom_message)
        
        ai_other_message = custom_message.copy()
        ai_other_message['role'] = 'user'
        conversation_history[ai_other_number].append(ai_other_message)
        
        _save_conversation_json('ai_{}_conversation_history.json'.format(ai_number), conversation_history[ai_number])

        return  
    
    if ai_number == 2:
        model_used = 'rb'
    else:
        model_used = 'llama3'
    
    
    ai_response = _chat_to_ai(conversation_history[ai_number], ai_number, model_used, ai_chat['temperature'])
    ai_message = ai_response


    conversation_history[2] = copy.deepcopy(system_info.Storage.interaction_list_bot2)


    # Depending on which bot is sending, add the message to the proper conversation histories:
    if ai_number == 1:
        conversation_history[ai_number].append(ai_message)
        original_content = ai_message['content']
        modified_content = activation.modify_bot_message(original_content)
        ai_other_message = {
            'role': 'user',
            'content': modified_content
        }
        conversation_history[ai_other_number].append(ai_other_message)
    else:
        conversation_history[ai_number].append(ai_message)
        ai_other_message = ai_message.copy()
        ai_other_message['role'] = 'user'
        conversation_history[ai_other_number].append(ai_other_message)


    for curved_ball in ai_chat['curved_ball_chat_messages']:
        if counter == int(curved_ball['chat_turn_number']) - 1:
            print('\n\n')
            _record_conversation('\n\n(Curved Ball) {}:\n{}\n'.format(ai_display_name, curved_ball['chat_message']))
            # Append the curved-ball message to the last message of both histories:
            formatted_curved_ball_message = '\n{}'.format(curved_ball['chat_message'])
            conversation_history[ai_number][-1]['content'] += formatted_curved_ball_message
            conversation_history[ai_other_number][-1]['content'] += formatted_curved_ball_message
            break

    _save_conversation_json('ai_{}_conversation_history.json'.format(ai_number), conversation_history[ai_number])


def run_chat_interaction(ai_chat):
    save_file_name = 'chat_history/our_chat.json'  # default file name
    try:
        # Check if the models are available
        if not _is_model_available(ai_chat['ai_one_model']):
            print(
                'AI One model "{}" is not available. Please download the model first or alter the config file to use one of these models:'.format(
                    ai_chat['ai_one_model']))
            for model in _get_List_of_downloaded_models():
                print('   ' + model)
            return
        if not _is_model_available(ai_chat['ai_two_model']):
            print(
                'AI Two model "{}" is not available. Please download the model first or alter the config file to use one of these models:'.format(
                    ai_chat['ai_two_model']))
            for model in _get_List_of_downloaded_models():
                print('   ' + model)
            return

        # create_a_conversation_history_file
        save_file_name = 'chat_history/ai_chat_{}_between_{}_and_{}.json'.format(
            datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),
            ai_chat['ai_one_conversation_history'][0][
                'display_name'],
            ai_chat['ai_two_conversation_history'][0][
                'display_name'])
            # Print the AI display names by using a list, so we can easily switch between the two AIs using 1 or 2
            # for AI One or AI Two
        ai_display_name = [None, ai_chat['ai_one_conversation_history'][0]['display_name'],
                           ai_chat['ai_two_conversation_history'][0]['display_name']]

        _record_conversation(
            "Starting chat between {} and {} in '{}'...\n".format(ai_display_name[1], ai_display_name[2],
                                                                    ai_chat['title']))
        _record_conversation(
            'AI One ({}) style is: {}'.format(ai_display_name[1], ai_chat['ai_one_conversation_history'][0]['content']))
        _record_conversation(
            'AI Two ({}) style is: {}'.format(ai_display_name[2], ai_chat['ai_two_conversation_history'][0]['content']))
        _record_conversation('-----')
        _record_conversation(
            '{} started the conversation: {}'.format(ai_chat['ai_two_conversation_history'][0]['display_name'],
                                                        ai_chat['ai_one_conversation_history'][1]['content']))
        _record_conversation('-----')

        print('(First chat output may be delayed while AI model is loaded...)')

        # by storing the conversation history in a list, we can easily switch between the two AIs: 1 or 2 for AI One or AI Two
        conversation_history = [None, ai_chat['ai_one_conversation_history'], ai_chat['ai_two_conversation_history']]
        
        chatting_to_ai_one = True
        chat_counter = 0
        
        copied_start = ai_chat['ai_two_conversation_history'].copy()
        copied_start2 = ai_chat['ai_one_conversation_history'].copy()
        part_copied1 = ai_chat['ai_one_conversation_history'][-1]['content'][:]

        global init_chist
        if init_chist == 0:
            system_info.Storage.interaction_list_bot2 = []
            system_info.Storage.interaction_list_bot2.extend(copied_start)
            system_info.Storage.interaction_list_bot2.append({
                        'role': 'assistant',
                        'content': part_copied1
                    })
            system_info.Storage.interaction_list_bot1 = []
            system_info.Storage.interaction_list_bot1.extend(copied_start2)
            init_chist = 1



        while True or chat_counter < int(ai_chat['number_of_chat_turns']):

            ai_number = 1 if chatting_to_ai_one else 2
            ai_other_number = 2 if chatting_to_ai_one else 1

            # Time to say goodbye
            if chat_counter >= int(ai_chat['number_of_chat_turns']) - 2:
                conversation_history[ai_number].append(ai_chat['ai_final_chat_message'][str(ai_other_number)])
                _record_conversation('\n\n(Saying goodbye) {}:\n{}\n'.format(ai_display_name[ai_other_number],
                                                                                ai_chat['ai_final_chat_message'][
                                                                                    str(ai_other_number)]['content']))
            

            # store clean conversation history
            if chat_counter > 0:
                if ai_number == 2:
                    temp_msg = conversation_history[1][-1]['content']
                    system_info.Storage.interaction_list_bot2.append({
                        'role': 'user',
                        'content': temp_msg
                    })
                    
                    system_info.Storage.interaction_list_bot1.append({
                        'role': 'assistant',
                        'content': temp_msg
                    })
                else:
                    temp_msg = conversation_history[2][-1]['content']
                    system_info.Storage.interaction_list_bot2.append({
                        'role': 'assistant',
                        'content': temp_msg
                    })
                    
                    system_info.Storage.interaction_list_bot1.append({
                        'role': 'user',
                        'content': temp_msg
                    })
            

            #print(f'Convo hist {conversation_history}, ai number: {ai_number}')
            #print(f'Conversation history ai 2 (supplier): {conversation_history[2]}')
            #print(f'interaction: {system_info.Storage.interaction_list_bot2}')

            # Perform a chat - calls interaction !!!
            _chat_run(conversation_history, ai_number, ai_display_name[ai_number], ai_other_number, chat_counter,
                      ai_chat)
                
            if system_info.Storage.end_convo == True:
                chat_counter += 1
                
                
                #### Save chat history
                if ai_number == 1:
                    temp_msg = conversation_history[1][-1]['content']
                    system_info.Storage.interaction_list_bot2.append({
                        'role': 'user',
                        'content': temp_msg
                    })
                    
                    system_info.Storage.interaction_list_bot1.append({
                        'role': 'assistant',
                        'content': temp_msg
                    })
                else:
                    temp_msg = conversation_history[2][-1]['content']
                    system_info.Storage.interaction_list_bot2.append({
                        'role': 'assistant',
                        'content': temp_msg
                    })
                    
                    system_info.Storage.interaction_list_bot1.append({
                        'role': 'user',
                        'content': temp_msg
                    })
                ####

                _chat_run(conversation_history, ai_other_number, ai_display_name[ai_other_number], ai_number, chat_counter, ai_chat)
                
                if ai_number == 2:
                    temp_msg = conversation_history[1][-1]['content']
                    system_info.Storage.interaction_list_bot2.append({
                        'role': 'user',
                        'content': temp_msg
                    })
                    
                    system_info.Storage.interaction_list_bot1.append({
                        'role': 'assistant',
                        'content': temp_msg
                    })
                else:
                    temp_msg = conversation_history[2][-1]['content']
                    system_info.Storage.interaction_list_bot2.append({
                        'role': 'assistant',
                        'content': temp_msg
                    })
                    
                    system_info.Storage.interaction_list_bot1.append({
                        'role': 'user',
                        'content': temp_msg
                    })
                ####


                system_info.saving_convo()
                print("\n\nNegotiation has reached a deal. Ending chat.")

                break  # Exit loop when DEAL is detected

            # Swap AIs
            chatting_to_ai_one = not chatting_to_ai_one
            chat_counter += 1
        
        
    except KeyboardInterrupt:
        print('Chat ended.')
        # create a file name that includes date and time:

        print('Conversation history saved {}.json.'.format(save_file_name))

    finally:
        print('\n\n')
        _save_conversation_json(save_file_name, ai_chat, display_save_message=True)
        _save_formatted_conversation(save_file_name.replace('.json', '_formatted.txt'))



if __name__ == '__main__':
    if len(sys.argv) > 1:
        ai_chat_file = sys.argv[1] + ('' if sys.argv[1].endswith('.json') else '.json')
    else:
        print('Please specify the AI chat file as a command-line parameter.')
        sys.exit(1)

    with open(ai_chat_file) as f:
        ai_chat_config = json.load(f)
    
    ai_chat_config['ai_one_conversation_history'][0]['display_name'] = rnd_param.role_other
    ai_chat_config['ai_two_conversation_history'][0]['display_name'] = rnd_param.role
    
    # give prompt dynamically
    if rnd_param.role == 'supplier':
        ai_chat_config['ai_two_conversation_history'][0]['content'] = f"Your Base Production Cost is {rnd_param.main_constraint}."
    else:
        ai_chat_config['ai_two_conversation_history'][0]['content'] = f"Your Base Retail Price is {rnd_param.main_constraint}."
    
    initial_msg = activation.initial()

    
    # Ensure ai_one_conversation_history has at least two entries
    if len(ai_chat_config["ai_one_conversation_history"]) > 1:
        ai_chat_config["ai_one_conversation_history"][1]["content"] = initial_msg
    else:
        sys.exit(1)
    
    run_chat_interaction(ai_chat_config)

