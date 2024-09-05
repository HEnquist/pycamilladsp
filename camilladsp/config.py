"""
Python library for communicating with CamillaDSP.

This module contains commands for managind configs.
"""

from typing import Dict, Optional

import yaml

from .commandgroup import _CommandGroup


class Config(_CommandGroup):
    """
    Collection of methods for configuration management
    """

    def file_path(self) -> Optional[str]:
        """
        Get path to current config file.

        Returns:
            str | None: Path to config file, or None.
        """
        name = self.client.query("GetConfigFilePath")
        return name

    def set_file_path(self, value: str):
        """
        Set path to config file, without loading it.
        Call `reload()` to apply the new config file.

        Args:
            value (str): Path to config file.
        """
        self.client.query("SetConfigFilePath", arg=value)

    def active_raw(self) -> Optional[str]:
        """
        Get the active configuration in raw yaml format (as a string).

        Returns:
            str | None: Current config as a raw yaml string, or None.
        """
        config_string = self.client.query("GetConfig")
        return config_string

    def set_active_raw(self, config_string: str):
        """
        Upload and apply a new configuration in raw yaml format (as a string).

        Args:
            config_string (str): Config as yaml string.
        """
        self.client.query("SetConfig", arg=config_string)

    def active_json(self) -> Optional[str]:
        """
        Get the active configuration in raw json format (as a string).

        Returns:
            str | None: Current config as a raw json string, or None.
        """
        config_string = self.client.query("GetConfigJson")
        return config_string

    def set_active_json(self, config_string: str):
        """
        Upload and apply a new configuration in raw json format (as a string).

        Args:
            config_string (str): Config as json string.
        """
        self.client.query("SetConfigJson", arg=config_string)

    def active(self) -> Optional[Dict]:
        """
        Get the active configuration as a Python object.

        Returns:
            Dict | None: Current config as a Python dict, or None.
        """
        config_string = self.active_raw()
        if config_string is None:
            return None
        config_object = yaml.safe_load(config_string)
        return config_object

    def previous(self) -> Optional[Dict]:
        """
        Get the previously active configuration as a Python object.

        Returns:
            Dict | None: Previous config as a Python dict, or None.
        """
        config_string = self.client.query("GetPreviousConfig")
        config_object = yaml.safe_load(config_string)
        return config_object

    def parse_yaml(self, config_string: str) -> Dict:
        """
        Parse a config from yaml string and return the contents
        as a Python object, with defaults filled out with their default values.

        Args:
            config_string (str): A config as raw yaml string.

        Returns:
            Dict | None: Parsed config as a Python dict.
        """
        config_raw = self.client.query("ReadConfig", arg=config_string)
        config_object = yaml.safe_load(config_raw)
        return config_object

    def read_and_parse_file(self, filename: str) -> Dict:
        """
        Read and parse a config file from disk and return the contents as a Python object.

        Args:
            filename (str): Path to a config file.

        Returns:
            Dict | None: Parsed config as a Python dict.
        """
        config_raw = self.client.query("ReadConfigFile", arg=filename)
        config = yaml.safe_load(config_raw)
        return config

    def set_active(self, config_object: Dict):
        """
        Upload and apply a new configuration from a Python object.

        Args:
            config_object (Dict): A configuration as a Python dict.
        """
        config_raw = yaml.dump(config_object)
        self.set_active_raw(config_raw)

    def validate(self, config_object: Dict) -> Dict:
        """
        Validate a configuration object.
        Returns the validated config with all optional fields filled with defaults.
        Raises a CamillaError on errors.

        Args:
            config_object (Dict): A configuration as a Python dict.

        Returns:
            Dict | None: Validated config as a Python dict.
        """
        config_string = yaml.dump(config_object)
        validated_string = self.client.query("ValidateConfig", arg=config_string)
        validated_object = yaml.safe_load(validated_string)
        return validated_object

    def title(self) -> Optional[str]:
        """
        Get the title of the active configuration.

        Returns:
            str | None: Config title if defined, else None.
        """
        title = self.client.query("GetConfigTitle")
        return title

    def description(self) -> Optional[str]:
        """
        Get the title of the active configuration.

        Returns:
            str | None: Config description if defined, else None.
        """
        desc = self.client.query("GetConfigDescription")
        return desc
