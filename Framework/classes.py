import setup
from errors import *
from nltk import pos_tag
import random
from Colors import *
import omni_parser
from itertools import groupby
import time
from operator import add, sub
from itertools import zip_longest
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


def exceptions_handler(exceptions, typ):
    """Handles things in which general/exception sets are declared."""
    # print('dictionary given in exceptions handler:', dictionary)
    # exceptions = dictionary['exceptions']
    # break out of the loop below if a condition passes
    exceptions = [{'if': [['egg', 'being_held', True]]}]
    for exception in exceptions:  # item is either name of object/actor/location, or 'player'
        print('\nNEW exception set')
        conditions_passed = False
        for condition_set in exception['if']:  # for every exception list in the 'if' key
            item = condition_set[0]  # e.g. player, lantern, troll, or 6a
            state = condition_set[1]  # e.g. 'lit' or 'guarding'
            condition = condition_set[2]  # e.g. True/False, 6a (location)
            if 'range' in str(condition):
                condition = list(eval(condition))

            print('{} state "{}" needs to be (in) {} in order for this exception to fire'.format(item, state, condition))

            if item == 'player':
                item_state = getattr(player, state)
            else:
                for dictionary in [LOCATIONS, OBJECTS, ACTORS]:
                    if item in dictionary:
                        print('item in dictinoary:', dictionary)
                        item_state = getattr(dictionary[item], state)
                        break
            try:
                print('{} state -- {} = {}'.format(item, state, item_state))
            except UnboundLocalError:
                print('\n\n\n\n\nERRORRRRRR\n\n\n\n')
            if type(condition) is list:  # this will work for inventory, too
                conditions_passed = True if item_state in condition else False
            else:
                conditions_passed = True if item_state == condition else False  # if for example the second time around
            # it doesn't pass the condition, set it back to false

        if conditions_passed:  # after looping through the condition set, if all the conditions have passed, then:
            print(BOLD + CYAN + 'CONDITIONS HAVE PASSED\n', END)
            actions = None
            if exception.get('actions'):
                actions = exception['actions']

            if typ == 'narrative':
                return exception['narrative'], actions
            else:
                reaction = [exception['reaction']]  # put it in a list for proper random.choice() functionality
                # (to not pick a letter out of a string)
                return random.choice(reaction), actions  # if there is only one given option (as in most cases),
            # it will only choose the one, and if there are more, it will choose it randomly.
    print(BOLD + RED + 'CONDITIONS HAVE FAILED\n', END)
    return None, None  # if NONE of conditions passed


def general_handler(general, typ, boolean=None):
    """Gets and returns proper general reaction."""

    if type(general) is str or all(k in general for k in (True, False)):  # meaning there are no actions associated with the reaction
        if typ == 'state change':
            return general[boolean], None  # None for no actions
        else:
            return general, None  # None for no actions
    else:
        actions = None
        if typ == 'state change':
            reaction = general['reaction'][boolean]
        elif typ == 'narrative':  # narrative
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
        print('under if actions:', actions)
        for action_set in actions:
            exec_action_from_file(action_set)


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
            return direction[1]
    return False


def check_for_verb(word, original_command):
    """Checks if the word is a verb."""

    def is_partial(word, command):
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
            indexes = [i for i, value in enumerate(command)]  # get all the indexes in the command to know if there is a next/previous word.
            next_word = command[index + 1] if index + 1 in indexes else False
            # print(f'The indexes inside the command of {command} ----- {indexes}')
            # print(f'The next word: "{next}" ---- and the previous word: "{prev}"')
            return next_word

        for dictionary in COMMANDS['general_commands']:  # looping over all the dicts of verbs + needs + action sets
            # The only commands I want are the ones that have spaces in them, which mean they are multi-word commands,
            # the ones that the word is in -- because why would I want to look at a command in which the word is not even
            # there?
            multi_word_cmds = [cmd for cmd in dictionary['verbs'] if ' ' in cmd and word in cmd.split()]
            # the cmd.split() above is very important, because I ran into an error like this before -- the user command was
            # 'let go of lantern', the current word in the iteration was 'of', and the multi-word command in the loop iteration
            # was 'throw off', and it passed the list comprehension conditions! -- How did this happen, you may ask? Because
            # there was a space in 'throw off' and the word 'of' was in 'throw off' -- so I needed to add the .split() method
            # to the command to make sure that the word is actually the same word as the word inside the multi-word command,
            # not simply 'inside' it, lurking there like 'of' inside 'off'.
            for cmd in multi_word_cmds:  # if the word is in the verbs list of current loop dict, now you have your verb
                print('dealing with this multi-word command: ---- :', cmd)
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

                    if check_for_item(next_word, 'OBJ'):  # if the next word is an object
                        try:
                            if user_command[word_index+2] == next_multiword:  # if the word after the object is the next word in the multi-word command
                                return True
                        except IndexError:
                            pass

    # Checking if the word is in all the general commands

    if is_partial(word, original_command):
        return word, 'PFVB'

    for dictionary in COMMANDS['general_commands']:  # looping over all the dicts of verbs + needs + action sets
        if word in dictionary['verbs']:  # if the word is in the verbs list of current loop dict, now you have your verb
            verb = dictionary['function']
            return verb, 'FVB'
        # if complete_match is True:
        #     verb = dictionary['function']
        #     return verb, 'FVB'
        # elif complete_match is False:
        #     return word, 'PFVB'
        # else:
        #     return False
            # return_partial = False
            # if word == cmd:
            #     if is_partial(word, cmd):
            #         return_partial = True
            #
            # elif word in cmd and ' ' in cmd:
            #     if is_partial(word, cmd):  # if the word is not equal to the command, but is rather inside of it, meaning it is partial
            #         return_partial = True
            #
            # if return_partial:
            #     return word, 'PFVB'  # PFVB = partial function verb
            # if word == cmd:
            #     verb = dictionary['function']
            #     return verb, 'FVB'  # FVB = function verb
    return False
    # Checking if the word is a special command, like for an object, location, or actor


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


def check_for_item(word, typ):
    """Checks if word is reference to an object or a location."""
    if typ == 'OBJ':
        dictionary = OBJECTS  # global objects dictionary
    elif typ == 'LOC':
        dictionary = LOCATIONS  # global locations dictionary
    elif typ == 'ACT':
        dictionary = ACTORS

    for item in dictionary:  # loop over dictionary which gives you the actual python objects of objects/locations.
        references = dictionary[item].references
        if word in references:
            item_reference = references[0]  # the first item in object/location's references is always official name of object
            if typ == 'OBJ':
                return item_reference
            elif typ == 'ACT':
                return item_reference
            elif typ == 'LOC':
                return item
    # for references in [item.references for item in dictionary.values()]:
    return False


def dir_to_loc(direction):
    """Translates a given direction to a location that the user goes to."""

    def rdir_to_dir (rd):
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

        print('\nnew direction')
        print('playing moving:', rd)
        print('index to rotate by:', dirs.index(player.orientation))
        print('player facing:', player.orientation)
        new_directions = rotate(dirs, dirs.index(player.orientation))
        print('new relative directions:', new_directions)
        print('final direction:', new_directions[rdirs.index(rd)])
        return new_directions[rdirs.index(rd)]

    if direction in ['L', 'R', 'F', 'B']:
        direction = rdir_to_dir(direction)

    new_loc = LOCATIONS[player.active_location].moves[direction]
    if type(new_loc) is list:  # which means that it's a warning with ability to accept
        print(new_loc[0])

    elif len(new_loc) > 2:  # which means it's not a location num, but rather a message, a no-go
        print(new_loc)
    else:
        return new_loc


def pos_tagger(command):
    """Tags each of the words in the command and returns a list of tuples with appropriate tags."""

    def add(word, POS):
        """Tag the word and add to the skeleton."""
        tagged.append((word, POS))
        i = skeleton.index(word)
        skeleton[i] = ' '

    def tag_word(index):
        """Checks the word for its type and adds the appropriate tag."""
        word = command[index].lower()
        direction = check_for_dir(word)
        verb = check_for_verb(word, intact_cmd)  # pass in word, the full command, and the current index + 1
        location = check_for_item(word, typ='LOC')
        object = check_for_item(word, typ='OBJ')
        actor = check_for_item(word, typ='ACT')
        if direction:
            for dir in direction:
                add(dir, 'DIR')
        elif verb:
            add(word, verb[1])  # verb[1] is the tag: tag can be 'FVB' for function verb or just 'VB' for an object/location/actor verb
        elif location:
            add(word, 'LOC')
        elif object:
            add(word, 'OBJ')
        elif actor:
            add(actor, 'ACT')
        elif word in ('all', 'everything'):  # later maybe add 'every object/item'
            add(word, 'ALL')
        elif word in ('but', 'except', 'excluding'):
            add(word, 'BUT')
        elif word in ('utilize', 'employ', 'apply', 'use', 'utilise'):
            add(word, 'USE')
        elif word == 'to':
            add(word, 'TO')
        elif pos_tag([word])[0][1] == 'IN':  # NLTK pos_tag, argument is list, index 0 is the
            # tuple inside the list, index 1 is second item of tuple, which is the part of speech.
            # the word in the 'but' check above might also be a preposition if it was run through the pos_add() function,
            # that's why it is above this elif statement
            add(word, 'PRP')
        elif word in ('and', 'then', ',', ';', '.'):
            add(word, 'AND')

    skeleton = command
    intact_cmd = command[:]  # the slice is necessary so that intact_cmd does not reference the same list as skeleton does,
    # for if it does, then intact_cmd will change when skeleton changes

    tagged = []
    # pass in the command.
    #
    for i in range(len(command)):
        tag_word(i)

    print('tagged after tagging:', tagged)

    def _rearrange(tagged):
        for dictionary in COMMANDS['general_commands']:
            print('dictionary in COMMANDS:', dictionary)
            multi_word_cmds = [cmd for cmd in dictionary['verbs'] if ' ' in cmd]
            print('all multi_word_cmds:', multi_word_cmds)
            for cmd in multi_word_cmds:
                print('dealing with this multi-word command: ---- :', cmd)
                cmd = cmd.split()
                print('cmd after split:', cmd)
                just_words = [word for word, tag in tagged]
                try:
                    starting_index = just_words.index(cmd[0])
                    print('starting index:', starting_index)
                except ValueError:
                    print(f'\nvalue error, {cmd[0]} is not in just words: {just_words}\n\n')
                    continue

                match = True
                zipped = zip(just_words[starting_index:], cmd)
                indexes_to_remove = [index for index, words in enumerate(zipped)]
                for usr_word, multi_word in zipped:
                    # print(f'tagged word: {usr_word} --- multi command word: {multi_word}')
                    if usr_word != multi_word:
                        print(f"{usr_word} != {multi_word}")
                        match = False
                if match:
                    print('its a match!!!')
                    print('slice indexes, starting index:', indexes_to_remove[0], 'to index', indexes_to_remove[-1]+1)
                    print('slice that is going to be removed:', tagged[indexes_to_remove[0]:indexes_to_remove[-1] + 1])
                    tagged[indexes_to_remove[0]:indexes_to_remove[-1] + 1] = [(dictionary['function'], 'FVB')]
                    return tagged

    def rearrange(label, tagged):
        """Rearranges multi-word command into single-word counterparts."""
        for dictionary in COMMANDS['general_commands']:
            multi_word_cmds = [cmd.split() for cmd in dictionary['verbs'] if ' ' in cmd]  # get all the multi-word commands
            # in the current (in loop) command
            for cmd in multi_word_cmds:
                partials_in_usr_cmd = [word for word, tag in tagged if word in cmd if tag == 'PFVB']  # get all the partial
                # words in the tagged user command. This will combine all the
                if partials_in_usr_cmd == cmd:
                    just_words = [word for word, tag in tagged]
                    if label == 'PFVB(S)-ITEM':
                        start = just_words.index(partials_in_usr_cmd[0])
                        end = just_words.index(partials_in_usr_cmd[-1])
                        tagged[start:end+1] = [('FVB', dictionary['function'])]
                        return tagged
                    elif label == 'PFVB(S)-ITEM-PFVB':
                        start = just_words.index(partials_in_usr_cmd[0])
                        before_item = just_words.index(partials_in_usr_cmd[-2])
                        after_item = just_words.index(partials_in_usr_cmd[-1])
                        len_before = len(tagged)
                        tagged[start:before_item+1] = [('FVB', dictionary['function'])]
                        difference = len_before - len(tagged)
                        del tagged[after_item-difference]
                        return tagged

    sep = ('and', 'AND')
    all_tagged = [list(group) for same_as_sep, group in groupby(tagged, sep.__eq__) if not same_as_sep]
    print('all tagged after all groups:', all_tagged)
    for command_set in all_tagged:
        print('set:', command_set)

    final_tagged = []

    print('rearranging tagged')
    for tagged_cmd in all_tagged:
        new('NEW PARTIAL TAGSET CHECKER')
        if 'PFVB' in str(tagged_cmd) or 'PVB' in str(tagged_cmd):
            match_set = omni_parser.get_labels_and_matches(tagged_cmd, typ='P')
            for label, match in match_set:  # typ can be anything other than 'NORMAL'
                rearranged = rearrange(label, match)
                print('rearranged:', rearranged)
                final_tagged.append(rearranged)
        else:
            final_tagged.append(tagged_cmd)

    print('\ntagged after rearranging:', final_tagged)

    return final_tagged, skeleton
# get_command(tagged)


class Reactor:
    """Class that can be used to react to anything."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def react(self, typ, something, boolean=None, location=None):
        """React to a state change, a command, or an object receipt."""

        # These below variables apply to all cases, all types of reactions
        dict_names = {'state change': 'sc_reactions', 'command': 'cmd_reactions', 'narrative': 'narratives'}
        main_dict = getattr(self, dict_names[typ])
        if typ == 'narrative' and something == 'short' and not main_dict.get('short'):  # if there is no short narrative key...
            dictionary = main_dict['long']  # ...set it to the long key.
        else:
            dictionary = main_dict[something]  # in all other cases, just set it to something

        has_exceptions = True if type(dictionary) is dict and dictionary.get('exceptions') else False
        print_general = True

        if has_exceptions:
            print('This reaction has exceptions')
            exceptions = dictionary['exceptions']
            reaction, actions = exceptions_handler(exceptions, typ)
            # add if there is a general without actions, then it would just be a string, so print(general),
            # but if the general is a dictionary, that means there are actions attached.
            if typ == 'state change':
                if reaction:
                    if reaction.get(boolean):  # if there is a reaction for that boolean change
                        print('reaction has reaction[boolean]')
                        print('exceptions passed, printing reaction')
                        print(reaction[boolean])
                        print_general = False
            else:
                if reaction:
                    print('exceptions passed, printing reaction')
                    print(reaction)
                    print_general = False

        if print_general:
            if type(dictionary) is str or not dictionary.get('general'):
                general = dictionary
            else:
                general = dictionary['general']
            reaction, actions = general_handler(general, typ, boolean)  # if it is not a state change reaction,
            # boolean will be None, and general_handler() will ignore it. If it is, then the boolean passed in will get used by the general_handler
            print(reaction)

        if typ == 'narrative':  # if it is a narrative, before we execute the actions, we need to print all the objects that are in the location
            location = LOCATIONS[location]
            objects = location.objects
            if len(objects) > 0:
                location.print_objects(location.objects)

        exec_actions_if_any(actions)


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
        self.description = obj_dict['description']
        self.short_description = obj_dict['short_desc']
        self.damage = obj_dict['damage']
        self.location = obj_dict['active_location']

        self.being_held = obj_dict.get('being_held')
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


# def react_to_command(self, command):
# 	"""React to a state change or command
# 	:param command: a command.
# 	:param typ: just there for no reason
# 	"""
# 	dictionary = self.cmd_reactions[command]
# 	has_exceptions = True if type(dictionary) is dict else False
# 	# print('dictionary[state_or_cmd] inside react:', dictionary, type(dictionary))
# 	# print('has exceptions:', has_exceptions)
#
# 	if has_exceptions:
# 		reaction, actions = exceptions_handler(dictionary['exceptions'], 'command')
# 		general = dictionary['general']
# 		print(reaction) if reaction else print(general)
# 		exec_actions_if_any(actions)
#
# 	else:
# 		print(dictionary)


class Container(Object):
    """Containers can hold objects inside them. Only one added attribute: inventory"""
    def __init__(self, obj_dict, obj_name):
        Object.__init__(self, obj_dict, obj_name)
        self.inventory = obj_dict['inventory']


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
            raise NotHoldingError
        else:
            if getattr(self, state) == value:
                print(GREEN + "{}'s state of {} is already {}".format(self.name, state, value) + END)  # unpack format
                return

            format = (self.name, state, getattr(self, state), value)
            print("Changing {}'s state of {} from {} to {}".format(*format))  # unpack format
            setattr(self, state, value)
            self.reactor.react('state change', state, value)
    # if player.active_location not in self.info.get('exceptions'):
    #     print(self.sc_reactions[new_state])
    # else:
    #     print(self.sc_reactions['exceptions']
    #           [player.active_location][new_state])

    def print_test(self, word):
        print('test passed with word:', word)

# def react(self, typ, state_or_cmd, boolean=None):
# 	"""React to a state change or command
# 	Must set the last two params to default values or else it will have a dif signature than the base class method
# 	:param state_or_cmd: The object's state that is being changed or the command that is being invoked
# 	:param boolean: The boolean value that the state is being change to. Only passed in for a state change reaction.
# 	:param typ: Either 'state change' or 'command'
# 	"""
# 	# print('typ inside react is:', typ)
# 	if typ == 'command':
# 		Object.react_to_command(self, state_or_cmd)
# 	else:  # if typ == state change
# 		dictionary = self.sc_reactions[state_or_cmd]
# 		has_exceptions = True if dictionary.get('exceptions') else False
#
# 		# print('dictionary[state_or_cmd] inside react:', dictionary, type(dictionary))
# 		# print('has exceptions:', has_exceptions)
#
# 		if has_exceptions:
# 			reaction, actions = exceptions_handler(dictionary['exceptions'], typ)
# 			general = dictionary['general'][boolean]
# 			if not reaction:
# 				print(general)
# 			else:
# 				if not reaction.get(boolean):
# 					print(general)
# 				else:
# 					print(reaction[boolean])
# 		else:
# 			try:
# 				print(dictionary[boolean])
# 			except KeyError:
# 				print('dictionary:', dictionary, 'has no reaction at boolean:', boolean)


class Actor(ComplexObject):
    """Higher level of complexity than a complex object."""

    def __init__(self, actor_dict, name):
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
                player.health -= damage_to_inflict
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

    @staticmethod
    def print_objects(objects):
        """Print all current objects in the location."""
        objects_here = 'With you in this location is '
        for i in range(len(objects)):
            obj = OBJECTS[objects[i]]  # objects[i], for example, is 'egg'. so OBJECTS['egg']
            if i == len(objects) - 1 and len(
                    objects) > 1:  # if it's the last object to add to the list AND if there is more than one object
                objects_here += ' and ' if len(
                    objects) == 2 else 'and '  # add an 'and', e.g. x, y, and z -- space before 'and' based on conditional
            objects_here += obj.short_description
            if len(objects) > 2:
                objects_here += ', '
        objects_here = objects_here.strip(', ') + '.'  # strip trailing comma and replace with a period.
        print(objects_here)

    def narrate(self, typ=None):
        """Does a few checks and then prints the appropriate narrative."""
        def check_narrative(nars):
            """Returns appropriate narrative."""
            if type(nars) is str:  # if there are no actions or exceptions, simply one narrative for all cases
                return nars, None  # None for no actions
            elif 'narrative' and 'action' in nars:  # one narrative for all cases, but an action -- for all cases --
                # that comes along with it
                return nars['narrative'], nars['actions']
            else:
                return exceptions_handler(nars['exceptions'], typ='narrative')

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
        Need to set active_location and inventory as parameters (instead of simply adding them as attributes) in order to allow progress saving.
        When I start up a game again, I will re-create the Player object with their saved active location.
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

    def take(self, reference):
        """To be called when user says to take an object."""
        reference = check_for_item(reference, typ='OBJ')  # Get official name of object
        if not reference:
            raise ObjectError
        if reference in self.inventory:
            raise AlreadyHoldingError  # print("You're already carrying the {}.".format(reference))
        else:
            location = LOCATIONS[self.active_location]
            if reference in location.objects:
                self.inventory.append(reference)  # add object to player's inventory
                location.objects.remove(reference)  # remove object from location
                OBJECTS[reference].react('command', 'take')
                print("The {} has been added to your inventory.".format(reference))
            else:
                print("There is no {} here.".format(reference))
    # def pick_up (self, item):
    #     """Pick an object, put in inventory, set its owner."""
    #     self.inventory.append(item)
    #     item.owner = self

    def drop(self, reference, throw=False):
        """To be called when user says to drop an object."""
        reference = check_for_item(reference, typ='OBJ')  # Get official name of object
        if not reference:
            raise ObjectError
        if reference not in self.inventory:
            raise NotHoldingError("You're not carrying a(n) {}.".format(reference))
        else:
            self.inventory.remove(reference)
            location = LOCATIONS[self.active_location]
            location.objects.append(reference)
            typ = 'throw' if throw else 'drop'
            OBJECTS[reference].reactor.react('command', typ)

    def throw(self, reference, actor=None):
        """Throw an object -- either a simple throw at nothing or a throw at an actor."""
        if not actor:
            self.drop(reference, throw=True)
        else:
            self.attack(actor, reference)

    def give(self, actor, reference):
        """

        :param actor:
        :param reference:
        """
        self.inventory.remove(reference)
        ACTORS[actor].accept(reference)

    def goto(self, *locations, typ=None):
        """

        :param locations:
        """

        def exec_warning(warning_dict):
            """Executes a warning."""
            warnings = COMMANDS['warnings']
            affirmations, negations = warnings['yes'], warnings['no']
            while True:
                answer = input(warning_dict['warning'] + ' ')
                if command_check(answer, affirmations, typ='simple'):
                    return True, warning_dict['yes']
                elif command_check(answer, negations, typ='simple'):
                    return False, warning_dict['no']
                else:
                    print("Answer must be in the affirmative or the negative. I'll ask again.")

        def play_random_message(dict_name):
            """Plays a random message from the random dictionary."""
            messages = RANDOMS[dict_name]
            choice = random.choice(messages)
            print(choice)

        for new_location in locations:
            going_to = True
            if str(new_location) not in LOCATIONS:  # I have to turn new_location into a str or else it raises a
                # TypeError: unhashable type: 'dict'
                if type(new_location) is dict:  # if it a dictionary that means it's a warning set
                    boolean, loc_or_reaction = exec_warning(new_location)
                    if boolean:
                        new_location = loc_or_reaction
                    else:
                        print(loc_or_reaction)
                        going_to = False
                elif new_location in RANDOMS:  # if it's in the RANDOM_DICTS dictionary...
                    play_random_message(new_location)  # ...play a random message from the dictionary
                    going_to = False
                else:
                    raise GoToError
            if going_to:
                print('Going to:', new_location)
                self.active_location = new_location
                LOCATIONS[new_location].narrate(typ)

    def attack(self, actor, with_object):
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

    def die(self):
        print('You has dieded, sorry bud.')
        raise SystemExit

    def __str__(self):
        return ('I am a player in this game. I am currently in location ' + self.active_location[-1]
                + ' and I am holding ' + str(self.inventory))


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


LOCATIONS = {}
OBJECTS = {}
ACTORS = {}
COMMANDS = actualize_data('COMMANDS', setup.cmd_filename)
RANDOMS = actualize_data('RANDOMS', setup.randoms_filename)
actualize_data('LOCATIONS', setup.loc_filename)
actualize_data('OBJECTS', setup.obj_filename)
actualize_data('ACTORS', setup.act_filename)

# class Character:
#
#     def __init__(self, health):
#         self.health = health
#
#     def attack(self, other):
#         raise NotImplementedError


def new(action):
    """Prints a header and the action that is being tested."""
    print('\n' + BOLD + BLACK_W_BG + '---NEW---' + END)
    print(BOLD + YELLOW + action.upper() + END)


def test_state_changes():
    """Testing testing 123."""

    # for attack in range(2):
    # 	print('\nattacking troll, iteration #'+str(attack))
    # 	ACTORS['troll'].is_attacked(random.randint(1, 25))
    #
    # for _ in range(2):
    # 	try:
    # 		print('throwing egg')
    # 		player.throw('egg')
    # 	except ObjectError:
    # 		print('There is no such thing as an egg in this game')
    # 	except NotHoldingError:
    # 		print("You're not carrying a(n) {}.".format('egg'))
    # 	finally:
    # 		player.inventory.append('egg')
    # 		try:
    # 			player.take('egg')
    # 		except AlreadyHoldingError:
    # 			print('you are already holding the egg')
    #
    # new('climbing in 6a while player can walk')
    # player.can_walk = True
    # LOCATIONS['6a'].react('climb')
    #
    # new('climbing in 6a')
    # LOCATIONS['6a'].react('climb')
    # loc = LOCATIONS['4a'].moves['S']
    # new('going to loc 4a')
    # player.goto(loc)
    # raise SystemExit
    #
    # new('going to loc 2')
    # player.goto('2')
    #
    # new('climbing in 6a while player can walk')
    # player.can_walk = True
    # LOCATIONS['6a'].react('climb')
    print('lantern being held:', OBJECTS['lantern'].being_held)
    player.inventory.append('lantern')
    new('changing lantern lit to True')
    OBJECTS['lantern'].change_state('lit', True)

    new('narrating LONG')
    LOCATIONS['6a'].narrate()

    new('narrating SHORT')
    LOCATIONS['6a'].narrate()

    new('throwing egg')
    print(set(OBJECTS.keys()), len(OBJECTS))
    OBJECTS['egg'].react('command', 'throw')
    print(set(OBJECTS.keys()), len(OBJECTS))
    # try:
    # 	print('\nthrowing lantern')
    # 	player.throw('lantern')
    # except NotHoldingError:
    # 	print('cant throw a lantern that ur not holding')
    #
    # player.inventory.append('lantern')
    # print('throwing lantern in 4a')
    # player.active_location = '4a'
    # player.throw('lantern')
    #
    # print('\n\ngiving troll egg')
    # player.give('troll', 'egg')
    #
    # print('\n\ntroll reactinggggg')
    # ACTORS['troll'].health -= 20
    # print('changing health:', ACTORS['troll'].health)
    # print('\n\ngiving troll egg after changed health')
    # player.give('troll', 'egg')
    #
    new('changing lantern lit to True')
    OBJECTS['lantern'].change_state('lit', True)

    new('changing lantern lit to False')
    OBJECTS['lantern'].change_state('lit', False)

    player.active_location = '6a'
    print('changed player location to 6a')

    new('changing lantern lit to False')
    OBJECTS['lantern'].change_state('lit', False)
    new('changing lantern lit to True')
    OBJECTS['lantern'].change_state('lit', True)
# new()
# player.active_location = '4a'
# exceptions_handler(LOCATIONS['4a'].narratives['long'], 'narrative')
#
# new()
# print('reacting to take command')
# OBJECTS['lantern'].react('command', 'take')
#
# new()
# print('reacting to throw command')
# OBJECTS['lantern'].react('command', 'throw')
#
# player.active_location = '5'
# new()
# print('reacting to throw command after players location is 5')
# OBJECTS['lantern'].react('command', 'throw')
# pass


def condense(p_input):
    """Condenses preliminary input. Removes predefined stop phrases and removes articles."""
    import re
    stop_phrases = ['go and', 'go forth and', 'go ahead and']
    for phrase in stop_phrases:
        if phrase in p_input:
            p_input = p_input.replace(phrase, '')

    delimiters = r'(; ?)|(, ?)|(\. ?)| a | an | the '  # the things in parentheses will be kept, those not in parentheses will be removed.
    split = re.split(delimiters, p_input)  # split by all the delimiters and keep the delimiters
    final = []
    # re.split() will return None because you have more than one capturing groups, and all groups are included as a part
    # of the re.split() result, so anything that doesn't match to all the groups will return None. So filter out the None
    # and turn the iterator returned by filter into a list.
    for word_set in list(filter(None, split)):
        for word in word_set.split():  # split automatically strips the whitespaces
            final.append(word)

    return final


def gameplay():
    """The gameplay function that will keep the game running till exit."""

    # test_inputs = ['pick lantern up', 'throw away knife', 'pick up knife', 'let go of lantern', 'let go lantern']
    while True:
        new('NEW PLAYER INPUT')
        player_input = condense(input('enter command: '))
        print('player input:', player_input)
        commands, unparsed = pos_tagger(player_input)
        print('tagged:', commands)
        print('skeleton:', unparsed)


if __name__ == '__main__':

    player_data = actualize_data('PLAYER', setup.player_filename)
    player = Player(player_data)

    # test_state_changes()
    # player.activate_func('take')

    gameplay()

    # player.inventory.append('egg')
    try:
        player.drop('egg')
    except AlreadyHoldingError:
        print('already holding object')
    except NotHoldingError:
        print('not holding object')


# print(player.inventory)
# gameplay()

#
# # Start game process
# for dir in ['S', 'E', 'E', 'S']:
#     direction_to_loc(dir)
#     print('player\'s active location:', player.active_location)
#
#
# for word in command:
#     check_command(word, command)

# Get user command. split into nouns and verbs.
# before doing anything based on nouns/verbs, loop through each word and
# check if the word is in the general command verbs:
# if word in general command verbs, then check what else the command needs.
# if 'needs' == 'object', check the rest of the words
# to see if it is in any of the references to any of the objects.
# If it is, then u have your verb and your object. save object name to a variable,
# and then get the object at object_variable from global list of objects.
# use player.get_attribute(verb) and then pass into that attribute the object
# from global list of objects.
# If not, tell user that there is no such object here or something like that.
# if 'needs' == 'location', check the rest of the words
# to see if it the number of a location.
# If it is, then you have your verb and location. Use same method specified
# above.
# if not, check if it's in any of the custom command verbs
# if not, check if its in any of the references of the objects.


# get player method based on verb, if it exists. If it doesn't exist, say that
# player can't do that.
# pass in argument to the player method based on the noun. If 'needs' a location,
# check if the noun is

# BELOW (COLLAPSED): old for word in command, if dir, if verb_result, etc...
# for word in command:

#     # ADD THAT IF THEY SAY ATTACK KEY AND THERE IS NO KEY, SAY THERE IS NO KEY

#     if direction:
#         # DEAL WITH THE DIR_TO_LOC FUNCTION
#         direction = dir_to_loc(direction)
#         for dir in direction:
#             all_commands.append(['goto', dir])
#
#     elif verb_result:
#
#         verb, needs = verb_result
#         verb_command = [verb]
#         command.remove(word)
#
#         for inner_word in command:
#             print('\n\ninner_word:', inner_word)
#             meets_requirement = check_requirements(inner_word, needs)
#             if meets_requirement:
#                 print('requirement:', meets_requirement)
#                 verb_command.append(meets_requirement)
#                 command.remove(inner_word)  # if it meets the requirement, we add it to the verb command,
#                 # but we don't want to accidentally use it again so we remove it
#
#         all_commands.append(verb_command)
#
#     elif location:
#         all_commands.append(['goto', location])
#     #
#     # elif object:
#     #     command.remove(word)
#     #     for inner_word in command:
#     #         verb_result = check_for_verb(inner_word)
#     #         if verb_result:
#     #             verb, needs = verb_result
#     #             meets_requirement = check_requirements(object, needs)
#     #             break  # once you find a verb, even if the object
#     #             # use lantern to attack troll
#
# return all_commands

# pick up, let go of
