class ObjectError(Exception):
    pass


class TakeObjectError(Exception):
    pass


class DropObjectError(Exception):
    pass


class NoSuchVerbError(Exception):
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
