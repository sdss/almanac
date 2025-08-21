import logging
import colorlog
import os
import yaml
import warnings
from typing import List, Dict, Optional
from dataclasses import dataclass, field, is_dataclass, asdict
from pathlib import Path


handler = colorlog.StreamHandler()

formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s [%(levelname)s] %(message)s',
    log_colors={
'DEBUG': 'cyan',
'INFO': 'white',
'WARNING': 'yellow',
'ERROR': 'red',
'CRITICAL': 'bold_red',
},
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler.setFormatter(formatter)

print("TODO: set logger by config default verbosity")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Set desired logging level

# Add the handler to the logger
logger.addHandler(handler)


@dataclass
class DatabaseConfig:
    user: str = "sdss_user"
    host: str = "operations.sdss.org"
    port: int = 5432
    domain: str = "operations.sdss.*"

@dataclass
class ObservatoryMJD:
    apo: int = 59_558
    lco: int = 59_558


@dataclass
class Config:
    sdssdb: DatabaseConfig = field(default_factory=DatabaseConfig)
    database_connect_time_warning: int = 3 # seconds

    sdssdb_exposure_min_mjd: ObservatoryMJD = field(default_factory=ObservatoryMJD)
    


def get_config_path():
    config_dir = Path.home() / ".almanac"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.yaml"


class ConfigManager:
    """A utility class to save and load dataclass configurations using YAML."""

    @staticmethod
    def save(config: object, file_path: str | Path):
        """Saves a dataclass object to a YAML file."""
        if not is_dataclass(config):
            raise TypeError("Provided object is not a dataclass.")

        data = asdict(config)
        with open(file_path, "w") as f:
            yaml.dump(data, f, sort_keys=False)


    @staticmethod
    def load(cls, file_path: str | Path):
        """Loads a dataclass object from a YAML file."""
        if not is_dataclass(cls):
            raise TypeError("Provided class is not a dataclass.")

        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        # Recursively create nested dataclasses from the dictionary
        def _load_recursive(cls, data):
            if not is_dataclass(cls):
                return data

            fields = {f.name: f.type for f in cls.__dataclass_fields__.values()}
            kwargs = {}
            for key, value in data.items():
                field_type = fields.get(key)
                if is_dataclass(field_type):
                    kwargs[key] = _load_recursive(field_type, value)
                else:
                    kwargs[key] = value
            return cls(**kwargs)

        if data:
            config = _load_recursive(cls, data)
        else:
            config = cls()
        return config


config_path = get_config_path()
if not os.path.exists(config_path):
    config = Config()
    ConfigManager.save(config, config_path)
else:
    config = ConfigManager.load(Config, config_path)

