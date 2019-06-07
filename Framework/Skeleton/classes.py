from Skeleton import setup
from Skeleton.errors import *
import random
import Colors
from Parser import omni_parser
import pickle
import logging
import time
import sys
logging.basicConfig(filename='adventureX.log', level=logging.DEBUG)


class GameHandler:
    """Handles game functions including saving/loading states and quitting.
    As of now, I separated save_state() and load_state() into separate functions because they have different functionality
    from a simple save/load."""

    @staticmethod
    def save_state(number):
        """Saves the current state of the game for undo capabilities."""
        data = (player, LOCATIONS, OBJECTS, ACTORS, COMMANDS, RANDOMS)
        with open('intermediate_data.pickle', 'rb') as file:
            dictionary = pickle.load(file)
        dictionary[number] = data
        with open('intermediate_data.pickle', 'wb') as file:
            pickle.dump(dictionary, file)

    @staticmethod
    def load_state(number):
        """Loads saved state of game for redo capabilities."""
        global player, LOCATIONS, OBJECTS, ACTORS, COMMANDS, RANDOMS
        print('Loading saved game...')
        with open('intermediate_data.pickle', 'rb') as file:
            dictionary = pickle.load(file)
        data = dictionary[number]
        player, LOCATIONS, OBJECTS, ACTORS, COMMANDS, RANDOMS = data

    @staticmethod
    def save():
        """Saves state of game."""
        print('Saving game...')
        with open('game_save.pickle', 'wb') as file:
            data = (player, LOCATIONS, OBJECTS, ACTORS, COMMANDS, RANDOMS)
            pickle.dump(data, file)

    @staticmethod
    def load():
        """Loads a saved state of the game."""
        global player, LOCATIONS, OBJECTS, ACTORS, COMMANDS, RANDOMS
        print('Loading saved game...')
        with open('game_save.pickle', 'rb') as file:
            data = pickle.load(file)
        player, LOCATIONS, OBJECTS, ACTORS, COMMANDS, RANDOMS = data
        # print(player)

    @staticmethod
    def quit():
        """Quits."""
        print('Ending game...')
        raise SystemExit


def type_write(words):
    for char in words:
        sys.stdout.write(char)
        sys.stdout.flush()
        if not testing:
            time.sleep(0.01)


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
                response = random_response('okays')
                print(response)
                logging.info(response)
                return

        has_exceptions = False
        print_general = True

        # have to check this below if statement before the next if statement block (if type(reaction_info) is dict) because
        # if there is a subdict, I have to set the reaction info to that first before checking for general/exception keys
        if reaction_subdict is not None:  # if they passed in a value for reaction_subdict...
            print('there is a reaction subdict, which is:', reaction_subdict) if debug else None
            print('the reaction info is:', reaction_info) if debug else None
            if type(reaction_info) is dict:  # if reaction_info is a str, so just a plain string reaction,
                    # then there is no attribute .get() so can't perform if-statement below
                # if ALL the above conditions combined evaluated to False, if not False, then do stuff below:
                if not reaction_info.get(reaction_subdict):  # ...but there is no reaction_subdict key
                    # raise YamlFormatError(f"YamlFormatError: There is no {reaction_subdict} key in the passed-in reaction info, which is: {reaction_info}")
                    logging.critical(f"YamlFormatError: There is no {reaction_subdict} key in the passed-in reaction info, which is: {reaction_info}")
                else:
                    print('reaction_info[reaction_subdict] is:', reaction_info[reaction_subdict]) if debug else None
                    reaction_info = reaction_info[reaction_subdict]

        if type(reaction_info) is dict:
            if reaction_info.get('exceptions'):  # if there is an exceptions key...
                if reaction_info.get('general'):
                    has_exceptions = True  # only time I set has_exceptions to True, if there are both keys
                else:  # ...but no general key...
                    # raise YamlFormatError('There is an exceptions key without a general key')
                    logging.critical('YamlFormatError: There is an exceptions key without a general key')
            elif reaction_info.get('general'):  # if there is not an exceptions key but there is a general key...
                # raise YamlFormatError('There is a general key without an exceptions key')
                logging.critical('YamlFormatError: There is a general key without an exceptions key')

        if has_exceptions:
            print('This reaction has exceptions') if debug else None
            exceptions = reaction_info['exceptions']
            reaction, actions = exceptions_handler(exceptions, typ)
            # add if there is a general without actions, then it would just be a string, so print(general),
            # but if the general is a dictionary, that means there are actions attached.
            if reaction is not None:
                print('exceptions passed, printing reaction') if debug else None

                type_write(reaction)
                logging.info(reaction)
                print_general = False

        if print_general:
            if type(reaction_info) is str or reaction_info.get('reaction') or reaction_info.get('narrative'):
                general = reaction_info
            elif reaction_info.get('general'):  # if the exceptions failed above and now it's just printing the
                # reaction within the general key
                general = reaction_info['general']
            else:
                raise YamlFormatError(f"The reaction within: {reaction_info}\nis not in a string or a 'reactions' key.")
            reaction, actions = general_handler(general, typ)
            type_write(reaction)
            logging.info(reaction)

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
        self.fixed = obj_dict.get('fixed', False)
        self.location = obj_dict['active_location']

        self.action_requirements = obj_dict.get('action_requirements', [])
        self.sc_requirements = obj_dict.get('state_change_requirements', [])
        self.weight = obj_dict.get('weight')  # actors have no weight so exception may be raised
        # print('{} object reactions: {}'.format(self.name, obj_dict['reactions']))
        self.cmd_reactions = obj_dict['reactions'].get('commands', {})  # object might not have specific commands
        self.kwargs = {}
        if self.cmd_reactions is not None:
            self.kwargs['cmd_reactions'] = self.cmd_reactions
        self.reactor = Reactor(**self.kwargs)

    def __str__(self):
        return f"{self.__class__.__name__}({self.name}), loc:{self.location}, weight:{self.weight}, damage:{self.damage}"


class Container(Object):
    """Containers can hold objects inside them. Only one added attribute: inventory"""
    def __init__(self, obj_dict, obj_name):
        Object.__init__(self, obj_dict, obj_name)
        self.inventory = obj_dict['inventory']
        self.carrying_capacity = obj_dict['carrying_capacity']
        self.locked = obj_dict.get('locked', False)


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

        format = (self.name, state, getattr(self, state), value)
        print("\nChanging {}'s state of {} from {} to {}".format(*format))  # unpack format
        approved, fail_msg = verify_actionability('sc', self.name, state, value)  # ('sc', self.name, value, )  # sc for state change
        if not approved:
            print(fail_msg)
            logging.error(fail_msg)
        else:
            if self.name not in player.inventory:
                raise Exception([TakeError(f"You can't do that because you're not carrying the {self.name}.")])  # must be in this
                # format for the try/except block in gameplay() to work.
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

    def accept(self, object):
        """
        :param object:
        """
        found_obj = False
        for obj in self.receive_reactions:
            if obj == object:
                found_obj = True
                self.reactor.react('receipt', object)

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

        self.num = num
        self.name = loc_info['name']
        self.references = loc_info.get('references', [])
        self.visited = loc_info.get('visited', 0)
        self.narratives = loc_info['NARRATIVES']
        self.moves = loc_info['MOVES']
        self.enter_requirements = loc_info.get('enter_requirements')
        self.action_requirements = loc_info.get('action_requirements')
        self.play_objects = loc_info.get('play_objects', True)

        # self.children = loc_info.get('CHILDREN', None)
        self.objects = loc_info.get('OBJECTS', [])
        self.actors = loc_info.get('ACTORS', [])

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
        def play_objects_here():
            if self.objects:
                descriptions = [OBJECTS[obj].short_description for obj in self.objects]  # get the descriptions for all
                # the objects in location
                objects = turn_to_sentence(descriptions, 'There is ', 'and', typ='objects here')
                print(objects+' here.')
                logging.info(objects + '.')
                containers = [OBJECTS[container] for container in self.objects if isinstance(OBJECTS[container], Container)]
                for container in containers:
                    descriptions = [OBJECTS[obj].short_description for obj in container.inventory]
                    objects = turn_to_sentence(descriptions, f'\tInside the {container.name} is ', 'and', typ='objects here')
                    print(objects+'.')
                    logging.info(objects+'.')

        if self.visited == 0 or typ == 'long':
            self.reactor.react('narrative', 'long', location=self.num)
            if self.play_objects:
                play_objects_here()
        else:
            self.reactor.react('narrative', 'short', location=self.num)
            play_objects_here()

        self.visited += 1

    def remove_object(self, object):
        """Removes an object from the location's objects list."""
        try:
            print('objects before:', self.objects)
            self.objects.remove(object)
            print('objects after:', self.objects)
        except ValueError:  # if th object is not in location's object list, .remove() will raise a ValueError
            print(f"Location doesn't contain a(n) {object} to remove.")


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
        self.carrying_capacity = player_info['carrying_capacity']
        self.recent_object = ''
        self.places_traveled = [self.active_location]
        self.prev_location = self.places_traveled[-1]
        self.object_capacity = player_info['object_capacity']
        self.states = player_info['states']
        for state in self.states:
            value = self.states[state]
            setattr(self, state, value)  # set custom object attributes based on the given states
        self.reactions = player_info['reactions']
        self.sc_reactions = self.reactions['state_changes']
        # self.num_sc_reactions = self.reactions['numerical_state_changes']
        self.kwargs = {}
        self.kwargs['sc_reactions'] = self.reactions['state_changes']
        # if self.cmd_reactions is not None:
        #     self.kwargs['cmd_reactions'] = self.cmd_reactions
        self.reactor = Reactor(**self.kwargs)

    def change_state(self, state, value):
        """Changes active state of object based on user's command or other circumstance."""
        format = (state, getattr(self, state), value)
        print("Changing player's state of {} from {} to {}".format(*format)) if debug else None # unpack format
        setattr(self, state, value)
        self.reactor.react('state change', state, value)
        if state == 'health' and value == 0:
            print('GAME OVER')
            raise SystemExit

    def describe(self, *things):
        """Describes a location or object."""
        errors = []
        for what in things:
            if what == 'health':
                if player.health == 100:
                    print('You are at full health.')
                else:
                    print('Your health is:', player.health)
            elif what == player.active_location:
                LOCATIONS[what].narrate('long')
            elif what in OBJECTS:
                if what not in player.inventory:
                    if what in LOCATIONS[player.active_location].objects:
                        print(f"You aren't holding the {what}, but from what you can see it is {OBJECTS[what].short_description}")
                    else:
                        print(f"There is no {what} here.")
                else:
                    print(OBJECTS[what].description)
            elif what == 'inventory':
                if len(self.inventory) > 0:
                    descriptions = [OBJECTS[obj].short_description for obj in self.inventory]
                    objects = turn_to_sentence(descriptions, 'There is ', 'and', typ='objects here')
                    print(objects + ' here.')
                    containers = [OBJECTS[container] for container in self.inventory if isinstance(OBJECTS[container], Container)]
                    for container in containers:
                        descriptions = [OBJECTS[obj].short_description for obj in container.inventory]
                        objects = turn_to_sentence(descriptions, f'\tInside the {container.name} is ', 'and',
                                                   typ='objects here')
                        print(objects + '.')
                else:
                    print("You are not holding anything.")

    def take(self, *references, label=None):
        """To be called when user says to take an object."""
        errors = []

        print(f"things passed into take: label: {label}, references: {references}") if debug else None

        def some(iterable):
            """Similar to python builtins all() and any(), but this function checks if more than
            one element in iterable is True."""
            truthy_counter = 0
            for element in iterable:
                if element:
                    truthy_counter += 1
                if truthy_counter == 2:
                    return True
            return False

        holding_weight = sum([OBJECTS[obj].weight for obj in player.inventory])  # the weight the player is holding
        items_in_locked_container = 0  # this is set for output message formatting, if player tries to take objects in
        # a locked container, look below to see its usage.
        print(f'player is holding {holding_weight} lbs.') if debug else None

        # check if player explicitly asked to take from a container
        if any(x in label for x in ('IN-CONT', 'FROM-CONT')):
            container_name = references[-1]
            container = OBJECTS[container_name]
            specified_container = True
            objects = references[:-1]
        else:  # if they are not taking from a container
            container = False
            specified_container = False
            container_name = 'from_nothing'  # constant in YAML, cannot change
            objects = references

        if container and container_name not in LOCATIONS[player.active_location].objects:
            raise Exception([TakeError(f"There is no {container_name} here.")])

        for reference in objects:
            # check if it's in an open or locked container
            player.recent_object = reference
            obj_weight = OBJECTS[reference].weight  # weight of current object

            in_locked_container = obj_in_container(reference, 'locked')
            in_open_container = obj_in_container(reference, 'open')
            for status in (in_locked_container, in_open_container):
                if status:  # if one of the above are true
                    if not specified_container:  # if player did not explicitly ask to take from container, but object IS inside container
                        if status is in_open_container:
                            print(f'The {reference} is inside the {status}.')
                        # else:
                        #     print('you don;t know whats inside the {
                    container = OBJECTS[status]  # container is OBJECTS[name of container]
                    container_name = status

            # verify action can be done
            if container or in_locked_container or in_open_container:  # if the objects are being taken from a container,
                # whether specified by player or not, then need to check if the player can take_from the container, and
                # THEN if they can take that specific object.
                approved, fail_msg = verify_actionability('action', container_name, 'take_from')
                if approved:  # if they are allowed to take from the container, then check if they can take that object
                    approved, fail_msg = verify_actionability('action', reference, 'take')
                else:  # if taking from the container itself is not allowed...
                    print(fail_msg)  # ...then print fail message and raise Exception right away
                    raise Exception([error(message) for error, message in errors])
            else:  # if they're not being taken from container....
                approved, fail_msg = verify_actionability('action', reference, 'take')  # ...then just check if they can
                # take the object
            if not approved:
                print(fail_msg)
                logging.error(fail_msg)

            # the two below elif statements have ability for custom messages in verify_actionability(), so if the conditions
            # in verification fail, it would play that fail message instead of the default ones below.
            # check if it's inside a locked container. If there is a custom message for taking the object from a locked
            # container, it would have evaluated that right above when it called verify_actionability(). This below if-statement
            # is here just in case there is no custom message.
            elif in_locked_container:
                print('in locked container container is:' + str(container))
                print('items_in_locked_container are:' + str(items_in_locked_container))
                if container:
                    if items_in_locked_container == 0:
                        error_message = f"As of now, the {in_locked_container} is unable to be opened."
                        errors.append((TakeError, error_message))
                else:
                    if items_in_locked_container == 1:  # if there was already an object found to be inside the locked
                        # container. If checking for 3 objects, this would fail, as items_in_locked_container would == 2,
                        # and no error would even be added to errors list because only need to change it if one or more,
                        # -- sorry, THEY are inside the container....
                        index_of_first_msg = [index for index, (err, msg) in enumerate(errors) if 'is inside the' in msg][0]  # get the
                        # index of where the first in locked container message is in within errors list. List comp says give me
                        # the index for the index and tuple returned by enumerate(errors) ONLY IF 'is inside the' is in the message
                        # because 'is inside the' is unique to the single object in locked container error message, as you can
                        # see below. [0] at the end just gives the value within the list comp. s
                        error_message = f"Sorry, they are inside the {in_locked_container}, which as of now is unable to" \
                                        f"be opened. If you find a way to open it, then you can take them."
                        errors[index_of_first_msg] = (TakeError, error_message)  # replace the old single obj in locked container
                        # error/message pair with the new one.

                    elif items_in_locked_container == 0:
                        error_message = f"The {reference} is inside the {in_locked_container}, which as of now is unable to" \
                                        f"be opened. If you find a way to open it, then you can take the {reference}."
                        errors.append((TakeError, error_message))
                items_in_locked_container += 1

            # check if object is able to be moved
            elif OBJECTS[reference].fixed:
                error_message = f"You can't take the {reference}, it is stuck to the ground."
                errors.append((TakeError, error_message))

            # all below elif statements don't have possibilities for custom messages

            # check if it's already in the player's inventory
            elif reference in self.inventory:
                error_message = f"You're already carrying the {reference}."
                errors.append((AlreadyHoldingError, error_message))

            # check if player has already reached his item hold capacity.
            elif len(self.inventory) == self.object_capacity:
                error_message = f"You can only hold {self.object_capacity} items in your hands without something to put" \
                                f" them in."
                errors.append((TakeError, error_message))

            # check if taking object would increase player's holding weight by an amount greater than he/she can hold.
            elif obj_weight + holding_weight > self.carrying_capacity:

                difference = (obj_weight + holding_weight) - self.carrying_capacity
                first = f"You can only hold {self.carrying_capacity} lbs"
                if len(self.inventory) > 0:  # if the player is actually holding something then add this message in
                    sum_of_weight = f", and you are currently carrying {holding_weight} lbs. "
                else:
                    sum_of_weight = '. '

                s = 's' if difference > 1 else ''
                last = f"Taking the {reference}, which weighs {obj_weight} lbs, would cause you to go {difference} lb{s} " \
                    f"above your carrying capacity."
                error_message = first + sum_of_weight + last
                errors.append((TakeError, error_message))

            # check if player asked to take something from a container and the thing is not in the container
            elif container and reference not in container.inventory:  # meaning the user entered a 'take from x' command
                # can't take something from something if the something is not in the something
                error_message = f"The {reference} is not in the {container_name}."
                errors.append((TakeError, error_message))

            else:
                location = LOCATIONS[self.active_location]
                obj_is_here = True if reference in location.objects or in_open_container else False
                print(f"{reference} is in open container: {in_open_container}") if debug else None
                if obj_is_here:
                    self.inventory.append(reference)  # add object to player's inventory
                    if reference in location.objects:
                        location.objects.remove(reference)  # remove object from location
                    elif container:
                        container.inventory.remove(reference)
                    OBJECTS[reference].reactor.react('command', 'take', reaction_subdict=container_name)
                else:
                    error_message = f"There is no {reference} here."
                    errors.append((TakeError, error_message))

        # create an Exception object with all the errors in the raising_error list
        # the list comp says give me the error and pass in the custom message for every error and message in the list of
        # all errors collected during runtime.
        raise Exception([error(message) for error, message in errors])

    def drop(self, *references, actor_from_throw=None):  # actor is just for when the throw() command calls drop()
        """To be called when user says to drop an object."""
        errors = []
        for reference in references:
            approved, fail_msg = verify_actionability('action', reference, 'throw', actor_from_throw)  # if actor is None the function
            # will not look at it.
            if not approved:
                print(fail_msg)
                logging.error(fail_msg)

            elif reference not in self.inventory:
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

    def throw(self, *references, label=None):
        """Throw an object -- either a simple throw at nothing or a throw at an actor."""
        errors = []
        if label == 'FVB-ACT/OBJ-WITH-OBJ':
            errors.append((ThrowError, "You can't throw something with something else, sorry."))

        actor = references[-1]
        # objects = references[:-1]
        if actor not in ACTORS:
            objects = references
            actor = 'at_nothing'
        else:
            objects = references[:-1]
        self.drop(*objects, actor_from_throw=actor)

    def place(self, *references, label=None):
        """Place an object into a container."""
        errors = []

        container_name = references[-1]
        container = OBJECTS[container_name]
        objects = references[:-1]
        if not isinstance(container, Container):
            error_message = f"You can't put anything inside the {container_name}."
            errors.append((PlaceError, error_message))
        else:
            for reference in objects:
                approved, fail_msg = verify_actionability('action', reference, 'place', sub_dict=container_name)
                if not approved:
                    print(fail_msg)
                    logging.error(fail_msg)
                else:
                    if container.locked:  # this has to be before the other ones. Think about it
                        error_message = f"You can't put things in the {container_name} because as of now, it is unable to be opened."
                        errors.append((PlaceError, error_message))
                    elif reference in container.inventory:
                        error_message = f"The {reference} is already in the {container_name}."
                        errors.append((PlaceError, error_message))

                    elif reference not in self.inventory:
                        article = 'an' if reference[0] in 'aeiou' else 'a'
                        error_message = f"You're not carrying {article} {reference}."
                        errors.append((NotHoldingError, error_message))
                    else:
                        self.inventory.remove(reference)
                        container.inventory.append(reference)
                        LOCATIONS[self.active_location].objects.append(reference)  # add the object to the location's
                        # objects list
                        OBJECTS[reference].reactor.react('command', 'place', reaction_subdict=container_name)

        raise Exception([error(message) for error, message in errors])

    def give(self, actor, reference):
        """

        :param actor:
        :param reference:
        """
        self.inventory.remove(reference)
        ACTORS[actor].accept(reference)

    def goto(self, *locations, label=None, long_or_short=None):
        """Takes player to a location.
        """

        def play_random_message(random_dict):
            """Plays a random message from the random dictionary."""
            print('dict name passed into play rand msg:', random_dict) if debug else None
            messages = RANDOMS[random_dict]
            choice = random.choice(messages)
            print(choice)
        print('goto was called') if debug else None
        errors = []
        starting_location = self.active_location
        went_to_already = []
        print('locs passed in:', locations) if debug else None
        for i in range(len(locations)):
            if locations[i] in LOCATIONS:
                new_location = locations[i]
                approved, fail_msg = verify_actionability('enter', new_location, action_or_state=None)
                if not approved:
                    print(fail_msg)
                else:
                    self.active_location = new_location
                    LOCATIONS[new_location].narrate(long_or_short)
                return

            if type(locations[i]) is tuple:
                self.goto(*locations[i], label=label)
                return

            if label and 'LOC' in label:
                new_location = locations[i]
                self.active_location = new_location
                if starting_location == new_location:
                    error_message = "You just went in circles. You're back at the same place." \
                        if len(locations) > 1 else "You're here already."
                    errors.append((GoToError, error_message))
                else:
                    self.places_traveled.append(new_location)
                    LOCATIONS[new_location].narrate(long_or_short)
            else:
                going_to = True
                print('loc in loc loop:', locations[i]) if debug else None
                new_location = dir_to_loc(locations[i])  # turns a direction into a location number
                if str(new_location) not in LOCATIONS:
                    if type(new_location) is dict and 'warning' in new_location:  # if it's a warning dict
                        if len(locations) > 1:
                            print(f"You went {' '.join(went_to_already)}. Now you are going {locations[i]}, but in order "
                                  f"for you to go there, you must first respond to the following warning:")
                        boolean, loc_or_reaction = ask_until_respond(new_location)
                        if boolean:
                            new_location = loc_or_reaction
                        else:
                            going_to = False
                            print(loc_or_reaction)
                            if len(locations) > 1:  # if there are multiple go-to locations passed in, then tell them
                                # that the rest of their directions will not be executed.
                                if went_to_already:  # if there is at least one already-went-to location in the list
                                    print(f"You went {' '.join(went_to_already)}. The rest of your direction commands will not be executed. ")
                                else:
                                    print("The rest of your direction commands will not be executed.")
                            return
                    elif new_location in RANDOMS:
                        play_random_message(new_location)
                        if len(locations) > 1:
                            you_went = f"You went {' '.join(went_to_already)}. " if went_to_already else ''
                            # if there is at least one already-went-to location in the list, then you_went is set to the
                            # string telling user which directions they went in. If not, then you_went is set to empty string
                            print(you_went + "The rest of your direction commands will not be executed.")
                        return

                    approved, fail_msg = verify_actionability('enter', new_location, action_or_state=None)
                    if not approved:
                        print(fail_msg)
                        if len(locations) > 1 or len(locations[i]) > 1:
                            you_went = f"You went {' '.join(went_to_already)}. " if went_to_already else ''
                            # if there is at least one already-went-to location in the list, then you_went is set to the
                            # string telling user which directions they went in. If not, then you_went is set to empty string
                            print(you_went + "The rest of your direction commands will not be executed.")
                        return

                went_to_already.append(locations[i])  # this is after everything to make sure that it's only added to the places
                # player went within a multiple-location command AFTER it was confirmed that they are able to go there.
                self.active_location = new_location  # same reasoning goes for setting active_location to the new_location
                print(f"type(locations[i])): {type(locations[i])}") if debug else None
                print(f'index of {locations[i]} in {locations[i]}:', locations[i].index(locations[i])) if debug else None
                print(f"len(locations[i])-1: {len(locations[i])-1}") if debug else None
                if type(locations[i]) is not tuple or locations[i].index(locations[i]) == len(locations[i])-1:  # if it's a tuple,
                    # that means they entered 'northeast' or something, so I'm not going to both north and east to the
                    # locations they traveled because they cut straight to northeast. But even if it is a tuple, if it's
                    # the last item in the tuple, then I add it to places_traveled.
                    self.places_traveled.append(new_location)
                    print('places travleed after appending:', self.places_traveled) if debug else None
                if going_to:
                    self.prev_location = self.places_traveled[-2]
                    print('players previous location is:', self.prev_location) if debug else None
                    print(f"player active location: {self.active_location}, and the new location: {new_location}") if debug else None
                    print(f"starting location is: {starting_location}\n") if debug else None
                    if starting_location == new_location:
                        error_message = "You just went in circles. You're back at the same place." \
                                        if len(locations) > 1 else "You're here already."
                        errors.append((GoToError, error_message))
                    else:
                        if i == len(locations) - 1:
                            LOCATIONS[new_location].narrate(long_or_short)

        raise Exception([error(message) for error, message in errors])

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
    def turn(self, *directions):
        """Turn in a given direction"""
        dir_maps = {
            'N': 'north',
            'E': 'east',
            'S': 'south',
            'W': 'west',
        }
        rdir_maps = {
            'R': 'to the right',
            'L': 'to the left',
            'B': 'backwards',
        }

        starting_orientation = self.orientation
        for direction in directions:
            print('direction passed into turn:', direction) if debug else None
            if direction == 'F':
                print('There is no point in turning forward. If you want to make a 180, ask to turn backward.')
            elif direction in dir_maps.keys():
                if starting_orientation == direction:
                    print("You're already facing that way.")
                else:
                    print(f"You turn towards the {dir_maps[direction]}.")
                    self.orientation = direction
            else:
                new_orientation = rdir_to_dir(direction)
                if starting_orientation == new_orientation:
                    print("You're already facing that way.")
                else:
                    self.orientation = new_orientation
                    print(f'You turn {rdir_maps[direction]}. You are now facing {dir_maps[new_orientation]}.')

    @staticmethod
    def die():
        """Kills player and ends game.
        Note: Should add a save option here."""
        print('You has dieded, sorry bud.')
        raise SystemExit

    def __str__(self):
        for data in self.__dict__:
            print(f"attribute: {data}, value: {self.__dict__[data]}") if debug else None
        return ('This is you. You are currently in location ' + self.active_location
                + ' and are holding ' + str(self.inventory))


def command_matches_something(command, something, typ):
    """
    Checks if a command is in something passed in.
    :param command: The thing to check.
    :param something: The list/group of items from which the function will check if command is in.
    :param typ: simple or complex.
    :return: True if the
    """
    if command in str(something):
        return True
    for item in something:
        if item in command and typ == 'simple':
            return True


def check_conditions(exception):
    """Checks if all the conditions in the passed in condition set (exception) are True.
    :param exception: dictionary of all the conditions that have to pass in order for function to return True.
    :return: True if conditions pass, False if they don't
    """
    conditions_passed = False

    for condition_set in exception['if']:  # for every exception list in the 'if' key
        print('condition set:', condition_set) if debug else None
        item = condition_set[0]  # e.g. player, lantern, troll, or 6a
        state = condition_set[1]  # e.g. 'lit' or 'guarding'
        condition = condition_set[2]  # e.g. True/False, 6a (location)
        if len(condition_set) == 4:
            boolean = condition_set[3]
        else:
            boolean = True
        if 'range' in str(condition):
            condition = list(eval(condition))

        if condition == 'inventory':
            if state == 'player':
                inventory = player.inventory
            else:
                for dict_type in (OBJECTS, ACTORS):
                    if state in dict_type:
                        try:
                            inventory = dict_type[state].inventory
                            break
                        except AttributeError:  # if dict_type[state] does not have an inventory
                            # raise YamlFormatError("Only place 'inventory' as a condition for an item that has an inventory.")
                            logging.critical("YamlFormatError: Only place 'inventory' as a condition for an item that has an inventory.")
            if boolean is False:
                return True if item not in inventory else False
            else:
                return True if item in inventory else False

        print('{} state "{}" needs to be (in) {} in order for this exception to fire'.format(item, state, condition)) if debug else None

        if item == 'player':
            try:
                item_state = getattr(player, state)
            except AttributeError:
                # raise YamlFormatError(f"Player has no attribute {state}, you must define that in Player.YAML")
                logging.critical(f"YamlFormatError: Player has no attribute {state}, you must define that in Player.YAML")
        else:
            for dictionary in [LOCATIONS, OBJECTS, ACTORS]:
                if item in dictionary:
                    print('item in dictionary:', dictionary[item]) if debug else None
                    item_state = getattr(dictionary[item], state)
                    break

        try:
            x = item_state  # just to check if item_state was set
            print(f'{item} STATE OF {state} IS {item_state}') if debug else None
        except UnboundLocalError:  # exception raised if item_state is referenced before assignment
            logging.critical(f"YamlFormatError(The {item} has no state of {state} set. Add this attribute to YAML file.")
            raise YamlFormatError(f"The {item} has no state of {state} set. Add this attribute to YAML file.")

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
            print('conditions passed is False') if debug else None
            return False
        # it doesn't pass the condition, set it back to false
    print('check_conditions returning:', conditions_passed) if debug else None
    return conditions_passed


def exceptions_handler(exceptions, typ):
    """Handles things in which general/exception sets are declared.
    :param exceptions: The list of all the exceptions that will be checked. There are predefined separate reactions that
            will be player if certain conditions in the exceptions pass.
    :param typ: The type of exception list it is -- for example if it's a narrative, it has a 'narrative' key as its
        reaction, as opposed to a 'reaction' key.
    :return: The reaction/narrative and the actions associated with the reaction/narrative. None for either if either
        don't exist.
    """
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


def general_handler(general: dict or str, typ):  # RETURN NONE FOR NO REACTION LOOK AT RETURN DOCSTRING
    """Gets and returns proper general reaction.
    :param general: The general reaction -- either a string or a dictionary containing the reaction and actions in
        their respective keys.
    :param typ: The type of general reaction it is -- 'narrative' or default.
    :return: The reaction/narrative and the actions associated with the reaction/narrative. None for either if either
        don't exist.
    """

    if type(general) is str:
        return general, None  # None for no actions. There are for sure no actions because the defined reaction is just a string.

    elif type(general) is dict:
        actions = None
        print('general passed in:', general) if debug else None

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
    :param action_set:
    :return:
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
        if command_matches_something(answer, affirmations, 'simple'):
            if warning:
                return True, question_info['yes']
            return True
        elif command_matches_something(answer, negations, 'simple'):
            if warning:
                return False, question_info['no']
            return False
        else:
            print("Answer must be in the affirmative or the negative. I'll ask again.")


def remove_from_game(object):
    """Removes an object from the game. FOREVER."""
    del OBJECTS[object]


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

    def rotate(l, n):
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


def dir_to_loc(direction):
    """Translates a given direction to a location that the user goes to."""

    if direction in ['L', 'R', 'F', 'B']:
        direction = rdir_to_dir(direction)
    new_loc = LOCATIONS[player.active_location].moves[direction]
    if new_loc is None:
        print(f'Going {direction} takes you nowhere.')
        new_loc = player.active_location
    print('new location is either a warning or a random:', new_loc) if type(new_loc) is dict and debug else print('returning new loc, value is:', new_loc) if debug else None
    return new_loc


def turn_to_sentence(words, starting_msg, and_or, typ='misunderstood'):
    """Print all current objects in the location."""
    message = starting_msg
    for i in range(len(words)):
        # obj = OBJECTS[objects[i]]  # objects[i], for example, is 'egg'. so OBJECTS['egg']
        if i == len(words) - 1 and len(words) > 1:  # if it's the last word to add to the list AND if there is more than one word
            message += f' {and_or} ' if len(words) == 2 else f'{and_or} '  # add an 'and', e.g. x, y, and z -- space before 'and' based on conditional
        # objects_here += obj.short_description
        if typ in ('no quotes', 'objects here'):
            message += words[i]
        else:
            message += f"'{words[i]}'"
        if len(words) > 2:
            message += ', '
    if typ == 'objects here':  # if printing out all the objects in a given location, then end the sentence nicely with a period.
        message = message.strip(', ')  # strip trailing comma
    return message


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


def verify_actionability(typ, item, action_or_state, sub_dict=None):
    """Verifies that the player can perform a certain action or change something's state.
    :param typ: The type of action that is trying to be verified: e.g. 'action' or
    :param item: The item that is trying to be acted upon.
    :param action_or_state: The action on which the function will verify if the user can perform.
    :param sub_dict: the sub-dictionary inside the action_or_state dict. For example, 'place' can have a subdict where you can define
            different requirements for different containers the object is being placed into.
    :return: (True, None) if user can perform the action, (False, fail_msg) if the user cannot. fail_msg is the message
            to play telling the user that they can't perform action.
    """

    # maybe change this function to raise a TakeError if the requirements fail
    print('item passed into verify:', item) if debug else None
    if item in OBJECTS:
        item_object = OBJECTS[item]
    elif item in LOCATIONS:
        item_object = LOCATIONS[item]
    elif item in ACTORS:
        item_object = ACTORS[item]
    print(f"in VERIFY: item: {item}, action/state: {action_or_state}, 'subdictionary: {sub_dict}") if debug else None

    try:
        print(f"item: {item}, action/state: {action_or_state}, 'subdictionary: {sub_dict}") if debug else None
        requirement_dict = getattr(item_object, typ+'_requirements')

        if action_or_state is None:
            requirements = requirement_dict
        else:
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


def obj_in_container(obj, status):
    """Checks if an object is inside a container, either a locked one or an open one."""
    objects = LOCATIONS[player.active_location].objects
    containers = [OBJECTS[container] for container in objects if isinstance(OBJECTS[container], Container)]
    print('in obj_in_container: all containers:', [str(x) for x in containers]) if debug else None
    for container in containers:
        if status == 'open':  # if checking if an object is in an open container
            if obj in container.inventory and not container.locked:
                return container.name
        elif status == 'locked':  # if checking if an object is in a locked container
            if obj in container.inventory and container.locked:
                return container.name
    return False


def random_response(message_type):
    """Calls the more random function with invalid response info. Created this function so all places could easily
    and clearly print invalid responses without having to write out the whole function call below."""
    if message_type == 'invalid':
        return more_random(invalid_input_responses, already_used_invalids, last_three_invalids)
    elif message_type == 'okays':
        return more_random(okays, already_used_okays, last_three_okays)
    elif message_type == 'partial match':
        return more_random(partial_match_responses, already_used_partial_responses, last_three_partial_responses)


def more_random(responses, already_used, last_three):
    """Chooses an invalid input response."""

    def update(choice):
        """Update already used list and last three list, and then return the choice."""
        already_used.append(choice)
        last_three[0] = last_three[1]
        last_three[1] = last_three[2]
        last_three[2] = choice
        return choice

    choice = random.choice(responses)

    if choice in already_used:
        if len(already_used) == len(responses):
            already_used.clear()
            while choice in last_three:
                choice = random.choice(responses)
            return update(choice)
        else:
            while choice in already_used:
                choice = random.choice(responses)
            return update(choice)
    else:
        return update(choice)


# Parser functions
def pos_tagger(command):
    """Tags each of the words in the command and returns a list of tuples with appropriate tags."""

    def add(word, POS, og_word=None):
        """Tag the word and add to the skeleton."""
        tagged.append((word, POS))
        if og_word is None:
            og_word = word
        if POS != 'ERR':
            i = skeleton.index(og_word)
            skeleton[i] = ' '

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

                        double_partials = ('PFVB-ALL/ITEM-PFVB', 'PVB-ALL/ITEM-PVB', 'PFVB-OBJ/ALL-PFVB')
                        single_partials = ('PFVB-ALL/ITEM', 'PVB-ALL/ITEM', 'PFVB-OBJ/ALL')
                        if any(structure in label for structure in double_partials):
                            start = just_words.index(partials_in_usr_cmd[0])
                            print('start:', start) if debug else None
                            print('just_words[start+1]:', just_words[start+1]) if debug else None
                            second_word = just_words[start+1]
                            second_word_is_item_or_all = check_for_item(second_word)[0] or second_word in ('all', 'everything')
                            if second_word_is_item_or_all:
                                after_item = just_words.index(partials_in_usr_cmd[1])
                            else:
                                for word in tagged[start+2:]:  # ignore the first and second word, which we have verified
                                    # above are not references to any items
                                    print('word in tagged[start+2:]:', word) if debug else None
                                    if check_for_item(word[0])[0]:  # this if statement will for sure pass at least once because
                                        # the label of the tagged command is 'pfvb-ITEM-pfvb' --- ITEM! -- the [0] is super
                                        # essential because check_for_item returns a tuple, and tuples are always True
                                        after_item = tagged.index(word) + 1  # get the index of where the partial verb continues
                                        # after the item.
                                        print('after item set: to :---:', after_item) if debug else None
                                before_item = after_item - 2
                                print(f"start: {start}, 'before item: {before_item}, 'after item: {after_item}") if debug else None

                            len_before = len(tagged)
                            function_name = dictionary['function'] if 'F' in label else dictionary['verbs'][0]
                            if second_word_is_item_or_all:
                                tagged[start] = (function_name, tag_type)
                            else:
                                tagged[start:before_item + 1] = [(function_name, tag_type)]
                            difference = len_before - len(tagged)
                            del tagged[after_item - difference:]  # delete everything after the item because they are just
                            # continuations of the partial verb
                            return tagged
                        elif any(structure in label for structure in single_partials):
                            start = just_words.index(partials_in_usr_cmd[0])
                            end = just_words.index(partials_in_usr_cmd[-1])
                            function_name = dictionary['function'] if 'F' in label else dictionary['verbs'][0]
                            tagged[start:end+1] = [(function_name, tag_type)]
                            return tagged

    def rearrange_obj_with_adj(label, tagged):
        """Rearranges partial objects -- that is, objects that include adjectives, into a single object word.
        Get the adjective and the
        Get list of tuples -- first value is the name of the object, second is the adjectives associated with it -- list
        comp, IF the adjective is """
        print('tagged passed in:', tagged) if debug else None
        print('label passed in:', label) if debug else None
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

    def tag_word(index):
        """Checks the word for its type and adds the appropriate tag."""
        word = command[index].lower()  # set word to the command at the index, convert to lowercase
        direction = check_for_dir(word)
        verb = check_for_verb(word, intact_cmd)  # pass in word, the full command
        location = check_for_item(word, typ='LOC')
        object = check_for_item(word, intact_cmd, typ='OBJ')
        container = check_for_item(word, intact_cmd, typ='CONT')
        actor = check_for_item(word, typ='ACT')
        location_cmd = check_for_loc_cmd(word, intact_cmd)
        # special_cmd = check_for_special_cmd(word)

        # player_object = check_for_item(word, typ='POBJ')

        for word_type in (direction, verb, location, object, container, actor, location_cmd):
            if word_type[0]:  # word_type[0] can be either the returned word or False, if it didn't match the check_for_x
                # function.
                add(*word_type, word)  # unpack word_type. word_type[0] is the word, word_type[1] is the tag. Also pass
                # in the original word so the skeleton can be edited.
                return

        # If all above failed, now checking if the word is a special word.
        special_words = [
                        [('all', 'everything'), 'ALL'],
                        [('with', 'using'), 'WITH'],
                        [('but', 'except', 'excluding'), 'BUT'],
                        [('utilize', 'employ', 'apply', 'use', 'utilise'), 'USE'],
                        [('in', 'inside', 'into', 'within'), 'IN'],
                        [('and', 'then', ',', ';', '.'), 'AND'],
                        [('on', 'onto', 'atop'), 'ON'],
                        [('to'), 'TO'], [('out'), 'OUT'], [('of'), 'OF'], [('from'), 'FROM'], [('at'), 'AT'],
                        ]

        for word_set, tag in special_words:
            if word in word_set:
                add(word, tag)
                return

        word_maps = [
            [('here', 'location', 'loc', 'positioning', 'site', 'spot', 'setting', 'situation', 'area', 'region'),
             (player.active_location, 'LOC')]
                     ]

        for word_set, tag_set in word_maps:
            if word in word_set and 'FVB' in str(tagged):
                add(*tag_set, word)
                return
        # if none of the above worked
        if word.isdigit():
            add(word, 'NUM', word)
        else:
            add(word, 'ERR')

    skeleton = command[:]
    intact_cmd = command[:]  # the slice is necessary so that intact_cmd does not reference the same list as skeleton does,
    # for if it does, then intact_cmd will change when skeleton changes

    tagged = []
    for i in range(len(command)):
        tag_word(i)

    print('tagged after tagging:', tagged) if debug else None

    old_tagged = tagged[:]  # slice to create copy, not reference
    print('old tagged after set:', old_tagged) if debug else None
    if any(partial_tag in str(tagged) for partial_tag in ('PFVB', 'PVB', 'POBJ', 'PLVB', 'LVB')):
        print('rearranging tagged') if debug else None
        match_set = omni_parser.get_labels_and_matches(tagged, typ='PARTIAL')  # typ can be anything other than 'NORMAL'
        for label, match in match_set:
            if label == 'FVB-LVB':
                if match[0][0] == 'goto':
                    tagged = [match[1]]  # just keep the location verb, put it in list
            elif 'VB' in label:  # don't need to specify the 'P' for partial because that has already been verified in outer
                # if statement
                print('match in partial matches:', match) if debug else None
                for word_set in match:
                    old_tagged.remove(word_set)
                print(f'old tagged after removing match: {old_tagged}') if debug else None
                tagged = rearrange_verb(label, match) + old_tagged
            else:
                tagged = rearrange_obj_with_adj(label, match)

    print('old tagged before concatenating with rearranged tagged:', old_tagged) if debug else None
    print('\ntagged after rearranging:', tagged) if debug else None

    return tagged, skeleton


def is_partial(word, command, all_words_to_check, typ):
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

    # The only commands I want are the ones that have spaces in them, which mean they are multi-word commands,
    # the ones that the word is in -- because why would I want to look at a command in which the word is not even
    # there?

    multi_word_cmds = [cmd for cmd in all_words_to_check if ' ' in cmd and word in cmd.split()]

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
                if next_word in ('all', 'everything'):
                    if get_next_word(user_command, word_index+2) == next_multiword:  # if the word after the object
                        # is the next word in the multi-word command
                        return True
                if check_for_item(next_word, typ='OBJ')[0]:  # if the next word is an item, then now I have to check if there
                    # are more items lurking after the already-verified item.
                    index = word_index + 2  # starting index at the index after next_word
                    while index < len(user_command):
                        if check_for_item(user_command[index], typ='OBJ')[0]:
                            index += 1  # increment the index to check if the word after that is an item or the
                            # next word in the multi-word command
                        else:
                            if user_command[index] == next_multiword:  # if the word after the object
                                # is the next word in the multi-word command
                                return True
                            else:
                                break  # abso-freakin-lutely necessary


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


def check_for_verb(word, original_command: list):
    """Checks if the word is a verb."""

    for dict_type in ('builtin_commands', 'custom_commands'):
        for dictionary in COMMANDS[dict_type]:  # looping over all the dicts of verbs + needs + action sets
            partial = is_partial(word, original_command, dictionary['verbs'], typ='VERB')  # is_partial takes the word,
            # the full user command, the list of all the words from which to check if the word is a partial, and a type (typ)
            # which tells the function what to check for as far as finding a partial
            if partial:
                print(f"{word} is partial") if debug else None
                return (word, 'PFVB') if dict_type == 'builtin_commands' else (word, 'PVB')  # return partial function verb
                # if the dictionary looping over is the builtin_commands, which are the builtins. Otherwise the tag is just
                # partial verb.
    for dict_type in ('builtin_commands', 'custom_commands'):
        for dictionary in COMMANDS[dict_type]:  # loop twice for a case such as 'throw down' -- when checking for partial,
            # and the loop is now on the dictionary of throw commands [throw, hurl, etc...], partial will evaluate to None
            # and then it will check if the word is in dictionary['verbs'] -- but it will do that before having a chance to
            # realize that the whole command is 'throw down' -- so if partial failed, then I loop again over all the commands
            # and check if the word is in dictionary['verbs'].
            if word in dictionary['verbs']:  # if the word is in the verbs list of current loop dict, now you have your verb
                if dict_type == 'builtin_commands':
                    verb, tag = dictionary['function'], 'FVB'
                else:
                    verb, tag = dictionary['verbs'][0], 'VB'
                return verb, tag
    return False, None
    # Checking if the word is a special command, like for an object, location, or actor


def check_for_item(word, full_command=None, typ='all'):
    """Checks if word is reference to an object or a location."""
    if typ in ('OBJ', 'CONT'):
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
            if typ in ('OBJ', 'CONT'):
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
                        # print('all objects with adjectives:', [str(x) for x in objs_with_adjectives]) if debug else None
                        for obj in objs_with_adjectives:
                            adjectives = obj.adjectives
                            print(f"{obj.name}'s adjectives: {adjectives}") if debug else None
                            for order in ('normal', 'reverse'):
                                # print('\nNEW ORDERRRRR\n') if debug else None
                                # print('order:', order) if debug else None
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
                                # print(f'next word after {word} is {next_word}') if debug else None
                                if word in adjectives:
                                    # if next_word == obj.name or next_word in adjectives:
                                    return True

                        return False

                    partial = is_partial(word, full_command)
                    if partial:
                        print('under if partial word:', word)
                        return (word, 'POBJ') if word in references else (word, 'ADJ')  # if it is a reference to the object,
                        # and not an adjective of the object, return 'POBJ'....
                if isinstance(OBJECTS[item_reference], Container):
                    return item_reference, 'CONT'
                else:
                    return item_reference, 'OBJ'
            elif typ == 'ACT':
                return item_reference, 'ACT'
            elif typ == 'LOC':
                return item, 'LOC'
    # for references in [item.references for item in dictionary.values()]:
    return False, None


def check_for_loc_cmd(word, original_command):
    """Checks if the word is a location command, that is, a command in the location's defined commands."""

    location = LOCATIONS[player.active_location]
    for command_set in location.commands:
        command_set = command_set['verbs']
        partial = is_partial(word, original_command, command_set, 'CMD')
        if partial:
            return word, 'PLVB'
        elif word in command_set:
            return command_set[0], 'LVB'
    return False, None


def actualize_data(typ, filename):
    """For each location/object in location/object dictionary,
    create python objects."""
    data = setup.get_data(filename)
    simple_data = 'COMMANDS | PLAYER | RANDOMS | intro | instructions | name'
    if typ in simple_data:  # used "|" just to differentiate and make it look nice
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


# Change these variables for testing/debugging capabilities. If testing is True, then it will ask after every command if
# you want to turn debug on or off.
debug = False
testing = False

# Setting up the backbone of the game
LOCATIONS = {}
OBJECTS = {}
ACTORS = {}

COMMANDS = actualize_data('COMMANDS', setup.cmd_filename)
RANDOMS = actualize_data('RANDOMS', setup.randoms_filename)

actualize_data('LOCATIONS', setup.loc_filename)
actualize_data('OBJECTS', setup.obj_filename)
actualize_data('ACTORS', setup.act_filename)

name = actualize_data('name', setup.loc_filename)
instructions = actualize_data('instructions', setup.loc_filename)
intro = actualize_data('intro', setup.loc_filename)

player_data = actualize_data('PLAYER', setup.player_filename)
player = Player(player_data)

# Response for invalid input
invalid_input_responses = COMMANDS['invalid_input_responses']
already_used_invalids = []
last_three_invalids = [None, None, None]

# If reactions aren't set for different action, it will just play an 'okay'-type word.
okays = COMMANDS['okays']
already_used_okays = []
last_three_okays = [None, None, None]

# Responses for partial matches.
partial_match_responses = COMMANDS['not_full_match_responses']
already_used_partial_responses = []
last_three_partial_responses = [None, None, None]
