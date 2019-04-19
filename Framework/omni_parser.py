# from nltk import pos_tag
#
#
# def get_command(command):
#     """Checks the command for verbs, references to objects & locations."""
#
#
# def check_for_dir(word):
#     """Checks if the word is a signifier for a direction."""
#     directions = [
#         [('north', 'n'), 'N'],
#         [('east', 'e'), 'E'],
#         [('south', 's'), 'S'],
#         [('west', 'w'), 'W'],
#         [('northeast', 'ne'), ('N', 'E')],
#         [('southeast', 'se'), ('S', 'E')],
#         [('southwest', 'sw'), ('S', 'W')],
#         [('northwest', 'nw'), ('N', 'W')],
#         [('left', 'l'), 'L'],
#         [('right', 'r'), 'R'],
#         [('forward', 'f', 'fwd', 'fd'), 'F'],
#         [('backward', 'b', 'back', 'bk', 'bkwd'), 'B'],
#     ]
#
#     for direction in directions:
#         if word in direction[0]:
#             return direction[1]
#     return False
#
#
# def check_for_verb(word):
#     """Checks if the word is a verb."""
#     for dict in COMMANDS['all_commands']:  # looping over all the dicts of verbs + needs + action sets
#         if word in dict['verbs']:  # if the word is in the verbs list of current loop dict, now you have your verb
#             verb = dict['action'][0]
#             needs = [need.split('/') for need in dict['needs']]
#             return verb, needs
#     return False
#
#
# def check_requirements (word, needs):
#     """Get the official action word (verb).
#     Needs is a list with sublists of the needed things. Each of those sublists can contain
#     a single need or more than one, which means that there is an option. So, loop over the sublists in
#     needs, and for each option (keeping in mind that there is most likely only one option) in each sublist,
#     """
#     for need in needs:  # loops over needs list -- all needs
#         print('need:', need)
#         for need_option in need:  # loops over options within each need sublist
#             print('either:', need_option)
#             requirement = Omnipotent.check_for_item(word,
#                                                     need_option)  # checks if the word fits the requirement/need
#             if requirement:
#                 return requirement
#     return False
#
#
# def check_for_item (word, typ):
#     """Checks if word is reference to an object or a location."""
#     if typ == 'OBJ':
#         dictionary = OBJECTS  # global objects dictionary
#     elif typ == 'LOC':
#         dictionary = LOCATIONS  # global locations dictionary
#     elif typ == 'ACT':
#         dictionary = ACTORS
#
#     for item in dictionary.values():  # loop over dict.values() which gives you the actual python objects of objects/locations.
#         references = item.references
#         if word in references:
#             item_reference = references[
#                 0]  # the first item in object/location's references is always official name of object
#             if typ == 'OBJ':
#                 return item_reference
#             elif typ == 'ACT':
#                 return item_reference
#             elif typ == 'LOC':
#                 return item
#     # for references in [item.references for item in dictionary.values()]:
#     return False
#
#
# def dir_to_loc(direction):
#     """Translates a given direction to a location that the user goes to."""
#
#     def rdir_to_dir (rd):
#         """Converts relative direction (left, forward) to a direction
#         based on player's orientation.
#         How does it do it?
#
#         1. Create list of N,E,S,W and list of F,R,B,L (North....Forward....)
#         2. Rotate the list of N,E,S,W by the index value of where the player's orientation is in the list of N,E,S,W
#             So if the player is facing (orientation) West, then get the index value of 'W' in the list of N,E,S,W --
#             which is 3, and rotate the normal list of N,E,S,W backwards 3 units.
#         3. Set the return of the rotate function to a variable, and now the old list of N,E,S,W becomes the a new list
#             that looks like: W,N,E,S.
#         4. Now we finally deal with the argument passed in -- either L(eft), R(ight), F(orward), etc.
#             Get the index value of the relative direction argument within the relative directions list (F,R,B,L)
#                 Which means: If the argument is R (Left), then get the index value of R in the F,R,B,L list, which is 2.
#             Now use that index value to access the proper direction in the recently created directions list.
#             This works because the relative directions (L,R,F,B) list and the directions list (N,E,S,W) are parallel lists,
#             and so now that you rotated the directions list, you can get the proper direction using the same index with
#             both lists.
#         5. Return the proper direction.
#         """
#
#         def rotate (l, n):
#             """Rotates a list backwards by n units"""
#             return l[n:] + l[:n]
#
#         dirs = ['N', 'E', 'S', 'W']
#         rdirs = ['F', 'R', 'B', 'L']
#
#         print('\nnew direction')
#         print('playing moving:', rd)
#         print('index to rotate by:', dirs.index(player.orientation))
#         print('player facing:', player.orientation)
#         new_directions = rotate(dirs, dirs.index(player.orientation))
#         print('new relative directions:', new_directions)
#         print('final direction:', new_directions[rdirs.index(rd)])
#         return new_directions[rdirs.index(rd)]
#
#     if direction in ['L', 'R', 'F', 'B']:
#         direction = rdir_to_dir(direction)
#
#     new_loc = LOCATIONS[player.active_location].moves[direction]
#     if type(new_loc) is list:  # which means that it's a warning with ability to accept
#         print(new_loc[0])
#
#     elif len(new_loc) > 2:  # which means it's not a location num, but rather a message, a no-go
#         print(new_loc)
#     else:
#         return new_loc
#
# all_commands = []
#
# # active_object = ''  # if they say take lantern and throw IT
# structure = ''
# word_structure = ''
#
# # BELOW (COLLAPSED): old for word in command, if dir, if verb_result, etc...
# # for word in command:
#
# #     # ADD THAT IF THEY SAY ATTACK KEY AND THERE IS NO KEY, SAY THERE IS NO KEY
#
# #     if direction:
# #         # DEAL WITH THE DIR_TO_LOC FUNCTION
# #         direction = dir_to_loc(direction)
# #         for dir in direction:
# #             all_commands.append(['goto', dir])
# #
# #     elif verb_result:
# #
# #         verb, needs = verb_result
# #         verb_command = [verb]
# #         command.remove(word)
# #
# #         for inner_word in command:
# #             print('\n\ninner_word:', inner_word)
# #             meets_requirement = check_requirements(inner_word, needs)
# #             if meets_requirement:
# #                 print('requirement:', meets_requirement)
# #                 verb_command.append(meets_requirement)
# #                 command.remove(inner_word)  # if it meets the requirement, we add it to the verb command,
# #                 # but we don't want to accidentally use it again so we remove it
# #
# #         all_commands.append(verb_command)
# #
# #     elif location:
# #         all_commands.append(['goto', location])
# #     #
# #     # elif object:
# #     #     command.remove(word)
# #     #     for inner_word in command:
# #     #         verb_result = check_for_verb(inner_word)
# #     #         if verb_result:
# #     #             verb, needs = verb_result
# #     #             meets_requirement = check_requirements(object, needs)
# #     #             break  # once you find a verb, even if the object
# #     #             # use lantern to attack troll
# #
# # return all_commands
#
#
# def pos_tagger(command):
#     """Tags each of the words in the command and returns a list of tuples with appropriate tags."""
#     tagged = []
#     for word in command:
#         direction = check_for_dir(word)
#         verb_result = check_for_verb(word)
#         location = check_for_item(word, typ='location')
#         object = check_for_item(word, typ='object')
#         actor = check_for_item(word, typ='actor')
#         if direction:
#             tagged.append((word, 'DIR'))
#         elif verb_result:
#             tagged.append((word, 'VB'))
#         elif location:
#             tagged.append((word, 'LOC'))
#         elif object:
#             tagged.append((word, 'OBJ'))
#         elif actor:
#             tagged.append((word, 'ACT'))
#         elif pos_tag([word])[0][1] == 'IN':  # NLTK pos_tag, argument is list, index 0 is the tuple inside the list,
#             # index 1 is second item of tuple, which is the part of speech.
#             tagged.append((word, 'PRP'))
#
#     get_command(tagged)

from nltk import RegexpParser
# dirCMD = RegexpParser(r"Chunk: {<VB><DIR>}")
# simpleCMD = RegexpParser(r"Chunk: {<VB><OBJ>}")

tagged = [('take', 'VB'), ('egg', 'OBJ'), ('go', 'VB'), ('north', 'DIR'), ('attack', 'VB'), ('TROLL', 'ACT')]

chunker = r"""
			VB-OBJ: {<VB><OBJ>}
			VB-DIR: {<VB><DIR>}
			VB-ACT: {<VB><ACT>}
			"""
# make sure egg to take, make sure it fits with user allowed weight

chunkparser = RegexpParser(chunker)

chunked = chunkparser.parse(tagged)

print(chunked.draw())
#
# for chunk in chunked:
# 	print(chunk[0][0], '|', chunk[1][0])
