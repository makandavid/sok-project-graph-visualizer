class Link(object):
    def __init__(self, id: int, source: int, target: int):
        self.id = id
        self.source = source
        self.target = target

    def __str__(self):
        return f"Link ID: {self.id}\Link Source: {self.source}\Link Target: {self.target}\n"
    
    def to_dict(self):
        return {"id": self.id, "source": self.source, "target": self.target}