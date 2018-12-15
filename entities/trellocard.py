class TrelloCard(object):
    card_id = None
    card_list_id = None
    card_name = None
    card_name_formatted = None
    card_due_date = None
    card_description = None
    card_attachments = []
    card_quote = None
    card_owner = None

    def __str__(self):
        return """
        Card Id: %s\n
        Card List Id: %s\n
        Card Name: %s\n
        Card Name Formatted: %s\n
        Card Due Date: %s\n
        Card Description: %s\n
        """ % (self.card_id, self.card_list_id, self.card_name,
               self.card_name_formatted, self.card_due_date, self.card_description)