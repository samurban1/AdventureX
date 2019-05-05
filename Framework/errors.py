class ObjectError(Exception):
    pass


class AlreadyHoldingError(Exception):
    pass


class NotHoldingError(Exception):
    pass


class VerbError(Exception):
    pass


class AttackError(Exception):
    pass

class GoToError(Exception):
    pass



if __name__ == '__main__':
    while True:
        text = input('input: ')
        try:
            if 'animal' in text:
                raise ObjectError
            if 'take' in text:
                raise TakeObjectError
            if 'drop' in text:
                raise DropObjectError
            if 'jump' in text:
                raise VerbError('no')
        # except ObjectError:
        #     print('no such object')
        except TakeObjectError:
            print('already holding object')
        except DropObjectError:
            print('not holding object')
