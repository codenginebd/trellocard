import requests
import json
import fileinput

####################################################################
# Get API key from params file
####################################################################
def get_api_key():
    file = open("params.txt", "r")
    for line in file:
        if "api_key" in line:
            api_key = line.split(" ")[1].strip()
            break
    file.close()
    return api_key

####################################################################
# Get API token from params file
####################################################################
def get_api_token():
    file = open("params.txt", "r")
    for line in file:
        if "api_token" in line:
            api_token = line.split(" ")[1].strip()
            break
    file.close()
    return api_token

####################################################################
# Get board id to sync from params file
####################################################################
def get_board_id_to_sync():
    file = open("params.txt", "r")
    for line in file:
        if "board_id_to_sync" in line:
            board_id_to_sync = line.split(" ")[1].strip()
            break
    file.close()
    return board_id_to_sync

####################################################################
# Get client name <-> board id mapping from file
####################################################################
def get_client_board_mapping():
    file = open("client_board_mapping.csv", "r")
    client_board_mapping = {}
    next(file)
    for line in file:
        client_name = line.split(";")[0].strip()
        board_id = line.split(";")[1].strip()
        client_board_mapping[client_name] = board_id
    file.close()
    return client_board_mapping

####################################################################
# Get all ids of cards located in a board
####################################################################
def get_cards_in_board(board_id, api_key, api_token):
    url = "https://api.trello.com/1/boards/" + board_id +"/cards?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    card_list = []
    for card in response_json_array:
        card_list.append(card["id"])
    return card_list

####################################################################
# Get the client name attached to a card based on the card id
####################################################################
def get_card_client_name(board_id, card_id, api_key, api_token):
    # Get custom field ids of all client custom fields in the board
    url = "https://api.trello.com/1/boards/" + board_id +"/customFields?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    client_custom_field_ids = []
    for custom_field in response_json_array:
        custom_field_id = custom_field["id"]
        custom_field_name = custom_field["name"]
        if "Client A-K" in custom_field_name or "Client L-Z" in custom_field_name:
            client_custom_field_ids.append(custom_field_id)

    # Get client custom field id and value id for the card
    url = "https://api.trello.com/1/cards/" + card_id + "?fields=name&customFieldItems=true&key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    card_custom_fields = response_json_array["customFieldItems"]
    client_custom_field_id = ""
    for i in range(len(card_custom_fields)):
        custom_field_id = card_custom_fields[i]["idCustomField"]
        if custom_field_id in client_custom_field_ids:
            client_custom_field_id = custom_field_id
            client_custom_field_value_id = card_custom_fields[i]["idValue"]

    # Get client name from client custom field id and value id for the card
    url = "https://api.trello.com/1/boards/" + board_id +"/customFields?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    client_name = ""
    for custom_field in response_json_array:
        custom_field_id = custom_field["id"]
        if custom_field_id == client_custom_field_id:
            custom_field_values = custom_field["options"]
            for value in custom_field_values:
                if value["id"] == client_custom_field_value_id:
                    client_name = value["value"]["text"].strip()
                    break
            break

    return client_name

####################################################################
# Get the name of a card
####################################################################
def get_card_name(card_id, api_key, api_token):
    url = "https://api.trello.com/1/cards/" + card_id + "?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    return response_json_array["name"]

####################################################################
# Get the due date of a card
####################################################################
def get_card_due_date(card_id, api_key, api_token):
    url = "https://api.trello.com/1/cards/" + card_id + "?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    return response_json_array["due"]

####################################################################
# Get the description of a card
####################################################################
def get_card_description(card_id, api_key, api_token):
    url = "https://api.trello.com/1/cards/" + card_id + "?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    return response_json_array["desc"]

####################################################################
# Get the attachments of a card
####################################################################
def get_card_attachments(card_id, api_key, api_token):
    url = "https://api.trello.com/1/cards/" + card_id + "/attachments?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    attachment_list = []
    for attachment in response_json_array:
        attachment_details = []
        attachment_details.append(attachment["name"])
        attachment_details.append(attachment["url"])
        attachment_list.append(attachment_details)

    return attachment_list

####################################################################
# Get the quote of a card
####################################################################
def get_card_quote(board_id, card_id, api_key, api_token):
    # Get quote custom field id
    url = "https://api.trello.com/1/boards/" + board_id +"/customFields?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    quote_custom_field_id = ""
    for custom_field in response_json_array:
        custom_field_id = custom_field["id"].strip()
        custom_field_name = custom_field["name"].strip()
        if custom_field_name == "Quote":
            quote_custom_field_id = custom_field_id

    # Get quote value for the card
    url = "https://api.trello.com/1/cards/" + card_id + "?fields=name&customFieldItems=true&key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    card_custom_fields = response_json_array["customFieldItems"]
    quote_value = ""
    for i in range(len(card_custom_fields)):
        custom_field_id = card_custom_fields[i]["idCustomField"]
        if custom_field_id == quote_custom_field_id:
            quote_value = card_custom_fields[i]["value"]["number"]
            break

    return quote_value

####################################################################
# Get the owner of a card
####################################################################
def get_card_owner(board_id, card_id, api_key, api_token):
    # Get owner custom field id
    url = "https://api.trello.com/1/boards/" + board_id +"/customFields?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    owner_custom_field_id = ""
    for custom_field in response_json_array:
        custom_field_id = custom_field["id"].strip()
        custom_field_name = custom_field["name"].strip()
        if custom_field_name == "Owner":
            owner_custom_field_id = custom_field_id

    # Get owner custom field value id for the card
    url = "https://api.trello.com/1/cards/" + card_id + "?fields=name&customFieldItems=true&key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    card_custom_fields = response_json_array["customFieldItems"]
    owner_custom_field_value_id = ""
    for i in range(len(card_custom_fields)):
        custom_field_id = card_custom_fields[i]["idCustomField"]
        if custom_field_id == owner_custom_field_id:
            owner_custom_field_value_id = card_custom_fields[i]["idValue"]

    # Get owner from owner custom field id and value id for the card
    url = "https://api.trello.com/1/boards/" + board_id +"/customFields?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    owner = ""
    for custom_field in response_json_array:
        custom_field_id = custom_field["id"]
        if custom_field_id == owner_custom_field_id:
            custom_field_values = custom_field["options"]
            for value in custom_field_values:
                if value["id"] == owner_custom_field_value_id:
                    owner = value["value"]["text"].strip()
                    break
            break

    return owner

####################################################################
# Get the list name a card id belongs to
####################################################################
def get_card_list_name_formatted(card_id, api_key, api_token):
    # Get the list id the card belongs to
    url = "https://api.trello.com/1/cards/" + card_id + "?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    card_list_id = response_json_array["idList"]

    # Get the list name from the list id
    url = "https://api.trello.com/1/lists/" + card_list_id + "?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    card_list_name = response_json_array["name"].strip()

    # Rename list names so they match with the client boards
    if card_list_name == "Suspendo": card_list_name = "Suspended"
    if card_list_name == "Finito": card_list_name = "Returned"

    return card_list_name

####################################################################
# Get the list id based on a list name
####################################################################
def get_list_id(board_id, name, api_key, api_token):
    url = "https://api.trello.com/1/boards/" + board_id + "/lists?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    for list in response_json_array:
        list_id = list["id"].strip()
        list_name = list["name"].strip()
        if list_name == name:
            return list_id
            break

####################################################################
# Create a card with name, due date and description
####################################################################
def create_card(board_id, list_id, name, due_date, description, api_key, api_token):
    # Create card
    url = "https://api.trello.com/1/cards?key=" + api_key + "&token=" + api_token
    querystring = {"name":name,"desc":description,"due":due_date,"idList":list_id}
    response = requests.request("POST", url, params = querystring)

    # Return id of the newly created card
    return response.json()["id"]

####################################################################
# Update a card with name, due date and description
####################################################################
def update_card(card_id, name, due_date, description, api_key, api_token):
    url = "https://api.trello.com/1/cards/" + card_id + "?key=" + api_key + "&token=" + api_token
    querystring = {"name":name,"desc":description,"due":due_date}
    response = requests.request("PUT", url, params = querystring)

####################################################################
# Store mapping source card id <-> destination card id in file
####################################################################
def store_card_mapping(source_card_id, destination_card_id, client_name):
    file = open("card_mapping.csv", "a")
    file.write(source_card_id + ";" + destination_card_id + ";" + client_name + "\n")
    file.close()

####################################################################
# Add attachments to a card
####################################################################
def add_card_attachments(card_id, card_attachments, api_key, api_token):
    for attachment in card_attachments:
        attachment_name = attachment[0]
        attachment_url = attachment[1]
        url = "https://api.trello.com/1/cards/" + card_id + "/attachments?key=" + api_key + "&token=" + api_token
        querystring = {"name":attachment_name,"url":attachment_url}
        response = requests.request("POST", url, params=querystring)

####################################################################
# Delete attachments of a card
####################################################################
def delete_card_attachments(card_id, api_key, api_token):
    # Get card attachments
    url = "https://api.trello.com/1/cards/" + card_id + "/attachments?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    attachment_list = []
    for attachment in response_json_array:
        attachment_list.append(attachment["id"])

    # Delete attachments
    for attachment_id in attachment_list:
        url = "https://api.trello.com/1/cards/" + card_id + "/attachments/" + attachment_id + "?key=" + api_key + "&token=" + api_token
        response = requests.request("DELETE", url)

####################################################################
# Update quote value
####################################################################
def update_card_quote(board_id, card_id, quote_value, api_key, api_token):
    # Get quote custom field id
    url = "https://api.trello.com/1/boards/" + board_id +"/customFields?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    quote_custom_field_id = ""
    for custom_field in response_json_array:
        custom_field_id = custom_field["id"].strip()
        custom_field_name = custom_field["name"].strip()
        if custom_field_name == "Quote":
            quote_custom_field_id = custom_field_id

    # Update quote value
    url = "https://api.trello.com/1/card/" + card_id + "/customField/" + quote_custom_field_id + "/item?key=" + api_key + "&token=" + api_token
    data = {"value":{"number":quote_value}}
    response = requests.put(url, json = data)

####################################################################
# Update owner
####################################################################
def update_card_owner(board_id, card_id, owner, api_key, api_token):
    # Get owner custom field id and value id
    url = "https://api.trello.com/1/boards/" + board_id +"/customFields?key=" + api_key + "&token=" + api_token
    response = requests.request("GET", url)
    response.encoding = None
    response_json_array = json.loads(response.text)

    owner_custom_field_id = ""
    owner_custom_field_value_id = ""
    for custom_field in response_json_array:
        custom_field_id = custom_field["id"].strip()
        custom_field_name = custom_field["name"].strip()
        if custom_field_name == "Owner":
            owner_custom_field_id = custom_field_id
            owner_custom_field_values = custom_field["options"]
            for value in owner_custom_field_values:
                if value["value"]["text"].strip() == owner:
                    owner_custom_field_value_id = value["id"]
                    break

    # Update owner value
    url = "https://api.trello.com/1/card/" + card_id + "/customField/" + owner_custom_field_id + "/item?key=" + api_key + "&token=" + api_token
    data = {"idValue":owner_custom_field_value_id}
    response = requests.put(url, json = data)

####################################################################
# Check if card has already been synced before
####################################################################
def get_corresponding_destination_card_id(card_id_to_find):
    file = open("card_mapping.csv", "r")
    destination_card_id = ""
    for line in file:
        card_id = line.split(";")[0].strip()
        if card_id == card_id_to_find:
            destination_card_id = line.split(";")[1].strip()
            break
    file.close()

    return destination_card_id

####################################################################
# Get client name of the previously synced card
####################################################################
def get_corresponding_destination_client_name(card_id_to_find):
    file = open("card_mapping.csv", "r")
    destination_client_name = ""
    for line in file:
        card_id = line.split(";")[0].strip()
        if card_id == card_id_to_find:
            destination_client_name = line.split(";")[2].strip()
            break
    file.close()

    return destination_client_name

####################################################################
# Delete card
####################################################################
def delete_card(card_id, api_key, api_token):
    url = "https://api.trello.com/1/cards/" + card_id + "?key=" + api_key + "&token=" + api_token
    response = requests.request("DELETE", url)

####################################################################
# Remove mapping source card id <-> destination card id in file
####################################################################
def remove_card_mapping(card_id):
    # Read all file content
    file = open("card_mapping.csv", "r")
    lines = file.readlines()
    file.close()

    # Write content without line to remove
    file = open("card_mapping.csv","w")
    for line in lines:
        if card_id not in line:
            file.write(line)
    file.close()

####################################################################
# List source cards in mapping file
####################################################################
def get_mapping_source_card_list():
    file = open("card_mapping.csv", "r")
    source_card_list = []
    for line in file:
        source_card_list.append(line.split(";")[0].strip())
    file.close()

    return source_card_list

####################################################################
# Move a card to a new list
####################################################################
def move_card(card_id, list_id, api_key, api_token):
    url = "https://api.trello.com/1/cards/" + card_id + "?key=" + api_key + "&token=" + api_token
    data = {"idList":list_id}
    response = requests.put(url, json = data)
