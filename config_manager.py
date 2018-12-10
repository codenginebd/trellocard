import os
import sys
import json


class ConfigManager(object):

    def __init__(self, config="config.json"):
        self.config = config
        self.config_json = self.load_config()

    def load_config(self):
        content = None
        with open(self.config, "r") as config_file:
            content = config_file.read()

        if content:
            return json.loads(content)
        else:
            return {}

    def read_api_config(self):
        api_json = self.config_json.get('api', {})
        return api_json

    def read_api_key(self):
        api_json = self.read_api_config()
        return api_json.get('api_key', '')

    def read_api_token(self):
        api_json = self.read_api_config()
        return api_json.get('api_token', '')

    def read_board_id_to_sync(self):
        return self.config_json.get('board_id_to_sync', '')

    def read_program_config(self):
        program_config = self.config_json.get("program", {})
        return program_config

    def read_files_config(self):
        files_config = self.config_json.get("files", {})
        return files_config

    def read_log_config(self):
        return self.config_json.get("log", {})

    def read_log_file_directory(self):
        log_config = self.read_log_config()
        default_log_dir = os.path.join(os.getcwd(), "log")
        return log_config.get("log_directory", default_log_dir) or default_log_dir

    def read_lock_file(self):
        program_config = self.read_program_config()
        lock_file_directory = program_config.get("lock_file_directory", os.getcwd())
        lock_file_name = program_config.get("lock_file_name", "program.lock")
        lock_file_path = os.path.join(lock_file_directory, lock_file_name)
        return lock_file_directory, lock_file_name, lock_file_path

    def read_card_mapping_file_path(self):
        files_config = self.read_files_config()
        return files_config.get('card_mapping_file')

    def read_client_board_mapping_file_path(self):
        files_config = self.read_files_config()
        return files_config.get('client_board_mapping')
