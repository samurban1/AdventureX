from nltk import RegexpParser
from CommandGrammar import *


def incoherent(function, arguments, tags, label):
    """Checks if the structure of a sentence makes sense. If returns True, the game plays a generic 'that didn't make sense
    command, and if function returns a string instead, it plays the string."""
    act_on_obj_functions = ['take', 'throw', 'drop', 'describe', 'place']
    act_on_actor_functions = ['attack', 'give']  # add 'speak' later
    if label in ('FVB-ITEM-OUT-OF/FROM-CONT', 'FVB-OBJ-FROM-CONT'):
        if function != 'take':
            return f"You can't {function} something out of something."
    elif label == 'USE-OBJ-TO-FVB-ACT/OBJ':
        if function in act_on_obj_functions:
            return f"You can {function} things all by yourself. You can't use something to {function} something."
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
    if len(full_cmd) == 1:
        if label == 'FVB':
            if word == 'goto':
                return 'go', 0,  "Go where?"
            elif word == 'turn':
                return 'turn', 0, "Please specify a direction in which to turn. Re-enter full command."
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
    elif label == 'FVB-ACT/OBJ-WITH-OBJ':
        return custom_function, args[0], args[1:]
    elif label == 'USE-OBJ-TO-VB-ACT/OBJ':
        pass


def exec_func_from_cmd(label, tagged_cmd):
    """Parses the command into its function and arguments"""

    # if above if statement fails
    first_label = tagged_cmd[0][1]
    print('label matched:', label) if debug else None
    if first_label != 'DIR':
        index = 0 if first_label == 'FVB' else 3  # the else is for a USE-0BJ-TO-VB-ACT command
        method = tagged_cmd[index][0]  # get the [insert index here] element of the list of tuples, then get the first element of the tuple,
                                    # which is the verb, which is the function name
        tagged_cmd.pop(index)
    args, tags = zip(*tagged_cmd)  # unpack zip object

    if first_label != 'DIR':  # the only chunk patterns with first label as DIR are 'DIR' and 'DIR-NUM', and there is no
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

    elif label == 'FVB-TO-DIR':
        return method, args[1:]

    elif label in ('DIR-NUM', 'FVB-DIR-NUM'):
        return 'goto', ((args[0]),)*int(args[1])  # multiply whatever DIR is by NUM. this multiplication creates a tuple
        # with multiple DIRs, e.g. ('N', 'N', 'N', 'N')

    elif label == 'DIR':
        method = 'goto'
        return method, args


# make sure egg to take, make sure it fits with user allowed weight

partialParser = RegexpParser(partial_rearrangements)

chunkParser = RegexpParser(command_structures)  # create the parser with the grammar defined above

errorParser = RegexpParser(specific_errors)


def get_labels_and_matches(tagged, typ='NORMAL'):
    """Processes a command and sends it to the appropriate function."""
    if typ == 'NORMAL':
        chunked = chunkParser.parse(tagged)  # get the chunks, the matches that fit with the grammar
    elif typ == 'ERRORS':
        chunked = errorParser.parse(tagged)
    else:
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


debug = False

if __name__ == '__main__':

    tagged1 = [('attack', FVB), ('troll', ACT), ('with', WITH), ('lantern', OBJ)]
    tagged2 = [('open', FVB), ('chest', OBJ), ('with', WITH), ('nut', OBJ)]
    # tagged3 = [('use', USE), ('sword', OBJ), ('to', TO), ('attack', VB), ('troll', ACT)]
    # tagged4 = [('use', USE), ('nut', OBJ), ('to', TO), ('open', VB), ('chest', OBJ)]
    #
    # partial1 = [('let', 'PFVB'), ('go', 'PFVB'), ('of', 'PFVB'), ('lantern', 'OBJ')]
    # partial2 = [('pick', 'PFVB'), ('up', 'PFVB'), ('lantern', 'OBJ')]
    # partial3 = [('pick', 'PFVB'), ('lantern', 'OBJ'), ('up', 'PFVB')]

    for tagged in tagged1, tagged2:  #, tagged3, tagged4:
        for label, match in get_labels_and_matches(tagged):
            print('label:', label)
            print('match:', match)
            exec_func_from_cmd(label, match)
        print('\n\nDONE 1!!')


# chunkParser = RegexpParser(long_phrases)
#
# chunked = chunkParser.parse(tagged)
#
# print(chunked.draw())
