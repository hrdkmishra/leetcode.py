import toml
import os

CONFIG_FILE_PATH = "config.toml"


def update_config(key_value_dict):
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r") as config_file:
            config_data = toml.load(config_file)
        config_data.update(key_value_dict)
    else:
        config_data = key_value_dict

    with open(CONFIG_FILE_PATH, "w") as config_file:
        toml.dump(config_data, config_file)


def load_config_from_file():
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r") as config_file:
            return toml.load(config_file)
    return {}


def save_credentials_to_config(leetcode_session, csrf_token):
    config_data = {
        "LEETCODE_SESSION": leetcode_session,
        "CSRF_TOKEN": csrf_token
    }
    update_config(config_data)


def load_credentials_from_config():
    config_data = load_config_from_file()
    return config_data.get("LEETCODE_SESSION"), config_data.get("CSRF_TOKEN")


def load_user_data_from_config():
    config_data = load_config_from_file()
    return config_data.get("USER_LANG", "").lower(), config_data.get("EDITOR_CLI", "").lower()


def save_user_data_to_config(user_lang):
    config_data = {"USER_LANG": user_lang}
    update_config(config_data)


def save_user_path_to_config(path):
    config_data = {"LEETCODE_PATH": path}
    update_config(config_data)
    
def load_user_path_from_config():
    config_data = load_config_from_file()
    return config_data.get("LEETCODE_PATH", "")
