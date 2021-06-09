### Wrapper class to manage thumbnail caching ###
import bpy
from pathlib import Path
from typing import Union
from ..t3dn_bip import previews


collection = None

def clear():
    '''clear out the collection by removing it from previews and instantiating a new one.sss'''
    global collection
    previews.remove(collection)
    collection = previews.new()


def get(path: Union[str, Path]) -> bpy.types.ImagePreview:
    '''Get the icon based on a supplied path.'''
    path = str(path)
    return collection.load_safe(path, path, 'IMAGE')


def register():
    global collection
    collection = previews.new()


def unregister():
    previews.remove(collection)