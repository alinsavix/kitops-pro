import sys
import traceback

import bpy

from bpy.types import PropertyGroup
from bpy.props import *
from bpy.utils import register_class, unregister_class

from . utility import addon, insert, update, shader, previews, enums, smart

authoring_enabled = True
try: from . utility import matrixmath
except:
    authoring_enabled = False
    traceback.print_exc()
    class matrixmath:
        class update:
            def type(prop, context): sys.exit()
            def author(prop, context): sys.exit()


def prepare_items(items: list) -> list:
    '''For each item, replace icon_path with icon_id and cast list to tuple.'''

    for index, item in enumerate(items):
        if isinstance(item, list):
            item[3] = previews.get(item[3]).icon_id
            items[index] = tuple(item)

    return items


def thumbnails(prop, context):
    option = addon.option()
    return option.get_kitops_insert_enum(prop.folder)


def kpack_enum(pt, context):
    option = addon.option()
    return option.get_kitops_category_enum()


class file(PropertyGroup):
    location: StringProperty()
    icon_path : StringProperty()


class folder(PropertyGroup):
    thumbnail: EnumProperty(update=update.thumbnails, items=thumbnails)
    active_index: IntProperty()
    blends: CollectionProperty(type=file)
    folder: StringProperty()


class kpack(PropertyGroup):
    active_index: IntProperty()
    categories: CollectionProperty(type=folder)


class mat(PropertyGroup):
    id: StringProperty()
    material: BoolProperty()


class data(PropertyGroup):
    id: StringProperty()
    insert: BoolProperty()


class object(PropertyGroup):
    id: StringProperty()
    collection: StringProperty()
    label: StringProperty()
    insert: BoolProperty()
    inserted: BoolProperty()
    main_object: PointerProperty(type=bpy.types.Object)
    reserved_target: PointerProperty(type=bpy.types.Object)
    applied: BoolProperty()
    duplicate: BoolProperty()
    mirror: BoolProperty()
    mirror_target: PointerProperty(type=bpy.types.Object)
    animated: BoolProperty()
    hide: BoolProperty()
    author: StringProperty()
    temp: BoolProperty()
    material_base: BoolProperty()
    bool_duplicate: BoolProperty()

    mirror_x: BoolProperty(
        name = 'X',
        description = 'Mirror INSERT on Y axis of the INSERT target',
        update = smart.update.mirror_x,
        default = False)

    mirror_y: BoolProperty(
        name = 'Y',
        description = 'Mirror INSERT on X axis of the INSERT target',
        update = smart.update.mirror_y,
        default = False)

    mirror_z: BoolProperty(
        name = 'Z',
        description = 'Mirror INSERT on Z axis of the INSERT target',
        update = smart.update.mirror_z,
        default = False)

    insert_target: PointerProperty(
        name = 'Insert target',
        description = 'Target obj for the INSERT',
        update = smart.update.insert_target,
        type = bpy.types.Object)

    main: BoolProperty(
        name = 'Main obj',
        description = 'This obj will become the main obj of all the other objs for this INSERT',
        update = smart.update.main,
        default = False)

    type: EnumProperty(
        name = 'Object type',
        description = 'Change KIT OPS obj type',
        items = [
            ('SOLID', 'Solid', 'This obj does NOT cut and is renderable'),
            ('WIRE', 'Wire', 'This obj does NOT cut and is NOT renderable'),
            ('CUTTER', 'Cutter', 'This obj does cut and is NOT renderable')],
        update = matrixmath.update.type,
        default = 'SOLID')

    boolean_type: EnumProperty(
        name = 'Boolean type',
        description = 'Boolean type to use for this obj',
        items = [
            ('DIFFERENCE', 'Difference', 'Combine two meshes in a subtractive way'),
            ('UNION', 'Union', 'Combine two meshes in an additive way'),
            ('INTERSECT', 'Intersect', 'Keep the part of the mesh that intersects with modifier object'),
            ('INSERT', 'Insert', 'The cutter is for the insert not the target')],
        default = 'DIFFERENCE')

    selection_ignore: BoolProperty(
        name = 'Selection ignore',
        description = 'Do not select this obj when using auto select',
        default = False)

    ground_box: BoolProperty(
        name = 'Ground box',
        description = 'Use to tell kitops that this is a ground box obj for thumbnail rendering',
        default = False)


class scene(PropertyGroup):
    factory: BoolProperty()
    thumbnail: BoolProperty()
    original_scene: StringProperty()
    last_edit: StringProperty()
    original_file: StringProperty()

    auto_parent: BoolProperty(
        name = 'Auto parent',
        description = 'Automatically parent all objs to the main obj when saving\n  Note: Incorrect parenting can lead to an unusable INSERT',
        default = False)

    animated: BoolProperty(
        name = 'Animated',
        description = 'Begin the timeline when you add this insert',
        default = False)


class options(PropertyGroup):
    addon: StringProperty(default=addon.name)
    kpack: PointerProperty(type=kpack)
    pro: BoolProperty(default=authoring_enabled)

    kpacks: EnumProperty(
        name = 'KPACKS',
        description = 'Available KPACKS',
        items = kpack_enum,
        update = update.kpacks)

    insert_name: StringProperty(
        name = 'INSERT Name',
        description = 'INSERT Name',
        default = 'Insert Name')

    author: StringProperty(
        name = 'Author Name',
        description = 'Kit author',
        update = matrixmath.update.author,
        default = 'Your Name')

    auto_scale: BoolProperty(
        name = 'Auto scale INSERT',
        description = 'Scale INSERTS based on obj size',
        default = True)

    parent_inserts: BoolProperty(
        name = 'Parent INSERTs to the target object',
        description = 'Automatically Parent the INSERTS to the target object',
        default = False)

    show_modifiers: BoolProperty(
        name = 'Modifiers',
        description = 'Toggle KIT OPS boolean modifier visibility',
        update = update.show_modifiers,
        default = True)

    show_solid_objects: BoolProperty(
        name = 'Solid objs',
        description = 'Show the KIT OPS solid objs',
        update = update.show_solid_objects,
        default = True)

    show_cutter_objects: BoolProperty(
        name = 'Cutter objs',
        description = 'Show the KIT OPS cutter objs',
        update = update.show_cutter_objects,
        default = True)

    show_wire_objects: BoolProperty(
        name = 'Wire objs',
        description = 'Show the KIT OPS wire objs',
        update = update.show_wire_objects,
        default = True)

    def get_kitops_category_enum(self):
        '''Get Enum list for KIT OPS Categories'''
        return prepare_items(enums.kitops_category_enums)

    def get_kitops_insert_enum(self, category):
        '''Get Enum List for KIT OPS Inserts related to a category'''
        if category in enums.kitops_insert_enum_map:
            return prepare_items(enums.kitops_insert_enum_map[category])
        return []


classes = [
    file,
    folder,
    kpack,
    mat,
    data,
    object,
    scene,
    options]


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.kitops = PointerProperty(name='KIT OPS', type=options)
    bpy.types.Scene.kitops = PointerProperty(name='KIT OPS', type=scene)
    bpy.types.Object.kitops = PointerProperty(name='KIT OPS', type=object)
    bpy.types.GreasePencil.kitops = PointerProperty(name='KIT OPS', type=data)
    bpy.types.Light.kitops = PointerProperty(name='KIT OPS', type=data)
    bpy.types.LightProbe.kitops = PointerProperty(name='KIT OPS', type=data)
    bpy.types.Camera.kitops = PointerProperty(name='KIT OPS', type=data)
    bpy.types.Speaker.kitops = PointerProperty(name='KIT OPS', type=data)
    bpy.types.Lattice.kitops = PointerProperty(name='KIT OPS', type=data)
    bpy.types.Armature.kitops = PointerProperty(name='KIT OPS', type=data)
    bpy.types.Curve.kitops = PointerProperty(name='KIT OPS', type=data)
    bpy.types.MetaBall.kitops = PointerProperty(name='KIT OPS', type=data)
    bpy.types.Mesh.kitops = PointerProperty(name='KIT OPS', type=data)
    bpy.types.Material.kitops = PointerProperty(name='KIT OPS', type=mat)

    update.icons()
    update.kpack(None, bpy.context)


def unregister():
    for cls in classes:
        unregister_class(cls)

    del bpy.types.WindowManager.kitops
    del bpy.types.Scene.kitops
    del bpy.types.Object.kitops
    del bpy.types.GreasePencil.kitops
    del bpy.types.Light.kitops
    del bpy.types.Camera.kitops
    del bpy.types.Speaker.kitops
    del bpy.types.Lattice.kitops
    del bpy.types.Armature.kitops
    del bpy.types.Curve.kitops
    del bpy.types.MetaBall.kitops
    del bpy.types.Mesh.kitops
    del bpy.types.Material.kitops

    addon.icons.clear()
