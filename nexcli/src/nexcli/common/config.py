from configparser import ConfigParser
import os
from typing import Dict, Optional

from .constants import config_dir

class Config:
    _config_map: Dict[str, "Config"] = {}

    @classmethod
    def get(cls, name: str) -> "Config":
        if name not in cls._config_map:
            cls._config_map[name] = cls(name)
        return cls._config_map[name]


    def __init__(self, name: str):
        os.makedirs(config_dir, exist_ok=True)
        self._path = config_dir / f"{name}.ini"
        self._delegate = ConfigParser()
        self._delegate.read(self._path)

    def str(self, section: str, option: str, fallback: Optional[str]=None) -> Optional[str]:
        return self._delegate.get(section, option, fallback=fallback)

    def bool(self, section: str, option: str, fallback: Optional[bool]=None) -> Optional[bool]:
        return self._delegate.getboolean(section, option, fallback=fallback)
    
    def int(self, section: str, option: str, fallback: Optional[int]=None) -> Optional[int]:
        return self._delegate.getint(section, option, fallback=fallback)
    
    def float(self, section: str, option: str, fallback: Optional[float]=None) -> Optional[float]:
        return self._delegate.getfloat(section, option, fallback=fallback)
    
    def set_str(self, section: str, option: str, value: str, no_flush: bool = False):
        if not self._delegate.has_section(section):
            self._delegate.add_section(section)
        self._delegate.set(section, option, value)
        if not no_flush:
            self.flush()
    
    def set_bool(self, section: str, option: str, value: bool, no_flush: bool = False) -> None:
        self.set_str(section, option, str(value), no_flush=no_flush)

    def set_int(self, section: str, option: str, value: int, no_flush: bool = False) -> None:
        self.set_str(section, option, str(value), no_flush=no_flush)

    def set_float(self, section: str, option: str, value: float, no_flush: bool = False) -> None:
        self.set_str(section, option, str(value), no_flush=no_flush)

    def flush(self) -> None:
        with open(self._path, "w") as file:
            self._delegate.write(file)
