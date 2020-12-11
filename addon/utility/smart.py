import os

import bpy

from bpy.types import Operator
from bpy.props import *
from bpy.utils import register_class, unregister_class

from . import addon, bbox, id, insert, modifier, remove


def authoring_save_pre():
    option = addon.option()

    thumbnail_scene = None
    for scene in bpy.data.scenes:
        if scene.kitops.thumbnail:
            thumbnail_scene = scene

            for obj in thumbnail_scene.collection.all_objects:
                exists = False
                for scn in bpy.data.scenes:
                    if scn == scene:
                        continue

                    if obj.name in scn.collection.all_objects:
                        exists = True
                        continue

                if not exists:
                    obj.kitops.temp = True

            break

    if not thumbnail_scene and bpy.data.filepath != addon.path.thumbnail():
        remove_temp_objects()

    if insert.authoring() and bpy.data.filepath != addon.path.thumbnail():
        for mat in bpy.data.materials:
            mat.kitops.id = id.uuid()

        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass

        for obj in bpy.context.visible_objects:
            obj.kitops.inserted = False

        main = False
        for obj in bpy.data.objects:
            obj.kitops.id = ''
            obj.kitops.author = option.author
            obj.kitops.insert = False
            obj.kitops.applied = False
            obj.kitops.animated = bpy.context.scene.kitops.animated
            obj.kitops.hide = obj not in bpy.context.visible_objects[:]
            obj.kitops['insert_target'] = None
            obj.kitops['mirror_target'] = None
            obj.kitops['reserved_target'] = None
            obj.kitops['main_object'] = None

            if obj.kitops.main:
                main = True

            if obj.data:
                obj.data.kitops.id = id.uuid()
                obj.data.kitops.insert = False

        if main:
            main = [obj for obj in bpy.data.objects if obj.kitops.main][0]

        else:
            bpy.data.objects[0].kitops.main = True
            main = bpy.data.objects[0]

        bpy.context.view_layer.objects.active = main
        main.select_set(True)

        if bpy.context.scene.kitops.auto_parent:
            # bpy.ops.object.visual_transform_apply()

            for obj in bpy.data.objects:
                obj['parent'] = None

            for obj in bpy.data.objects:
                obj.select_set(True)

            try:
                bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            except:
                pass

    elif not insert.authoring():
        for obj in bpy.data.objects:
            if obj.kitops.insert:
                continue

            obj.kitops['insert_target'] = None
            obj.kitops['mirror_target'] = None
            obj.kitops['reserved_target'] = None
            obj.kitops['main_object'] = None


def authoring_load_post():
    option = addon.option()

    scene_objects = bpy.context.scene.collection.all_objects[:]
    for obj in bpy.data.objects:
        if obj not in scene_objects:
            remove_object(obj)

    main = False
    for obj in bpy.data.objects:
        if obj.kitops.main:
            bpy.context.view_layer.objects.active = obj
            main = True
            break

    if not main:
        if bpy.context.active_object:
            bpy.context.active_object.kitops.main = True
        elif len(bpy.data.objects):
            bpy.context.view_layer.objects.active = bpy.data.objects[0]
            bpy.data.objects[0].kitops['main'] = True

    author = False
    for obj in bpy.data.objects:
        if obj.kitops.author and obj.kitops.author != 'Your Name':
            author = obj.kitops.author
            break

    if author:
        option.author = author

    else:
        option.author = addon.preference().author
        for obj in bpy.data.objects:
            obj.kitops.author = addon.preference().author


# XXX: type and reference error
def toggles_depsgraph_update_post():
    option = addon.option()

    solid_inserts = insert.collect(solids=True, all=True)
    count = 0
    for obj in solid_inserts:
        try:
            if obj.hide_viewport:
                option['show_solid_objects'] = False
                break
            elif obj.name in bpy.context.view_layer.objects and not obj.select_get():
                count += 1
        except RuntimeError:
            pass

    if count > 2 and count == len(solid_inserts):
        option['show_solid_objects'] = True

    boolean_inserts = insert.collect(cutters=True, all=True)
    count = 0
    for obj in boolean_inserts:
        try:
            if obj.hide_viewport:
                option['show_cutter_objects'] = False
                break
            elif not obj.select_get():
                count += 1
        except RuntimeError:
            pass

    if count > 2 and count == len(boolean_inserts):
        option['show_cutter_objects'] = True

    wire_inserts = insert.collect(wires=True, all=True)
    count = 0
    for obj in wire_inserts:
        try:
            if obj.hide_viewport:
                option['show_wire_objects'] = False
                break
            elif not obj.select_get():
                count += 1
        except RuntimeError:
            pass

    if count > 2 and count == len(wire_inserts):
        option['show_wire_objects'] = True


def authoring_depsgraph_update_post():
    if len(bpy.data.objects) == 1:
        bpy.data.objects[0].kitops['main'] = True

    for obj in bpy.data.objects:
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE'} and obj.kitops.type != 'WIRE':
            obj.kitops.type = 'WIRE'
        if obj.type != 'MESH' and obj.kitops.type == 'CUTTER' and obj.kitops.type != 'WIRE':
            obj.kitops.type = 'WIRE'
        if obj.kitops.main and obj.kitops.selection_ignore:
            obj.kitops.selection_ignore = False

    if hasattr(bpy, 'context') and bpy.context.scene and bpy.context.scene.kitops.factory:
        for obj in bpy.context.scene.collection.all_objects:
            if not obj.kitops.ground_box:
                continue

            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN' and mod.object:
                    if mod.object.kitops.boolean_type != mod.operation:
                        mod.operation = mod.object.kitops.boolean_type


def insert_depsgraph_update_pre():
    collected_objects = bpy.context.scene.collection.all_objects[:]

    if not hasattr(bpy.context, 'visible_objects'):
        return

    if bpy.context.scene and not bpy.context.scene.kitops.thumbnail:
        for obj in bpy.context.visible_objects:
            for mod in obj.modifiers:
                if mod.type != 'BOOLEAN':
                    continue

                if mod.object and mod.object not in collected_objects:
                    obj.modifiers.remove(mod)

    if addon.preference().mode != 'SMART':
        return

    if not insert.operator:
        insert.show_solid_objects()
        insert.show_cutter_objects()
        insert.show_wire_objects()

    objects = [
        obj for obj in collected_objects if not obj.kitops.insert and obj.type == 'MESH']
    inserts = [obj for obj in sorted(
        collected_objects, key=lambda o: o.name) if obj.kitops.insert and not obj.kitops.applied]

    for ins in inserts:
        if ins.kitops.type == 'CUTTER' and ins.kitops.insert_target:
            available = False
            for mod in ins.kitops.insert_target.modifiers:
                if mod.type == 'BOOLEAN' and mod.object == ins:
                    available = True

                    break

            if not available and ins.kitops.boolean_type != 'INSERT':
                insert.add_boolean(ins)

        if ins.kitops.type != 'CUTTER':
            continue

        for obj in objects:
            for mod in obj.modifiers:
                if mod.type != 'BOOLEAN':
                    continue

                if mod.object == obj and obj != obj.kitops.insert_target and obj.kitops.boolean_type != 'INSERT':
                    obj.modifiers.remove(mod)


def new_empty():
    empty = bpy.data.objects.new('KIT OPS Mirror Target', None)
    empty.location = bpy.context.active_object.kitops.insert_target.location
    empty.empty_display_size = 0.01

    bpy.data.collections['INSERTS'].objects.link(empty)

    return empty


def add_mirror(obj, axis='X'):
    obj.kitops.mirror = True
    mod = obj.modifiers.new(name='KIT OPS Mirror', type='MIRROR')

    if mod:
        mod.show_expanded = False
        mod.use_axis[0] = False

        index = {'X': 0, 'Y': 1, 'Z': 2}  # patch inplace for api change
        mod.use_axis[index[axis]] = getattr(
            obj.kitops, F'mirror_{axis.lower()}')

        mod.mirror_object = obj.kitops.insert_target
        obj.kitops.mirror_target = obj.kitops.insert_target


def validate_mirror(inserts, axis='X'):
    for obj in inserts:
        if obj.kitops.mirror:

            available = False
            # assuming our mirror is most recent
            for modifier in reversed(obj.modifiers):

                if modifier.type == 'MIRROR' and modifier.mirror_object == obj.kitops.mirror_target:
                    available = True
                    # patch inplace for api change
                    index = {'X': 0, 'Y': 1, 'Z': 2}
                    modifier.use_axis[index[axis]] = getattr(
                        obj.kitops, F'mirror_{axis.lower()}')

                    if True not in modifier.use_axis[:]:
                        obj.kitops.mirror = False
                        obj.kitops.mirror_target = None
                        obj.modifiers.remove(modifier)

                    break

            if not available:
                add_mirror(obj, axis=axis)

        else:
            add_mirror(obj, axis=axis)


def apply_booleans(inserts):
    targets = []
    for obj in inserts:
        if obj.kitops.insert_target not in targets:
            targets.append(obj.kitops.insert_target)

    for target in targets:
        duplicate = target.copy()
        duplicate.data = target.data.copy()

        target_inserts = []
        for modifier in duplicate.modifiers:
            if modifier.type == 'BOOLEAN' and modifier.object and modifier.object in inserts and modifier.object.kitops.boolean_type != 'INSERT':
                target_inserts.append(modifier.object)

        duplicate.modifiers.clear()

        for obj in target_inserts:
            obj.kitops['insert_target'] = duplicate

        duplicate.data = bpy.data.meshes.new_from_object(
            duplicate.evaluated_get(bpy.context.evaluated_depsgraph_get()))

        old_data = bpy.data.meshes[target.data.name]
        name = old_data.name

        target.data = duplicate.data
        target.data.name = name

        duplicate.data = old_data
        remove_object(duplicate)


def remove_booleans(inserts, targets=[], clear_target=False):
    for obj in inserts:
        if obj.kitops.insert_target and obj.kitops.insert_target not in targets:
            targets.append(obj.kitops.insert_target)

    for target in targets:
        for modifier in target.modifiers:
            if modifier.type == 'BOOLEAN' and modifier.object and modifier.object in inserts and modifier.object.kitops.boolean_type != 'INSERT':
                target.modifiers.remove(modifier)

    if clear_target:
        for obj in inserts:
            obj.kitops['insert_target'] = None


def clear(inserts):
    for obj in inserts:
        obj.kitops.insert = False
        obj.kitops['insert_target'] = None
        obj.kitops['main_object'] = None
        obj.kitops['reserved_target'] = None
        obj.kitops['mirror_target'] = None


def delete(inserts):
    for obj in inserts:
        remove_object(obj)


class KO_OT_apply_insert(Operator):
    bl_idname = 'ko.apply_insert'
    bl_label = 'Apply'
    bl_description = 'Apply selected INSERTS\n  Shift - Apply modifiers\n'
    bl_options = {'UNDO'}

    def invoke(self, context, event):

        inserts = insert.collect(context.selected_objects)

        if event.shift:
            apply_booleans(inserts)

        clear(inserts)

        return {'FINISHED'}


def link_object_to(bpy_type, obj, children=False):
    if children:
        for child in obj.children:
            link_object_to(bpy_type, child, children=True)

    if hasattr(bpy_type, 'collection') and obj.name not in bpy_type.collection.all_objects:
        bpy_type.collection.objects.link(obj)

        return

    if obj.name not in bpy_type.objects:
        bpy_type.objects.link(obj)


def bool_objects(obj):
    bools = []
    for mod in obj.modifiers:
        if mod.type != 'BOOLEAN' or not mod.object:
            continue
        bools.append(mod.object)
        for ob in bool_objects(mod.object):
            bools.append(ob)

    return list(set(bools))


# original_materials = {}
def new_factory_scene(context, link_selected=False, link_children=False, duplicate=False, material_base=False):
    # global original_materials
    preference = addon.preference()
    path = addon.path.thumbnail()

    def strip_num(string): return string.rstrip(
        '0123456789.') if len(string.split('.')) == 2 else string

    context.window_manager.kitops.author = preference.author

    original = bpy.data.scenes[context.scene.name]
    active_name = context.active_object.name
    material = context.active_object.active_material
    materials = [
        slot.material for slot in context.active_object.material_slots if slot.material]

    insert = []
    bools = []
    if not material_base:
        for obj in context.selected_objects[:]:
            insert.append(obj)
            insert.extend(bool_objects(obj))
            bools.extend(bool_objects(obj))

            # if hasattr(obj, 'material_slots'):
            #     original_materials[obj.name] = [slot.material.name for slot in obj.material_slots if slot.material]

        for obj in insert:
            insert.extend([o for o in bpy.data.objects if o.parent == obj])

        # for obj in bpy.data.objects:
        #     if obj.parent in context.visible_objects[:]:
        #         insert.append(obj)

    insert = sorted(list(set(insert)), key=lambda o: o.name)
    bools = sorted(bools, key=lambda o: o.name)

    with bpy.data.libraries.load(path) as (blend, imported):
        imported.scenes = blend.scenes
        imported.objects = blend.objects

    objects = imported.objects[:]
    scene = imported.scenes[0]

    if material_base:
        with bpy.data.libraries.load(addon.path.material()) as (blend, imported):
            imported.objects = blend.objects

        objects.append(*imported.objects)  # should only ever be one object

    scene.name = 'KITOPS FACTORY'
    scene.kitops.factory = True
    scene.kitops.thumbnail = True
    context.window.scene = scene

    context.scene.kitops.last_edit = ''

    for obj in objects:
        obj.kitops.id = ''
        obj.kitops.insert = False
        obj.kitops.insert_target = None
        obj.kitops.main = False
        obj.kitops.temp = True
        obj.select_set(False)

        if obj.kitops.material_base:
            obj.kitops.temp = False
            link_object_to(scene, obj)
            context.view_layer.objects.active = obj
            context.window_manager.kitops.insert_name = material.name

            for mat in materials:
                mat.kitops.id = id.uuid()
                mat.kitops.material = True
                obj.data.materials.append(mat)

    if link_selected:
        for obj in insert:
            link_object_to(scene, obj)
            obj.hide_set(False)
            obj.kitops.duplicate = duplicate

            if obj in bools:
                obj.kitops.duplicate = duplicate
                if not duplicate:
                    obj.kitops.type = 'CUTTER'
                    obj.kitops.boolean_type = 'INSERT'
                else:
                    obj.kitops.bool_duplicate = True

            for ob in bpy.data.objects:
                if not hasattr(ob, 'modifiers'):
                    continue

                for mod in ob.modifiers:
                    if mod.type != 'BOOLEAN' or mod.object != obj or mod.object not in insert or mod.object in bools:
                        continue

                    mod.object.kitops.type = 'CUTTER'

            if obj.name == active_name:
                context.view_layer.objects.active = obj
                obj.kitops.main = True

    for obj in context.visible_objects:
        if not obj.kitops.temp or obj.kitops.material_base:
            obj.select_set(True)

    if duplicate:
        bpy.ops.object.duplicate()

        for obj in insert:
            obj.kitops.duplicate = False

        for obj in bools:
            obj.kitops.duplicate
            obj.kitops.bool_duplicate = False

        bpy.ops.object.delete({'selected_objects': insert + bools})

        duplicates = [
            obj for obj in scene.collection.all_objects if not obj.kitops.temp]
        bases = [obj for obj in duplicates if not obj.kitops.bool_duplicate]

        for obj in duplicates:
            obj.kitops.duplicate = False
            if obj.parent in insert:
                for ob in bases:
                    for mod in ob.modifiers:
                        if mod.type != 'BOOLEAN' or not mod.object or mod.object != obj:
                            continue

                        obj['parent'] = ob

            if obj.kitops.bool_duplicate:
                obj.kitops.type = 'CUTTER'
                obj.kitops.boolean_type = 'INSERT'
            elif obj.kitops.type != 'CUTTER':
                obj.kitops.type = 'SOLID'
            else:
                obj.kitops.type = 'CUTTER'

            if hasattr(obj, 'data') and obj.data:
                obj.data = obj.data.copy()

            if strip_num(obj.name) == active_name:
                context.view_layer.objects.active = obj

            obj.kitops.bool_duplicate = True

        del insert
        del bools
        del duplicates
        del bases

    for obj in context.visible_objects:
        if not obj.kitops.temp or obj.kitops.material_base:
            obj.select_set(True)

    for obj in context.scene.collection.all_objects:
        if obj.kitops.temp and obj.type == 'CAMERA':
            context.scene.camera = obj

    scene.kitops.original_scene = original.name
    return original, scene


class KO_OT_edit_insert_confirm(Operator):
    bl_idname = 'ko.edit_insert_confirm'
    bl_label = 'Lose unsaved changes?'
    bl_description = 'Edit the active KITOPS INSERT'

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        return KO_OT_edit_insert.execute(self, context)


class KO_OT_edit_insert(Operator):
    bl_idname = 'ko.edit_insert'
    bl_label = 'Edit INSERT'
    bl_description = 'Edit the active KITOPS INSERT'

    # @classmethod
    # def poll(cls, context):
    #     return not bpy.data.is_dirty or bpy.data.filepath

    def invoke(self, context, event):
        if bpy.data.is_dirty:
            return bpy.ops.ko.edit_insert_confirm('INVOKE_DEFAULT')
        return self.execute(context)

    def execute(self, context):
        option = context.window_manager.kitops
        path = option.kpack.categories[option.kpack.active_index].blends[
            option.kpack.categories[option.kpack.active_index].active_index].location
        bpy.ops.wm.open_mainfile(filepath=path)

        return {'FINISHED'}


class create_insert():
    bl_options = {'INTERNAL'}

    duplicate: BoolProperty(default=False)
    material: BoolProperty(default=False)
    children: BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        return context.active_object and context.selected_objects

    def invoke(self, context, event):
        bpy.ops.object.mode_set(mode='OBJECT')

        if not self.duplicate and not self.material:
            self.duplicate = not event.ctrl

        new_factory_scene(context, link_selected=not self.material, link_children=self.children,
                          duplicate=self.duplicate and not self.material, material_base=self.material)

        bpy.ops.view3d.camera_to_view_selected()

        return {'FINISHED'}

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')

        # if not self.duplicate and not self.material:
        #     self.duplicate = not event.ctrl

        new_factory_scene(context, link_selected=not self.material, link_children=self.children,
                          duplicate=self.duplicate and not self.material, material_base=self.material)

        bpy.ops.view3d.camera_to_view_selected()

        return {'FINISHED'}

class KO_OT_create_insert(Operator, create_insert):
    bl_idname = 'ko.create_insert'
    bl_label = 'Create INSERT'
    bl_description = ('Create INSERT.\n\n'
                      '  Ctrl - Link selected objects')


class KO_OT_create_insert_material(Operator, create_insert):
    bl_idname = 'ko.create_insert_material'
    bl_label = 'Create Material INSERT'
    bl_description = 'Create new material and thumbnail from active object\'s active material'

    @classmethod
    def poll(cls, context):
        return create_insert.poll(context) and context.active_object.active_material


def directory_from(kpack):
    current = kpack.categories[kpack.active_index]
    return os.path.realpath(os.path.dirname(current.blends[current.active_index].location))


def insert_path(context):
    insert_name = context.window_manager.kitops.insert_name
    file_name = '_'.join(insert_name.split(' ')) + '.blend'
    directory = directory_from(context.window_manager.kitops.kpack)

    return os.path.join(directory, file_name)


def set_active_category_from_last_edit(context):
    bpy.ops.ko.refresh_kpacks()
    option = context.window_manager.kitops

    kpack = context.window_manager.kitops.kpack
    for ic, category in enumerate(kpack.categories):
        for ib, blend in enumerate(category.blends):
            if os.path.realpath(blend.location) != context.scene.kitops.last_edit:
                continue

            option.kpacks = category.name
            option.kpack.active_index = ic
            current = option.kpack.categories[category.name]
            current.active_index = ib
            current.thumbnail = blend.name

            break


def remove_temp_objects(duplicates=False):
    print('')
    # material_base = False
    for obj in bpy.data.objects:
        # if not material_base and obj.kitops.material_base:
        #     material_base = True
        if obj.data and hasattr(obj.data, 'materials'):
            for mat in obj.data.materials:
                if mat and 'KITOPS FACTORY' in mat.name:
                    print(
                        F'        KITOPS: Removing material datablock: {mat.name}')
                    bpy.data.materials.remove(mat)

        if obj.kitops.temp or (duplicates and (obj.kitops.duplicate or obj.kitops.bool_duplicate)) or 'KITOPS FACTORY' in obj.name or obj.kitops.material_base:
            print(F'        KITOPS: Removing object datablock: {obj.name}')
            remove_object(obj)

            continue

    if bpy.app.version[-1] > 83:
        for lib in bpy.data.libraries:
            if lib.filepath in {addon.path.render(), addon.path.material()}:
                bpy.data.libraries.remove(lib)


def save_file(context, path=''):
    versions = context.preferences.filepaths.save_version
    context.preferences.filepaths.save_version = 0

    try:
        bpy.ops.wm.save_mainfile(filepath=os.path.realpath(
            path) if path else bpy.data.filepath)
        bpy.ops.wm.save_mainfile()
    except:
        print(f'KITOPS: Save file exception{(" @" + path) if path else ""}')

    context.preferences.filepaths.save_version = versions


def save_insert(path='', objects=[]):
    context = bpy.context

    path = insert_path(context) if not path else path
    path = os.path.realpath(path)

    scene = bpy.data.scenes.new(name='main')
    scene.kitops.animated = context.scene.kitops.animated

    objs = objects if objects else [
        obj for obj in context.scene.collection.all_objects if not obj.kitops.temp]

    was_duplicate = False

    for obj in objs:
        link_object_to(scene, obj)

        obj.kitops.id = ''
        obj.kitops.author = context.window_manager.kitops.author
        obj.kitops.insert = False
        obj.kitops.applied = False
        obj.kitops.animated = scene.kitops.animated
        obj.kitops['insert_target'] = None
        obj.kitops['mirror_target'] = None
        obj.kitops['reserved_target'] = None
        obj.kitops['main_object'] = None

        if obj.kitops.duplicate:
            was_duplicate = True
            obj.kitops.duplicate = False

        if hasattr(obj, 'data') and obj.data:
            obj.data.kitops.id = id.uuid()
            obj.data.kitops.insert = False

        # if hasattr(obj, 'data') and obj.data and hasattr(obj.data, 'materials'):
            # for mat in obj.data.materials:
        if hasattr(obj, 'material_slots'):
            for slot in obj.material_slots:
                if slot.material and 'KITOPS FACTORY' in slot.material.name:
                    obj.active_material_index = 0
                    for _ in range(len(obj.material_slots)):
                        bpy.ops.object.material_slot_remove({'object': obj})

                    break

        if obj.kitops.material_base:
            obj.kitops.material_base = False
            for slot in reversed(obj.material_slots[:]):
                if slot.material and slot.material.name.rstrip('0123456789.') == 'Material':
                    slot.material.name = context.window_manager.kitops.insert_name

    bpy.data.libraries.write(path, {scene}, compress=True)
    import subprocess
    subprocess.Popen([bpy.app.binary_path, '-b', path, '--python',
                      os.path.join(addon.path(), 'addon', 'utility', 'save.py')])

    bpy.data.scenes.remove(scene)

    for obj in objs:
        obj.kitops.type = obj.kitops.type
        if was_duplicate:
            obj.kitops.duplicate = True

    context.scene.kitops.last_edit = path
    bpy.ops.ko.refresh_kpacks()
    set_active_category_from_last_edit(context)


class KO_OT_save_as_insert(Operator):
    bl_idname = 'ko.save_as_insert'
    bl_label = 'Save INSERT'
    bl_description = 'Save the INSERT'
    bl_options = {'INTERNAL'}

    hide_props_region: BoolProperty(default=True, options={'HIDDEN'})
    filter_folder: BoolProperty(default=True, options={'HIDDEN'})
    filter_blender: BoolProperty(default=True, options={'HIDDEN'})
    check_existing: BoolProperty(default=True, options={'HIDDEN'})

    filepath: StringProperty(
        name='File Path',
        description='File path used for saving INSERT\'s',
        maxlen=1024,
        subtype='FILE_PATH')

    def check(self, conext):
        filepath = self.filepath

        if os.path.basename(filepath):
            filepath = bpy.path.ensure_ext(filepath, '.blend')

            if filepath != self.filepath:
                self.filepath = filepath

        return filepath

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = insert_path(context)

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        save_insert(path=self.filepath)
        return {'FINISHED'}


class KO_OT_save_insert(Operator):
    bl_idname = 'ko.save_insert'
    bl_label = 'Save INSERT'
    bl_description = 'Save the INSERT'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.window_manager.kitops.insert_name

    def invoke(self, context, event):
        local_factory = not context.scene.kitops.factory

        if local_factory:
            save_file(context)
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath, load_ui=True)

            self.report({'INFO'}, F'Saved Insert: {bpy.data.filepath}')
            return {'FINISHED'}

        if not context.scene.kitops.last_edit or event.ctrl:
            bpy.ops.ko.save_as_insert('INVOKE_DEFAULT')

            return {'FINISHED'}

        save_insert()

        return {'FINISHED'}


class KO_OT_create_snapshot(Operator):
    bl_idname = 'ko.create_snapshot'
    bl_label = 'Create Snapshot'
    bl_description = 'Uses the current camera and scene settings to create a snapshot'

    def execute(self, context):
        original_path = context.scene.render.filepath
        path = context.scene.kitops.last_edit[:-
                                              5] if context.scene.kitops.last_edit else bpy.data.filepath[:-5]

        if not path:
            self.report(
                {'WARNING'}, 'Unable to save rendered thumbnail, no reference PATH (Save your file first?)')
            return {'FINISHED'}

        if not context.scene.camera:
            for obj in context.scene.collection.all_objects:
                if obj.kitops.temp and obj.type == 'CAMERA':
                    context.scene.camera = obj

                    break

        context.scene.render.filepath = path + 'png'
        bpy.ops.render.render(write_still=True)

        context.scene.render.filepath = original_path
        bpy.ops.ko.refresh_kpacks()

        return {'FINISHED'}


def remove_object(obj):
    collection_lookup = {
        "ARMATURE": bpy.data.armatures,
        "CAMERA": bpy.data.cameras,
        "CURVE": bpy.data.curves,
        "FONT": bpy.data.curves,
        "GPENCIL": bpy.data.grease_pencils,
        "LATTICE": bpy.data.lattices,
        "LIGHT": bpy.data.lights,
        "LIGHT_PROBE": bpy.data.lightprobes,
        "MESH": bpy.data.meshes,
        "SPEAKER": bpy.data.speakers,
        "SURFACE": bpy.data.curves,
        "VOLUME": bpy.data.volumes}

    if obj.type in collection_lookup:
        print(
            F'        KITOPS: Removing {obj.type.lower()} datablock: {obj.data.name}')
        collection_lookup[obj.type].remove(obj.data)

    if obj in bpy.data.objects[:]:
        print(F'        KITOPS: Removing object datablock: {obj.name}')
        bpy.data.objects.remove(obj)


class KO_OT_close_factory_scene(Operator):
    bl_idname = 'ko.close_factory_scene'
    bl_label = 'Close FACTORY Scene'
    bl_description = 'Exit the FACTORY Scene'
    bl_options = {'UNDO'}

    def execute(self, context):
        try:
            original_scene = bpy.data.scenes[context.scene.kitops.original_scene]
        except:
            original_scene = None

        if not original_scene:
            context.scene.name = 'Scene'
            context.scene.kitops.factory = False
            remove_temp_objects()
            return {'FINISHED'}

        remove_temp_objects(duplicates=True)

        if original_scene:
            bpy.data.scenes.remove(bpy.data.scenes[context.scene.name])
            context.window.scene = original_scene

        return {'FINISHED'}


class KO_OT_close_thumbnail_scene(Operator):
    bl_idname = 'ko.close_thumbnail_scene'
    bl_label = 'Close THUMBNAIL Scene'
    bl_description = 'Exit the THUMBNAIL Scene'
    bl_options = {'UNDO'}

    def execute(self, context):
        remove_temp_objects(duplicates=True)

        bpy.data.scenes.remove(context.scene)

        return {'FINISHED'}


class KO_OT_remove_insert(Operator):
    bl_idname = 'ko.remove_insert'
    bl_label = 'Delete'
    bl_description = 'Remove selected INSERTS\n  Shift - KITOPS properties only'
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        inserts = insert.collect(context.selected_objects)

        if not event.shift:
            for obj in inserts:
                for o in bpy.data.objects:
                    for modifier in o.modifiers:
                        if modifier.type == 'BOOLEAN' and modifier.object == obj:
                            o.modifiers.remove(modifier)

            for obj in inserts:
                remove_object(obj)

        else:
            clear(inserts)

        return {'FINISHED'}


# TODO: render scene needs to be the kpack render scene if any
# TODO: progress report update
class KO_OT_render_thumbnail(Operator):
    bl_idname = 'ko.render_thumbnail'
    bl_label = 'Render thumbnail'
    bl_description = 'Render and save a thumbnail for this INSERT.\n  Shift - Import thumbnail scene\n  Ctrl - Render all thumbnails for the current working directory\n  Alt - Scale fitting\n\n  Use system console to see progress (Window > Toggle system console)'
    bl_options = {'INTERNAL'}

    render: BoolProperty(default=False)
    import_scene: BoolProperty(default=False)
    max_dimension = 1.8
    skip_scale = False

    def invoke(self, context, event):
        preference = addon.preference()
        init_active = bpy.data.objects[context.active_object.name]
        init_scene = bpy.data.scenes[context.scene.name]
        init_objects = bpy.data.objects[:]
        duplicates = []
        parents = []
        self.skip_scale = not event.alt

        if not self.import_scene:
            self.import_scene = event.shift

        if not self.render:

            print('\nKIT OPS beginning thumbnail rendering')
            preference.mode = 'SMART'

            with bpy.data.libraries.load(addon.path.thumbnail()) as (blend, imported):
                print('\tImported thumbnail rendering scene')
                imported.scenes = blend.scenes
                imported.materials = blend.materials

            scene = imported.scenes[0]
            scene.kitops.thumbnail = True
            context.window.scene = scene

            for obj in scene.collection.objects:
                obj.select_set(False)
                obj.kitops.temp = True

            floor = [
                obj for obj in context.scene.collection.all_objects if obj.kitops.ground_box][0]

            for obj in sorted(init_objects, key=lambda o: o.name):
                duplicate = obj.copy()
                duplicate.name = 'ko_duplicate_{}'.format(obj.name)
                if duplicate.type != 'EMPTY':
                    duplicate.data = obj.data.copy()

                duplicates.append(duplicate)
                parents.append((duplicate, obj.parent))

                context.scene.collection.objects.link(duplicate)

                duplicate.kitops.insert = True
                duplicate.kitops.id = 'tmp'
                duplicate.kitops.applied = False
                duplicate.kitops['insert_target'] = floor
                duplicate.kitops.duplicate = True

                duplicate.select_set(True)
                duplicate.hide_viewport = False

                if duplicate.kitops.type == 'CUTTER' and duplicate.kitops.boolean_type == 'UNION':
                    duplicate.data.materials.clear()
                    duplicate.data.materials.append(
                        floor.material_slots[1].material)

                elif duplicate.kitops.type == 'CUTTER' and duplicate.kitops.boolean_type in {'DIFFERENCE', 'INTERSECT'}:
                    duplicate.data.materials.clear()
                    duplicate.data.materials.append(
                        floor.material_slots[2].material)

                elif duplicate.type in {'MESH', 'CURVE', 'SURFACE', 'FONT'}:
                    if not len(duplicate.data.materials):
                        duplicate.data.materials.append(
                            floor.material_slots[3].material)

            context.view_layer.update()
            modifier.sort(floor)

            print('\tDuplicated objects from initial scene')
            print('\tConverted duplicates into a temporary insert')
            print('\nUpdated:')
            print('\tInsert materials')

            for duplicate, parent in parents:
                if parent and 'ko_duplicate_{}'.format(parent.name) in [duplicate.name for duplicate in duplicates]:
                    duplicate['parent'] = bpy.data.objects['ko_duplicate_{}'.format(
                        parent.name)]

            print('\tInsert parenting')

            main = [duplicate for duplicate in duplicates if duplicate.kitops.main][0]
            context.view_layer.objects.active = main
            bpy.ops.view3d.view_camera()
            dimension = main.dimensions

            if not self.skip_scale:
                axis = 'x'
                if dimension.y > dimension.x:
                    axis = 'y'
                if dimension.z > getattr(dimension, axis):
                    axis = 'z'

                setattr(dimension, axis, self.max_dimension)

                remaining_axis = [a for a in 'xyz' if a != axis]
                setattr(main.scale, remaining_axis[0], getattr(
                    main.scale, axis))
                setattr(main.scale, remaining_axis[1], getattr(
                    main.scale, axis))

                print('\tInsert size (max dimension of {})'.format(
                    self.max_dimension))

            context.scene.render.filepath = bpy.data.filepath[:-6] + '.png'
            print('\tRender path: {}'.format(context.scene.render.filepath))

            if self.import_scene:
                bpy.ops.object.convert(target='MESH')

            else:
                print('\nRendering...')
                bpy.ops.render.render(write_still=True)

            if not self.import_scene and not event.ctrl:

                print('Cleaning up\n')
                for obj in duplicates:
                    remove_object(obj)

                context.window.scene = init_scene

                for scene in imported.scenes:
                    for obj in scene.collection.objects:
                        remove_object(obj)

                    bpy.data.scenes.remove(scene, do_unlink=True)

                for material in imported.materials:
                    bpy.data.materials.remove(
                        material, do_unlink=True, do_id_user=True, do_ui_user=True)

                context.view_layer.objects.active = init_active

                for obj in init_scene.collection.objects:
                    obj.select_set(True)
                    obj.hide_viewport = False

                print('Finished\n')

            if not self.import_scene and event.ctrl:

                print('KITOPS: Removing insert')
                for obj in duplicates:
                    remove_object(obj)

                working_directory = os.path.abspath(
                    os.path.join(bpy.data.filepath, '..'))
                print('\n\nBeginning batch rendering in {}\n'.format(
                    working_directory))
                for file in os.listdir(working_directory):
                    if file.endswith('.blend') and os.path.join(working_directory, file) != bpy.data.filepath:
                        location = os.path.join(working_directory, file)

                        with bpy.data.libraries.load(location) as (blend, imported):
                            print('\nImported objects from {}'.format(location))
                            imported.scenes = blend.scenes
                            imported.materials = blend.materials

                        scene = [
                            scene for scene in imported.scenes if not scene.kitops.thumbnail][0]

                        if not len(scene.collection.objects):
                            print('Invalid file... skipping\n')
                            continue

                        elif not len([obj for obj in scene.collection.objects if obj.kitops.main]):
                            print('Invalid file... skipping\n')
                            continue

                        for obj in sorted(scene.collection.all_objects, key=lambda o: o.name):
                            context.scene.collection.objects.link(obj)

                            obj.kitops.insert = True
                            obj.kitops.id = 'tmp'
                            obj.kitops.applied = False
                            obj.kitops['insert_target'] = floor
                            obj.kitops.temp = True

                            obj.select_set(True)
                            obj.hide_viewport = False

                            if obj.kitops.type == 'CUTTER' and obj.kitops.boolean_type == 'UNION':
                                obj.data.materials.clear()
                                obj.data.materials.append(
                                    bpy.data.materials['ADD'])

                            elif obj.kitops.type == 'CUTTER' and obj.kitops.boolean_type in {'DIFFERENCE', 'INTERSECT'}:
                                obj.data.materials.clear()
                                obj.data.materials.append(
                                    bpy.data.materials['SUB'])

                            elif obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT'}:
                                if not len(obj.data.materials):
                                    obj.data.materials.append(
                                        floor.material_slots[3].material)

                        context.view_layer.update()
                        modifier.sort(floor)

                        print('\nUpdated:')
                        print('\tInsert target: {}'.format(floor.name))
                        print('\tInsert materials')

                        main = [
                            obj for obj in context.scene.collection.all_objects if obj.kitops.main][0]
                        dimension = main.dimensions

                        if not self.skip_scale:
                            axis = 'x'
                            if dimension.y > dimension.x:
                                axis = 'y'
                            if dimension.z > getattr(dimension, axis):
                                axis = 'z'

                            setattr(dimension, axis, self.max_dimension)

                            remaining_axis = [a for a in 'xyz' if a != axis]
                            setattr(main.scale, remaining_axis[0], getattr(
                                main.scale, axis))
                            setattr(main.scale, remaining_axis[1], getattr(
                                main.scale, axis))

                            print('\tInsert size (max dimension of {})'.format(
                                self.max_dimension))

                        context.scene.render.filepath = location[:-6] + '.png'
                        print('\tRender path: {}'.format(
                            context.scene.render.filepath))
                        # context.view_layer.depsgraph.update()
                        context.area.tag_redraw()

                        print('\nRendering...')
                        bpy.ops.render.render(write_still=True)

                        print('Cleaning up\n')
                        for scene in imported.scenes:
                            for obj in scene.collection.objects:
                                remove_object(obj)

                            bpy.data.scenes.remove(scene, do_unlink=True)

                        for material in imported.materials:
                            bpy.data.materials.remove(
                                material, do_unlink=True, do_id_user=True, do_ui_user=True)

                else:
                    context.window.scene = init_scene

                    try:
                        for scene in imported.scenes:
                            for obj in scene.collection.objects:
                                remove_object(obj)

                        bpy.data.scenes.remove(scene, do_unlink=True)

                        for material in imported.materials:
                            bpy.data.materials.remove(
                                material, do_unlink=True, do_id_user=True, do_ui_user=True)
                    except ReferenceError:
                        pass

                    context.view_layer.objects.active = init_active

                    for obj in init_scene.collection.objects:
                        obj.select_set(True)
                        obj.hide_viewport = False

                    print('Finished\n')

        else:
            bpy.ops.render.render(write_still=True)

        return {'FINISHED'}


# XXX: align needs to check dimensions with current insert disabled
class KO_OT_align_horizontal(Operator):
    bl_idname = 'ko.align_horizontal'
    bl_label = 'Align horizontal'
    bl_description = 'Align selected INSERTS horizontally within target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    y_axis: BoolProperty(
        name='Y Axis',
        description='Use the y axis of the INSERT TARGET for alignment',
        default=False)

    def execute(self, context):

        # get mains
        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                center = bbox.center(main.kitops.insert_target)
                setattr(main.location, 'y' if self.y_axis else 'x',
                        getattr(center, 'y' if self.y_axis else 'x'))

        return {'FINISHED'}


class KO_OT_align_vertical(Operator):
    bl_idname = 'ko.align_vertical'
    bl_label = 'Align vertical'
    bl_description = 'Align selected INSERTS vertically within target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    z_axis: BoolProperty(
        name='Z Axis',
        description='Use the Z axis of the INSERT TARGET for alignment',
        default=False)

    def execute(self, context):

        # get mains
        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                center = bbox.center(main.kitops.insert_target)
                setattr(main.location, 'z' if self.z_axis else 'y',
                        getattr(center, 'z' if self.z_axis else 'y'))

        return {'FINISHED'}


class KO_OT_align_left(Operator):
    bl_idname = 'ko.align_left'
    bl_label = 'Align left'
    bl_description = 'Align selected INSERTS to the left of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    y_axis: BoolProperty(
        name='Y Axis',
        description='Use the y axis of the INSERT TARGET for alignment',
        default=False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                left = bbox.back(main.kitops.insert_target).y if self.y_axis else bbox.left(
                    main.kitops.insert_target).x
                setattr(main.location, 'y' if self.y_axis else 'x', left)

        return {'FINISHED'}


class KO_OT_align_right(Operator):
    bl_idname = 'ko.align_right'
    bl_label = 'Align right'
    bl_description = 'Align selected INSERTS to the right of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    y_axis: BoolProperty(
        name='Y Axis',
        description='Use the y axis of the INSERT TARGET for alignment',
        default=False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                right = bbox.front(main.kitops.insert_target).y if self.y_axis else bbox.right(
                    main.kitops.insert_target).x
                setattr(main.location, 'y' if self.y_axis else 'x', right)

        return {'FINISHED'}


class KO_OT_align_top(Operator):
    bl_idname = 'ko.align_top'
    bl_label = 'Align top'
    bl_description = 'Align selected INSERTS to the top of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    z_axis: BoolProperty(
        name='Z Axis',
        description='Use the Z axis of the INSERT TARGET for alignment',
        default=False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                top = bbox.top(main.kitops.insert_target).z if self.z_axis else bbox.back(
                    main.kitops.insert_target).y
                setattr(main.location, 'z' if self.z_axis else 'y', top)

        return {'FINISHED'}


class KO_OT_align_bottom(Operator):
    bl_idname = 'ko.align_bottom'
    bl_label = 'Align bottom'
    bl_description = 'Align selected INSERTS to the bottom of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    z_axis: BoolProperty(
        name='Z Axis',
        description='Use the Z axis of the INSERT TARGET for alignment',
        default=False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                bottom = bbox.bottom(main.kitops.insert_target).z if self.z_axis else bbox.front(
                    main.kitops.insert_target).y
                setattr(main.location, 'z' if self.z_axis else 'y', bottom)

        return {'FINISHED'}


class KO_OT_stretch_wide(Operator):
    bl_idname = 'ko.stretch_wide'
    bl_label = 'Stretch wide'
    bl_description = 'Stretch selected INSERTS to the width of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    y_axis: BoolProperty(
        name='X axis',
        description='Use the Y axis of the INSERT TARGET for stretching',
        default=False)

    halve: BoolProperty(
        name='Halve',
        description='Halve the stretch amount',
        default=False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                dimension = main.kitops.insert_target.dimensions[1 if self.y_axis else 0]

                if self.halve:
                    dimension /= 2

                main.scale.x = dimension / main.dimensions[0] * main.scale.x

        return {'FINISHED'}


class KO_OT_stretch_tall(Operator):
    bl_idname = 'ko.stretch_tall'
    bl_label = 'Stretch tall'
    bl_description = 'Stretch selected INSERTS to the height of the target bounds'
    bl_options = {'REGISTER', 'UNDO'}

    z_axis: BoolProperty(
        name='Side',
        description='Use the Z axis of the INSERT TARGET for stretching',
        default=False)

    halve: BoolProperty(
        name='Halve',
        description='Halve the stretch amount',
        default=False)

    def execute(self, context):

        mains = insert.collect(context.selected_objects, mains=True)

        for main in mains:
            if main.kitops.insert_target:
                dimension = main.kitops.insert_target.dimensions[2 if self.z_axis else 1]

                if self.halve:
                    dimension /= 2

                main.scale.y = dimension / main.dimensions[1] * main.scale.y

        return {'FINISHED'}


class KO_OT_camera_to_insert(Operator):
    bl_idname = 'ko.camera_to_insert'
    bl_label = 'Camera to INSERT'
    bl_description = 'Align camera to the INSERT'

    @classmethod
    def poll(cls, context):
        return context.scene.kitops.thumbnail

    def execute(self, context):
        # active_object = bpy.data.objects[context.active_object.name]
        selected_objects = context.selected_objects[:]
        objects = context.scene.collection.all_objects[:]
        # other_scene_objects = [scene for scene in bpy.data.scenes[:] if not scene.kitops.thumbnail][0].collection.all_objects[:]

        for obj in objects:
            if obj.kitops.temp:
                obj.select_set(False)
                continue

            obj.select_set(True)

        for obj in objects:
            if obj.kitops.material_base:
                obj.select_set(True)

        bpy.ops.view3d.camera_to_view_selected()

        for obj in objects:
            if obj in selected_objects:
                obj.select_set(True)
                continue

            obj.select_set(False)

        return {'FINISHED'}


class update:
    def main(prop, context):
        for obj in bpy.data.objects:
            if obj != context.active_object:
                obj.kitops['main'] = False
            else:
                obj.kitops['main'] = True

    def author(prop, context):
        if not hasattr(context, 'active_object'):
            return

        for obj in bpy.data.objects:
            obj.kitops.author = context.active_object.kitops.author

    def type(prop, context):
        # obj = context.active_object
        try:
            ground_box = [
                obj for obj in context.scene.collection.all_objects if obj.kitops.ground_box][0]
        except:
            ground_box = None  # ground box not detected

        # for obj in bpy.data.objects:
        for obj in context.scene.collection.all_objects:
            if obj.kitops.type == 'SOLID' or obj.type == 'GPENCIL':
                obj.display_type = 'SOLID' if obj.type != 'GPENCIL' else 'TEXTURED'

                if obj.type == 'MESH':
                    obj.hide_render = False

                    obj.cycles_visibility.camera = True
                    obj.cycles_visibility.diffuse = True
                    obj.cycles_visibility.glossy = True
                    obj.cycles_visibility.transmission = True
                    obj.cycles_visibility.scatter = True
                    obj.cycles_visibility.shadow = True

            elif (obj.kitops.type == 'WIRE' or obj.kitops.type == 'CUTTER') and obj.type == 'MESH':
                obj.display_type = 'WIRE'

                obj.hide_render = True

                obj.cycles_visibility.camera = False
                obj.cycles_visibility.diffuse = False
                obj.cycles_visibility.glossy = False
                obj.cycles_visibility.transmission = False
                obj.cycles_visibility.scatter = False
                obj.cycles_visibility.shadow = False

        if ground_box and context.scene.kitops.factory:
            mats = [
                slot.material for slot in ground_box.material_slots if slot.material]
            for obj in sorted(context.scene.collection.all_objects, key=lambda o: o.name):
                if obj.kitops.temp or obj.type != 'MESH' or obj.kitops.material_base or obj.kitops.duplicate:
                    continue

                boolean = None
                for mod in ground_box.modifiers:
                    if mod.type == 'BOOLEAN' and mod.object == obj:
                        mod.show_viewport = obj.kitops.type == 'CUTTER' and obj.kitops.boolean_type != 'INSERT'
                        mod.show_render = mod.show_viewport
                        mod.operation = obj.kitops.boolean_type
                        boolean = mod

                if not boolean:
                    mod = ground_box.modifiers.new(
                        name='KITOPS Boolean', type='BOOLEAN')
                    mod.object = obj
                    mod.operation = obj.kitops.boolean_type

                    if hasattr(mod, 'solver'):
                        mod.solver = addon.preference().boolean_solver

                    boolean = mod
                    modifier.sort(ground_box)

                if not obj.material_slots:
                    obj.data.materials.append(
                        ground_box.material_slots[3].material)

                if not obj.material_slots or obj.material_slots[0].material in mats:
                    if obj.kitops.boolean_type == 'UNION':
                        boolean.operation = 'UNION'
                        obj.material_slots[0].material = ground_box.material_slots[1].material

                    elif obj.kitops.boolean_type == 'DIFFERENCE':
                        boolean.operation = 'DIFFERENCE'
                        obj.material_slots[0].material = ground_box.material_slots[2].material

                    else:
                        boolean.operation = 'INTERSECT'

                    if obj.kitops.type != 'CUTTER' or obj.kitops.boolean_type in {'INTERSECT', 'INSERT'}:
                        obj.material_slots[0].material = ground_box.material_slots[3].material

    def insert_target(prop, context):
        inserts = insert.collect(context.selected_objects)

        for obj in inserts:
            obj.kitops.applied = False
            obj.kitops['insert_target'] = context.active_object.kitops.insert_target

            if obj.kitops.insert_target:
                obj.kitops.reserved_target = context.active_object.kitops.insert_target

    def mirror_x(prop, context):
        inserts = insert.collect(context.selected_objects)

        for obj in inserts:
            obj.kitops['mirror_x'] = bpy.context.active_object.kitops.mirror_x

        validate_mirror(inserts, axis='X')

    def mirror_y(prop, context):
        inserts = insert.collect(context.selected_objects)

        for obj in inserts:
            obj.kitops['mirror_y'] = bpy.context.active_object.kitops.mirror_y

        validate_mirror(inserts, axis='Y')

    def mirror_z(prop, context):
        inserts = insert.collect(context.selected_objects)

        for obj in inserts:
            obj.kitops['mirror_z'] = bpy.context.active_object.kitops.mirror_z

        validate_mirror(inserts, axis='Z')


classes = [
    KO_OT_apply_insert,
    KO_OT_edit_insert,
    KO_OT_edit_insert_confirm,
    KO_OT_create_insert,
    KO_OT_create_insert_material,
    KO_OT_save_as_insert,
    KO_OT_save_insert,
    KO_OT_create_snapshot,
    KO_OT_remove_insert,
    KO_OT_close_factory_scene,
    KO_OT_close_thumbnail_scene,
    KO_OT_render_thumbnail,
    KO_OT_camera_to_insert,
    KO_OT_align_horizontal,
    KO_OT_align_vertical,
    KO_OT_align_left,
    KO_OT_align_right,
    KO_OT_align_top,
    KO_OT_align_bottom,
    KO_OT_stretch_wide,
    KO_OT_stretch_tall]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
