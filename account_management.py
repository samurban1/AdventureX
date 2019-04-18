from passlib.hash import pbkdf2_sha256


def create_account():
    """Gets username & password and ensures that it contains at least one uppercase and one number."""
    username = input('Enter username: ')
    password = input("Password must contain one uppercase letter and one number:"
                     "\nEnter password: ")
    while not any(char.isupper() for char in password) or not any(char.isdigit() for char in password):
        # checking if there's uppercase and number
        password = input("Password must contain one uppercase letter and one number."
                         "\nEnter again: ")
    hash_password(username, password)  # calls function below


def hash_password(username, password):
    """Turns the password into a hash and writes to file."""
    hash_key = pbkdf2_sha256.hash(password)  # builtin passlib function
    with open(username + '_credentials.txt', 'w') as pass_file:
        pass_file.write(hash_key)  # write hash to file using username


def verify_account():
    username = input('Enter username: ')
    password = input("Enter password: ")
    try:
        with open(username + '_credentials.txt', 'r') as pass_file:
            saved_hash = pass_file.read()  # store hash from file in variable, type = str
    except Exception as e:
        print(Exception, e)

    while not pbkdf2_sha256.verify(password, saved_hash):  # if hash not verified, re-enter password
        password = input('Incorrect password. Please enter another password: ')
    else:
        print('Password VERIFIED')


create_account()
verify = input("Would you like to verify your account? ")
if verify == 'yes':
    verify_account()

# add comment for git
# new comment
