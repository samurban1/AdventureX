import setup
from errors import *
from nltk import pos_tag
import random
import Colors
import omni_parser
import pickle
import re
import time
import fuckit
# Add in documentation, that if you want to have a randomly chosen response, define your responses at the top of the document
# or maybe in another document, so for example create a dict with key 'boundary', and then u can just write 'boundary; wherever
# and the program will choose something random from the dictionary with that key.

# Make sure for go_to, that its not 'boundary', in that case, randomly choose a boundary response


def command_check(command, main, typ):
    if command in str(main):
        return True
    for item in main:
        if item in command and typ == 'simple':
            return True


def failed_exception_msg(item, state, value):
    """Tells the player what exceptions have to pass in order for their command or action to go through."""
    message = f"The {item}"
    if value is True:
        message += f" has to be {state}"
    elif value is False:
        message += f" cannot be {state}"
    elif type(value) is list:
        message += f"'s {state} has to be within {value[0]} and {value[-1]}"
    return message


def check_conditions(exception, print_msg=False):
    """Checks if all the conditions in the passed in condition set (exception) are True."""
    conditions_passed = False

    for condition_set in exception['if']:  # for every exception list in the 'if' key
        item = condition_set[0]  # e.g. player, lantern, troll, or 6a
        state = condition_set[1]  # e.g. 'lit' or 'guarding'
        condition = condition_set[2]  # e.g. True/False, 6a (location)
        if len(condition_set) == 4:
            boolean = condition_set[3]
        else:
            boolean = True
        if 'range' in str(condition):
            condition = list(eval(condition))
        elif condition == 'inventory':
            condition = player.inventory

        print('{} state "{}" needs to be (in) {} in order for this exception to fire'.format(item, state, condition)) if debug else None

        if item == 'player':
            item_state = getattr(player, state)
        else:
            for dictionary in [LOCATIONS, OBJECTS, ACTORS]:
                if item in dictionary:
                    print('item in dictionary:', dictionary[item]) if debug else None
                    item_state = getattr(dictionary[item], state)
                    break
        try:
            print(f'{item} STATE OF {state} IS {item_state}') if debug else None
        except UnboundLocalError:  # exception raised if item_state is referenced before assignment
            print('\n\n\n\n\nERRORRRRRR\n\n\n\n')
        if type(condition) is list:  # this will work for inventory, too
            if boolean is False:
                conditions_passed = True if item_state not in condition else False
            else:
                conditions_passed = True if item_state in condition else False
        else:
            if boolean is False:
                conditions_passed = True if item_state != condition else False
            else:
                conditions_passed = True if item_state == condition else False
        if not conditions_passed:  # if the conditions did not pass, then return False right away, no need to check if the other one is True
            # raise error? saying that certain conditions need to pass
            print('conditions passed is False')
            return False
        # it doesn't pass the condition, set it back to false
    print('check_conditions returning:', conditions_passed) if debug else None
    return conditions_passed


def exceptions_handler(exceptions, typ):
    """Handles things in which general/exception sets are declared."""
    # print('dictionary given in exceptions handler:', dictionary)
    # exceptions = dictionary['exceptions']
    # break out of the loop below if a condition passes
    for exception in exceptions:  # item is either name of object/actor/location, or 'player'
        print('\nNEW exception set') if debug else None
        conditions_passed = check_conditions(exception)

        if conditions_passed:  # after looping through the condition set, if all the conditions have passed, then:
            print(Colors.BOLD + Colors.CYAN + 'CONDITIONS HAVE PASSED\n', Colors.END) if debug else None
            actions = None
            if exception.get('actions'):
                actions = exception['actions']

            if typ == 'narrative':
                if not exception.get('narrative'):  # if it doesn't have a narrative key. This would be the case if the game
                    # designer wants to just run an action if an exception passes, and not have a narration
                    return None, actions
                return exception['narrative'], actions  # even though the dictionary key happens to be the same as typ,
                # the key does not correspond to typ. In the else statement below, 'reaction' has nothing to do with typ,
                # because typ can be 'command', 'narrative', etc.
            else:
                reaction = exception['reaction']
                if type(reaction) is str:
                    reaction = [reaction] # put it in a list to not pick a letter out of a string in random.choice()
                return random.choice(reaction), actions  # if there is only one given option (as in most cases),
                # it will only choose the one, and if there are more, it will choose it randomly.
    print(Colors.BOLD + Colors.RED + 'CONDITIONS HAVE FAILED\n', Colors.END) if debug else None
    return None, None  # if NONE of conditions passed


def general_handler(general: dict or str, typ):
    """Gets and returns proper general reaction."""

    if type(general) is str:
        return general, None  # None for no actions. There are for sure no actions because the defined reaction is just a string.

    elif type(general) is dict:
        actions = None
        print('general passed in:', general)

        if typ == 'narrative':  # narrative
            reaction = general['narrative']
        else:
            reaction = general['reaction']
        if general.get('actions'):
            actions = general['actions']
        return reaction, actions


def exec_action_from_file(action_set):
    """Executes an action specified in a yaml file, ALWAYS under the key 'actions'.
    These actions will only refer to functions that have one parameter -- the functions that
    have multiple parameters are ones that the player can call.
    """
    if action_set[0] == 'die':
        player.die()

    elif len(action_set) == 2:  # e.g. remove object from game completely function
        function = action_set[0]
        argument = action_set[1]
        globals()[function](argument)
    else:
        reference = action_set[0]
        function = action_set[1]
        argument = action_set[2]
        if 'range' in argument:  # troll, attack, range(4,16)
            argument = list(eval(argument))

        if reference == 'player':
            function = getattr(player, function)

        else:
            if reference in LOCATIONS:
                dictionary = LOCATIONS
            elif reference in OBJECTS:
                dictionary = OBJECTS
            elif reference in ACTORS:
                dictionary = ACTORS
            function = getattr(dictionary[reference], function)  # get the method of the (python) object

        if len(action_set) == 4:  # e.g. player, change state, health, 90
            function(argument, action_set[3])
        else:
            function(argument)


def exec_actions_if_any(actions):
    """Executes all the actions provided, if there are any. Hence the function name."""
    if actions:
        print('under if actions:', actions) if debug else None
        for action_set in actions:
            exec_action_from_file(action_set)


def ask_until_respond(question_info):
    """Asks a question until player answers it. Function can be used with a goto location
    warning, with disambiguation, or with player input error handling."""
    warnings = COMMANDS['warnings']
    affirmations, negations = warnings['yes'], warnings['no']

    warning = False if type(question_info) is str else True
    query = question_info['warning'] if warning else question_info
    while True:
        answer = input(query + ' ')
        if command_check(answer, affirmations, 'simple'):
            if warning:
                return True, question_info['yes']
            return True
        elif command_check(answer, negations, 'simple'):
            if warning:
                return False, question_info['no']
            return False
        else:
            print("Answer must be in the affirmative or the negative. I'll ask again.")


def natural_random(msg, used_msgs, msg_list):
    if msg in used_msgs:
        if len(msg_list) > 1:
            msg_list.remove(msg)
            return random.choice(msg_list)
    else:
        pass


def remove_from_game(object):
    """Removes an object from the game. FOREVER."""
    del OBJECTS[object]


def describe(something):
    """Describes an object or a location."""
    if something in LOCATIONS:
        print(OBJECTS[something].description)
    elif something in LOCATIONS:
        LOCATIONS[something].narrate(typ='long')
    else:
        print("I can't describe something that doesn't exist.")


def is_partial(word, command, all_words, typ):
    """Checks if the word is a partial verb, that is, a part of a multi-word verb.
    Have to do 2 things:
    1. check if the word is inside a multi-word verb.
    2. Ensure that it is not a one-word verb -- for example, if the word is 'throw', but the word after it is 'away',
       it is not the one-word verb 'throw' that maps to the function throw() but it is rather the two-word verb 'throw away'
       that maps to the function drop().
    How do you ensure that it is not a one-word verb? By looking at the word after it. If the word after it is the next word
    in the multi-word verb, then you know the word is officially part of a multi-word verb, so you can "go ahead"
    and return True."""

    def get_next_word(command, index):
        """Sets the next word and the previous word of a given command. If there is no next or previous word, it
        sets it to False.
        :param command: The command, either the user's command or the multi-word command from which the function will retrieve
        the next/previous word.
        :param index: The index from which the function will add or subtract 1 to get the next/previous word.
        """
        indexes = [i for i, value in enumerate(
            command)]  # get all the indexes in the command to know if there is a next/previous word.
        next_word = command[index + 1] if index + 1 in indexes else False
        # print(f'The indexes inside the command of {command} ----- {indexes}')
        # print(f'The next word: "{next}" ---- and the previous word: "{prev}"')
        return next_word

    # The only commands I want are the ones that have spaces in them, which mean they are multi-word commands,
    # the ones that the word is in -- because why would I want to look at a command in which the word is not even
    # there?
    multi_word_cmds = [cmd for cmd in all_words if ' ' in cmd and word in cmd.split()]
    # the cmd.split() above is very important, because I ran into an error like this before -- the user command was
    # 'let go of lantern', the current word in the iteration was 'of', and the multi-word command in the loop iteration
    # was 'throw off', and it passed the list comprehension conditions! -- How did this happen, you may ask? Because
    # there was a space in 'throw off' and the word 'of' was in 'throw off' -- so I needed to add the .split() method
    # to the command to make sure that the word is actually the same word as the word inside the multi-word command,
    # not simply 'inside' it, lurking there like 'of' inside 'off'.
    for cmd in multi_word_cmds:  # if the word is in the verbs list of current loop dict, now you have your verb
        print('dealing with this multi-word command: ---- :', cmd) if debug else None
        for order in ('normal', 'reverse'):
            # REFACTOR THIS, MOVE THE .SPLIT() TO LIST COMP ABOVE [CMD.SPLIT() FOR CMD IN....]
            multiword_cmd = cmd.split()  # split the multi-word cmd by space
            if order == 'reverse':
                # Reversing everything allows me to just look at the next word (or next two words) without having to
                # essentially double the code by looking at the previous -- in 'reverse mode', the next word is really
                # the previous word.
                user_command = list(reversed(command))  # reversed returns in iterator, turn the iterator into a list
                multiword_cmd = list(reversed(multiword_cmd))
            else:
                user_command = command  # resetting this is necessary in the case of multiple loops through the
                # 'for cmd in multi_word_cmds' loop. After one loop in reverse mode, the command would have been
                # already reversed and if I did not set this again, the function would be looking at a reversed
                # list instead of looking at a non-reversed list like it should be. That's why I need to set the
                # user_command variable every time I go through the 'for order...' loop. The multiword_cmd var
                # doesn't need to be set in this else statement because it is always reset every time through the
                # 'for cmd in multi_word_cmds' loop.

            # Get the index of where the word is in the user command and get next word of user command
            word_index = user_command.index(word)
            next_word = get_next_word(user_command, word_index)

            # Get the index of where the word is in the multi-word command and get next word of multi-word command
            word_in_cmd_index = multiword_cmd.index(word)
            next_multiword = get_next_word(multiword_cmd, word_in_cmd_index)

            # Comparison time!
            if next_word and next_multiword:  # if there are words in the user command AFTER the main word and there are
                # next words in the multi-word command
                if next_word == next_multiword:  # if next word of user's command = next word of multiword command
                    return True

            if typ == 'VERB':
                if check_for_item(next_word):  # if the next word is an item, then now I have to check if there
                    # are more items lurking after the already-verified item.
                    index = word_index + 2  # starting index at the index after next_word
                    while index < len(user_command):
                        if check_for_item(user_command[index]):
                            index += 1  # increment the index to check if the word after that is an item or the
                            # next word in the multi-word command
                        else:
                            if user_command[index] == next_multiword:  # if the word after the object
                                # is the next word in the multi-word command
                                return True
                            else:
                                break  # abso-freakin-lutely necessary


def check_for_verb(word, original_command: list):
    """Checks if the word is a verb."""

    for dict_type in ('builtin_commands', 'custom_commands'):
        for dictionary in COMMANDS[dict_type]:  # looping over all the dicts of verbs + needs + action sets
            partial = is_partial(word, original_command, dictionary['verbs'], typ='VERB')  # is_partial takes the word,
            # the full user command, the list of all the words from which to check if the word is a partial, and a type (typ)
            # which tells the function what to check for as far as finding a partial
            if partial:
                return (word, 'PFVB') if dict_type == 'builtin_commands' else (word, 'PVB')  # return partial function verb
                # if the dictionary looping over is the builtin_commands, which are the builtins. Otherwise the tag is just
                # partial verb.
            elif word in dictionary['verbs']:  # if the word is in the verbs list of current loop dict, now you have your verb
                if dict_type == 'builtin_commands':
                    verb, tag = dictionary['function'], 'FVB'
                else:
                    verb, tag = dictionary['verbs'][0], 'VB'
                return verb, tag
    return False, None
    # Checking if the word is a special command, like for an object, location, or actor


def check_for_loc_cmd(word, original_command):
    """Checks if the word is a location command, that is, a command in the location's defined commands."""

    location = LOCATIONS[player.active_location]
    for command_set in location.commands:
        partial = is_partial(word, original_command, command_set, 'CMD')
        if partial:
            return word, 'PLVB'
        elif word in command_set:
            return command_set[0], 'LVB'
    return False, None


def disambiguate(query, active_item, unprovided):
    """Disambiguate a command.
    :param query: i.e. '<verb> what?' or 'what about the <object>?
    :param active_item: i.e. 'throw', 'troll', 'lantern'.
    :param unprovided: i.e. 'verb', 'object', 'location', 'actor'."""
    placeholder = '<' + unprovided + '>'
    clarify = input(query.replace(placeholder, active_item) + ' ')

    # articles = ['a', 'an', 'the']
    # if unprovided == 'verb':
    #     while not check_for_verb(clarify):
    #         clarify = input('You must enterquery.replace(placeholder, active_item) + ' ')
    #     player_input =
    #     player_input = [word for word in player_input if word not in articles]
    # commands, unparsed = pos_tagger(clarify)
    # print('tagged:', commands)
    # print('skeleton:', unparsed)


def check_requirements(word, needs):  # OBSOLETE FUNCTION - REMOVE!!!!
    """Get the official action word (verb).
    Needs is a list with sublists of the needed things. Each of those sublists can contain
    a single need or more than one, which means that there is an option. So, loop over the sublists in
    needs, and for each option (keeping in mind that there is most likely only one option) in each sublist,
    """
    for need in needs:  # loops over needs list -- all needs
        print('need:', need)
        for need_option in need:  # loops over options within each need sublist
            print('either:', need_option)
            requirement = check_for_item(word, need_option)  # checks if the word fits the requirement/need
            if requirement:
                return requirement
    return False


def check_for_item(word, full_command=None, typ='all'):
    """Checks if word is reference to an object or a location."""
    if typ == 'OBJ':
        dictionary = OBJECTS  # global objects dictionary
    elif typ == 'LOC':
        dictionary = LOCATIONS  # global locations dictionary
    elif typ == 'ACT':
        dictionary = ACTORS
    else:
        all_items = {**OBJECTS, **LOCATIONS, **ACTORS}  # this combines all the dictionaries
        return True if word in all_items else False  # this doesn't need to return a tuple of (reference, tag) because
        # it will only be called if just checking whether a word is a reference to any item

    for item in dictionary:  # loop over dictionary which gives you the actual python objects of objects/locations.
        references = dictionary[item].references
        adjectives = dictionary[item].adjectives if typ == 'OBJ' else []
        if word in references or word in adjectives:
            item_reference = references[0]  # the first item in object/location's references is always official name of object
            if typ == 'OBJ':
                if full_command is not None:
                    def is_partial(word, command):
                        """Checks if the word is a partial object, that is, a part of an object reference that includes an
                        adjective."""

                        def get_next_word(command, index):
                            """Sets the next word and the previous word of a given command. If there is no next or previous word, it
                            sets it to False.
                            :param command: The command, either the user's command or the multi-word command from which the function will retrieve
                            the next/previous word.
                            :param index: The index from which the function will add or subtract 1 to get the next/previous word.
                            """
                            indexes = [i for i, value in enumerate(command)]  # get all the indexes in the command to know if there is a next/previous word.
                            next_word = command[index + 1] if index + 1 in indexes else False
                            # print(f'The indexes inside the command of {command} ----- {indexes}')
                            # print(f'The next word: "{next}" ---- and the previous word: "{prev}"')
                            return next_word

                        objs_with_adjectives = [OBJECTS[obj] for obj in OBJECTS if hasattr(OBJECTS[obj], 'adjectives')]
                        print('all objects with adjectives:', [str(x) for x in objs_with_adjectives]) if debug else None
                        for obj in objs_with_adjectives:
                            adjectives = obj.adjectives
                            print(f"{obj.name}'s adjectives: {adjectives}") if debug else None
                            for order in ('normal', 'reverse'):
                                print('\nNEW ORDERRRRR\n') if debug else None
                                print('order:', order) if debug else None
                                if order == 'reverse':
                                    # Reversing everything allows me to just look at the next word (or next two words) without having to
                                    # essentially double the code by looking at the previous -- in 'reverse mode', the next word is really
                                    # the previous word.
                                    user_command = list(reversed(command))  # reversed returns in iterator, turn the iterator into a list
                                else:
                                    user_command = command  # resetting this is necessary in the case of multiple loops through the
                                    # 'for obj in objs_with_adjectives' loop. After one loop in reverse mode, the command would have been
                                    # already reversed and if I did not set this again, the function would be looking at a reversed
                                    # list instead of looking at a non-reversed list like it should be. That's why I need to set the
                                    # user_command variable every time I go through the 'for obj...' loop.
                                # Get the index of where the word is in the user command and get next word of user command

                                word_index = user_command.index(word)
                                next_word = get_next_word(user_command, word_index)
                                print(f'next word after {word} is {next_word}') if debug else None
                                if word in adjectives:
                                    return True

                        return False

                    partial = is_partial(word, full_command)
                    if partial:
                        print('under if partial word:', word)
                        return (word, 'POBJ') if word in references else (word, 'ADJ')  # if it is a reference to the object,
                        # and not an adjective of the object, return 'POBJ'....
                return item_reference, 'OBJ'
            elif typ == 'ACT':
                return item_reference, 'ACT'
            elif typ == 'LOC':
                return item, 'LOC'
    # for references in [item.references for item in dictionary.values()]:
    return False, None


def check_for_dir(word):
    """Checks if the word is a signifier for a direction."""
    directions = [
        [('north', 'n'), 'N'],
        [('east', 'e'), 'E'],
        [('south', 's'), 'S'],
        [('west', 'w'), 'W'],
        [('northeast', 'ne'), ('N', 'E')],
        [('southeast', 'se'), ('S', 'E')],
        [('southwest', 'sw'), ('S', 'W')],
        [('northwest', 'nw'), ('N', 'W')],
        [('left', 'l'), 'L'],
        [('right', 'r'), 'R'],
        [('forward', 'f', 'fwd', 'fd'), 'F'],
        [('backward', 'b', 'back', 'bk', 'bkwd'), 'B'],
    ]

    for direction in directions:
        if word in direction[0]:
            return direction[1], 'DIR'
    return False, None


def dir_to_loc(direction):
    """Translates a given direction to a location that the user goes to."""

    def rdir_to_dir(rd):
        """Converts relative direction (left, forward) to a direction
        based on player's orientation.
        How does it do it?

        1. Create list of N,E,S,W and list of F,R,B,L (North....Forward....)
        2. Rotate the list of N,E,S,W by the index value of where the player's orientation is in the list of N,E,S,W
            So if the player is facing (orientation) West, then get the index value of 'W' in the list of N,E,S,W --
            which is 3, and rotate the normal list of N,E,S,W backwards 3 units.
        3. Set the return of the rotate function to a variable, and now the old list of N,E,S,W becomes the a new list
            that looks like: W,N,E,S.
        4. Now we finally deal with the argument passed in -- either L(eft), R(ight), F(orward), etc.
            Get the index value of the relative direction argument within the relative directions list (F,R,B,L)
                Which means: If the argument is R (Left), then get the index value of R in the F,R,B,L list, which is 2.
            Now use that index value to access the proper direction in the recently created directions list.
            This works because the relative directions (L,R,F,B) list and the directions list (N,E,S,W) are parallel lists,
            and so now that you rotated the directions list, you can get the proper direction using the same index with
            both lists.
        5. Return the proper direction.
        """

        def rotate (l, n):
            """Rotates a list backwards by n units"""
            return l[n:] + l[:n]

        dirs = ['N', 'E', 'S', 'W']
        rdirs = ['F', 'R', 'B', 'L']

        if debug:
            print('\nnew direction')
            print('playing moving:', rd)
            print('index to rotate by:', dirs.index(player.orientation))
            print('player facing:', player.orientation)
        new_directions = rotate(dirs, dirs.index(player.orientation))
        if debug:
            print('new relative directions:', new_directions)
            print('final direction:', new_directions[rdirs.index(rd)])
        return new_directions[rdirs.index(rd)]

    if direction in ['L', 'R', 'F', 'B']:
        direction = rdir_to_dir(direction)
    new_loc = LOCATIONS[player.active_location].moves[direction]
    if new_loc is None:
        print(f'Going {direction} takes you nowhere.')
        new_loc = player.active_location
    print('new location is either a warning or a random:', new_loc) if type(new_loc) is dict else print('returning new loc, value is:', new_loc)
    return new_loc


def turn_to_sentence(words, starting_msg, and_or, typ='misunderstood'):
    """Print all current objects in the location."""
    message = starting_msg
    for i in range(len(words)):
        # obj = OBJECTS[objects[i]]  # objects[i], for example, is 'egg'. so OBJECTS['egg']
        if i == len(words) - 1 and len(words) > 1:  # if it's the last word to add to the list AND if there is more than one word
            message += f' {and_or} ' if len(words) == 2 else f'{and_or} '  # add an 'and', e.g. x, y, and z -- space before 'and' based on conditional
        # objects_here += obj.short_description
        message += f"'{words[i]}'"
        if len(words) > 2:
            message += ', '
    if typ == 'objects here':
        message += message.strip(', ') + '.'  # strip trailing comma and replace with a period.
    return message


def pos_tagger(command):
    """Tags each of the words in the command and returns a list of tuples with appropriate tags."""

    def add(word, POS, og_word=None):
        """Tag the word and add to the skeleton."""
        tagged.append((word, POS))
        if og_word is None:
            og_word = word
        i = skeleton.index(og_word)
        skeleton[i] = ' '

    def tag_word(index):
        """Checks the word for its type and adds the appropriate tag."""
        word = command[index].lower()  # set word to the command at the index, convert to lowercase
        direction = check_for_dir(word)
        verb = check_for_verb(word, intact_cmd)  # pass in word, the full command
        location = check_for_item(word, typ='LOC')
        object = check_for_item(word, intact_cmd, typ='OBJ')
        location_cmd = check_for_loc_cmd(word, intact_cmd)
        # player_object = check_for_item(word, typ='POBJ')
        actor = check_for_item(word, typ='ACT')

        for word_type in (direction, verb, location, object, location_cmd, actor):
            if word_type[0]:  # word_type[0] can be either the returned word or False, if it didn't match the check_for_x
                # function.
                add(word_type[0], word_type[1], word)  # word_type[1] is the tag, pass in the original word so the skeleton
                # can be edited.
                return

        # If all above failed, now checking if the word is a special word.
        special_words = [[('all', 'everything'), 'ALL'], [('but', 'except', 'excluding'), 'BUT'],
                         [('utilize', 'employ', 'apply', 'use', 'utilise'), 'USE'], [('to'), 'TO'],
                         [('in', 'inside', 'into', 'within'), 'IN'], [('and', 'then', ',', ';', '.'), 'AND'],
                         [('on', 'onto', 'atop'), 'ON'], [('at'), 'AT']]

        for word_set, tag in special_words:
            if word in word_set:
                add(word, tag)
                return
        #
        # if direction:
        #     for dir in direction:
        #         add(dir, 'DIR')
        #     i = skeleton.index(word)
        #     skeleton[i] = ' '
        # elif verb:
        #     add(verb[0], verb[1], word)  # verb[1] is the tag: tag can be 'FVB' for function verb or just 'VB' for an object/location/actor verb
        # elif location:
        #     add(location, 'LOC', word)
        # elif object:
        #     print('object if object:', object) if debug else None
        #     add(object[0], object[1], word)
        # elif location_cmd:
        #     add(location_cmd[0], location_cmd[1], word)
        # elif actor:
        #     add(actor, 'ACT', word)
        # elif word in ('all', 'everything'):  # later maybe add 'every object/item'
        #     add(word, 'ALL', word)
        # elif word in ('but', 'except', 'excluding'):
        #     add(word, 'BUT', word)
        # elif word in ('utilize', 'employ', 'apply', 'use', 'utilise'):
        #     add(word, 'USE', word)
        # elif word == 'to':
        #     add(word, 'TO', word)
        # elif pos_tag([word])[0][1] == 'IN':  # NLTK pos_tag, argument is list, index 0 is the
        #     # tuple inside the list, index 1 is second item of tuple, which is the part of speech.
        #     # the word in the 'but' check above might also be a preposition if it was run through the pos_add() function,
        #     # that's why it is above this elif statement
        #     add(word, 'PRP', word)
        # elif word in ('and', 'then', ',', ';', '.'):
        #     add(word, 'AND', word)
        if word.isdigit():
            add(int(word), 'NUM', word)

    skeleton = command
    intact_cmd = command[:]  # the slice is necessary so that intact_cmd does not reference the same list as skeleton does,
    # for if it does, then intact_cmd will change when skeleton changes

    tagged = []
    # pass in the command.
    #
    for i in range(len(command)):
        tag_word(i)

    def rearrange_verb(label, tagged):
        """Rearranges multi-word command into single-word counterparts."""
        print('tagged passed into rearrange:', tagged, '---- and label:', label) if debug else None
        for dict_type, tag_type in [('builtin_commands', 'FVB'), ('custom_commands', 'VB')]:
            for dictionary in COMMANDS[dict_type]:
                multi_word_cmds = [cmd.split() for cmd in dictionary['verbs'] if ' ' in cmd]  # get all the multi-word commands
                # in the current (in loop) command
                for cmd in multi_word_cmds:
                    partials_in_usr_cmd = [word for word, tag in tagged if word in cmd if tag == 'P'+tag_type]  # get all the partial
                    print('partials_in_usr_cmd:', partials_in_usr_cmd) if debug else None
                    # words in the tagged user command. This will combine all the
                    if partials_in_usr_cmd == cmd:
                        just_words = [word for word, tag in tagged]
                        print('just_words:', just_words) if debug else None
                        if label == 'PFVB-ITEM' or label == 'PVB-ITEM':
                            start = just_words.index(partials_in_usr_cmd[0])
                            end = just_words.index(partials_in_usr_cmd[-1])
                            function_name = dictionary['function'] if 'F' in label else dictionary['verbs'][0]
                            tagged[start:end+1] = [(function_name, tag_type)]
                            return tagged
                        elif label == 'PFVB-ITEM-PFVB' or label == 'PVB-ITEM-PVB':
                            start = just_words.index(partials_in_usr_cmd[0])
                            print('start:', start) if debug else None
                            print('just_words[start+1]:', just_words[start+1]) if debug else None
                            second_word_is_item = check_for_item(just_words[start+1])
                            print('second_word_is_item:', second_word_is_item) if debug else None
                            if second_word_is_item:
                                after_item = just_words.index(partials_in_usr_cmd[1])
                            else:
                                for word in tagged[start+2:]:  # ignore the first and second word, which we have verified
                                    # above are not references to any items
                                    print('word in tagged[start+2:]:', word) if debug else None
                                    if check_for_item(word[0]):  # this if statement will for sure pass at least once because
                                        # the label of the tagged command is 'pfvb-ITEM-pfvb' --- ITEM!
                                        after_item = tagged.index(word) + 1  # get the index of where the partial verb continues
                                        # after the item.
                                        print('after item set: to :---:', after_item) if debug else None
                                before_item = after_item - 2
                                print(f"start: {start}, 'before item: {before_item}, 'after item: {after_item}") if debug else None

                            len_before = len(tagged)
                            function_name = dictionary['function'] if 'F' in label else dictionary['verbs'][0]
                            if second_word_is_item:
                                tagged[start] = (function_name, tag_type)
                            else:
                                tagged[start:before_item+1] = [(function_name, tag_type)]
                            difference = len_before - len(tagged)
                            del tagged[after_item-difference:]  # delete everything after the item because they are just
                            # continuations of the partial verb
                            return tagged

    def rearrange_obj_with_adj(label, tagged):
        """Rearranges partial objects -- that is, objects that include adjectives, into a single object word.
        Get the adjective and the
        Get list of tuples -- first value is the name of the object, second is the adjectives associated with it -- list
        comp, IF the adjective is """
        print('tagged passed in:', tagged)
        print('label passed in:', label)
        just_tags = [tag for word, tag in tagged]
        obj_index = tagged[just_tags.index('POBJ')]
        obj_reference = tagged[obj_index][0]

        adjectives = [adj for adj, tag in tagged if tag == 'ADJ']

        for obj in OBJECTS:
            print('\n\nloop obj:', obj)
            obj = OBJECTS[obj]
            is_not = []
            if obj_reference in obj.references:
                matching_adjective = True
                for adj in adjectives:
                    print('cur adj:', adj)
                    if adj not in obj.adjectives:
                        print('appending to is not')
                        is_not.append(adj)
            if is_not:
                turn_to_sentence(is_not, f"The {obj.name} is not ", 'or')

    # for tagged_cmd in all_tagged:
    # new('NEW PARTIAL TAGSET CHECKER')
    print('tagged after tagging:', tagged) if debug else None
    if 'PFVB' in str(tagged) or 'PVB' in str(tagged) or 'POBJ' in str(tagged):
        print('rearranging tagged') if debug else None
        match_set = omni_parser.get_labels_and_matches(tagged, typ='partial')  # typ can be anything other than 'NORMAL'
        for label, match in match_set:
            if 'VB' in label:  # don't need to specify the 'P' for partial because that has already been verified in outer
                # if statement
                tagged = rearrange_verb(label, match)
            else:
                tagged = rearrange_obj_with_adj(label, match)

            print('\ntagged after rearranging:', tagged) if debug else None

    return tagged, skeleton
# get_command(tagged)


def verify_actionability(typ, item, action_or_state, sub_dict=None):
    """Verifies that the player can perform a certain action or change something's state."""
    # maybe change this function to raise a TakeError if the requirements fail
    if item in OBJECTS:
        dictionary = OBJECTS[item]
    elif item in LOCATIONS:
        dictionary = LOCATIONS[item]
    elif item in ACTORS:
        dictionary = ACTORS[item]
    print(f"item: {item}, action/state: {action_or_state}, 'subdictionary: {sub_dict}")

    try:
        print(f"item: {item}, action/state: {action_or_state}, 'subdictionary: {sub_dict}") if debug else None
        requirement_dict = getattr(dictionary, typ + '_requirements')
        requirements = requirement_dict[action_or_state]
        if sub_dict is not None:
            requirements = requirements[sub_dict]
        for condition_set in requirements:
            cant_do_it = check_conditions(condition_set)  # check conditions will return True if all the conditions pass. If
            # it returns True, that means the player cannot perform the action.
            print('stop message in verify:', condition_set['stop_msg']) if debug else None
            if cant_do_it:
                return False, condition_set['stop_msg']  # False for not verified. Return the opposite of what cant_do_it is. If cant_do_it is True,
                # that means that the conditions passed and the player cannot perform the action.

        # if cant_do_it always evaluated to False in above for loop, then just return True, meaning APPROVED
        return True, None

    except (AttributeError, TypeError, KeyError):  # AttributeError if the dictionary doesn't have an action_requirements
        # attribute, KeyError if the action_requirements doesn't have requirements for this command, and TypeError if
        # the item's action_requirements is set to None
        return True, None  # None because there is no fail message


class Reactor:
    """Class that can be used to react to anything."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():  # these are gonna be the reactions passed in
            setattr(self, key, value)  # set the attribute of whatever key is to the value

    def react(self, typ, something, reaction_subdict=None, location=None):
        """React to a state change, a command, or an object receipt."""

        # These below variables apply to all cases, all types of reactions
        dict_names = {'state change': 'sc_reactions', 'command': 'cmd_reactions', 'narrative': 'narratives'}
        main_dict = getattr(self, dict_names[typ])  # get the attribute of the type of reaction defined in dictionary on line above
        if typ == 'narrative' and something == 'short' and not main_dict.get('short'):  # if there is no short narrative key...
            reaction_info = main_dict['long']  # ...set it to the long key.
        else:
            if main_dict.get(something):  # if there is no specific reaction for this something
                reaction_info = main_dict[something]  # in all other cases, just set it to something
            else:
                return

        has_exceptions = False
        print_general = True

        # have to check this below if statement before the next if statement block (if type(reaction_info) is dict) because
        # if there is a subdict, I have to set the reaction info to that first before checking for general/exception keys
        if reaction_subdict is not None:  # if they passed in a value for reaction_subdict...
            print('there is a reaction subdict, which is:', reaction_subdict) if debug else None
            if not reaction_info.get(reaction_subdict):  # ...but there is no reaction_subdict key
                raise YamlFormatError(f"There is no {reaction_subdict} key in the passed-in reaction info.")
            else:
                print('reaction_info[reaction_subdict] is:', reaction_info[reaction_subdict]) if debug else None
                reaction_info = reaction_info[reaction_subdict]

        if type(reaction_info) is dict:
            if reaction_info.get('exceptions'):  # if there is an exceptions key...
                if reaction_info.get('general'):
                    has_exceptions = True  # only time I set has_exceptions to True, if there are both keys
                else:  # ...but no general key...
                    raise YamlFormatError('There is an exceptions key without a general key')
            elif reaction_info.get('general'):  # if there is not an exceptions key but there is a general key...
                raise YamlFormatError('There is a general key without an exceptions key')

        if has_exceptions:
            print('This reaction has exceptions') if debug else None
            exceptions = reaction_info['exceptions']
            reaction, actions = exceptions_handler(exceptions, typ)
            # add if there is a general without actions, then it would just be a string, so print(general),
            # but if the general is a dictionary, that means there are actions attached.
            if reaction is not None:
                print('exceptions passed, printing reaction') if debug else None
                print(reaction)
                print_general = False

        if print_general:
            if type(reaction_info) is str:
                general = reaction_info
            elif reaction_info.get('reaction'):
                general = reaction_info['reaction']
            elif reaction_info.get('general'):  # if the exceptions failed above and now it's just printing the
                # reaction within the general key
                general = reaction_info['general']
            else:
                raise YamlFormatError(f"The reaction within: {reaction_info}\nis not in a string or a 'reactions' key.")
            reaction, actions = general_handler(general, typ)
            print(reaction)

        if typ == 'narrative':  # if it is a narrative, before we execute the actions, we need to print all the objects that are in the location
            location = LOCATIONS[location]
            objects = location.objects
            if len(objects) > 0:
                turn_to_sentence(location.objects, 'With you in this location is ', 'and')

        exec_actions_if_any(actions)  # actions will for sure be set in one of the above if statements


class Object:
    """Simple object, i.e. an egg."""

    def __init__(self, obj_dict, obj_name):
        """
        :param obj_dict: named after what it is -- the dictionary that contains all the object info
        :param obj_name: this is the only way to know what the object is called, because the obj_dict we pass in is just the
                        inner dict without the name (the name is the key whose value is the obj_dict)
        """
        self.info = obj_dict
        self.name = obj_name

        self.references = obj_dict['references']
        self.adjectives = obj_dict.get('adjectives', [])
        self.description = obj_dict['description']
        self.short_description = obj_dict['short_desc']
        self.damage = obj_dict['damage']
        self.location = obj_dict['active_location']

        self.action_requirements = obj_dict.get('action_requirements', [])
        self.sc_requirements = obj_dict.get('state_change_requirements', [])
        self.weight = obj_dict.get('weight')  # actors have no weight so exception may be raised
        # print('{} object reactions: {}'.format(self.name, obj_dict['reactions']))
        self.cmd_reactions = obj_dict['reactions'].get('commands')  # object might not have specific commands
        self.kwargs = {}
        if self.cmd_reactions is not None:
            self.kwargs['cmd_reactions'] = self.cmd_reactions
        self.reactor = Reactor(**self.kwargs)

    def react(self, typ, command):
        """Reacts to a command. The only thing a simple object can react to is a command, since simple objects
        don't have state changes."""
        self.reactor.react(typ, command)

    def __str__(self):
        return f"{self.__class__.__name__}({self.name}, in location {self.location})"


class Container(Object):
    """Containers can hold objects inside them. Only one added attribute: inventory"""
    def __init__(self, obj_dict, obj_name):
        Object.__init__(self, obj_dict, obj_name)
        self.inventory = obj_dict['inventory']
        self.locked = obj_dict['locked']


class ComplexObject(Object):
    """More complex object that has mutable states."""

    def __init__(self, obj_dict, obj_name):
        Object.__init__(self, obj_dict, obj_name)

        self.states = obj_dict['states']
        for state in self.states:
            value = self.states[state]
            setattr(self, state, value)  # set custom object attributes based on the given states
        self.reactions = obj_dict['reactions']
        self.sc_reactions = self.reactions['state_changes']
        self.kwargs['sc_reactions'] = self.reactions['state_changes']  # there has to be state change reactions for
        # complex objects, so no need for if x is not None
        if self.cmd_reactions is not None:
            self.kwargs['cmd_reactions'] = self.cmd_reactions
        self.reactor = Reactor(**self.kwargs)

    def change_state(self, state, value):
        """Changes active state of object based on user's command or other circumstance."""

        if self.name not in player.inventory:
            raise Exception([TakeError(f"You can't do that because you're not carrying the {self.name}.")])  # must be in this
            # format for the try/except block in gameplay() to work.
        else:
            format = (self.name, state, getattr(self, state), value)
            print("\nChanging {}'s state of {} from {} to {}".format(*format))  # unpack format
            approved, fail_msg = verify_actionability('sc', self.name, state, value)  # ('sc', self.name, value, )  # sc for state change
            if not approved:
                print(fail_msg)
            else:
                setattr(self, state, value)
                self.reactor.react('state change', state, value)


    # if player.active_location not in self.info.get('exceptions'):
    #     print(self.sc_reactions[new_state])
    # else:
    #     print(self.sc_reactions['exceptions']
    #           [player.active_location][new_state])


class Actor(ComplexObject):
    """Higher level of complexity than a complex object."""

    def __init__(self, actor_dict, name):
        """

        :param actor_dict: The dictionary containing the actor data
        :param name: The name of the actor, i.e. 'troll'
        """
        ComplexObject.__init__(self, actor_dict, name)
        self.health = actor_dict['health']
        self.receive_reactions = self.reactions.get('receive')
        if self.receive_reactions is not None:
            self.kwargs['receive_reactions'] = self.receive_reactions
        self.reactor = Reactor(cmd_reactions=self.cmd_reactions,
                               sc_reactions=self.reactions['state_changes'],
                               receive_reactions=self.receive_reactions)

    # def react(self, typ, state_or_obj, boolean=None):
    # 	"""React to a state change or command
    # 	:param boolean:
    # 	:param state_or_obj: The object's state that is being changed or the command that is being invoked
    # 	:param typ: Either 'state change' or 'receipt'
    # 	"""
    #
    # 	if typ == 'state change':
    # 		ComplexObject.react(self, typ, state_or_obj, boolean)
    # 	elif typ == 'receipt':
    # 		dictionary = self.receive_reactions[state_or_obj]['reaction']
    # 		has_exceptions = True if type(dictionary) is dict else False
    # 		# print('dictionary for typ: {}: {}'.format(typ, dictionary))
    #
    # 		if has_exceptions:
    # 			reaction, actions = exceptions_handler(dictionary['exceptions'], typ)
    # 			general = dictionary['general']
    # 			print(reaction) if reaction else print(general)
    # 			exec_actions_if_any(actions)
    #
    # 		else:
    # 			print(dictionary)
    # 			actions = self.receive_reactions[state_or_obj].get('actions')
    # 			exec_actions_if_any(actions)
    #
    # 	elif typ == 'numeric state change':
    # 		conditions_list = self.num_sc_reactions[state_or_obj]
    # 		reaction, actions = exceptions_handler(conditions_list, typ=typ)
    # 		if reaction:
    # 			print(reaction)
    # 			exec_actions_if_any(actions)
    # 	else:
    # 		print('TypError: we don\'t support a reaction of type:', typ)

    def accept(self, object):
        """
        :param object:
        """
        found_obj = False
        for obj in self.receive_reactions:
            if obj == object:
                found_obj = True
                self.react('receipt', object)

        if not found_obj:
            print(self.name, 'has no use for a', object)

    def print_test(self, word):
        print('this is an override of the higher class\'s function print_test')


class ViolentActor(Actor):
    """This is a violent actor that can attack."""
    def __init__(self, actor_dict, name):
        Actor.__init__(self, actor_dict, name)
        self.attack_reactions = self.reactions['attack']

    def attack(self, damage_range):
        """
        :param damage_range:
        """
        damage_to_inflict = random.choice(damage_range)
        print('damage to inflict upon player:', damage_to_inflict)
        for option in self.attack_reactions['response']['message']:
            damage_range = eval(option['if'][0])
            # print('damage received range:', damage_received_range)
            if damage_to_inflict in damage_range:
                old_health = player.health
                player.health = max(0, player.health-damage_to_inflict)  # return whichever is bigger -- 0, or the new
                # player's health. We don't want player health going below 0.
                print('player health before attack:', old_health, '| and after:', player.health)
                message = random.choice(option['message'])
                print(message)
                break

    def is_attacked(self, damage_received):
        """
        :param damage_received:
        """
        print('damage received:', damage_received)
        self.health -= damage_received
        print('troll health:', self.health)
        retaliations = self.attack_reactions['response']['actions']
        # print('retaliation:', retaliation)
        for retaliation in retaliations:
            exec_action_from_file(retaliation)


class Location:
    """Location class that knows everything about a specific location"""
    def __init__(self, loc_info, num):
        self.loc_info = loc_info

        # Locations always have
        self.num = num
        self.name = loc_info['name']
        self.visited = loc_info['visited']
        self.narratives = loc_info['NARRATIVES']
        self.moves = loc_info['MOVES']

        # Locations can have
        self.children = loc_info.get('CHILDREN', None)
        self.objects = loc_info.get('OBJECTS', [])
        self.actors = loc_info.get('ACTORS', [])
        self.references = loc_info.get('references', [])
        self.commands = loc_info.get('COMMANDS', [])
        self.cmd_reactions = loc_info.get('REACTIONS', None)
        self.kwargs = {'narratives': self.narratives}  # set up the dictionary with the  narratives "reactions"
        if self.cmd_reactions is not None:
            self.kwargs['cmd_reactions'] = self.cmd_reactions
        self.reactor = Reactor(**self.kwargs)

    def react(self, command):
        """Reacts to a command. The only thing a location can react to is a command."""
        self.reactor.react('command', command)

    def narrate(self, typ=None):
        """Does a few checks and then prints the appropriate narrative."""

        if self.visited == 0 or typ == 'long':
            self.reactor.react('narrative', 'long', location=self.num)
            self.visited += 1
        else:
            self.reactor.react('narrative', 'short', location=self.num)

    def remove_object(self, object):
        """Removes an object from the location's objects list."""
        try:
            print('objects before:', self.objects)
            self.objects.remove(object)
            print('objects after:', self.objects)
        except ValueError:  # if th object is not in location's object list, .remove() will raise a ValueError
            print(f"Location doesn't contain a(n) {object} to remove.")

# forward back left right for user's orientation, and n s e w fixed


class Player:
    """Player object containing all relevant info."""
    def __init__(self, player_info):
        """
        Create the player object from player info dictionary. This will be updated every game.
        """
        self.active_location = player_info['active_location']
        self.inventory = player_info['inventory']  # keeps list inputted as the parameter, if no inventory given, change inventory to empty list
        self.orientation = player_info['orientation']
        self.health = player_info['health']
        self.states = player_info['states']
        for state in self.states:
            value = self.states[state]
            setattr(self, state, value)  # set custom object attributes based on the given states
        self.reactions = player_info['reactions']
        self.sc_reactions = self.reactions['state_changes']
        # self.num_sc_reactions = self.reactions['numerical_state_changes']
        self.kwargs = {}

    def change_state(self, state, value):
        """Changes active state of object based on user's command or other circumstance."""
        format = (state, getattr(self, state), value)
        print("Changing player's state of {} from {} to {}".format(*format))  # unpack format
        self.states[state] = value  # if state is True, then change it to False, and vice versa.
        self.react('state change', state, value)
        if state == 'health' and value == 0:
            print('GAME OVER')
            raise SystemExit
    # if player.active_location not in self.info.get('exceptions'):
    #     print(self.sc_reactions[new_state])
    # else:
    #     print(self.sc_reactions['exceptions']
    #           [player.active_location][new_state])

    def take(self, *references):
        """To be called when user says to take an object."""
        errors = []
        for reference in references:
            approved, fail_msg = verify_actionability('action', reference, 'take')
            in_container = obj_in_container(reference)
            if not approved:
                print(fail_msg)
            elif in_container:
                error_message = f"You cannot take the {reference} because it is inside the {in_container}, which is locked."
                errors.append((TakeError, error_message))
            else:
                if reference in self.inventory:
                    error_message = f"You're already carrying the {reference}."
                    errors.append((AlreadyHoldingError, error_message))
                else:
                    location = LOCATIONS[self.active_location]
                    if reference in location.objects:
                        self.inventory.append(reference)  # add object to player's inventory
                        location.objects.remove(reference)  # remove object from location
                        OBJECTS[reference].react('command', 'take')
                    else:
                        error_message = f"There is no {reference} here."
                        errors.append((TakeError, error_message))
        
        # create an Exception object with all the errors in the raising_error list
        # the list comp says give me the error and pass in the custom message for every error and message in the list of 
        # all error collected during runtime.
        raise Exception([error(message) for error, message in errors])

        # def pick_up (self, item):
        #     """Pick an object, put in inventory, set its owner."""
        #     self.inventory.append(item)
        #     item.owner = self

    def drop(self, *references, actor_from_throw=None):  # actor is just for when the throw() command calls drop()
        """To be called when user says to drop an object."""
        errors = []
        for reference in references:
            print('reference:', reference)
            approved, fail_msg = verify_actionability('action', reference, 'throw', actor_from_throw)  # if actor is None the function
            # will not look at it.
            if not approved:
                print(fail_msg)
            else:
                if reference not in self.inventory:
                    article = 'an' if reference[0] in 'aeiou' else 'a'
                    error_message = f"You're not carrying {article} {reference}."
                    errors.append((NotHoldingError, error_message))
                else:
                    self.inventory.remove(reference)
                    location = LOCATIONS[self.active_location]
                    if actor_from_throw is None:
                        location.objects.append(reference)
                    typ = 'throw' if actor_from_throw else 'drop'

                    OBJECTS[reference].reactor.react('command', typ, reaction_subdict=actor_from_throw)

        raise Exception([error(message) for error, message in errors])

    def throw(self, *references, in_or_at=None):
        """Throw an object -- either a simple throw at nothing or a throw at an actor."""
        if in_or_at is None:
            in_or_at = 'at_nothing'
        self.drop(*references, actor_from_throw=in_or_at)

    def place(self, *references, in_or_at):
        """Place an object in a container."""
        errors = []
        container = OBJECTS[in_or_at]
        if not isinstance(container, Container):
            error_message = f"You can't put anything inside the {in_or_at}."
            errors.append((PlaceError, error_message))
        else:
            for reference in references:
                approved, fail_msg = verify_actionability('action', reference, 'place', sub_dict=in_or_at)
                if not approved:
                    print(fail_msg)
                else:
                    if reference in container.inventory:
                        error_message = f"The {reference} is already in the {in_or_at}."
                        errors.append((PlaceError, error_message))
                    elif reference not in self.inventory:
                        article = 'an' if reference[0] in 'aeiou' else 'a'
                        error_message = f"You're not carrying {article} {reference}."
                        errors.append((NotHoldingError, error_message))
                    else:
                        container.inventory.append(reference)
                        LOCATIONS[self.active_location].objects.append(reference)  # add the object to the location's
                        # objects list
                        OBJECTS[reference].reactor.react('command', 'place', reaction_subdict=in_or_at)

        raise Exception([error(message) for error, message in errors])

    def give(self, actor, reference):
        """

        :param actor:
        :param reference:
        """
        self.inventory.remove(reference)
        ACTORS[actor].accept(reference)

    def goto(self, *locations, long_or_short=None):
        """

        :param locations:
        """

        def play_random_message(random_dict):
            """Plays a random message from the random dictionary."""
            print('dict name passed into play rand msg:', random_dict)
            messages = RANDOMS[random_dict]
            choice = random.choice(messages)
            print(choice)

        for i in range(len(locations)):
            new_location = dir_to_loc(locations[i])
            going_to = True
            if str(new_location) not in LOCATIONS:
                # self.active_location = new_location
                # LOCATIONS[new_location].narrate(typ)
                if type(new_location) is dict and 'warning' in new_location:
                    if len(locations) > 1:
                        print(f"{i} of your direction commands have already been executed. I am now trying to take you "
                              f"{locations[i]}. But in order for you to go there, you must first respond to the following warning:")
                    boolean, loc_or_reaction = ask_until_respond(new_location)
                    if boolean:
                        new_location = loc_or_reaction
                    else:
                        print(loc_or_reaction)
                        if len(locations) > 1:
                            print("The rest of your direction commands will not be executed.")
                            return
                        going_to = False
                elif new_location in RANDOMS:
                    play_random_message(new_location)
                    going_to = False
            if going_to:
                self.active_location = new_location
                if i == len(locations) - 1:
                    LOCATIONS[new_location].narrate(long_or_short)

    def attack(self, actor, with_object):
        print(f'attacking {actor} with {with_object}')
        """Attack an actor."""
        if actor not in ACTORS:
            raise AttackError
        else:
            pass

    def speak(self, to_actor):
        """Converse with an actor. This might be complicated, but I will try to make it super simple."""
        pass

    # def inflict_damage (self, damage):
    #     self.health -= damage
    #
    def turn(self, direction):
        """Turn in a given direction"""
        self.orientation = direction
        print('You are now facing')

    def die(self):
        print('You has dieded, sorry bud.')
        raise SystemExit

    def __str__(self):
        for data in self.__dict__:
            print(f"attribute: {data}, value: {self.__dict__[data]}") if debug else None
        return ('This is you. You are currently in location ' + self.active_location
                + ' and are holding ' + str(self.inventory))


def actualize_data(typ, filename):
    """For each location/object in location/object dictionary,
    create python objects."""
    data = setup.get_data(filename)
    if typ in 'COMMANDS | PLAYER | RANDOMS':
        return data[typ]
    for sub_dict in data[typ]:  # for example: sub_dict = 'egg' or '6a', in data['OBJECTS] or data['LOCATIONS']-
        title = sub_dict
        sub_dict = data[typ][sub_dict]
        if typ == 'OBJECTS':
            level = data[typ][title]['type']
            if level == 'SIMPLE':
                OBJECTS[title] = Object(sub_dict, title)
            elif level == 'COMPLEX':
                OBJECTS[title] = ComplexObject(sub_dict, title)
            elif level == 'CONTAINER':
                OBJECTS[title] = Container(sub_dict, title)
        # if title == 'lantern':
        #     pyaml.pprint(sub_dict['reactions']['state_changes']['lit'])
        elif typ == 'ACTORS':
            level = data[typ][title]['type']
            if level == 'Violent':
                ACTORS[title] = ViolentActor(sub_dict, title)
            else:
                ACTORS[title] = Actor(sub_dict, title)
        elif typ == 'LOCATIONS':
            LOCATIONS[title] = Location(sub_dict, title)  # passes in the loc/obj dict & loc/obj number/name


debug = True
LOCATIONS = {}
OBJECTS = {}
ACTORS = {}
COMMANDS = actualize_data('COMMANDS', setup.cmd_filename)
RANDOMS = actualize_data('RANDOMS', setup.randoms_filename)
actualize_data('LOCATIONS', setup.loc_filename)
actualize_data('OBJECTS', setup.obj_filename)
actualize_data('ACTORS', setup.act_filename)
# class Character:
# #
# #    def __init__(self, health):
#         self.health = health
#
#     def attack(self, other):
#         raise NotImplementedError


def new(action):
    """Prints a header and the action that is being tested."""
    print('\n' + Colors.BOLD + Colors.BLACK_W_BG + '---NEW---' + Colors.END)
    print(Colors.BOLD + Colors.YELLOW + action.upper() + Colors.END)


def obj_in_container(obj):
    """Checks if an object is inside a container, and therefore untakeable."""
    object_names = LOCATIONS[player.active_location].objects
    objects = [OBJECTS[obj_name] for obj_name in object_names]
    containers = [container for container in objects if isinstance(container, Container)]  # isinstance(OBJECTS[container], Container)]
    print('all containers:', containers) if debug else None
    cannot_take = [obj_in_cont for container in containers
                   for obj_in_cont in container.inventory if container.locked]  # give me every object in every container's inventory
    for container in containers:
        objs_in_cont = container.inventory
        if obj in objs_in_cont and container.locked:
            return container.name
    return False


def filter_all_except_x(method, arguments):
    """
    Filters the objects/actors passed in. Either returns them all, or everything BUT the ones explicitly excluded.
    :param method: the function name
    :param arguments: the arguments to be passed into the method. The first one is either "ALL" or "ALL-BUT", and the rest
    (if there is a BUT) are the objects/actors that should not be included as arguments.
    :return: the objects/actors to pass into the method.
    """
    if method == 'goto':
        print("You can't use 'all' when referring to directions.")
        return False
    elif method == 'attack':
        all = LOCATIONS[player.active_location].actors
    elif method in ('take', 'describe'):
        objects = LOCATIONS[player.active_location].objects
        all = [obj for obj in objects if not obj_in_container(obj)]
        error_text = "There is no {} to not {}, sorry."
    elif method in ('throw', 'drop'):
        all = [obj for obj in player.inventory if obj not in ('hand', 'leg')]
        error_text = "You don't have a {} to not {}, sorry."

    print('all before filtering:', all) if debug else None
    if 'BUT' in arguments[0]:
        for but in arguments[1:]:
            print('but:', but) if debug else None
            try:
                all.remove(but)
            except ValueError:
                print(error_text.format(but, method))
    print('all after filtering:', all) if debug else None
    return all


def condense_and_split(p_input):
    """Condenses preliminary input. Removes predefined stop phrases and removes articles.
    :returns Nicely stripped player input, without anything extra. No articles and no stop phrases."""

    def and_strip(sentence, sub):
        """If the sentence starts or ends with whatever is passed in for {sub}, remove it."""
        if sub == 'go':
            if sentence.startswith('go') and not sentence.startswith('go and'):  # if it starts with 'go' and doesn't start
                # with 'go and', because 'go and' is a stop phrase anyways (defined below)
                split_sentence = sentence.split()
                if len(split_sentence) >= 2:  # if there is a second word in the sentence
                    direction = check_for_dir(sentence[1])
                    if not direction[0]:  # if check_for_dir returned (False, None), direction[0] == False
                        sentence = sentence[len('go'):]  # remove the 'go'
        else:
            if sentence.startswith(sub):
                sentence = sentence[len(sub):]
            if sentence.endswith(sub):
                sentence = sentence[:-len(sub)]
        return sentence

    ands = ('and', 'then', ',', ';', '.')
    for item in ands:
        p_input = and_strip(p_input.strip(), item)  # strip every 'and' character from the beginning and end

    stop_phrases = ['go and', 'go forth and', 'go ahead and']  # The reason stop_phrases is separate is to make it easy
    # for the user in case they want to add more.
    split_by = r'(; ?)|(, ?)|(\. ?)|( ?save ?)|( ?(resume|load) ?)| a | an | the '
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
            final.append(word)

    # go through each word and if its not an AND, add it to the list of commands. If there is an AND, then check if the word
    # after it is a verb, and if yes, then take the current list of commands and put that in a sublist within itself. If not,
    # then add the word (which is after the AND) to the list of commands.
    separated_cmds = [[]]
    index_of_sublist, i = 0, 0

    while i < len(final):
        regular_appendage = True
        if final[i] in ands:
            regular_appendage = False  # if the word is an AND, for sure don't add it to the list of commands
            check_for_verb(final[i + 1], final)
            next_word_is_verb = check_for_verb(final[i+1], final)[0]
            if next_word_is_verb or final[i+1] in ('save', 'exit', 'resume', 'load'):
                index_of_sublist += 1
                separated_cmds.insert(index_of_sublist, [])
        if regular_appendage:
            print(f'appending {final[i]} to separated cmds: {separated_cmds}')
            separated_cmds[index_of_sublist].append(final[i])
        i += 1

    def missing_and(command):
        """Check if the user command contains multiple commands without an AND character separating them."""

        both_dicts = [COMMANDS['builtin_commands'], COMMANDS['custom_commands']]  # combine both

        all_commands = []
        # Get all the verbs
        for dictionary in both_dicts:  # loop over each in both dicts
            for verb_set in dictionary:  # each verb_set is the dictionary containing all the verbs and respective functions/actions
                for word in verb_set['verbs']:
                    all_commands.append(word)  # add the word

        # Check if command contains multiple verbs. The command passed in was already stripped of all ANDs and split into
        # separate commands based on those ANDs, so anything passed in should only have one verb in it. If it has nultiple
        # verbs, then we know there is a missing AND.
        verb_counter = 0
        for word in command:
            if word in all_commands:
                verb_counter += 1
        if verb_counter > 1:
            return True  # True that there is an AND missing
        return False

    for command in separated_cmds:
        if missing_and(command):
            correcting_input = input("There seems to be multiple commands in your input, one or more of which are not "
                                     "separated by an 'and' character.\nPlease enter your command again: ")
            separated_cmds = condense_and_split(correcting_input)
            # break

    return separated_cmds


def gameplay():
    """The gameplay function that will keep the game running till exit."""

    player.active_location = '4a'
    ACTORS['troll'].guarding = True
    print(player) if debug else None
    player.inventory.append('lantern')
    # player.throw(*args)
    # function = getattr(player, method)
    # if 'ALL' in args[0]:
    #     args = filter_all_except_x(method, args)
    # print('method:', method, '\narguments:', args) if debug else None
    # if debug:
    #     function(*args)

    while True:
        new('NEW PLAYER INPUT')
        player_input = condense_and_split(input('enter command: '))
        print('player input:', player_input) if debug else None
        for command_set in player_input:
            print('command set in player_input:', command_set) if debug else None
            if command_set[0] == 'save':
                save()
                raise SystemExit
            elif command_set[0] == 'resume':
                load()
            command, unparsed = pos_tagger(command_set)
            print('\nFINAL command:', command) if debug else None
            print('skeleton:', unparsed, '\n') if debug else None
            not_understood = [word for word in unparsed if word != ' ']
            yes_understood = [word for word, tag in command]
            proceed_with_action = True
            if len(not_understood) > 0 and len(yes_understood) > 1:
                errors = turn_to_sentence(not_understood, "I didn't understand ", 'or')
                space = '' if len(not_understood) > 2 else ' '
                passed = f"{space}but I did understand '{' '.join([word for word, tag in command])}'."
                question = errors + passed + ' Would you like to proceed with this action?'
                if not ask_until_respond(question):
                    proceed_with_action = False

            if proceed_with_action:
                action, tag = command[0]
                print('action:', action, '\ntag:', tag) if debug else None
                if tag in ('DIR', 'FVB', 'USE'):
                    matches = omni_parser.get_labels_and_matches(command)  # [[], []]
                    matches_list = list(omni_parser.get_labels_and_matches(command))
                    if len(matches_list) == 0:
                        print("I do not understand your command.")
                        break
                    for label, match in matches:
                        method, args = omni_parser.exec_func_from_cmd(label, match)
                        funcs_with_kwargs = (player.place, player.throw)
                        function = getattr(player, method)
                        if label == 'FVB-ITEM-AT/IN-ITEM':
                            if function not in funcs_with_kwargs:
                                print("You can't do that.")
                                break
                            else:
                                args, kwarg = args
                        if 'ALL' in args[0]:
                            args = filter_all_except_x(method, args)
                        print('method:', method, '\narguments:', args) if debug else None
                        if debug:
                            # if function in funcs_with_keywd_params:
                            #     function(*args, in_or_at=)
                            if label == 'FVB-ITEM-AT/IN-ITEM' and function in funcs_with_kwargs:
                                function(*args, in_or_at=kwarg)
                            else:
                                function(*args)

                        else:
                            try:
                                print('functioning with try except')
                                print('function:', function)
                                print('args:', args)
                                if label == 'FVB-ITEM-AT/IN-ITEM' and function in funcs_with_kwargs:
                                    function(*args, in_or_at=kwarg)
                                else:
                                    function(*args)
                            except Exception as error:
                                print('\nException was raised.')
                                print('error args:', error.args)
                                for e in error.args[0]:  # args[0] contains a list with all the errors
                                    print(e)  # e is the custom error message itself
                elif tag == 'VB':
                    for label, match in omni_parser.get_labels_and_matches(command):
                        obj, method, args = omni_parser.exec_custom_func_from_cmd(label, match)
                    for obj_command in COMMANDS['custom_commands']:
                        pass

    gameplay()


# command = 'save'
# globals()[command]()


def save():
    print('Saving game...')
    with open('game_save.pickle', 'wb') as file:
        data = (player, LOCATIONS, OBJECTS, ACTORS, COMMANDS, RANDOMS)
        pickle.dump(data, file)


def load():
    global player, LOCATIONS, OBJECTS, ACTORS, COMMANDS, RANDOMS
    print('Loading saved game...')
    with open('game_save.pickle', 'rb') as file:
        data = pickle.load(file)
    player, LOCATIONS, OBJECTS, ACTORS, COMMANDS, RANDOMS = data
    print(player)


if __name__ == '__main__':

    player_data = actualize_data('PLAYER', setup.player_filename)
    player = Player(player_data)

    # test_state_changes()
    # player.activate_func('take')

    gameplay()
