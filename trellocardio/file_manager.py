import os
import json
import csv
from pathlib import Path
import shutil
from trellocard_logger import TrelloCardLogger


csv.field_size_limit(100000000)


logger = TrelloCardLogger.get_logger()


class FileManager(object):
    def __init__(self, file_directory=os.getcwd()):
        pass

    @classmethod
    def read_program_id(cls, file_path):
        batch_id = ""
        with open(file_path, "r") as f:
            batch_id = f.read()
        return batch_id

    @classmethod
    def delete_file(cls, file_path):
        if os.path.exists(file_path):
            os.remove(file_path)

    @classmethod
    def read_csv_file(cls, file_path):
        lines = []
        with open(file_path, newline='', encoding='iso-8859-1') as csvfile:
            source_file = csv.reader(csvfile)
            for line in source_file:
                lines += [line]
        return lines

    @classmethod
    def read_client_board_mapping(cls, file_path):
        client_board_data = cls.read_csv_file(file_path)
        if not client_board_data:
            logger.log_warning("client board mapping contains no data: %s" % file_path)
            return {}
        else:
            client_board_mapping = {}
            client_board_data = client_board_data[1:]
            for index, row in enumerate(client_board_data):
                if not row:
                    logger.log_warning(
                        "Found empty line %s in client board mapping: %s. Data: %s" % (index + 2, file_path, str(row)))
                elif len(row) != 2:
                    logger.log_warning(
                        "Found empty line %s in client board mapping: %s. Data: %s" % (index + 2, file_path, str(row)))
                else:
                    client_board_mapping[row[0].strip()] = row[1].strip()
            return client_board_mapping