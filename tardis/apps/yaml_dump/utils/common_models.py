
from dataclasses import dataclass

@dataclass
class UsernameYAMLDataclass:
    username: str

def username_representer(dumper, data):
    return dumper.represent_mapping("!Username", data.username)