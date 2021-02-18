import re

from copy import deepcopy as copy

import bpy

from mathutils import *
from pathlib import Path

from bpy.types import Operator
from bpy.props import *
from bpy.utils import register_class, unregister_class
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .. utility import addon, backup, bbox, dpi, insert, ray, remove, update, view3d

smart_enabled = True
try: from .. utility import smart
except: smart_enabled = False


class KO_OT_purchase(Operator):
    bl_idname = 'ko.purchase'
    bl_label = 'KIT OPS PRO'
    bl_description = 'Buy KIT OPS PRO'

    def execute(self, context):
        # Do nothing, this option should always be disabled in the ui
        return {'FINISHED'}


class KO_OT_store(Operator):
    bl_idname = 'ko.store'
    bl_label = 'Store'
    bl_description = 'Visit the KIT OPS Store'

    def execute(self, context):
        bpy.ops.wm.url_open('INVOKE_DEFAULT', url='https://www.kit-ops.com/the-store')

        return {'FINISHED'}


class KO_OT_documentation(Operator):
    bl_idname = 'ko.documentation'
    bl_label = 'Documentation'
    bl_description = 'View the KIT OPS documentation'

    authoring: BoolProperty(default=False)

    def execute(self, context):
        bpy.ops.wm.url_open('INVOKE_DEFAULT', url='http://cw1.me/kops2docs')

        return {'FINISHED'}


class KO_OT_add_kpack_path(Operator):
    bl_idname = 'ko.add_kpack_path'
    bl_label = 'Add KIT OPS KPACK path'
    bl_description = 'Add a path to a KIT OPS KPACK'

    def execute(self, context):
        preference = addon.preference()

        folder = preference.folders.add()
        folder['location'] = 'Choose Path'

        return {'FINISHED'}


class KO_OT_remove_kpack_path(Operator):
    bl_idname = 'ko.remove_kpack_path'
    bl_label = 'Remove path'
    bl_description = 'Remove path'

    index: IntProperty()

    def execute(self, context):
        preference = addon.preference()

        preference.folders.remove(self.index)

        update.kpack(None, context)

        return {'FINISHED'}


class KO_OT_refresh_kpacks(Operator):
    bl_idname = 'ko.refresh_kpacks'
    bl_label = 'Refresh KIT OPS KPACKS'
    bl_description = 'Refresh KIT OPS KPACKS'

    def execute(self, context):
        update.kpack(None, context)
        return {'FINISHED'}


class KO_OT_next_kpack(Operator):
    bl_idname = 'ko.next_kpack'
    bl_label = 'Next KPACK'
    bl_description = 'Change to the next INSERT\n  Ctrl - Change KPACK'
    bl_options = {'INTERNAL'}


    def invoke(self, context, event):
        option = addon.option()

        if event.ctrl:
            index = option.kpack.active_index + 1 if option.kpack.active_index + 1 < len(option.kpack.categories) else 0

            option.kpacks = option.kpack.categories[index].name

        else:
            category = option.kpack.categories[option.kpack.active_index]
            index = category.active_index + 1 if category.active_index + 1 < len(category.blends) else 0

            category.active_index = index
            category.thumbnail = category.blends[category.active_index].name

        return {'FINISHED'}


class KO_OT_previous_kpack(Operator):
    bl_idname = 'ko.previous_kpack'
    bl_label = 'Previous KPACK'
    bl_description = 'Change to the previous INSERT\n  Ctrl - Change KPACK'
    bl_options = {'INTERNAL'}


    def invoke(self, context, event):
        option = addon.option()

        if event.ctrl:
            index = option.kpack.active_index - 1 if option.kpack.active_index - 1 > -len(option.kpack.categories) else 0

            option.kpacks = option.kpack.categories[index].name

        else:
            category = option.kpack.categories[option.kpack.active_index]
            index = category.active_index - 1 if category.active_index - 1 > -len(category.blends) else 0

            category.active_index = index
            category.thumbnail = category.blends[category.active_index].name

        return {'FINISHED'}


class add_insert():
    bl_options = {'REGISTER', 'UNDO'}

    location: StringProperty(
        name = 'Blend path',
        description = 'Path to blend file')

    material: BoolProperty(name='Material')
    material_link: BoolProperty(name='Link Materials')

    mouse = Vector()
    main = None
    duplicate = None

    data_to = None
    boolean_target = None

    inserts = list()

    init_active = None
    init_selected = list()

    insert_scale = ('LARGE', 'MEDIUM', 'SMALL')

    import_material = None

    @classmethod
    def poll(cls, context):
        return not context.space_data.region_quadviews and not context.space_data.local_view


    def invoke(self, context, event):
        global smart_enabled

        preference = addon.preference()

        insert.operator = self

        self.init_active = bpy.data.objects[context.active_object.name] if context.active_object and context.active_object.select_get() else None
        self.init_selected = [bpy.data.objects[obj.name] for obj in context.selected_objects]

        #TODO: collection helper: collection.add
        if 'INSERTS' not in bpy.data.collections:
            context.scene.collection.children.link(bpy.data.collections.new(name='INSERTS'))
        else:
            objects = bpy.data.collections['INSERTS'].objects[:]
            children = bpy.data.collections['INSERTS'].children[:]

            bpy.data.collections.remove(bpy.data.collections['INSERTS'])

            context.scene.collection.children.link(bpy.data.collections.new(name='INSERTS'))

            for obj in objects:
                bpy.data.collections['INSERTS'].objects.link(obj)

            for child in children:
                bpy.data.collections['INSERTS'].children.link(child)

        for obj in bpy.data.objects:
            for modifier in obj.modifiers:
                if modifier.type == 'BOOLEAN' and not modifier.object:
                    obj.modifiers.remove(modifier)

        if self.init_active:
            if self.init_active.kitops.insert and self.init_active.kitops.insert_target:
                self.boolean_target = self.init_active.kitops.insert_target
            elif preference.mode == 'REGULAR' and self.init_active.kitops.reserved_target:
                self.boolean_target = self.init_active.kitops.reserved_target
            elif self.init_active.kitops.insert:
                self.boolean_target = None
            elif self.init_active.type == 'MESH':
                self.boolean_target = self.init_active
            else:
                self.boolean_target = None
        else:
            self.boolean_target = None

        for obj in context.selected_objects:
            obj.select_set(False)

        if self.init_active and self.init_active.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if self.boolean_target:
            ray.make_duplicate(self, self.boolean_target)

        # if not self.material:
        #    self.material = event.ctrl

        self.material_link = not event.ctrl
        insert.add(self, context)

        prev_name = ''
        if self.material and self.init_active and self.import_material:
            if hasattr(self.init_active, 'material_slots') and len(self.init_active.material_slots[:]) and self.init_active.material_slots[0].material:
                prev_name = self.init_active.material_slots[0].material.name
            self.init_active.data.materials.clear()
            self.init_active.data.materials.append(self.import_material)

            for obj in self.init_selected:
                if obj != self.init_active and obj.type == 'MESH':
                    obj.data.materials.clear()
                    obj.data.materials.append(self.import_material)

        if self.material:
            if not self.import_material:
                self.report({'WARNING'}, 'No materials found to import')

            elif not prev_name:
                self.report({'INFO'}, F'Imported material: {self.import_material.name}')

            else:
                self.report({'INFO'}, F'Material assigned: {self.import_material.name}')

            self.exit(context, clear=True)
            return {'FINISHED'}

        insert.show_solid_objects()
        insert.show_cutter_objects()
        insert.show_wire_objects()

        if self.main.kitops.animated:
            bpy.ops.screen.animation_play()

        if self.init_selected and self.boolean_target:
            self.mouse = Vector((event.mouse_x, event.mouse_y))
            self.mouse.x -= view3d.region().x - preference.insert_offset_x * dpi.factor()
            self.mouse.y -= view3d.region().y - preference.insert_offset_y * dpi.factor()

            insert.hide_handler(self)

            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}
        else:
            self.main.location = bpy.context.scene.cursor.location
            self.exit(context)
            return {'FINISHED'}


    def modal(self, context, event):
        preference = addon.preference()
        option = addon.option()

        if not insert.operator:
            self.exit(context)
            return {'FINISHED'}

        if event.type == 'MOUSEMOVE':
            self.mouse = Vector((event.mouse_x, event.mouse_y))
            self.mouse.x -= view3d.region().x - preference.insert_offset_x * dpi.factor()
            self.mouse.y -= view3d.region().y - preference.insert_offset_y * dpi.factor()
            update.location()

        insert.hide_handler(self)

        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':

            self.exit(context, clear=True)
            return {'CANCELLED'}

        elif event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            if ray.location:
                if event.shift and preference.mode == 'SMART':
                    self.exit(context)
                    bpy.ops.ko.add_insert('INVOKE_DEFAULT', location=self.location)
                else:
                    self.exit(context)
                return{'FINISHED'}
            else:

                self.exit(context, clear=True)
                return {'CANCELLED'}

        elif event.type == 'WHEELDOWNMOUSE':
            if option.auto_scale:
                if self.insert_scale.index(preference.insert_scale) + 1 < len(self.insert_scale):
                    preference.insert_scale = self.insert_scale[self.insert_scale.index(preference.insert_scale) + 1]
            else:
                step = 0.1 if not event.shift else 0.01
                self.main.scale -= self.main.scale * step
            return {'RUNNING_MODAL'}

        elif event.type == 'WHEELUPMOUSE':
            if option.auto_scale:
                if self.insert_scale.index(preference.insert_scale) - 1 >= 0:
                    preference.insert_scale = self.insert_scale[self.insert_scale.index(preference.insert_scale) - 1]
            else:
                step = 0.1 if not event.shift else 0.01
                self.main.scale += self.main.scale * step
            return {'RUNNING_MODAL'}

        elif event.type in {'G', 'R', 'S'}:
            insert.operator = None

        return {'PASS_THROUGH'}


    def exit(self, context, clear=False):
        option = addon.option()

        if self.main.kitops.animated:
            bpy.ops.screen.animation_cancel(restore_frame=True)

        if not option.show_cutter_objects:
            for obj in self.cutter_objects:
                obj.hide_viewport = True

        if clear:
            for obj in self.inserts:
                bpy.data.objects.remove(obj)

            for obj in self.init_selected:
                obj.select_set(True)

            if self.init_active:
                context.view_layer.objects.active = self.init_active

        else:
            for obj in self.inserts:
                if obj.select_get() and obj.kitops.selection_ignore:
                    obj.select_set(False)
                else:
                    obj.select_set(True)

        #TODO: collection helper: collection.remove
        if 'INSERTS' in bpy.data.collections:
            for child in bpy.data.collections['INSERTS'].children:
                if not child.objects and not child.children:
                    bpy.data.collections.remove(child)

        ray.success = bool()
        ray.location = Vector()
        ray.normal = Vector()
        ray.face_index = int()

        insert.operator = None

        if 'INSERTS' in bpy.data.collections and not bpy.data.collections['INSERTS'].objects and not bpy.data.collections['INSERTS'].children:
            bpy.data.collections.remove(bpy.data.collections['INSERTS'])

        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        # context.view_layer.depsgraph.update()

        insert.show_solid_objects()
        insert.show_cutter_objects()
        insert.show_wire_objects()


#TODO: Collections
class KO_OT_add_insert(Operator, add_insert):
    bl_idname = 'ko.add_insert'
    bl_label = 'Add INSERT'
    bl_description = 'Add INSERT to the scene'
    # bl_options = {'REGISTER', 'UNDO'}


class KO_OT_add_insert_material(Operator, add_insert):
    bl_idname = 'ko.add_insert_material'
    bl_label = 'Add Material'
    bl_description = ('Add INSERT\'s materials to target \n'
                      '  Ctrl - Add unique material instance')


class KO_OT_select_inserts(Operator):
    bl_idname = 'ko.select_inserts'
    bl_label = 'Select All'
    bl_description = 'Select all INSERTS'
    bl_options = {'REGISTER', 'UNDO'}

    solids: BoolProperty(
        name = 'Solid inserts',
        description = 'Select solid INSERTS',
        default = True)

    cutters: BoolProperty(
        name = 'Cutter inserts',
        description = 'Select cutter INSERTS',
        default = True)

    wires: BoolProperty(
        name = 'Wire inserts',
        description = 'Select wire INSERTS',
        default = True)


    def draw(self, context):
        layout = self.layout

        preference = addon.preference()
        option = addon.option()

        if preference.mode == 'SMART':
            layout.prop(option, 'auto_select')

        column = layout.column()
        column.active = not option.auto_select or preference.mode == 'REGULAR'
        column.prop(self, 'solids')
        column.prop(self, 'cutters')
        column.prop(self, 'wires')


    def check(self, context):
        return True


    def execute(self, context):
        solids = insert.collect(solids=True, all=True)
        cutters = insert.collect(cutters=True, all=True)
        wires = insert.collect(wires=True, all=True)

        if self.solids:
            for obj in solids:
                obj.select_set(True)

        if self.cutters:
            for obj in cutters:
                obj.select_set(True)

        if self.wires:
            for obj in wires:
                obj.select_set(True)

        return {'FINISHED'}


class remove_insert_properties():
    bl_options = {'UNDO'}

    remove: BoolProperty()
    uuid: StringProperty()

    # @classmethod
    # def poll(cls, context):
    #     return context.active_object or cls.uuid


    def execute(self, context):
        objects = context.selected_objects if not self.uuid else [obj for obj in bpy.data.objects if obj.kitops.id == self.uuid]
        for obj in objects:
            obj.kitops['insert'] = False
            obj.kitops['insert_target'] = None
            obj.kitops['mirror_target'] = None
            obj.kitops['reserved_target'] = None
            obj.kitops['main_object'] = None

        if self.remove:
            bpy.ops.object.delete({'active_object': objects[0], 'selected_objects': objects}, confirm=False)

        return {'FINISHED'}


class KO_OT_remove_insert_properties(Operator, remove_insert_properties):
    bl_idname = 'ko.remove_insert_properties'
    bl_label = 'Remove KIT OPS props'
    bl_description = 'Remove properties from the selected OBJECTS'


class KO_OT_remove_insert_properties_x(Operator, remove_insert_properties):
    bl_idname = 'ko.remove_insert_properties_x'
    bl_label = 'Remove INSERT'
    bl_description = 'Deletes selected INSERTS'


class KO_OT_export_settings(Operator, ExportHelper):
    bl_idname = 'ko.export_settings'
    bl_label = 'Export Settings'
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_description = '.\n'.join((
        'Save KIT OPS preferences to a file',
        'Made possible by PowerBackup'))

    filter_glob: bpy.props.StringProperty(default='*.json', options={'HIDDEN'})
    filename_ext: bpy.props.StringProperty(default='.json', options={'HIDDEN'})


    def invoke(self, context, event):
        self.filepath = backup.filepath()
        return super().invoke(context, event)


    def execute(self, context):
        result = backup.backup(self.filepath)
        self.report(result[0], result[1])
        return result[2]


class KO_OT_import_settings(Operator, ImportHelper):
    bl_idname = 'ko.import_settings'
    bl_label = 'Import Settings'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = '.\n'.join((
        'Load KIT OPS preferences from a file',
        'Made possible by PowerBackup'))

    filter_glob: bpy.props.StringProperty(default='*.json', options={'HIDDEN'})
    filename_ext: bpy.props.StringProperty(default='.json', options={'HIDDEN'})


    def invoke(self, context, event):
        self.filepath = backup.filepath()
        return super().invoke(context, event)


    def execute(self, context):
        result = backup.restore(self.filepath)
        self.report(result[0], result[1])
        return result[2]


class KO_OT_convert_to_mesh(Operator):
    bl_idname = 'ko.convert_to_mesh'
    bl_label = 'Convert to mesh'
    bl_description = 'Apply modifiers and remove kitops properties of selected objects'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects


    def execute(self, context):
        bpy.ops.object.convert(target='MESH')

        for obj in context.selected_objects:
            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN' and mod.object:
                    mod.object.kitops['insert_target'] = None
                    mod.object.kitops['mirror_target'] = None
                    mod.object.kitops['reserved_target'] = None
                    mod.object.kitops['main_object'] = None

            obj.kitops['insert'] = False
            obj.kitops['main'] = False
            obj.kitops['insert_target'] = None
            obj.kitops['mirror_target'] = None
            obj.kitops['reserved_target'] = None
            obj.kitops['main_object'] = None

        for obj in context.selected_objects:
            for mod in obj.modifiers:
                obj.modifiers.remove(mod)

        return {'FINISHED'}


class KO_OT_remove_wire_inserts(Operator):
    bl_idname = 'ko.remove_wire_inserts'
    bl_label = 'Remove Unused Wire INSERTS'
    bl_description = 'Remove unused wire objects from the INSERTS collection, keeping transforms on child objects'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return 'INSERTS' in bpy.data.collections


    def execute(self, context):
        collection = bpy.data.collections['INSERTS']
        wires = {obj for obj in collection.all_objects if obj.display_type in {'WIRE', 'BOUNDS'}}

        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue

            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN' and mod.object in wires:
                    wires.remove(mod.object)

        for obj in collection.all_objects:
            if obj.parent in wires:
                obj.matrix_local = obj.matrix_world
                obj.parent = None

        for obj in wires:
            bpy.data.objects.remove(obj)

        return {'FINISHED'}


class KO_OT_clean_duplicate_materials(Operator):
    bl_idname = 'ko.clean_duplicate_materials'
    bl_label = 'Clean Duplicate Materials'
    bl_description = 'Find duplicate materials by name, remap users and remove them'
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        count = len(bpy.data.materials)

        for mat in bpy.data.materials[:]:
            if re.search('[0-9][0-9][0-9]$', mat.name):
                original = mat.name[:-4]

                if original in bpy.data.materials:
                    mat.user_remap(bpy.data.materials[original])
                    bpy.data.materials.remove(mat)

        self.report({'INFO'}, F'Removed {count - len(bpy.data.materials)} materials')
        return {'FINISHED'}


class KO_OT_move_folder(Operator):
    bl_idname = 'ko.move_folder'
    bl_label = 'Move Folder'
    bl_description = 'Move the chosen folder up or down in the list'
    bl_options = {'REGISTER', 'INTERNAL'}

    index: IntProperty()
    direction: IntProperty()


    def execute(self, context):
        preference = addon.preference()
        neighbor = max(0, self.index + self.direction)
        preference.folders.move(neighbor, self.index)
        return {'FINISHED'}


classes = [
    KO_OT_purchase,
    KO_OT_store,
    KO_OT_documentation,
    KO_OT_add_kpack_path,
    KO_OT_remove_kpack_path,
    KO_OT_refresh_kpacks,
    KO_OT_next_kpack,
    KO_OT_previous_kpack,
    KO_OT_add_insert,
    KO_OT_add_insert_material,
    KO_OT_select_inserts,
    KO_OT_remove_insert_properties,
    KO_OT_remove_insert_properties_x,
    KO_OT_export_settings,
    KO_OT_import_settings,
    KO_OT_convert_to_mesh,
    KO_OT_remove_wire_inserts,
    KO_OT_clean_duplicate_materials,
    KO_OT_move_folder]


def register():
    for cls in classes:
        register_class(cls)

    try:
        from .. utility import smart
        smart.register()
    except: pass


def unregister():
    for cls in classes:
        unregister_class(cls)

    try:
        from .. utility import smart
        smart.unregister()
    except: pass
