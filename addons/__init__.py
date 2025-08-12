import importlib
import os
import logging

# from addons.access_token_management import init as token_init
from addons.custom_field_management import init as field_init

def init():
    # token_init()
    field_init()
