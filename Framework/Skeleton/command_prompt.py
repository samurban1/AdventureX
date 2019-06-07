"""Handles the input from the user."""
from Skeleton.classes import *
from Parser import omni_parser
import copy
import re


def print_big(action):
    """Prints a header and the action that is being tested."""
    print('\n' + Colors.BOLD + Colors.BLACK_W_BG + '---NEW---' + Colors.END)
    print(Colors.BOLD + Colors.YELLOW + action.upper() + Colors.END)


def condense_and_split(p_input):
    """Condenses preliminary input. Removes predefined stop phrases and removes articles.
    :returns Nicely stripped player input, without anything extra. No articles and no stop phrases."""

    def and_strip(sentence, sub):
        """If the sentence starts or ends with whatever is passed in for {sub}, remove it."""
        if sub == 'go':
            if sentence.startswith('go') and not sentence.startswith('go and'):  # if it starts with 'go' and doesn't start
                # with 'go and', because 'go and' is a stop phrase anyways (defined below)
                if len(sentence.split()) >= 2:  # if there is a second word in the sentence
                    direction = check_for_dir(sentence[1])
                    if not direction[0]:  # if check_for_dir returned (False, None), direction[0] == False
                        sentence = sentence[len('go'):]  # remove the 'go'
        else:
            if sentence.startswith(sub):
                sentence = sentence[len(sub):]
            if sentence.endswith(sub):
                sentence = sentence[:-len(sub)]
        return sentence

    def missing_and(command):
        """Check if the user command contains multiple commands without an AND character separating them."""

        def multiple(iterable):
            """Similar to python builtins all() and any(), but this function checks if more than
            one element in iterable is True."""
            truthy_counter = 0
            for element in iterable:
                if element:
                    truthy_counter += 1
                if truthy_counter == 2:
                    return True
            return False

        valid_verbs = [command_set['verbs'] for command_set in LOCATIONS[player.active_location].commands]
        loc_commands = [LOCATIONS[location].commands for location in LOCATIONS if player.active_location != location]
        invalid_loc_verbs = []
        for cmd in loc_commands:
            if cmd:
                for verb_set in cmd:
                    invalid_loc_verbs.extend(verb_set['verbs'])
        # print('all verb tags:', word_tag_set)
        multiple_verb_conditions = ['VB' in tag
                                    or (word not in invalid_loc_verbs and word in valid_verbs)
                                    for word, tag in command]
        if multiple(multiple_verb_conditions):
            return True

        #
        # both_dicts = [COMMANDS['builtin_commands'], COMMANDS['custom_commands']]  # combine both
        # location_cmds = [LOCATIONS[location].commands for location in LOCATIONS if LOCATIONS[location].commands]
        # both_dicts.extend(location_cmds)
        #
        # all_commands = []
        # # Get all the verbs
        # for dictionary in both_dicts:  # loop over each in both dicts
        #     for verb_set in dictionary:  # each verb_set is the dictionary containing all the verbs and respective functions/actions
        #         for word in verb_set['verbs']:
        #             all_commands.append(word)  # add the word
        #
        # # Check if command contains multiple verbs. The command passed in was already stripped of all ANDs and split into
        # # separate commands based on those ANDs, so anything passed in should only have one verb in it. If it has nultiple
        # # verbs, then we know there is a missing AND.
        # verb_counter = 0
        # print('all_cmds:', all_commands) if debug else None
        # for word in command:
        #     print('word to check for missing and:', word) if debug else None
        #     print(f"{word} in all commands: {word in all_commands}") if debug else None
        #     if word in all_commands and not is_partial(word, command, all_commands, typ='VERB'):
        #         verb_counter += 1
        # if verb_counter > 1:
        #     return True  # True that there is an AND missing
        return False

    ands = ('and', 'then', ',', ';', '.')
    for item in ands:
        p_input = and_strip(p_input.strip(), item)  # strip every 'and' character from the beginning and end

    print('pinput after strip ands:', p_input) if debug else None
    stop_phrases = ['go and', 'go forth and', 'go ahead and']  # The reason stop_phrases is separate is to make it easy
    # for the user in case they want to add more.
    split_by = r'(;)|(,)|(\.)|( ?save ?)|( ?(resume|load) ?)| a | an | ?the | that is '  # 'that is' removed in a case of
    # 'take the egg that is in the backpack' / or 'attack the troll that is guarding'. The '?the' allows the user to type
    # in thelantern, but it is necessary in the case of 'take lantern;the egg'.

    for phrase in stop_phrases:
        split_by += f'| ?{phrase} '  # add the stop phrases to the regex expression

    split = re.split(split_by, p_input)  # split by all the delimiters -- the delimiters in parentheses will be kept,
    # those not in parentheses (a, an, the) will be removed.
    final = []
    # re.split() will return None because you have more than one capturing groups, and all groups are included as a part
    # of the re.split() result, so anything that doesn't match to all the groups will return None. So filter out the None
    # and turn the iterator returned by filter into a list.
    for word_set in list(filter(None, split)):
        for word in word_set.split():  # split automatically strips the whitespaces
            final.append(word.lower())

    # go through each word and if its not an AND, add it to the list of commands. If there is an AND, then check if the word
    # after it is a verb, and if yes, then take the current list of commands and put that in a sublist within itself. If not,
    # then add the word (which is after the AND) to the list of commands.
    separated_cmds = [[]]
    index_of_sublist, i = 0, 0

    words_to_remove = ['times']
    while i < len(final):
        regular_appendage = True
        if final[i] in ands:
            regular_appendage = False  # if the word is an AND, for sure don't add it to the list of commands
            next_word_is_verb = check_for_verb(final[i+1], final)[0]
            next_word_is_dir = check_for_dir(final[i+1])[0]
            if next_word_is_verb or final[i+1] in ('save', 'exit', 'resume', 'load'):
                index_of_sublist += 1
                separated_cmds.insert(index_of_sublist, [])
            elif next_word_is_dir:
                x = i+1
                no_verb_yet = True
                while x >= 0:  # loop backwards
                    verb = check_for_verb(final[x], final)[0]
                    if verb:
                        if verb != 'turn':
                            no_verb_yet = False
                    x -= 1
                if not no_verb_yet:
                    index_of_sublist += 1
                    separated_cmds.insert(index_of_sublist, [])

        if regular_appendage and final[i] not in words_to_remove:  # remove words in a case of 'go north 5 times', or whatever
            # is defined in words_to_remove above
            print(f'appending {final[i]} to separated cmds: {separated_cmds}') if debug else None
            separated_cmds[index_of_sublist].append(final[i])
        i += 1




    # turn right, left
    # turn towards the right, the left

    for command in separated_cmds:
        temp_command = command[:]
        tagged_cmd = pos_tagger(temp_command)[0]
        if missing_and(tagged_cmd):
            correcting_input = input("There seems to be multiple commands in your input, one or more of which are not "
                                     "separated by an 'and' character.\nIf I am wrong, don't type anything and just press enter."
                                     "\nIf not, enter your command again: ")
            if correcting_input:
                separated_cmds = condense_and_split(correcting_input)

            # break
    return separated_cmds


def partial_understanding(command, unparsed):
    """Checks if part of the command was understood and asks user if they want to execute the understood part."""
    not_understood = [word for word in unparsed if word != ' ']
    yes_understood = [(word, tag) for word, tag in command if tag != 'ERR']
    print(f"not understood: {not_understood}, yes understood: {yes_understood}") if debug else None
    if len(not_understood) > 0 and len(yes_understood) > 1:  # there are some not-understood words and there is at
        # least 1 word that IS understood. If there are no words that are understood, then why bother going through a
        # function that tells the user what it DOES understand from the command when it does't understand anything
        # in the first place?!
        errors = turn_to_sentence(not_understood, "I don't understand ", 'or')
        amt_of_matches = list(omni_parser.get_labels_and_matches(yes_understood))
        print('amt of matches:', amt_of_matches) if debug else None
        if len(amt_of_matches) == 0:  # if there are NO matches to any of the defined chunks in the parser grammar
            response = random_response('invalid')
            print(response)  # then tell them that their command was stupid and invalid
            logging.error(response)
            return None
        else:
            yes_understood = ' '.join([word for word, tag in amt_of_matches[0][1]])
            space = '' if len(not_understood) > 2 else ' '
            yes_understood = yes_understood.replace('goto', 'go')
            question = f"{space}but in my limited understanding, am I correct in that you want to {yes_understood}?"
            logging.error(errors + question)
            if not ask_until_respond(errors + question):
                print('Okay, okay...Jeez.')
                logging.error('Okay, okay...Jeez.')
                return None
            command = amt_of_matches[0][1]
            print('command after saying yes:', command)
            return command
    else:
        return command


def ask_for_unprovided_if_any(command):
    """Asks the user to provide any unprovided objects/verbs/anything missing in their command."""
    unprovided = omni_parser.get_labels_and_matches(command, typ='ERRORS')
    for label, match in unprovided:
        print('ERROR | label:', label, 'match:', match) if debug else None
        error = omni_parser.cmd_with_unprovided(label, match, command)
        print('error returned from cmd_with_unprovided:', error) if debug else None
        if error:
            if type(error) is str:
                print(error)
                return None
            else:
                insert_word, index_to_insert, message = error
                print(message)
                intermediate_cmd = input('FIX COMMAND ◢▲◢◣◢▲◣ ')
                if label == 'OBJ/ACT':
                    while 'it' not in intermediate_cmd:
                        print(random_response('invalid'))
                        intermediate_cmd = input(' ')
                        full_input = intermediate_cmd.replace('it', insert_word)
                else:
                    intermediate_cmd = intermediate_cmd.split()
                    intermediate_cmd.insert(index_to_insert, insert_word)
                    full_input = ' '.join(intermediate_cmd)
                full_input = condense_and_split(full_input)
                input_handler(full_input)
                return None
        else:
            return command
    return command


def not_full_match(command):
    """Checks if the player's command is not a full match, meaning: The matched chunk of the player's command does not cover
    the entire command; i.e. there are some parts of the player's command that was chunked, but not the whole thing,
    so the command doesn't make sense."""
    matches_list = list(omni_parser.get_labels_and_matches(command))
    if len(matches_list) == 0:
        response = random_response('invalid')
        print(response)
        logging.error(response)
        return None
    chunked_part = matches_list[0][1]
    if len(command) > len(chunked_part):
        # print("The command that the player passed in is greater than the part of the command that was chunked. Meaning,"
        #     "there are some parts of the player's command that was chunked, but not the whole thing, so their command"
        #     "doesn't make sense.")
        # print(f"btw, the chunked part is {chunked_part}")
        response = random_response('partial match')
        print(response)
        logging.error(response)
        return None
    else:
        return command


def bad_location_verb(command):
    try:
        loc_verb_index = [tag for word, tag in command].index('ERR')
    except ValueError:
        return command
    location_verb = command[loc_verb_index][0]
    valid_verbs = [command_set['verbs'] for command_set in LOCATIONS[player.active_location].commands]
    loc_commands = [LOCATIONS[location].commands for location in LOCATIONS if player.active_location != location]
    invalid_verbs = []
    for cmd in loc_commands:
        if cmd:
            for verb_set in cmd:
                invalid_verbs.extend(verb_set['verbs'])
    if location_verb not in valid_verbs:
        if location_verb in invalid_verbs:
            print(f"You can't do that here.")
            return None
    return command


def filter_all_except_command(method, arguments, container=None):
    """
    Filters the objects/actors passed in. Either returns them all, or everything BUT the ones explicitly excluded.
    :param method: the function name
    :param arguments: the arguments to be passed into the method. The first one is either "ALL" or "ALL-BUT", and the rest
    (if there is a BUT) are the objects/actors that should not be included as arguments.
    :param container: optional, if given then 'all' refers to everything inside the container.
    :return: the objects/actors to pass into the method.
    """

    if container:  # if taking from a container
        print(f"all things in {container}'s inventory: {OBJECTS[container].inventory}")
        all = OBJECTS[container].inventory[:]  # it is necessary to make a COPY of the inventory list instead of just setting
        # all to the list, because when all changes, the inventory will change, which is Badddddd.
    elif method in ('take', 'describe'):
        objects = LOCATIONS[player.active_location].objects
        objs_in_containers = []
        for obj in objects:
            if isinstance(OBJECTS[obj], Container) and not OBJECTS[obj].locked:
                for cont_obj in OBJECTS[obj].inventory:
                    objs_in_containers.append(cont_obj)
        all = [obj for obj in objects if not obj_in_container(obj, status='locked')] + objs_in_containers
        error_text = "There is no {} to not {}, sorry."
    elif method in ('throw', 'drop'):
        all = [obj for obj in player.inventory if obj not in ('hand', 'leg')]
        error_text = "You don't have a {} to not {}, sorry."

    print('all before filtering:', all) if debug else None
    if 'BUT' in arguments[0]:
        args_to_loop_over = arguments[2:] if container else arguments[1:]
        for but in args_to_loop_over:
            print('but:', but) if debug else None
            try:
                all.remove(but)
            except ValueError:
                print(error_text.format(but, method))
    print('all after filtering:', all) if debug else None
    return all


def input_handler(player_input):
    """Gets input from user, strips it down to most essential components, runs it through the POS tagger, gets matches,
    and calls appropriate functions."""

    for command_set in player_input:
        print('command set in player_input:', command_set) if debug else None

        if not command_set:  # if input is empty
            print('Please enter SOMETHING. I mean, anything, really, but something.')
            return

        # checking for builtin one-word commands.
        special_commands = {
            'save': GameHandler.save,
            'load': GameHandler.load,
            'quit': quit,
            'inventory': lambda: player.describe('inventory'),
            'diagnose': lambda: player.describe('health'),
            'look': lambda: player.describe(player.active_location),
            'leave': lambda: player.goto(player.places_traveled[-1])
        }

        if command_set[0] in special_commands:
            special_commands[command_set[0]]()
            return

        command, unparsed = pos_tagger(command_set)  # parsing the text and getting tagged command back

        logging.debug(f"User Command: {command}. Unparsed: {unparsed}")
        print('\nFINAL command:', command) if debug else None
        print('skeleton:', unparsed, '\n') if debug else None

        for cmd_check_func in [bad_location_verb,  # this must be first to ensure that the error evaluates
                              partial_understanding,
                              ask_for_unprovided_if_any,
                              not_full_match]:
            if cmd_check_func is partial_understanding:
                command_check = cmd_check_func(command, unparsed)
            else:
                command_check = cmd_check_func(command)
            if command_check is None:
                return
            else:
                command = command_check

        tags = [tag for word, tag in command]

        if 'LVB' in tags:
            location_cmd = command[0][0]
            approved, fail_msg = verify_actionability('action', player.active_location, action_or_state=location_cmd)
            if not approved:
                print(fail_msg)
                return
            for loc_cmd_set in LOCATIONS[player.active_location].commands:
                if location_cmd in loc_cmd_set['verbs']:
                    actions = loc_cmd_set.get('actions')

            try:
                if actions:
                    exec_actions_if_any(actions)
                LOCATIONS[player.active_location].react(location_cmd)
            except Exception as error:
                if len(error.args[0]) > 0:  # args[0] contains a list with all the errors
                    all_errors = [str(e) for e in error.args[0]]  # str(e) returns just the error message
                    unique_errors = list(set(all_errors))  # set() removes the duplicates
                    for e in unique_errors:
                        print(e)  # e is the custom error message itself

        elif 'VB' in tags:
            matches = omni_parser.get_labels_and_matches(command)
            for label, match in matches:
                custom_func, items, with_object = omni_parser.exec_custom_func_from_cmd(label, match)
                print('RESULTS:', custom_func, items, with_object)

            for obj_command in COMMANDS['custom_commands']:
                for item in items:
                    print('item in loop:', item)
                    if item in obj_command['valid_items'] and custom_func == obj_command['verbs'][0]:
                        if with_object:
                            if not obj_command.get('optional_argument'):  # if there is no option for an optional argument
                                # for this specific command, then tell the player that.
                                print(f"You can't use an object to do that.")
                                return
                            else:
                                if with_object == obj_command['optional_argument']:
                                    # if user specifically asked to open door with key, then verify_actionability() will check
                                    # the action requirement of opening the door, if there is a specific key in action requirement
                                    # dict called 'key', then the conditions will be evaluated.
                                    approved, fail_msg = verify_actionability('action', item, custom_func, with_object)
                                    if not approved:
                                        print(fail_msg)
                                        logging.error(fail_msg)
                                    else:
                                        if with_object not in player.inventory:
                                            print(f"You're not carrying the {with_object}.")
                                            return
                                else:
                                    print(f"You can't use the {item} to do that.")
                                    return
                        else:
                            # if user did not ask to open door with key, then verify_actionability() will just check the
                            # 'with_nothing' key within the action requirements dict
                            approved, fail_msg = verify_actionability('action', item, custom_func, 'with_nothing')
                            if not approved:
                                print(fail_msg)
                                logging.error(fail_msg)
                                return

                        actions = copy.deepcopy(obj_command['actions'])  # have to make a DEEP copy so don't change original
                        # deep copy copies every object within the list as well, so the sublists will be copied and not
                        # remain as references to the original.
                        for action in actions:
                            index = action.index('item')
                            action[index] = action[index].replace('item', item)
                        try:
                            exec_actions_if_any(actions)
                        except Exception as error:
                            if len(error.args[0]) > 0:  # args[0] contains a list with all the errors
                                all_errors = [str(e) for e in error.args[0]]  # str(e) returns just the error message
                                unique_errors = list(set(all_errors))  # set() removes the duplicates
                                print('all errors:', all_errors)
                                for e in unique_errors:
                                    print(e)  # e is the custom error message itself

        else:  # if it's a FUNCTION VERB
            matches = omni_parser.get_labels_and_matches(command)  # [[], []]
            for label, match in matches:
                print('match from omni final:', match) if debug else None
                print('final label in match in matches:', label) if debug else None
                method, args = omni_parser.exec_func_from_cmd(label, match)
                if args is None:  # meaning the sentence is incoherent
                    if method is True:  # True just means to print a default invalid message.
                        print(random_response('invalid'))
                        return
                    else:  # here, the invalid response message was specified
                        print(method)
                else:
                    function = getattr(player, method)
                    print('all args:', args) if debug else None
                    print('args[0]:', args[0], 'all in args[0]', 'ALL' in args[0]) if debug else None

                    if 'ALL' in args[0]:
                        if 'ALL-IN-CONT' in args[0]:
                            container = args[1]
                        else:
                            container = None
                        args = filter_all_except_command(method, args, container)
                        if len(args) == 0:
                            if method == 'drop':
                                print(f"You have nothing to drop.")
                            else:
                                if container:
                                    print(f"The {container} has nothing inside it.")
                                else:
                                    print(f"There is nothing to {method} here.")
                            return
                        if container:
                            args.append(container)

                    # player.active_location = '4a'
                    # player.orientation = 'E'
                    # function(*args)
                    # function(*args, label=label)

                    print('method:', method, '\narguments:', args) if debug else None
                    if debug:
                        print('debugging')
                        if function in (player.take, player.throw, player.place):
                            function(*args, label=label)  # these methods need the label to execute command properly
                        else:
                            function(*args)  # every other method doesn't

                    else:
                        try:
                            if function in (player.take, player.throw, player.place, player.goto):
                                function(*args, label=label)
                            else:
                                function(*args)
                        except Exception as error:
                            if len(error.args[0]) > 0:  # args[0] contains a list with all the errors
                                all_errors = [str(e) for e in error.args[0]]  # str(e) returns just the error message
                                unique_errors = list(set(all_errors))  # set() removes the duplicates
                                print('full error:', error.args[0])
                                for e in unique_errors:
                                    logging.info(e)
                                    print(e)  # e is the custom error message itself


def gameplay():
    """The gameplay function that will keep the game running till exit."""

    # player.active_location = '1'
    # player.inventory.append('lantern')
    # OBJECTS['backpack'].inventory.remove('lantern')
    print(instructions)
    print(intro)  # intro to game
    import Skeleton.classes as classes  # just importing this to allow changing of debug variable
    while True:
        print_big('NEW PLAYER INPUT') if debug else None
        if testing:
            classes.debug = bool(input('Debug: True or False? '))
            print('debug is now', classes.debug)
        player_input = condense_and_split(input('◢▲◢◣◢▲◣ '))
        print('player input:', player_input) if debug else None
        input_handler(player_input)


if __name__ == '__main__':

    # test_state_changes()
    # player.activate_func('take')

    gameplay()
