import pickle


def save_state(number):
    data = (players, locations)
    with open('intermediate_data.pickle', 'rb') as file:
        dictionary = pickle.load(file)
    dictionary[number] = data
    with open('intermediate_data.pickle', 'wb') as file:
        pickle.dump(dictionary, file)


def load_state(number):
    global player, locations
    print('Loading saved game...')
    with open('intermediate_data.pickle', 'rb') as file:
        dictionary = pickle.load(file)
    data = dictionary[number]
    players, locations = data


players = 5
locations = 20
with open('intermediate_data.pickle', 'wb') as file:
    dictionary = {1: (players, locations)}
    pickle.dump(dictionary, file)
with open('intermediate_data.pickle', 'rb') as file:
    print('firt load')
    print(pickle.load(file))
print('saving state')
save_state(1)
players += 10
locations += 4
print('players and locs before load:', players, '--', locations)
load_state(1)
print('players and locs AFTER load:', players, '--', locations)
