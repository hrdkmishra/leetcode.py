import toml
import os

CONFIG_FILE_PATH = "config.toml"


def save_credentials_to_config(leetcode_session, csrf_token):
    config_data = {"LEETCODE_SESSION": leetcode_session, "CSRF_TOKEN": csrf_token}
    with open(CONFIG_FILE_PATH, "w") as config_file:
        toml.dump(config_data, config_file)


def load_credentials_from_config():
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r") as config_file:
            config_data = toml.load(config_file)
        return config_data.get("LEETCODE_SESSION"), config_data.get("CSRF_TOKEN")
    return None, None


def load_user_data_from_config():
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r") as config_file:
            config_data = toml.load(config_file)
        return config_data.get("USER_LANG", "").lower()
    return None


def save_user_data_to_config(user_lang):
    config_data = {"USER_LANG": user_lang}
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r") as config_file:
            existing_config_data = toml.load(config_file)
        existing_config_data.update(config_data)
        config_data = existing_config_data
    with open(CONFIG_FILE_PATH, "w") as config_file:
        toml.dump(config_data, config_file)
