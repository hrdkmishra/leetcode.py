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


def create_python_code_edit_file(question_id, title_slug, python3_code):
    if python3_code is None:
        print(f"No Python3 code snippet found for question '{question_id}'.")
        return

    file_name = f"code_editor/{question_id}_{title_slug}.py"
    with open(file_name, "w") as file:
        file.write(python3_code.code)
