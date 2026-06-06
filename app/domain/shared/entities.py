import uuid

class Entity:
    def __init__(self, id=None):
        self.id = id or uuid.uuid4()
