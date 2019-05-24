import re
import ruamel.yaml
from ruamel.yaml import error
import warnings
import pyaml  # just for pretty printing


def get_synonyms():
    """Gets the synonyms for game creator to add to data file."""
    from nltk.corpus import stopwords, wordnet
    words = input('enter words separated by comma: ').split(',')
    pos = input('enter part of speech of word group, ADJ, ADJ_SAT, ADV, NOUN, VERB = a, s, r, n, v: ')
    if pos == '':
        pos = None
    print('words:', words)
    matches = []

    for w in words:
        synonyms = []
        syns = wordnet.synsets(w.strip(), pos)
        print('full syns:', syns)
        for syn in syns:
            for l in syn.lemmas():
                synonyms.append(l.name())

        print(f'\nSynonyms of {w}:', *list(set(synonyms)), sep=', ')
        matches.append(set(synonyms))  # set removes the duplicate synonyms

    print('\n\nPRINTING ALL MATCHES IN LOOP')
    for match in matches:
        print('final match x:', *list(match), sep=', ')
    # print('final matches:', matches)

    final = set.intersection(*matches)
    print('final set:', *list(final), sep=', ')


def get_data(filename):
    """
    Takes data from .yaml file and parses into a dictionary.
    """

    with open(filename) as infile:
        dic = ruamel.yaml.safe_load(infile)
    return dic


main_filename = '/Users/Sam/Documents/Shalhevet/CompSci/CompSci Work/Capstone/Github/AdventureX/Data Models/'
loc_filename = main_filename + 'Location Data.yaml'
obj_filename = main_filename + 'Objects Data.yaml'
act_filename = main_filename + 'Actors Data.yaml'
cmd_filename = main_filename + 'Commands.yaml'
player_filename = main_filename + 'Player.yaml'
randoms_filename = main_filename + 'Random Dicts.yaml'

warnings.simplefilter("ignore", error.ReusedAnchorWarning)


if __name__ == '__main__':

    get_synonyms()
    exit()
    location_data = get_data(loc_filename)
    objects_data = get_data(obj_filename)

    pyaml.pprint(location_data, sort_dicts=False)
    pyaml.pprint(objects_data, sort_dicts=False)







# player = Player()
# print(player)
#
# location = Location(locations_data, player)
#location.narrate()


"""
objects=[x for x in data[6].split(',') if len(x) > 1],  # turns all items in data[6] into a list split by comma, only if word > 1 char
verbs=[x for x in data[7].split(',') if len(x) > 1],
negative_verbs=[x for x in data[8].split(',') if len(x) > 1],
actors=[x for x in data[9].split(',') if len(x) > 1])
#narrative=loc_nar[int(data[1])].strip('\n'),  # get index of readlines list from location number, remove newline char
                     
"""
