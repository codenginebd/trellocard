import os
import json
import csv
from pathlib import Path
import shutil

from trellocard_exception import TrelloCardException
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
    def read_csv_file(cls, file_path, delim=','):
        lines = []
        with open(file_path, newline='', encoding='iso-8859-1') as csvfile:
            source_file = csv.reader(csvfile, delimiter=delim)
            for line in source_file:
                lines += [line]
        return lines

    @classmethod
    def write_csv_file(cls, file_path, data, delim=','):
        try:
            file_mode = 'w'
            if os.path.exists(file_path):
                file_mode = 'a'
            with open(file_path, file_mode, encoding='iso-8859-1', newline='\n') as f:
                csv_file_writer = csv.writer(f, delimiter=delim)
                csv_file_writer.writerow(data)
            return True
        except TrelloCardException as exp:
            logger.log_info("File write failed. File: %s, Exception: %s" % (file_path, str(exp)))
            return False

    @classmethod
    def read_client_board_mapping(cls, file_path):
        client_board_data = cls.read_csv_file(file_path, delim=';')
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

    @classmethod
    def save_card_mapping(cls, card_mapping_file_path, source_card_id, destination_card_id, client_name):
        data_row = [source_card_id, destination_card_id, client_name]
        return cls.write_csv_file(card_mapping_file_path, data_row)

    @classmethod
    def read_corresponding_destination_card_id(cls, file_path, card_id_to_find):
        rows = cls.read_csv_file(file_path, delim=';')
        for row in rows:
            if len(row) < 3:
                continue
            card_id = row[0].strip()
            if card_id == card_id_to_find:
                destination_card_id = row[1].strip()
                return destination_card_id

    @classmethod
    def read_corresponding_destination_client_name(cls, file_path, card_id_to_find):
        rows = cls.read_csv_file(file_path, delim=';')
        for row in rows:
            if len(row) < 3:
                continue
            card_id = row[0].strip()
            if card_id == card_id_to_find:
                destination_client_name = row[2].strip()
                return destination_client_name

    @classmethod
    def remove_card_id_mapping(cls, file_path, card_id):
        rows = cls.read_csv_file(file_path, delim=';')
        new_rows = [row for row in rows if card_id not in row]
        cls.delete_file(file_path)
        for row in new_rows:
            cls.write_csv_file(file_path, row)

    @classmethod
    def read_mapping_source_card_list(cls, file_path):
        rows = cls.read_csv_file(file_path, delim=';')
        source_card_list = [row[0].strip() for row in rows if row]
        return source_card_list


