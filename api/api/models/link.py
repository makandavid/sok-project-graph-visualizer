class Link(object):
    def __init__(self, id: int, source: int, target: int):
        self.id = id
        self.source = source
        self.target = target

    def __str__(self):
        return "Link ID: {}\Link Source: {}\Link Target: {}\n".format(self.id, self.source, self.target)
    
    def to_dict(self):
        return {"id": self.id, "source": self.source, "target": self.target}