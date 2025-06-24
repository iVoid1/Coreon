import json

class Config:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r", encoding="utf-8") as file:
            self._data = json.load(file)

    def __getattr__(self, name):
        return self._data.get(name)


config = Config()
