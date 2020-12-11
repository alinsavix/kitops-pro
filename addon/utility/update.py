import os

from copy import deepcopy as copy

import bpy

from bpy.utils import register_class, unregister_class, previews

from . import addon, insert, math, modifier, ray, regex

smart_mode = True
try:
    from . import smart
except:
    smart_mode = False


def kpacks(prop, context):
    option = addon.option()

    for index, category in enumerate(option.kpack.categories):
        if category.name == option.kpacks:
            option.kpack.active_index = index

            break

def kpack(prop, context):
    preference = addon.preference()
    option = addon.option()

    if not option:
        return

    def add_blend(location, folder, category):
        for file in os.listdir(os.path.join(location, folder)):
            if file.endswith('.blend') and regex.clean_name(file, use_re=preference.clean_names) not in [blend.name for blend in category.blends]:
                blend = category.blends.add()
                blend.name = regex.clean_name(
                    file, use_re=preference.clean_names)
                blend.location = os.path.join(location, folder, file)
                blend.icon = 'FILE_BLEND'

                filepath = os.path.join(location, folder, file[:-6] + '.png')
                if os.path.exists(filepath):
                    thumb = insert.thumbnails[folder].load(
                        os.path.basename(filepath), filepath, 'IMAGE')
                    icon_id = thumb.icon_id
                elif 'thumb.png' not in insert.thumbnails[folder]:
                    thumb = insert.thumbnails[folder].load(
                        'thumb.png', addon.path.default_thumbnail(), 'IMAGE')
                    icon_id = thumb.icon_id
                else:
                    icon_id = insert.thumbnails[folder]['thumb.png'].icon_id

                blend.icon_id = icon_id
                insert.thumbnails[folder].images.append([blend.name, icon_id])

    def add_folder(master):
        for folder in [file for file in os.listdir(master.location) if os.path.isdir(os.path.join(master.location, file))]:
            if regex.clean_name(folder, use_re=preference.clean_names) not in [category.name for category in option.kpack.categories]:
                category = option.kpack.categories.add()
                category.name = regex.clean_name(
                    folder, use_re=preference.clean_names)
                category.icon = 'FILE_FOLDER'
                category.folder = folder

                if folder in insert.thumbnails:
                    previews.remove(insert.thumbnails[folder])

                thumbnails = previews.new()
                thumbnails.location = os.path.join(master.location, folder)
                thumbnails.images = []

                insert.thumbnails[folder] = thumbnails

                add_blend(master.location, folder, category)

                if not len(category.blends):
                    option.kpack.categories.remove(
                        [category.name for category in option.kpack.categories].index(category.name))
            else:
                category = option.kpack.categories[regex.clean_name(
                    folder, use_re=preference.clean_names)]

                add_blend(master.location, folder, category)

            images = insert.thumbnails[folder].images
            enum_items = []
            for index, image in enumerate(images):
                enum_items.append(
                    (images[index][0], images[index][0][:14], images[index][0], images[index][1], index))

            insert.thumbnails[folder].images = enum_items

    option.kpack.categories.clear()

    reset = False
    for master in preference.folders:
        if master.location and master.location != 'Choose Path':
            if os.path.isdir(master.location):
                add_folder(master)
            else:
                master.name = 'KPACK'
                master.location = addon.path.default_kpack()

                add_folder(master)

                reset = True

    if reset:
        kpack(None, context)


def options():
    option = addon.option()

    kpack(None, bpy.context)


def icons():
    preview = previews.new()

    for file in os.listdir(addon.path.icons()):
        if file.endswith('.png'):
            preview.load(
                file[:-4], os.path.join(addon.path.icons(), file), 'IMAGE')

    addon.icons['main'] = preview


def libpath(prop, context):
    preference = addon.preference()

    for folder in preference.folders:
        if folder.location and folder.location != 'Choose Path':
            folder['location'] = os.path.abspath(
                bpy.path.abspath(folder.location))
            if not folder.name:
                folder.name = regex.clean_name(
                    os.path.basename(folder.location), use_re=True)
        elif not folder.location:
            folder['location'] = 'Choose Path'

    kpack(None, context)


def thumbnails(prop, context):
    option = addon.option()

    prop['active_index'] = [
        blend.name for blend in prop.blends].index(prop.thumbnail)
    option.kpack.active_index = [
        kpack.name for kpack in option.kpack.categories].index(prop.name)
    # bpy.ops.ko.add_insert('INVOKE_DEFAULT', location=prop.blends[prop.active_index].location)


def active_index(prop, context):
    pass
    # bpy.ops.ko.add_insert('INVOKE_DEFAULT', location=prop.blends[prop.active_index].location)


def mode(prop, context):
    inserts = [obj for obj in bpy.data.objects if obj.kitops.insert]

    for obj in inserts:
        obj.kitops.applied = True

        if prop.mode == 'REGULAR':
            obj.kitops['insert_target'] = None


def show_modifiers(prop, context):
    option = addon.option()

    inserts = insert.collect(all=True)

    for obj in bpy.data.objects:
        for modifier in obj.modifiers:
            if modifier.type == 'BOOLEAN' and modifier.object and modifier.object in inserts:
                modifier.show_viewport = option.show_modifiers


def show_solid_objects(prop, context):
    option = addon.option()

    for obj in insert.collect(solids=True, all=True):
        obj.hide_viewport = not option.show_solid_objects


def show_cutter_objects(prop, context):
    option = addon.option()

    for obj in insert.collect(cutters=True, all=True):
        obj.hide_viewport = not option.show_cutter_objects


def show_wire_objects(prop, context):
    option = addon.option()

    for obj in insert.collect(wires=True, all=True):
        obj.hide_viewport = not option.show_wire_objects


def location():
    if ray.success:
        track_quaternion = ray.normal.to_track_quat('Z', 'Y')
        matrix = track_quaternion.to_matrix().to_4x4()

        scale = insert.operator.main.matrix_world.to_scale()
        insert.operator.main.matrix_world = matrix
        insert.operator.main.matrix_world.translation = ray.location
        insert.operator.main.scale = scale


def insert_scale(prop, context):
    preference = addon.preference()
    option = addon.option()

    if option.auto_scale:
        if not insert.operator:
            print("not insert operator")
            mains = insert.collect(context.selected_objects, mains=True)
        else:
            print("operator")
            mains = [insert.operator.main]

        modifiers_shown = bool(option.show_modifiers)
        option.show_modifiers = False
        context.view_layer.update()

        for main in mains:
            if main.kitops.insert_target and smart_mode or insert.operator and not smart_mode:
                init_hide = copy(main.hide_viewport)
                main.hide_viewport = False

                scale = getattr(preference, '{}_scale'.format(
                    preference.insert_scale.lower()))

                if not main.kitops.insert_target:
                    continue

                bounds = modifier.unmodified_bounds(main.kitops.insert_target)
                coords = math.coordinates_dimension(bounds)
                largest_dimension = max(*coords) * (scale * 0.01)

                dimension = main.dimensions

                axis = 'x'
                if dimension.y > dimension.x:
                    axis = 'y'
                if dimension.z > getattr(dimension, axis):
                    axis = 'z'

                setattr(main.scale, axis, largest_dimension /
                        getattr(dimension, axis) * getattr(main.scale, axis))

                remaining_axis = [a for a in 'xyz' if a != axis]
                setattr(main.scale, remaining_axis[0], getattr(
                    main.scale, axis))
                setattr(main.scale, remaining_axis[1], getattr(
                    main.scale, axis))

                main.hide_viewport = init_hide

        if modifiers_shown:
            option.show_modifiers = True

    # context.view_layer.depsgraph.update()


sort_options = (
    'sort_modifiers',
    'sort_bevel',
    'sort_array',
    'sort_mirror',
    'sort_solidify',
    'sort_weighted_normal',
    'sort_simple_deform',
    'sort_triangulate',
    'sort_decimate',
    'sort_remesh',
    'sort_subsurf',
    'sort_bevel_last',
    'sort_array_last',
    'sort_mirror_last',
    'sort_solidify_last',
    'sort_weighted_normal_last',
    'sort_simple_deform_last',
    'sort_triangulate_last',
    'sort_decimate_last',
    'sort_remesh_last',
    'sort_subsurf_last')


def sync_sort(prop, context):
    for option in sort_options:

        if addon.hops() and hasattr(addon.hops().property, option):
            addon.hops().property[option] = getattr(prop, option)

        elif not hasattr(addon.hops().property, option):
            print(
                F'Unable to sync sorting options with Hard Ops; KIT OPS {option}\nUpdate Hard Ops!')

        if addon.bc() and hasattr(addon.bc().behavior, option):
            addon.bc().behavior[option] = getattr(prop, option)

        elif not hasattr(addon.bc().behavior, option):
            print(
                F'Unable to sync sorting options with Box Cutter; KIT OPS {option}\nUpdate Box Cutter!')
