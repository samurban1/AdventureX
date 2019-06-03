"""Handles the input from the user."""
from Skeleton.classes import *
#     (player, debug, save, load, quit, pos_tagger, turn_to_sentence, random_response,
#                      ask_until_respond, filter_all_except_command, print_big, condense_and_split)
from Parser import omni_parser


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
            'save': save,
            'load': load,
            'quit': quit,
            'inventory': lambda: player.describe('inventory'),
            'diagnose': lambda: player.describe('health'),
            'look': lambda: player.describe('location'),
        }

        if command_set[0] in special_commands:
            special_commands[command_set[0]]

        command, unparsed = pos_tagger(command_set)  # parsing the text and getting tagged command back

        print('\nFINAL command:', command) if debug else None
        print('skeleton:', unparsed, '\n') if debug else None

        def partial_understanding(command, unparsed):
            not_understood = [word for word in unparsed if word != ' ']
            yes_understood = [(word, tag) for word, tag in command if tag != 'ERR']
            print(f"not understood: {not_understood}, yes understood: {yes_understood}") if debug else None
            if len(not_understood) > 0 and len(yes_understood) > 1:  # there are some not-understood words and there is at
                # least 1 word that IS understood. If there are no words that are understood, then why bother going through a
                # function that tells the user what it DOES understand from the command when it does't understand anything
                # in the first place?!
                errors = turn_to_sentence(not_understood, "I don't understand ", 'or')
                amt_of_matches = list(omni_parser.get_labels_and_matches(yes_understood))
                print('amt of matches:', amt_of_matches)
                if len(amt_of_matches) == 0:  # if there are NO matches to any of the defined chunks in the parser grammar
                    print(random_response('invalid'))  # then tell them that their command was stupid and invalid
                    return None
                else:
                    yes_understood = ' '.join([word for word, tag in amt_of_matches[0][1]])
                    space = '' if len(not_understood) > 2 else ' '
                    yes_understood = yes_understood.replace('goto', 'go')
                    question = f"{space}but in my limited understanding, am I correct in that you want to {yes_understood}?"
                    if not ask_until_respond(errors + question):
                        print('Okay, okay...Jeez.')
                        return None
                    command = [(word, tag) for word, tag in command if tag != 'ERR']
                    return command
            else:
                return command

        command = partial_understanding(command, unparsed)
        if command is None:
            return

        unprovided = omni_parser.get_labels_and_matches(command, typ='ERRORS')
        for label, match in unprovided:
            print('ERROR | label:', label, 'match:', match) if debug else None
            error = omni_parser.cmd_with_unprovided(label, match, command)
            if error:
                if type(error) is str:
                    print(error)
                    return
                else:
                    insert_word, index_to_insert, message = error
                    print(message)
                    intermediate_cmd = input('◢▲◢◣◢▲◣ ')
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
                    return

        matches_list = list(omni_parser.get_labels_and_matches(command))
        if len(matches_list) == 0:
            print(random_response('invalid'))
            return
        chunked_part = matches_list[0][1]
        if len(command) > len(chunked_part):
            print("The command that the player passed in is greater than the part of the command that was chunked. Meaning,"
                  "there are some parts of the player's command that was chunked, but not the whole thing, so their command"
                  "doesn't make sense.")
            print(f"btw, the chunked part is {chunked_part}")
            return
        action, tag = command[0]
        tags = [tag for word, tag in command]
        print('action:', action, '\ntag:', tag) if debug else None
        if 'VB' in tags:
            for label, match in omni_parser.get_labels_and_matches(command):
                custom_func, items, args = omni_parser.exec_custom_func_from_cmd(label, match)
                print('RESULTS:', custom_func, items, args)

            for obj_command in COMMANDS['custom_commands']:
                for item in items:
                    print('item in loop:', item)
                    if item in obj_command['valid_items'] and custom_func in obj_command['verbs'][0]:
                        actions = obj_command['actions']
                        for action in actions:
                            index = action.index('item')
                            action[index] = action[index].replace('item', item)
                        try:
                            exec_actions_if_any(actions)
                        except Exception as error:
                            if len(error.args[0]) > 0:  # args[0] contains a list with all the errors
                                all_errors = [str(e) for e in error.args[0]]  # str(e) returns just the error message
                                unique_errors = list(set(all_errors))  # set() removes the duplicates
                                for e in unique_errors:
                                    print(e)  # e is the custom error message itself

        else:
            matches = omni_parser.get_labels_and_matches(command)  # [[], []]
            for label, match in matches:
                print('match from omni final:', match) if debug else None
                print('final label in match in matches:', label) if debug else None
                method, args = omni_parser.exec_func_from_cmd(label, match)
                if args is None:  # meaning the sentence is incoherent
                    if method is True:
                        print(random_response('invalid'))
                        return
                    else:
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
                    print('method:', method, '\narguments:', args) if debug else None
                    if debug:
                        if function in (player.take, player.throw, player.place):
                            function(*args, label=label)
                        else:
                            function(*args)
                    else:
                        try:
                            if function in (player.take, player.throw, player.place):
                                function(*args, label=label)
                            else:
                                function(*args)
                        except Exception as error:
                            if len(error.args[0]) > 0:  # args[0] contains a list with all the errors
                                all_errors = [str(e) for e in error.args[0]]  # str(e) returns just the error message
                                unique_errors = list(set(all_errors))  # set() removes the duplicates
                                for e in unique_errors:
                                    print(e)  # e is the custom error message itself



def gameplay():
    """The gameplay function that will keep the game running till exit."""

    player.active_location = '8a'
    # ACTORS['troll'].guarding = True
    print(player) if debug else None

    while True:
        print_big('NEW PLAYER INPUT') if debug else None
        player_input = condense_and_split(input('◢▲◢◣◢▲◣ '))
        print('player input:', player_input) if debug else None
        input_handler(player_input)


if __name__ == '__main__':

    # test_state_changes()
    # player.activate_func('take')

    gameplay()
