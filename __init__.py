# Copyright (C) 2018-2020 chippwalters, masterxeon1001 All Rights Reserved

bl_info = {
    'name': 'KIT OPS',
    'author': 'Chipp Walters, MX2, proxe, bonjorno7, Mark Kingsnorth',
    'version': (2, 18, 10),
    'blender': (2, 83, 0),
    'location': 'View3D > Toolshelf (T)',
    'description': 'Streamlined kit bash library with additional productivity tools',
    'wiki_url': 'http://cw1.me/kops2docs',
    'category': '3D View'}

import bpy

from . addon import preference, property
from . addon.interface import operator, panel
from . addon.utility import handler


def register():
    preference.register()
    property.register()

    operator.register()
    panel.register()

    handler.register()


def unregister():
    handler.unregister()

    panel.unregister()
    operator.unregister()

    property.unregister()
    preference.unregister()
