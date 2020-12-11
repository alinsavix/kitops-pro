import os

import bpy

from . import update

name = __name__.partition('.')[0]
icons = {}


class path:

    def __new__(self):
        return os.path.abspath(os.path.join(__file__, '..', '..', '..'))

    def icons():
        return os.path.join(os.path.realpath(path()), 'icons')

    def default_kpack():
        return os.path.join(os.path.realpath(path()), 'Master')

    def thumbnail():
        return os.path.join(path.default_kpack(), 'render.blend')

    def material():
        return os.path.join(path.default_kpack(), 'material.blend')

    def default_thumbnail():
        return os.path.join(path.default_kpack(), 'thumb.png')


def preference():
    preference = bpy.context.preferences.addons[name].preferences

    if not len(preference.folders):
        folder = preference.folders.add()
        folder.name = 'KPACK'
        folder.location = path.default_kpack()

    return preference


def option():
    wm = bpy.context.window_manager
    if not hasattr(wm, 'kitops'):
        return False

    option = bpy.context.window_manager.kitops

    if not option.name:
        option.name = 'options'
        update.options()

    return option


def hops():
    wm = bpy.context.window_manager

    if hasattr(wm, 'Hard_Ops_folder_name'):
        return bpy.context.preferences.addons[wm.Hard_Ops_folder_name].preferences

    return False


def bc():
    wm = bpy.context.window_manager

    if hasattr(wm, 'bc'):
        return bpy.context.preferences.addons[wm.bc.addon].preferences

    return False
