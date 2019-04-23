import setup
from errors import *
from nltk import pos_tag

# Add in documentation, that if you want to have a randomly chosen response, define your responses at the top of the document
# or maybe in another document, so for example create a dict with key 'boundary', and then u can just write 'boundary; wherever
# and the program will choose something random from the dictionary with that key.

# Make sure for go_to, that its not 'boundary', in that case, randomly choose a boundary response


def exceptions_handler(dictionary, typ):
    """Handles things in which general/exception sets are declared."""
    exceptions = dictionary['exceptions']
    # break out of the loop below if a condition passes
    for exception in exceptions:  # item is either name of object/actor/location, or 'player'
        conditions_passed = False
        for condition_set in exception[0]['if']:  # for every exception list in the 'if' key
            item = condition_set[0]  # e.g. player, lantern, troll, or 6a
            state = condition_set[1]  # e.g. 'lit' or 'guarding'
            condition = condition_set[2]  # e.g. True/False, 6a (location)
            print('{} state "{}" needs to be {} in order for this exception to fire'.format(item, state, condition))

            if item == 'player':
                item_state = getattr(player, state)
            else:
                for dictionary in [LOCATIONS, OBJECTS, ACTORS]:
                    if item in dictionary:
                        item_state = getattr(dictionary[item], state)
                        break

            print('{} state -- {} = {}'.format(item, state, item_state))
            if item_state == condition:
                conditions_passed = True
            else:
                conditions_passed = False  # if for example the second time around it doesn't pass the condition,
                # set it back to false

        if conditions_passed:
            if typ == 'state change' or 'command':
                return exception[1]['reaction']
            elif typ == 'narrative':
                return exception[1]['narrative']


class Omnipotent:
    """My class, where I figure everything out for the user and then spoon-feed it back to him."""

    @staticmethod
    def describe(something):
        """Describes an object or a location."""
        if something in LOCATIONS:
            print(OBJECTS[something].description)
        elif something in LOCATIONS:
            LOCATIONS[something].narrate(typ='long')
        else:
            print("I can't describe something that doesn't exist.")

    @staticmethod
    def get_command(command):
        """Checks the command for verbs, references to objects & locations."""

    @staticmethod
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

    @staticmethod
    def check_for_verb(word):
        """Checks if the word is a verb."""
        for dict in COMMANDS['general_commands']:  # looping over all the dicts of verbs + needs + action sets
            if word in dict['verbs']:  # if the word is in the verbs list of current loop dict, now you have your verb
                verb = dict['action'][0]
                # needs = [need.split('/') for need in dict['needs']]
                return verb #, needs
        return False

    @staticmethod
    def check_requirements(word, needs):
        """Get the official action word (verb).
        Needs is a list with sublists of the needed things. Each of those sublists can contain
        a single need or more than one, which means that there is an option. So, loop over the sublists in
        needs, and for each option (keeping in mind that there is most likely only one option) in each sublist,
        """
        for need in needs:  # loops over needs list -- all needs
            print('need:', need)
            for need_option in need:  # loops over options within each need sublist
                print('either:', need_option)
                requirement = Omnipotent.check_for_item(word, need_option)  # checks if the word fits the requirement/need
                if requirement:
                    return requirement
        return False

    @staticmethod
    def check_for_item(word, typ):
        """Checks if word is reference to an object or a location."""
        if typ == 'OBJ':
            dictionary = OBJECTS  # global objects dictionary
        elif typ == 'LOC':
            dictionary = LOCATIONS  # global locations dictionary
        elif typ == 'ACT':
            dictionary = ACTORS

        for item in dictionary.values():  # loop over dict.values() which gives you the actual python objects of objects/locations.
            references = item.references
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

    @staticmethod
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

    all_commands = []

    # active_object = ''  # if they say take lantern and throw IT
    structure = ''
    word_structure = ''

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

    @staticmethod
    def pos_tagger(command):
        """Tags each of the words in the command and returns a list of tuples with appropriate tags."""
        tagged = []
        for word in command:
            direction = Omnipotent.check_for_dir(word)
            verb = Omnipotent.check_for_verb(word)
            location = Omnipotent.check_for_item(word, typ='LOC')
            object = Omnipotent.check_for_item(word, typ='OBJ')
            actor = Omnipotent.check_for_item(word, typ='ACT')
            if direction:
                tagged.append((word, 'DIR'))
            elif verb:
                tagged.append((word, 'VB'))
            elif location:
                tagged.append((word, 'LOC'))
            elif object:
                tagged.append((word, 'OBJ'))
            elif actor:
                tagged.append((word, 'ACT'))
            elif pos_tag([word])[0][1] == 'IN':  # NLTK pos_tag, argument is list, index 0 is the tuple inside the list,
                # index 1 is second item of tuple, which is the part of speech.
                tagged.append((word, 'PRP'))
            elif word == 'and':
                tagged.append((word, 'AND'))
        return tagged
        # Omnipotent.get_command(tagged)


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
        self.damage = obj_dict['damage']
        self.location = obj_dict['active_location']
        try:
            self.weight = obj_dict['weight']
        except KeyError:
            pass


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
            self.__setattr__(state, value)  # set custom object attributes based on the given states
        self.sc_reactions = obj_dict['reactions']['state_changes']
        try:
            self.cmd_reactions = obj_dict['reactions']['commands']
        except KeyError:
            pass

    def change_state(self, state):
        """Changes active state of object based on user's command or other circumstance."""
        self.states[state] = not self.states[state]  # if state is True, then change it to False, and vice versa.
        # if player.active_location not in self.info.get('exceptions'):
        #     print(self.sc_reactions[new_state])
        # else:
        #     print(self.sc_reactions['exceptions']
        #           [player.active_location][new_state])

    def print_test(self):
        print('test passed')

    def react(self, typ, state_or_cmd, boolean=None):
        """React to a state change or command
        :param state_or_cmd: The object's state that is being changed or the command that is being invoked
        :param boolean: The boolean value that the state is being change to. Only passed in for a state change reaction.
        :param typ: Either 'state change' or 'command'
        """
        if typ == 'state change':
            dictionary = self.sc_reactions
            has_exceptions = True if dictionary[state_or_cmd].get('general') else False
        elif typ == 'command':
            dictionary = self.cmd_reactions
            has_exceptions = True if type(dictionary[state_or_cmd]) is dict else False

        if has_exceptions:
            reaction = exceptions_handler(dictionary[state_or_cmd], typ=typ)
            general = dictionary[state_or_cmd]['general']
            if typ == 'state change':
                general = general[boolean]
            if not reaction:
                print(general)
            else:
                if typ == 'state change':
                    if not reaction.get(boolean):
                        print(general)
                    else:
                        print(reaction[boolean])
                else:
                    print(reaction)
        else:
            if typ == 'state change':
                print(dictionary[state_or_cmd][boolean])  # there will always be both a True and False reaction, so
                # [boolean] won't fail / raise an exception
            else:
                print(dictionary[state_or_cmd])


class Actor(ComplexObject):
    """Higher level of complexity than a complex object."""

    def __init__(self, actor_dict, name):
        ComplexObject.__init__(self, actor_dict, name)
        self.health = actor_dict['health']


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
        self.conditions = loc_info.get('conditions', None)
        self.objects = loc_info.get('objects', [])
        self.references = loc_info.get('references', [])

        self.attributes = []

    def narrate(self, typ=None):
        """Does a few checks and then prints the appropriate narrative."""
        def check_narrative(nars):
            """Returns appropriate narrative."""
            if type(nars) is not dict:
                return nars
            else:
                return exceptions_handler(nars, typ='narrative')

        if self.visited == 0 or typ == 'long':
            print('\nprinting long in location', self.num)
            printable = check_narrative(self.narratives['long'])
            print(printable)

        else:
            print('\nprinting short in location', self.num)
            printable = check_narrative(self.narratives.get('short'))
            if printable is None:  # if the dict doesn't have a short nar, .get() returns None, which
                # is subsequently passed to check_narrative, which in turn returns the None value.
                printable = check_narrative(self.narratives.get('long'))
            print(printable)

# subclasses dif behaviors for dif locations
# subclasses for objects fixed or not
# forward back left right for user's orientation, and n s e w fixed


class Player:
    """Player object containing all relevant info."""
    def __init__(self, active_location='0', inventory=None, orientation='N',
                 health=100, attributes=None):
        """
        Need to set active_location and inventory as parameters (instead of simply adding them as attributes) in order to allow progress saving.
        When I start up a game again, I will re-create the Player object with their saved active location.
        """
        self.active_location = active_location
        self.inventory = inventory if inventory else []  # keeps list inputted as the parameter, if no inventory given, change inventory to empty list
        self.orientation = orientation
        self.health = health
        self.attributes = attributes if attributes else []
        # for thing in self.attributes:
        #     print(1)
        #     # pass in players location, get the narrative dict for location, search in the narrative dict for thing, and if found,
        #     # print narratives[thing]

    def take(self, reference):
        """To be called when user says to take an object."""
        reference = Omnipotent.check_for_item(reference, typ='object')  # Get official name of object
        if reference in self.inventory:
            raise TakeObjectError #print("You're already carrying the {}.".format(reference))
        else:
            location = LOCATIONS[self.active_location]
            if reference in location.objects:
                self.inventory.append(reference)
                location.objects.remove(reference)
                print("The {} has been added to your inventory.".format(reference))
            else:
                print("There is no {} here.".format(reference))

    def drop(self, reference):
        """To be called when user says to drop an object."""
        reference = Omnipotent.check_for_item(reference, typ='object')  # Get official name of object
        if reference not in self.inventory:
            raise DropObjectError  # print("You're not carrying a(n) {}.".format(reference))
        else:
            self.inventory.remove(reference)
            location = LOCATIONS[self.active_location]
            location.objects.append(reference)

    def goto(self, *locations):
	    if len(locations) > 1:
		    for new_location in locations:
		        print('Going to:', new_location)
		        self.active_location = new_location
		        LOCATIONS[new_location].narrate()
		        LOCATIONS[new_location].visited += 1

    def attack(self, actor, with_object):
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

    def activate_func(self, func, *args):
        getattr(self, func)(args)

    def __str__(self):
        return ('I am a player in this game. I am currently in location ' + self.active_location[-1]
                + ' and I am holding ' + str(self.inventory))


def actualize_data(typ, filename):
    """For each location/object in location/object dictionary,
    create python objects."""
    data = setup.get_data(filename)

    if typ == 'COMMANDS':
        return data['COMMANDS']
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
            ACTORS[title] = Actor(sub_dict, title)
        elif typ == 'LOCATIONS':
            LOCATIONS[title] = Location(sub_dict, title) # passes in the loc/obj dict & loc/obj number/name


LOCATIONS = {}
OBJECTS = {}
ACTORS = {}
COMMANDS = actualize_data('COMMANDS', setup.cmd_filename)
actualize_data('LOCATIONS', setup.loc_filename)
actualize_data('OBJECTS', setup.obj_filename)
actualize_data('ACTORS', setup.obj_filename)


def test_state_changes():

    print('---NEW---')
    print('changing lantern lit to True')
    OBJECTS['lantern'].react('state change', 'lit', False)
    
    print('\n---NEW---')
    print('changing lantern lit to False')
    OBJECTS['lantern'].react('state change', 'lit', False)
    
    player.active_location = '6a'
    print('changed player location to 6a')
    
    print('\n---NEW---')
    print('changing lantern lit to False')
    OBJECTS['lantern'].react('state change', 'lit', False)
    print('\n---NEW---')
    print('changing lantern lit to True')
    OBJECTS['lantern'].react('state change', 'lit', True)
    print('\n---NEW---')
    player.active_location = '4a'
    exceptions_handler(LOCATIONS['4a'].narratives['long'], 'narrative')

    print('\n---NEW---')
    print('reacting to take command')
    OBJECTS['lantern'].react('command', 'take')

    print('\n---NEW---')
    print('reacting to throw command')
    OBJECTS['lantern'].react('command', 'throw')

    player.active_location = '5'
    print('\n---NEW---')
    print('reacting to throw command')
    OBJECTS['lantern'].react('command', 'throw')


def gameplay():
    """The gameplay function that will keep the game running till exit."""
    while True:
        player_input = input('input command: ').split()
        commands = Omnipotent.pos_tagger(player_input)
        print('tagged:', commands)


if __name__ == '__main__':

    player = Player()
    test_state_changes()
    player.activate_func('take')
    gameplay()
    # player.inventory.append('egg')
    try:
        player.drop('egg')
    except TakeObjectError:
        print('already holding object')
    except DropObjectError:
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
#     Omnipotent.check_command(word, command)

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
