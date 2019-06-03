class ObjectError(Exception):
    def __init__(self, message):
        self.message = message


class AlreadyHoldingError(Exception):
    def __init__(self, message):
        self.message = message


class PlaceError(Exception):
    pass


class Info(Exception):
    pass

class NotHoldingError(Exception):
    pass


class ThrowError(Exception):
    pass


class StateChangeError(Exception):
    pass

class VerbError(Exception):
    pass


class TakeError(Exception):
    pass

class AttackError(Exception):
    pass

class GoToError(Exception):
    pass


class YamlFormatError(Exception):
    pass
