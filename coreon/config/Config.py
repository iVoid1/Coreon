import json
import typing
from typing import Union, Any, Dict, List
from pathlib import Path
from coreon.utils.logger import logger


class Config:
    """A class for managing configuration files."""
    @staticmethod
    def get_item(List:list[Any]|None, index:int) -> Any|None:
        return List[index] if List != None and index < len(List) and index >= -len(List) else None
    
    @staticmethod
    def get_index(List:list[Any]|None, value:Any) -> int|None:
        return List.index(value) if List != None and value in List else None

    def __init__(self, file_name: Union[str, Path], auto_save: bool = True):
        """Initializes the Config object, loading the config file if it exists.

        Args:
            file_name: Path to configuration file
            config_type: Expected type of configuration (dict or list)
            auto_save: Whether to automatically save changes
        """

        self.file_name = Path(file_name)
        if not self.file_name.suffix:
            self.file_name = self.file_name.with_suffix('.json')
            
        self.auto_save = auto_save
        self.file = self.load()
        
        
    def load(self) -> Dict[Any, Any]|List[Any]|None:
        """Loads the configuration from the file.

        Returns:
            Configuration data or None if loading fails
        """

        try:
            with self.file_name.open('r', encoding='utf-8') as file:
                return json.load(file)
                
            
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.file_name}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in config file: {self.file_name}")
            return None

    def get(self, key_index:Any|int, default:Any = None) -> Any:
        """Retrieves a value from the config using a key (for dicts) or index (for lists)."""
        if isinstance(self.file, dict) and key_index in self.file:
            return self.file.get(key_index, default)
        
        if isinstance(self.file, list) and isinstance(key_index, int):
            return self.get_item(self.file, key_index)
        
        return default
    
    def index(self, keys:Any, default:Any = None) -> int|Any|None:
        """Finds the index of a key in a dict or value in a list."""
        if isinstance(self.file, dict):
            return next((item[0] for item in enumerate(self.file) if item[1] == keys), default)
        
        if keys in self.file:
            return self.get_index(self.file, keys)
        return default
    
    def save(self) -> bool:
        """Saves the config to the file."""
        if not self.file:
            return False
            
        try:
            with self.file_name.open('w') as file:
                json.dump(self.file, file, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def add(self, keys:Any, value:Any = None):
        """Adds a key-value pair (for dicts) or appends a value (for lists)."""
        if self.file == None:
            print("No config found")
            return None
        
        if isinstance(self.file, dict) :
            self.file[keys] = value
            self.save() if self.auto_save else None
            return {keys:value} 

        self.file.append(keys)
        self.save() if self.auto_save else None
        return keys

    def remove(self, key_or_index:Any|int) -> bool|None:
        """Removes a key (for dicts) or index (for lists)."""
        if isinstance(self.file, dict):
            if key_or_index in self.file:
                self.file.pop(key_or_index)
                self.save() if self.auto_save else None
                return True
            
        if isinstance(self.file, list) and isinstance(key_or_index, int) and key_or_index < len(self.file) and key_or_index >= -len(self.file):
            self.file.pop(key_or_index)
            self.save() if self.auto_save else None
            return True
        return False

    def update(self, keys: Any|int, new_value:Any|None = None, new_key:Any|None = None) -> bool|None:
        """Updates a key's value (for dicts) or replaces an index (for lists)."""
        if self.file == None:
            print("No config found")
            return None
        
        if isinstance(self.file, dict) and keys in self.file:
            if new_value != None:
                self.file[keys] = new_value
            
            if new_key != None:
                self.file[new_key] = self.file.pop(keys)
                
            self.save() if self.auto_save else None
            return True
        
        if isinstance(self.file, list) and (keys < len(self.file) or keys >= -len(self.file)):
            self.file.pop(keys)
            self.file.insert(keys, new_value)
            self.save() if self.auto_save else None
            return True
        
        return False
    
    def merges(self, other: object|dict[Any, Any]|list[Any]):
        """Merges another configuration into the current one."""
        if isinstance(other, Config):
            other = other.file
        
        if isinstance(self.file, dict) and isinstance(other, dict):
            for key, value in typing.cast(dict[Any, Any], other.items()):
                if key in self.file and isinstance(self.file[key], list) and isinstance(value, list):
                    self.file[key].extend(value)
                else:
                    self.file[key] = value    
            return self.file
        elif isinstance(self.file, list) and isinstance(other, list):
            self.file.extend(typing.cast(list[Any], other))
        else:
            return None
        self.save() if self.auto_save else None
        return self.file
    
    def items(self) -> list[Any]|None:
        if self.file == None:
            return None
        return list(self.file.items()) if isinstance(self.file, dict) else self.file

    def __setitem__(self, key, value):
        self.add(key, value)

    def __getitem__(self, key):
        return self.get(key)

    def __delitem__(self, key):
        self.remove(key)

    def __contains__(self, key) -> bool:
        return key in self.file


