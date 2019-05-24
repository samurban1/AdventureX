from nltk import RegexpParser
from classes import debug


# Constants
OBJ = 'OBJ'
WITH = 'WITH'
FVB = 'FVB'
ACT = 'ACT'
AND = 'AND'
DIR = 'DIR'
USE = 'USE'
TO = 'TO'
AT = 'AT'
IN = 'IN'
BUT = 'BUT'
ALL = 'ALL'
CONT = 'CONT'


command_structures = r"""
                USE-POBJ-TO-FVB-ACT/OBJ: {<USE><POBJ><TO><FVB><(ACT|OBJ)>}
                USE-OBJ-TO-FVB-ACT/OBJ: {<USE><OBJ><TO><FVB><(ACT|OBJ)>}
                FVB-ITEM-AT/IN-ITEM: {<FVB><OBJ>+<(AT|IN)><(ACT|OBJ)>}
                FVB-ACT/OBJ-WITH-OBJ: {<FVB><(ACT|OBJ)><WITH><OBJ>}
                FVB-ACT/OBJ-WITH-POBJ: {<FVB><(ACT|OBJ)><WITH><POBJ>}
                FVB-ALL-BUT-ACT/OBJ: {<FVB><ALL><BUT><(ACT|OBJ)>+}
                FVB-TO-DIR: {<FVB><TO><DIR>+}
                VB-ITEM: {<VB><(ACT|OBJ|LOC)>}
                ITEM-VB: {<(ACT|OBJ|LOC)><VB>}
                DIR-NUM: {<FVB><DIR><NUM>}
                         {<DIR><NUM>}
                FVB-ALL: {<FVB><ALL>}
                FVB-ITEM: {<FVB><OBJ>+}
                          {<FVB><DIR>+}
                          {<FVB><ACT>}
                DIR: {<DIR>+}
                LVB: {<LVB>}
                BUILTIN-CMD: {<asf>}
                """

partial_rearrangements = r"""
                        PFVB-ITEM-PFVB: {<PFVB>+<(ACT|OBJ|LOC)>+<PFVB>+}
                        PVB-ITEM-PVB: {<PVB>+<(ACT|OBJ|LOC)>+<PVB>+}
                        PFVB-ITEM: {<PFVB>+<(ACT|OBJ|LOC)>+}
                        PVB-ITEM: {<PVB>+<(ACT|OBJ|LOC)>+}
                        POBJ-ADJ: {<POBJ><ADJ>+}
                        ADJ-POBJ: {<ADJ>+<POBJ>}
                        """


def exec_custom_func_from_cmd(label, tagged_cmd):
    item = [tagged_cmd]


def exec_func_from_cmd(label, tagged_cmd):
    """Parses the command into its function and arguments"""
    first_word = tagged_cmd[0][1]
    print('label matched:', label) if debug else None
    if first_word != 'DIR':
        index = 0 if first_word == 'FVB' else 3  # the else is for a USE-0BJ-TO-VB-ACT command
        method = tagged_cmd[index][0]  # get the [insert index here] element of the list of tuples, then get the first element of the tuple,
                                    # which is the verb, which is the function name
        tagged_cmd.pop(index)
    args = [arg[0] for arg in tagged_cmd]  # get the 0th value, which is the item -- an obj, dir, act, etc...

    if label == 'FVB-ALL-BUT-ACT/OBJ':
        return method, ('ALL-BUT:', *args[2:])

    elif label == 'FVB-ALL':
        return method, 'ALL'
    
    elif label == 'FVB-ITEM-AT/IN-ITEM':
        objects = args[:-2]
        at_or_in_item = args[-1]
        return method, (objects, at_or_in_item)

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

    elif label == 'DIR-NUM':
        return 'goto', ((args[0]),)*int(args[1])

    elif label == 'DIR':
        method = 'goto'
        return method, args


# make sure egg to take, make sure it fits with user allowed weight

partialParser = RegexpParser(partial_rearrangements)

chunkParser = RegexpParser(command_structures)  # create the parser with the grammar defined above


def get_labels_and_matches(tagged, typ='NORMAL'):
    """Processes a command and sends it to the appropriate function."""
    if typ == 'NORMAL':
        chunked = chunkParser.parse(tagged)  # get the chunks, the matches that fit with the grammar
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

# for label, match in zip(labels, matches):
#     print(f"\nlabel: {label}")
#     print(f"match: {match}\n")
#     if typ == 'partial':
#         rearrange(label, match, all_commands)
#     else:
#         exec_func_from_cmd(label, match)


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
