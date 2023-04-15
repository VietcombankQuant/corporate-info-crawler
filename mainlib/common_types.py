class Location:
    def __init__(self, *, id, name, level, level_name, url, parent_id=None, parent=None):
        self.id = id
        self.name = name
        self.level = level
        self.level_name = level_name
        self.url = url
        self.parent_id = parent_id
        self.parent = parent
