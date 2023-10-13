import json
from typing import Dict

class NoPauseObject(object):
    def __init__(self, data: Dict):
        for key, value in data.items():
            if isinstance(value, dict):
                cls = type(key, (type(self),), {})
                setattr(self, key, cls(value))
            elif isinstance(value, list):
                lst = []
                for item in value:
                    if isinstance(item, dict):
                        lst.append(NoPauseObject(item))
                    else:
                        lst.append(item)
                setattr(self, key, lst)
            else:
                setattr(self, key, value)

    @classmethod
    def create(cls, data: Dict, name: str = None):
        if name is not None:
            custom_cls = type(f'{name}{cls.class_suffix()}', (cls,), {})
            return custom_cls(data)
        else:
            return cls(data)
    
    def __str__(self):
        return f'{type(self)}' + '\n' + json.dumps(self, default=lambda o: o.__dict__, indent=2)
    
    def to_dict(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__, indent=2))
        
    @classmethod
    def class_suffix(cls):
        return ''

class NoPauseResponse(NoPauseObject):
    @classmethod
    def class_suffix(cls):
        return 'Response'
