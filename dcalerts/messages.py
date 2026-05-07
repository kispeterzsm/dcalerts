from typing import Union

import requests
from .settings import DEFAULTS

class MessageHandler:
    """
    This class lets you send messages via the given webhook.
    """
    def __init__(self, webhook_url: Union[str, object]):
        if type(webhook_url)==MessageHandler:
            self.webhook_url=webhook_url.webhook_url
        else:
            self.webhook_url=webhook_url

    def send(self, message, list_item_sep=DEFAULTS["separator"]):
        """
        Send a message to the objects given webhook.
        """
        send_message(webhook_url=self.webhook_url, message=message, list_item_sep=list_item_sep)

def send_message(webhook_url: Union[str, dict], message: str, list_item_sep: str=DEFAULTS["separator"]):
    """
    Send a message to a Discord webhook.
    """
    if( type(webhook_url)== dict):
        webhook_url=webhook_url["webhook"]
    payload = {"content": make_message(message, list_item_sep=list_item_sep)}
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()

def make_message(input, list_item_sep=DEFAULTS["separator"]):
    """
    Converts strings, lists of strings, functions and other inputs into a single string and returns it.
    """
    if list_item_sep is None:
        list_item_sep=DEFAULTS["separator"]

    final_message=""
    
    if type(input)==str:
        final_message+=input

    elif callable(input):
        final_message+=make_message(input(), list_item_sep=list_item_sep)

    elif type(input)==list:
        first_item = True
        for item in input:
            if type(item)==Specialsep: # this exception has to exist because of how utils.py functions operate
                list_item_sep=item.separator
                continue
            if not first_item:
                final_message += list_item_sep
            final_message += make_message(item, list_item_sep=list_item_sep)
            first_item = False
    else:
        final_message+=str(input)

    return final_message

class Specialsep():
    """Class used to define separator character exceptions for `makemessage`."""
    def __init__(self, separator=""):
        self.separator = separator

    def separator(self):
        return self.separator