import bpy

from bpy.types import Panel, UIList
from bpy.utils import register_class, unregister_class

from .. utility import addon, dpi, insert, update, modifier

smart_enabled = True
try: from .. utility import smart
except: smart_enabled = False


# TODO: on no categories show add path preferences
# TODO: should display options for the render scene, ground box toggle
class KO_PT_ui(Panel):
    bl_space_type = 'VIEW_3D'
    bl_label = 'KIT OPS'
    bl_region_type = 'UI'
    bl_category = 'KIT OPS'

    def draw(self, context):
        global smart_enabled

        layout = self.layout
        preference = addon.preference()
        option = addon.option()
        scene = context.scene

        if not smart_enabled and preference.mode == 'SMART':
            preference.mode = 'REGULAR'

        if insert.authoring():
            if not smart_enabled:
                layout.label(icon='ERROR', text='Purchase KIT OPS PRO')
                layout.label(icon='BLANK1', text='To use these features')

            if context.scene.kitops.factory:
                column = layout.column()
                column.enabled = smart_enabled

                # kpacks = context.window_manager.kitops.kpack
                # current = kpacks.categories[kpacks.active_index]
                # bases = [os.path.basename(blend.location)[:-6] for blend in current.blends]
                # name_overlap = '_'.join(option.insert_name.split(' ')) in bases

                column.label(text='INSERT name')# if not name_overlap else 'INSERT name (Overwrite!)')
                # column.alert = name_overlap
                column.prop(option, 'insert_name', text='')

            column = layout.column()
            column.enabled = smart_enabled
            column.label(text='Author')
            column.prop(option, 'author', text='')

        if not insert.authoring() and not context.scene.kitops.thumbnail:

            if len(option.kpack.categories):
                # if not context.scene.kitops.thumbnail:

                layout.label(text='KPACKS')

                column = layout.column(align=True)
                row = column.row(align=True)
                row.prop(option, 'filter', text='', icon='VIEWZOOM')
                column.separator()

                row = column.row(align=True)
                row.prop(option, 'kpacks', text='')
                row.operator('ko.refresh_kpacks', text='', icon='FILE_REFRESH')

                if option.kpack.active_index < len(option.kpack.categories):
                    category = option.kpack.categories[option.kpack.active_index]

                    row = column.row(align=True)

                    sub = row.row(align=True)
                    sub.scale_y = 6
                    sub.operator('ko.previous_kpack', text='', icon='TRIA_LEFT')

                    row.template_icon_view(category, 'thumbnail', show_labels=preference.thumbnail_labels)

                    sub = row.row(align=True)
                    sub.scale_y = 6
                    sub.operator('ko.next_kpack', text='', icon='TRIA_RIGHT')

                    row = column.row(align=True)
                    row.scale_y = 1.5
                    op = row.operator('ko.add_insert')
                    op.location = category.blends[category.active_index].location
                    op.material = False

                    row.scale_y = 1.5
                    op = row.operator('ko.add_insert_material')
                    op.location = category.blends[category.active_index].location
                    op.material = True

                    row = layout.row()
                    row.label(text='INSERT Name: {}'.format(category.blends[category.active_index].name))

                    if smart_enabled:
                        row = layout.row()
                        row.operator('ko.edit_insert')

                        layout.separator()

                        split = layout.split(factor=0.3)
                        split.label(text='Mode')
                        row = split.row()
                        row.prop(preference, 'mode', expand=True)

                column = layout.column(align=True)
                column.enabled = option.auto_scale
                row = column.row(align=True)
                row.prop(preference, 'insert_scale', expand=True)
                column.prop(preference, '{}_scale'.format(preference.insert_scale.lower()), text='Scale')
                layout.separator()

                layout.prop(option, 'auto_scale')

                column = layout.column()
                column.active = preference.mode == 'SMART' or preference.enable_auto_select
                column.prop(option, 'auto_select')

                if context.window_manager.kitops.pro:
                    if context.scene.kitops.thumbnail:
                        layout.separator()

                        row = layout.row()
                        row.scale_y = 1.5
                        op = row.operator('ko.render_thumbnail', text='Render thumbnail')
                        op.render = True
                        op.import_scene = False

                    # else:
                if not context.scene.kitops.thumbnail:
                    layout.separator()

                    row = layout.row(align=True)
                    row.scale_y = 1.5
                    op = row.operator('ko.remove_insert_properties')
                    op.remove = False
                    op.uuid = ''

                    sub = row.row(align=True)
                    sub.enabled = context.active_object.kitops.insert if context.active_object else False
                    op = sub.operator('ko.remove_insert_properties_x', text='', icon='X')
                    op.remove = True
                    op.uuid = ''

                    # if not bpy.data.filepath and bpy.data.is_dirty:
                    #     row = layout.row()
                    #     row.label(text='Save File to Create INSERTS')

                if context.window_manager.kitops.pro:
                    if not context.scene.kitops.thumbnail:
                        row = layout.row()
                        row.scale_y = 1.5
                        op = row.operator('ko.create_insert')
                        op.material = False
                        op.children = True

                        row = layout.row()
                        row.scale_y = 1.5
                        op = row.operator('ko.create_insert_material')
                        op.material = True
                        op.children = False

                if not context.scene.kitops.thumbnail:
                    row = layout.row()
                    row.scale_y = 1.5
                    row.operator('ko.convert_to_mesh', text='Convert to mesh')

                # if preference.mode == 'SMART':
                #     layout.label(text='Display')

                #     row = layout.row()
                #     row.scale_y = 1.5
                #     row.scale_x = 1.5
                #     row.prop(option, 'show_modifiers', text='', icon_value=addon.icons['main']['modifier' if option.show_modifiers else 'modifier-off'].icon_id, toggle=True)
                #     row.prop(option, 'show_solid_objects', text='', icon_value=addon.icons['main']['solid' if option.show_solid_objects else 'solid-off'].icon_id, toggle=True)
                #     row.prop(option, 'show_cutter_objects', text='', icon_value=addon.icons['main']['cutter'if option.show_cutter_objects else 'cutter-off'].icon_id, toggle=True)
                #     row.prop(option, 'show_wire_objects', text='', icon_value=addon.icons['main']['wire' if option.show_wire_objects else 'wire-off'].icon_id, toggle=True)

                active = context.active_object
                if active and hasattr(active, 'kitops') and active.kitops.insert:

                    if preference.mode == 'SMART':
                        layout.separator()

                        if context.active_object.kitops.insert_target and preference.mode == 'SMART':
                            row = layout.row()
                            row.enabled = smart_enabled
                            row.label(text='Mirror')

                            sub = row.row(align=True)
                            sub.alignment = 'RIGHT'
                            sub.scale_x = 0.75
                            sub.prop(context.active_object.kitops, 'mirror_x', text='X', toggle=True)
                            sub.prop(context.active_object.kitops, 'mirror_y', text='Y', toggle=True)
                            sub.prop(context.active_object.kitops, 'mirror_z', text='Z', toggle=True)

                        row = layout.row(align=True)
                        row.enabled = smart_enabled
                        if context.active_object.kitops.insert_target:
                            row.prop(context.active_object.kitops.insert_target, 'hide_select', text='', icon='RESTRICT_SELECT_OFF' if not context.active_object.hide_select else 'RESTRICT_SELECT_ON')
                        row.prop(context.active_object.kitops, 'insert_target', text='')

                        row = layout.row()
                        row.active = smart_enabled
                        sub = row.row()
                        sub.enabled = bool(context.active_object.kitops.insert_target)
                        sub.operator('ko.apply_insert' if smart_enabled else 'ko.purchase', text='Apply')
                        row.operator('ko.remove_insert' if smart_enabled else 'ko.purchase', text='Delete')

                if preference.mode == 'SMART' and context.active_object and context.active_object.kitops.insert_target:
                    row = layout.row()
                    row.scale_y = 1.5
                    row.operator('ko.select_inserts')

                    layout.label(text='Align')

                    row = layout.row()
                    row.active = smart_enabled
                    row.scale_y = 1.5
                    row.scale_x = 1.5
                    row.operator('ko.align_top' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-top'].icon_id)
                    row.operator('ko.align_bottom' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-bottom'].icon_id)
                    row.operator('ko.align_left' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-left'].icon_id)
                    row.operator('ko.align_right' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-right'].icon_id)

                    row = layout.row()
                    row.active = smart_enabled
                    row.scale_y = 1.5
                    row.scale_x = 1.5
                    row.operator('ko.align_horizontal' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-horiz'].icon_id)
                    row.operator('ko.align_vertical' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-vert'].icon_id)
                    row.operator('ko.stretch_wide' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['stretch-wide'].icon_id)
                    row.operator('ko.stretch_tall' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['stretch-tall'].icon_id)

        elif context.active_object and not context.active_object.kitops.temp or scene.kitops.factory:
            if context.active_object.type not in {'LAMP', 'CAMERA', 'SPEAKER', 'EMPTY'}:
                row = layout.row()
                row.enabled = smart_enabled and not context.active_object.kitops.temp and not context.active_object.kitops.material_base
                row.prop(context.active_object.kitops, 'main')

            row = layout.row()
            row.enabled = smart_enabled and not context.active_object.kitops.temp and not context.active_object.kitops.material_base
            row.prop(context.active_object.kitops, 'type', expand=True)

            if context.active_object.type == 'MESH' and context.active_object.kitops.type == 'CUTTER':
                row = layout.row()
                row.enabled = smart_enabled and not context.active_object.kitops.temp and not context.active_object.kitops.material_base
                row.prop(context.active_object.kitops, 'boolean_type', text='Type')

        elif context.active_object and context.active_object.type == 'MESH' and scene.kitops.thumbnail:
            row = layout.row()
            row.enabled = smart_enabled
            row.prop(context.active_object.kitops, 'ground_box')

        if insert.authoring() or context.scene.kitops.thumbnail:
            layout.separator()

            column = layout.column()
            column.active = preference.mode == 'SMART' or preference.enable_auto_select
            column.prop(option, 'auto_select')

            if context.active_object:
                row = layout.row()
                row.enabled = smart_enabled and not context.active_object.kitops.main and not context.active_object.kitops.temp
                row.prop(context.active_object.kitops, 'selection_ignore')

            layout.separator()

            if not context.scene.kitops.thumbnail:
                column = layout.column()
                column.enabled = smart_enabled and bool(context.active_object) and not context.active_object.kitops.temp
                column.prop(scene.kitops, 'animated')
                column.prop(scene.kitops, 'auto_parent')

                layout.separator()

            if not context.scene.kitops.thumbnail or context.scene.kitops.factory:
                row = layout.row()
                row.active = smart_enabled
                row.scale_y = 1.5
                row.operator('ko.save_insert' if smart_enabled else 'ko.purchase')

            if insert.authoring() or context.scene.kitops.thumbnail:
                if context.scene.camera:
                    row = layout.row()
                    # row.active = smart_enabled and context.active_object and (not context.active_object.kitops.temp or context.active_object.kitops.material_base)
                    row.scale_y = 1.5
                    # row.operator('view3d.camera_to_view_selected', text='Align Camera To INSERT')
                    row.operator('ko.camera_to_insert')

                if not context.scene.kitops.thumbnail:
                    row = layout.row()
                    row.scale_y = 1.5
                    # row.operator('ko.render_thumbnail', text='Render thumbnail', icon='BLANK1')
                    op = row.operator('ko.render_thumbnail', text='Load Render Scene', icon='BLANK1')
                    op.render = False
                    op.import_scene = True

            if context.scene.kitops.factory or context.scene.kitops.thumbnail:
                row = layout.row()
                row.active = smart_enabled and not (context.scene.kitops.factory and not context.scene.kitops.last_edit)
                row.scale_y = 1.5
                row.operator('ko.create_snapshot' if smart_enabled else 'ko.purchase', text='Render Thumbnail')
                row = layout.row()

            if context.scene.kitops.factory:
                row.active = smart_enabled
                row.scale_y = 1.5
                row.operator('ko.close_factory_scene' if smart_enabled else 'ko.purchase')

            elif context.scene.kitops.thumbnail:
                row.active = smart_enabled
                row.scale_y = 1.5
                row.operator('ko.close_thumbnail_scene' if smart_enabled else 'ko.purchase')

            row = layout.row()
            row.scale_y = 1.5
            row.operator('ko.remove_wire_inserts')

            row = layout.row()
            row.scale_y = 1.5
            row.operator('ko.clean_duplicate_materials')

            layout.separator()

            row = layout.row()
            row.alignment = 'RIGHT'
            row.scale_x = 1.5
            row.scale_y = 1.5
            op = row.operator('ko.documentation', text='', icon_value=addon.icons['main']['question-sign'].icon_id)
            op.authoring = True

        elif not context.scene.kitops.thumbnail:
            # if preference.mode == 'SMART' and context.active_object and context.active_object.kitops.insert_target:
            #     layout.label(text='Align')

            #     row = layout.row()
            #     row.active = smart_enabled
            #     row.scale_y = 1.5
            #     row.scale_x = 1.5
            #     row.operator('ko.align_top' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-top'].icon_id)
            #     row.operator('ko.align_bottom' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-bottom'].icon_id)
            #     row.operator('ko.align_left' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-left'].icon_id)
            #     row.operator('ko.align_right' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-right'].icon_id)

            #     row = layout.row()
            #     row.active = smart_enabled
            #     row.scale_y = 1.5
            #     row.scale_x = 1.5
            #     row.operator('ko.align_horizontal' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-horiz'].icon_id)
            #     row.operator('ko.align_vertical' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['align-vert'].icon_id)
            #     row.operator('ko.stretch_wide' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['stretch-wide'].icon_id)
            #     row.operator('ko.stretch_tall' if smart_enabled else 'ko.purchase', text='', icon_value=addon.icons['main']['stretch-tall'].icon_id)

            row = layout.row()
            row.scale_y = 1.5
            row.operator('ko.remove_wire_inserts')

            row = layout.row()
            row.scale_y = 1.5
            row.operator('ko.clean_duplicate_materials')

            layout.separator()

            row = layout.row()
            row.enabled = True
            row.alignment = 'RIGHT'
            row.scale_x = 1.5
            row.scale_y = 1.5
            row.operator('ko.store', text='', icon_value=addon.icons['main']['cart'].icon_id)
            op = row.operator('ko.documentation', text='', icon_value=addon.icons['main']['question-sign'].icon_id)
            op.authoring = False


class KO_PT_sort_last(Panel):
    bl_label = 'Sort Last'
    bl_space_type = 'TOPBAR'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        layout = self.layout

        preference = addon.preference()
        row = layout.row(align=True)
        # row.scale_x = 1.5
        # row.scale_y = 1.5

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
            sub = row.row(align=True)
            sub.enabled = getattr(preference, F'sort_{type.lower()}')
            sub.prop(preference, F'sort_{type.lower()}_last', text='', icon=icon)

        if preference.sort_bevel:
            label_row(preference, 'sort_bevel_ignore_vgroup', layout.row(), label='Ignore Bevels with VGroups')
            label_row(preference, 'sort_bevel_ignore_only_verts', layout.row(), label='Ignore Bevels using Only Verts')


def label_row(path, prop, row, label=''):
    row.label(text=label)
    row.prop(path, prop, text='')


classes = [
    KO_PT_ui,
    KO_PT_sort_last]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
