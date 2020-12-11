import os

import bpy

from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import *
from bpy.utils import register_class, unregister_class

from . utility import addon, shader, update, modifier


class folder(PropertyGroup):
    icon: StringProperty(default='FILE_FOLDER')

    name: StringProperty(
        name = 'Path Name',
        default = '')

    location: StringProperty(
        name = 'Path',
        description = 'Path to KIT OPS library',
        update = update.libpath,
        subtype = 'DIR_PATH',
        default = '')


class kitops(AddonPreferences):
    bl_idname = addon.name

    context: EnumProperty(
        name = 'Context',
        description = 'KIT OPS preference settings context',
        items = [
            ('GENERAL', 'General', ''),
            # ('THEME', 'Theme', ''),
            ('FILEPATHS', 'File Paths', '')],
        default = 'GENERAL')

    folders: CollectionProperty(type=folder)

    author: StringProperty(
        name = 'Author',
        description = 'Name that will be used when creating INSERTS',
        default = 'Your Name')

    insert_offset_x: IntProperty(
        name = 'INSERT offset X',
        description = 'Offset used when adding the INSERT from the mouse cursor',
        soft_min = -40,
        soft_max = 40,
        subtype = 'PIXEL',
        default = 0)

    insert_offset_y: IntProperty(
        name = 'INSERT offset Y',
        description = 'Offset used when adding the INSERT from the mouse cursor',
        soft_min = -40,
        soft_max = 40,
        subtype = 'PIXEL',
        default = 20)

    clean_names: BoolProperty(
        name = 'Clean names',
        description = 'Capatilize and clean up the names used in the UI from the KPACKS',
        update = update.kpack,
        default = True)

    thumbnail_labels: BoolProperty(
        name = 'Thumbnail labels',
        description = 'Displays names of INSERTS under the thumbnails in the preview popup',
        default = True)

    enable_auto_select: BoolProperty(
        name = 'Enable auto select',
        description = 'Enable auto select in regular mode',
        default = True)

    border_color: FloatVectorProperty(
        name = 'Border color',
        description = 'Color used for the border',
        min = 0,
        max = 1,
        size = 4,
        precision = 3,
        subtype = 'COLOR',
        default = (1.0, 0.030, 0.0, 0.9))

    border_size: IntProperty(
        name = 'Border size',
        description = 'Border size in pixels\n  Note: DPI factored',
        min = 1,
        soft_max = 6,
        subtype = 'PIXEL',
        default = 1)

    border_offset: IntProperty(
        name = 'Border size',
        description = 'Border size in pixels\n  Note: DPI factored',
        min = 1,
        soft_max = 16,
        subtype = 'PIXEL',
        default = 8)

    logo_color: FloatVectorProperty(
        name = 'Logo color',
        description = 'Color used for the KIT OPS logo',
        min = 0,
        max = 1,
        size = 4,
        precision = 3,
        subtype = 'COLOR',
        default = (1.0, 0.030, 0.0, 0.9))

    off_color: FloatVectorProperty(
        name = 'Off color',
        description = 'Color used for the KIT OPS logo when there is not an active insert with an insert target',
        min = 0,
        max = 1,
        size = 4,
        precision = 3,
        subtype = 'COLOR',
        default = (0.448, 0.448, 0.448, 0.1))

    logo_size: IntProperty(
        name = 'Logo size',
        description = 'Logo size in the 3d view\n  Note: DPI factored',
        min = 1,
        soft_max = 500,
        subtype = 'PIXEL',
        default = 10)

    logo_padding_x: IntProperty(
        name = 'Logo padding x',
        description = 'Logo padding in the 3d view from the border corner\n  Note: DPI factored',
        subtype = 'PIXEL',
        default = 18)

    logo_padding_y: IntProperty(
        name = 'Logo padding y',
        description = 'Logo padding in the 3d view from the border corner\n  Note: DPI factored',
        subtype = 'PIXEL',
        default = 12)

    logo_auto_offset: BoolProperty(
        name = 'Logo auto offset',
        description = 'Offset the logo automatically for HardOps and BoxCutter',
        default = True)

    text_color: FloatVectorProperty(
        name = 'Text color',
        description = 'Color used for the KIT OPS help text',
        min = 0,
        max = 1,
        size = 4,
        precision = 3,
        subtype = 'COLOR',
        default = (1.0, 0.030, 0.0, 0.9))

    # displayed in panel
    mode: EnumProperty(
        name = 'Mode',
        description = 'Insert mode',
        items = [
            ('REGULAR', 'Regular', 'Stop creating modifiers for all INSERT objs except for new INSERTS\n  Note: Removes all insert targets'),
            ('SMART', 'Smart', 'Create modifiers as you work with an INSERT on the target obj')],
        update = update.mode,
        default = 'REGULAR')

    insert_scale: EnumProperty(
        name = 'Insert Scale',
        description = 'Insert scale mode based on the active obj when adding an INSERT',
        items = [
            ('LARGE', 'Large', ''),
            ('MEDIUM', 'Medium', ''),
            ('SMALL', 'Small', '')],
        update = update.insert_scale,
        default = 'LARGE')

    large_scale: IntProperty(
        name = 'Primary Scale',
        description = 'Percentage of obj size when adding an INSERT for primary',
        min = 1,
        soft_max = 200,
        subtype = 'PERCENTAGE',
        update = update.insert_scale,
        default = 100)

    medium_scale: IntProperty(
        name = 'Secondary Scale',
        description = 'Percentage of obj size when adding an INSERT for secondary',
        min = 1,
        soft_max = 200,
        subtype = 'PERCENTAGE',
        update = update.insert_scale,
        default = 50)

    small_scale: IntProperty(
        name = 'Tertiary Scale',
        description = 'Percentage of obj size when adding an INSERT for tertiary',
        min = 1,
        soft_max = 200,
        subtype = 'PERCENTAGE',
        update = update.insert_scale,
        default = 25)

    boolean_solver: EnumProperty(
        name='Solver',
        description='',
        items=[
            ('FAST', 'Fast', 'fast solver for booleans'),
            ('EXACT', 'Exact', 'exact solver for booleans')],
        default='FAST')

    sort_modifiers: BoolProperty(
        name = 'Sort Modifiers',
        description = '\n Sort modifier order',
        update = update.sync_sort,
        default = False)

    sort_bevel: BoolProperty(
        name = 'Sort Bevel',
        description = '\n Ensure bevel modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_weighted_normal: BoolProperty(
        name = 'Sort Weighted Normal',
        description = '\n Ensure weighted normal modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_array: BoolProperty(
        name = 'Sort Array',
        description = '\n Ensure array modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_mirror: BoolProperty(
        name = 'Sort Mirror',
        description = '\n Ensure mirror modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_solidify: BoolProperty(
        name = 'Sort Soldify',
        description = '\n Ensure solidify modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_triangulate: BoolProperty(
        name = 'Sort Triangulate',
        description = '\n Ensure triangulate modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_simple_deform: BoolProperty(
        name = 'Sort Simple Deform',
        description = '\n Ensure simple deform modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_decimate: BoolProperty(
        name = 'Sort Decimate',
        description = '\n Ensure decimate modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_remesh: BoolProperty(
        name = 'Sort Remesh',
        description = '\n Ensure remesh modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_subsurf: BoolProperty(
        name = 'Sort Subsurf',
        description = '\n Ensure subsurf modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_weld: BoolProperty(
        name = 'Sort Weld',
        description = '\n Ensure weld modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_uv_project: BoolProperty(
        name = 'Sort UV Project',
        description = '\n Ensure uv project modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = True)

    sort_bevel_last: BoolProperty(
        name = 'Sort Bevel',
        description = '\n Only effect the most recent bevel modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_weighted_normal_last: BoolProperty(
        name = 'Sort Weighted Normal Last',
        description = '\n Only effect the most recent weighted normal modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_array_last: BoolProperty(
        name = 'Sort Array Last',
        description = '\n Only effect the most recent array modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_mirror_last: BoolProperty(
        name = 'Sort Mirror Last',
        description = '\n Only effect the most recent mirror modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_solidify_last: BoolProperty(
        name = 'Sort Soldify Last',
        description = '\n Only effect the most recent solidify modifier when sorting',
        update = update.sync_sort,
        default = False)

    sort_triangulate_last: BoolProperty(
        name = 'Sort Triangulate Last',
        description = '\n Only effect the most recent triangulate modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_simple_deform_last: BoolProperty(
        name = 'Sort Simple Deform Last',
        description = '\n Only effect the most recent simple deform modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_decimate_last: BoolProperty(
        name = 'Sort Decimate Last',
        description = '\n Only effect the most recent decimate modifier when sorting',
        update = update.sync_sort,
        default = False)

    sort_remesh_last: BoolProperty(
        name = 'Sort Remesh Last',
        description = '\n Only effect the most recent remesh modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_subsurf_last: BoolProperty(
        name = 'Sort Subsurf Last',
        description = '\n Only effect the most recent subsurface modifier when sorting',
        update = update.sync_sort,
        default = False)

    sort_weld_last: BoolProperty(
        name = 'Sort Weld Last',
        description = '\n Only effect the most recent weld modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_uv_project_last: BoolProperty(
        name = 'Sort UV Project Last',
        description = '\n Only effect the most recent uv project modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_bevel_ignore_vgroup: BoolProperty(
        name = 'Ignore VGroup Bevels',
        description = '\n Ignore bevel modifiers that are using the vertex group limit method while sorting',
        update = update.sync_sort,
        default = True)

    sort_bevel_ignore_only_verts: BoolProperty(
        name = 'Ignore Only Vert Bevels',
        description = '\n Ignore bevel modifiers that are using the only vertices option while sorting',
        update = update.sync_sort,
        default = True)


    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        row = column.row(align=True)
        row.prop(self, 'context', expand=True)

        box = column.box()

        box.separator()
        getattr(self, self.context.lower())(context, box)
        box.separator()


    def general(self, context, layout):
        row = layout.row()
        row.label(text='Author')
        row.prop(self, 'author', text='')

        layout.separator()

        row = layout.row()
        row.label(text='INSERT offset X')
        row.prop(self, 'insert_offset_x', text='')

        row = layout.row()
        row.label(text='INSERT offset Y')
        row.prop(self, 'insert_offset_y', text='')

        if bpy.app.version[1] > 90:
            row = layout.row()
            row.label(text='Boolean Solver')
            row.prop(self, 'boolean_solver', expand=True)

        row = layout.row()
        row.label(text='Clean list names')
        row.prop(self, 'clean_names', text='')

        row = layout.row()
        row.label(text='Thumbnail labels')
        row.prop(self, 'thumbnail_labels', text='')

        row = layout.row()
        row.label(text='Enable auto select in regular mode')
        row.prop(self, 'enable_auto_select', text='')

        row = layout.row()
        row.label(text='Sort Modifiers')
        row.prop(self, 'sort_modifiers', text='')

        if self.sort_modifiers:
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            split = row.split(align=True, factor=0.85)

            row = split.row(align=True)
            for type in modifier.sort_types:
                icon = F'MOD_{type}'
                if icon == 'MOD_WEIGHTED_NORMAL':
                    icon = 'MOD_NORMALEDIT'
                elif icon == 'MOD_SIMPLE_DEFORM':
                    icon = 'MOD_SIMPLEDEFORM'
                elif icon == 'MOD_DECIMATE':
                    icon = 'MOD_DECIM'
                elif icon == 'MOD_WELD':
                    icon = 'AUTOMERGE_OFF'
                elif icon == 'MOD_UV_PROJECT':
                    icon = 'MOD_UVPROJECT'
                row.prop(self, F'sort_{type.lower()}', text='', icon=icon)

            row = split.row(align=True)
            row.scale_x = 1.5
            row.popover('KO_PT_sort_last', text='', icon='SORT_ASC')

        # if self.sort_modifiers:
        #     row = layout.row(align=True)
        #     row.alignment = 'RIGHT'
        #     row.prop(self, 'sort_bevel_last', text='', icon='SORT_ASC')
        #     row.separator()
        #     row.prop(self, 'sort_bevel', text='', icon='MOD_BEVEL')
        #     row.prop(self, 'sort_weighted_normal', text='', icon='MOD_NORMALEDIT')
        #     row.prop(self, 'sort_array', text='', icon='MOD_ARRAY')
        #     row.prop(self, 'sort_mirror', text='', icon='MOD_MIRROR')
        #     row.prop(self, 'sort_solidify', text='', icon='MOD_SOLIDIFY')
        #     row.prop(self, 'sort_simple_deform', text='', icon='MOD_SIMPLEDEFORM')
        #     row.prop(self, 'sort_triangulate', text='', icon='MOD_TRIANGULATE')
        #     row.prop(self, 'sort_decimate', text='', icon='MOD_DECIM')

        row = layout.row()
        row.operator('ko.export_settings')
        row.operator('ko.import_settings')


    def theme(self, context, layout):
        row = layout.row()
        row.label(text='Border color')
        row.prop(self, 'border_color', text='')

        row = layout.row()
        row.label(text='Border size')
        row.prop(self, 'border_size', text='')

        row = layout.row()
        row.label(text='Border offset')
        row.prop(self, 'border_offset', text='')

        row = layout.row()
        row.label(text='Logo color')
        row.prop(self, 'logo_color', text='')

        row = layout.row()
        row.label(text='Off color')
        row.prop(self, 'off_color', text='')

        row = layout.row()
        row.label(text='Logo size')
        row.prop(self, 'logo_size', text='')

        row = layout.row()
        row.label(text='Logo padding x')
        row.prop(self, 'logo_padding_x', text='')

        row = layout.row()
        row.label(text='Logo padding y')
        row.prop(self, 'logo_padding_y', text='')

        row = layout.row()
        row.label(text='Logo auto offset')
        row.prop(self, 'logo_auto_offset', text='')

        row = layout.row()
        row.label(text='Text color')
        row.prop(self, 'text_color', text='')


    def filepaths(self, context, layout):

        for index, folder in enumerate(self.folders):
            row = layout.row()
            split = row.split(factor=0.2)
            split.prop(folder, 'name', text='', emboss=False)

            split.prop(folder, 'location', text='')

            op = row.operator('ko.remove_kpack_path', text='', emboss=False, icon='PANEL_CLOSE')
            op.index = index

        row = layout.row()
        split = row.split(factor=0.2)

        split.separator()
        split.operator('ko.add_kpack_path', text='', icon='PLUS')

        sub = row.row()
        sub.operator('ko.refresh_kpacks', text='', emboss=False, icon='FILE_REFRESH')

classes = [
    folder,
    kitops]


def register():
    for cls in classes:
        register_class(cls)

    addon.preference()


def unregister():
    for cls in classes:
        unregister_class(cls)
