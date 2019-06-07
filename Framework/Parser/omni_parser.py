from nltk import RegexpParser
import CommandGrammar


def turn_to_sentence(words, starting_msg):
    """Print all current objects in the location."""
    message = starting_msg
    for i in range(len(words)):
        # obj = OBJECTS[objects[i]]  # objects[i], for example, is 'egg'. so OBJECTS['egg']
        if i == len(words) - 1 and len(words) > 1:  # if it's the last word to add to the list AND if there is more than one word
            message += f' and ' if len(words) == 2 else f'and '  # add an 'and', e.g. x, y, and z -- space before 'and' based on conditional
        # objects_here += obj.short_description
        message += words[i]
        if len(words) > 2:
            message += ', '
    message = message.strip(', ')
    return message


def incoherent(function, arguments, tags, label):
    """Checks if the structure of a sentence makes sense. If returns True, the game plays a generic 'that didn't make sense
    command, and if function returns a string instead, it plays the string."""
    act_on_obj_functions = ['take', 'throw', 'drop', 'describe', 'place']
    act_on_actor_functions = ['attack', 'give']  # add 'speak' later
    if label in ('FVB-ITEM-OUT-OF/FROM-CONT', 'FVB-OBJ-FROM-CONT'):
        if function != 'take':
            return f"You can't {function} something out of something."
    elif label in ('USE-OBJ-TO-FVB-ACT/OBJ', 'FVB-ACT/OBJ-WITH-OBJ'):
        if function in act_on_obj_functions:
            obj = arguments[0] if label == 'USE-OBJ-TO-FVB-ACT/OBJ' else arguments[-1]
            add_text = 'in something' if function == 'place' else ''
            return f"You don't need an {obj} to {function} something {add_text}. You can do it all by yourself."
    elif label == 'FVB-OBJ/ALL-IN/FROM-CONT':
        if function in ('throw', 'drop'):
            return f"If you want to put an object into something, then say so."
        elif function == 'place' and arguments[0] == arguments[2]:
            return "You can't put something inside itself."
        elif function == 'describe':
            return f"If you want to get a description "
        elif function not in ('place', 'take'):  # because this structure can be used to: take egg in backpack
            return True
        # if function in
    elif label == 'FVB-OBJ-AT-ACT':  # only thing that works with this structure is throw object at actor
        if function != 'throw':
            return True
    elif label == 'FVB-ACT/OBJ-WITH-OBJ':
        pass
    elif label == 'FVB-ALL-BUT-ACT/OBJ':
        if function not in act_on_obj_functions:
            return True
    elif 'FVB-OBJ/ALL' in label and 'CONT' in label:  # the and 'CONT' in label is just a precaution, not necessary because
        # there are only a few chunks with 'FVB-OBJ/ALL' in them, all of them which I would like to apply this function to.
        print("'FVB-OBJ/ALL' in label and 'CONT' in label") if debug else None
        if 'BUT' in tags:
            if tags[0] != 'ALL':
                return "That sentence structure just did not make any sense."

    elif label == 'FVB-TO-DIR':
        if function != 'goto':
            return True
    elif label == 'FVB-ALL':
        if function not in act_on_obj_functions:
            return True
    elif label == 'FVB-ALL-BUT-ALL':
        if function not in act_on_obj_functions:
            return True
        else:
            return f"Ok, {function}ing nothing."


def cmd_with_unprovided(label, match, full_cmd):
    """Checks if player just ended a one-word command, like 'lantern' or 'go' and returns appropriate response."""
    act_on_obj_functions = ['take', 'throw', 'drop', 'describe', 'place']
    word = match[0][0]
    tags = [tag for word, tag in full_cmd]
    if len(full_cmd) == 1:
        if label == 'FVB':
            if word == 'goto':
                return 'go', 0,  "Go where?"
            elif word == 'turn':
                return 'turn', 0, "Please specify a direction in which to turn. No need to re-enter full command."
            else:
                return word, 0, f"{word} what?"
        elif label == 'OBJ/ACT':
            return word, 1, f"What about the {word}?"
    else:
        if label == 'FVB-ERR':
            if word in act_on_obj_functions:
                return "There is no such thing here."
            elif word == 'goto':
                return "That is neither a place nor a direction."
            elif word == 'turn':
                return "That is not a direction (that you can turn in)."
        elif label == 'PLACE-OBJ':
            if word == 'place' and 'CONT' not in tags:
                objects = [word for word, tag in match[1:]]
                return f"{turn_to_sentence(objects, 'Put the ')} in what?"


# this needs MAJOR MAJOR MAJOR fixing. I mean doing. It needs doing. It's not done. Simple. Do it.
def exec_custom_func_from_cmd(label, tagged_cmd):
    """Returns the proper arguments for a custom, game-designer-created function."""
    # label == VB-ITEM == on lantern, lantern on
    tags = [tag for word, tag in tagged_cmd]
    index = tags.index('VB')
    custom_function = tagged_cmd[index][0]
    tagged_cmd.pop(index)

    print('label matched:', label) if debug else None

    args = [word for word, tag in tagged_cmd]

    if label in ('VB-ITEM', 'ITEM-VB'):
        return custom_function, args, None
    elif label in ('VB-ACT/OBJ-WITH-OBJ', 'ACT/OBJ-VB-WITH-OBJ'):
        actor_or_obj, with_object = args[0], args[-1]
        return custom_function, [actor_or_obj], with_object  # actor_or_obj must be in list for command_prompt to treat it
        # as if multiple objects are being acted on, then looping over each object in the list. If not put in list, it will
        # loop over the letters in the object name, and we DON'T want that.
    elif label == 'USE-OBJ-TO-VB-ACT/OBJ':
        actor_or_obj, with_object = args[-1], args[1]
        return custom_function, [actor_or_obj], with_object


def exec_loc_verb_from_cmd(tagged_cmd):
    command = tagged_cmd[0][0]
    return command


def exec_func_from_cmd(label, tagged_cmd):
    """Parses the command into its function and arguments"""

    # if above if statement fails
    first_label = tagged_cmd[0][1]
    print('label matched:', label) if debug else None
    if first_label not in ('DIR', 'LOC'):
        index = 0 if first_label == 'FVB' else 3  # the else is for a USE-0BJ-TO-VB-ACT command
        method = tagged_cmd[index][0]  # get the [insert index here] element of the list of tuples, then get the first element of the tuple,
                                    # which is the verb, which is the function name
        tagged_cmd.pop(index)
    args, tags = zip(*tagged_cmd)  # unpack zip object
    args = list(args)

    if first_label not in ('DIR', 'LOC'):  # the only chunk patterns with first label as DIR are 'DIR' and 'DIR-NUM', and there is no
        # possibility of incoherency with those two patterns.
        print(f"calling incoherent() on {method, args, tags, label}") if debug else None
        incoherent_cmd = incoherent(method, args, tags, label)
        if incoherent_cmd:
            return incoherent_cmd, None

    if 'CONT-BUT-OBJ' in label:
        i = tags.index('CONT')  # will find the index of the first container, so even if the OBJ is a CONT in this case,
        # it will work fine.
        return method, ('ALL-IN-CONT-BUT', args[i], *args[i+2:])

    elif 'FVB-OBJ/ALL' in label and 'CONT' in label:  # the and 'CONT' in label is just a precaution, not necessary because
        # there are only a few chunks with 'FVB-OBJ/ALL' in them, all of them which I would like to apply this function to.
        if 'ALL' in tags:
            if 'BUT' in tags:
                container_index = tags.index('CONT')
                container = args[container_index]
                starting_but = tags.index('BUT') + 1
                return method, ('ALL-IN-CONT-BUT', container, *args[starting_but:])
            else:
                return method, ('ALL-IN-CONT', args[-1])  # args[-1] is the container
        elif 'OBJ' in tags or 'CONT' in tags:  # could use else, but as the Zen of Python says, 'Explicit is better than implicit.'
            # if the tag is FVB-OBJ/ALL-OUT-....', then the objects stop right before the 'OUT', but if the tag is
            # FVB-OBJ/ALL-IN-..., then the objects stop right before the 'IN'. Same goes for 'FROM'.
            for tag in ('OUT', 'FROM', 'IN'):  # the order of this tuple is super important. It needs to check 'FROM' before
                # checking 'IN' because if the tag is 'FVB-OBJ/ALL-FROM-IN-CONT' then it will think 'IN' is the stop index,
                # which is wrong -- FROM should be the stop index.
                if tag in tags:
                    stop = tags.index(tag)
                    break

            return method, (*args[0:stop], args[-1])

    elif label == 'FVB-ALL-BUT-OBJ':
        return method, ('ALL-BUT', *args[2:])

    elif label == 'FVB-ALL':
        return method, ['ALL']

    elif label in ('FVB-OBJ-FROM-CONT', 'FVB-OBJ-IN-CONT', 'FVB-OBJ-AT-ACT'):
        args = args[:-2] + args[-1:]
        print('returning take lantern, args:', args)
        return method, args

    elif label == 'FVB-OBJ-OUT-OF/FROM-CONT':
        # Take egg out of/from backpack
        args = [args[0], args[-1]]
        return method, args

    elif label == 'USE-OBJ-TO-FVB-ACT/OBJ':
        actor_or_obj, with_object = args[-1], args[1]
        # print(actor_or_obj, with_object)
        # function(actor_or_obj, with_object)
        return method, (actor_or_obj, with_object)

    elif label == 'FVB-ACT/OBJ-WITH-OBJ':
        actor_or_obj, with_object = args[0], args[2]  # skip over the WITH which is at args[1]
        # print(actor_or_obj, with_object)
        # function(actor_or_obj, with_object)
        return method, (actor_or_obj, with_object)

    elif label == 'FVB-ITEM':
        return method, args

    elif label in ('FVB-TO-DIR', 'FVB-TO-LOC'):
        return method, args[1:]

    elif label in ('DIR-NUM', 'FVB-DIR-NUM'):
        return 'goto', ((args[0]),)*int(args[1])  # multiply whatever DIR is by NUM. this multiplication creates a tuple
        # with multiple DIRs, e.g. ('N', 'N', 'N', 'N')

    elif label in ('DIR', 'LOC'):
        method = 'goto'
        return method, args


def get_labels_and_matches(tagged, typ='NORMAL'):
    """Processes a command and sends it to the appropriate function."""
    if typ == 'NORMAL':
        chunked = chunkParser.parse(tagged)  # get the chunks, the matches that fit with the grammar
    elif typ == 'ERRORS':
        chunked = errorParser.parse(tagged)
    elif typ == 'PARTIAL':
        chunked = partialParser.parse(tagged)

    responses = list(chunked.subtrees())[1:]  # turn the generator that is returned by chunked.subtrees() into a list and
    # get all the matches but the 0th (which is a Tree that contains ALL the subtrees -- the other list elements are the subtrees themselves)

    labels = [response.label() for response in responses]  # for every chunk/response Tree in the responses list, get the label from that Tree
    matches = [response.leaves() for response in responses]  # for every chunk/response Tree in the responses list, get the leaves (which are the commands themselves,) from that Tree
    # print(response)

    # zip returns an iterable of python tuples where each element of the tuple will be from the lists passed into zip().
    # zip() is mainly used to combine data of two iterable elements together
    print('labels:', labels, '\nmatches:', matches) if debug else None
    return zip(labels, matches)


partialParser = RegexpParser(CommandGrammar.partial_rearrangements)

chunkParser = RegexpParser(CommandGrammar.command_structures)  # create the parser with the grammar defined above

errorParser = RegexpParser(CommandGrammar.specific_errors)

debug = False

