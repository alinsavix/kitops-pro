import os

import bpy

from . import addon, id, ray, remove, regex, update, modifier

thumbnails = {}
operator = None

def authoring():
    if not bpy.context or not hasattr(bpy.context, 'scene'):
        return False

    preference = addon.preference()

    if bpy.context.scene.kitops.factory:
        return True

    insert_file = False
    for folder in preference.folders:
        path = os.path.commonprefix([bpy.data.filepath, os.path.realpath(folder.location)])
        if path == os.path.realpath(folder.location):
            if os.path.basename(bpy.data.filepath) != 'render.blend':
                insert_file = True
                break

    return insert_file if not bpy.context.scene.kitops.thumbnail else False

def hide_handler(op):
    option = addon.option()
    hide = False

    if op.duplicate:
        ray.cast(op)
        hide = not ray.success

        for obj in op.inserts:
            obj.hide_viewport = hide

        for obj in op.cutter_objects:
            for modifier in op.boolean_target.modifiers:
                if modifier.type == 'BOOLEAN' and modifier.object == obj:
                    modifier.show_viewport = not hide

def collect(objs=[], mains=False, solids=False, cutters=False, wires=False, all=False):
    if all:
        inserts = [obj for obj in bpy.data.objects if obj.kitops.insert]

    else:
        inserts = [obj for obj in objs if obj.kitops.insert]

        for check_object in inserts:
            for obj in bpy.data.objects:
                if obj.kitops.id == check_object.kitops.id:
                    if obj not in inserts:
                        inserts.append(obj)

    inserts = sorted(inserts, key=lambda o: o.name)

    if mains:
        return [obj for obj in inserts if obj.kitops.main]

    elif solids:
        return [obj for obj in inserts if obj.kitops.type == 'SOLID']

    elif cutters:
        return [obj for obj in inserts if obj.kitops.type == 'CUTTER']

    elif wires:
        return [obj for obj in inserts if obj.kitops.type == 'WIRE']

    return inserts

def add(op, context):
    preference = addon.preference()
    option = addon.option()

    strip_num = lambda string: string.rstrip('0123456789.') if len(string.split('.')) == 2 else string

    basename = os.path.basename(op.location)
    material_ids = [mat.kitops.id for mat in bpy.data.materials if mat.kitops.id]
    kitops_materials = [regex.clean_name(strip_num(mat.name), use_re=preference.clean_names) for mat in bpy.data.materials if mat.kitops.material]

    with bpy.data.libraries.load(op.location) as (blend, imported):
        imported.objects = blend.objects
        # imported.scenes = blend.scenes
        imported.materials = blend.materials

    op.inserts = []

    for obj in sorted(imported.objects, key=lambda obj: obj.name):
        if not obj.kitops.hide:
            op.inserts.append(obj)

    op.cutter_objects = [obj for obj in op.inserts if obj.kitops.type == 'CUTTER']

    new_id = id.uuid()

    for obj in op.inserts:
        obj.name = regex.clean_name(F'{basename[:-6].title()}_{obj.name.title()}', use_re=preference.clean_names)
        obj.kitops.inserted = True
        obj.kitops.id = new_id
        obj.kitops.label = regex.clean_name(basename, use_re=preference.clean_names)
        obj.kitops.collection = regex.clean_name(os.path.basename(str(op.location)[:-len(os.path.basename(op.location)) - 1]), use_re=preference.clean_names)

        if preference.mode == 'REGULAR':
            obj.kitops.applied = True

        if op.boolean_target:
            obj.kitops['insert_target'] = op.boolean_target
            obj.kitops.reserved_target = op.boolean_target

        for slot in obj.material_slots:
            if slot.material:
                slot.material.kitops.material = False

            # needs id check for standard assign
            if slot.material and regex.clean_name(slot.material.name, use_re=preference.clean_names) in kitops_materials and not op.material:
                old_material = bpy.data.materials[slot.material.name]
                slot.material = bpy.data.materials[regex.clean_name(slot.material.name, use_re=preference.clean_names)]

                if old_material.users == 0:
                    bpy.data.materials.remove(old_material, do_unlink=True, do_id_user=True, do_ui_user=True)

            elif slot.material and not op.material:
                slot.material.name = regex.clean_name(slot.material.name, use_re=preference.clean_names)
                bpy.data.materials[slot.material.name].kitops.material = True

            elif slot.material and op.material_link:
                if slot.material.kitops.id:
                    if slot.material.kitops.id in material_ids:
                        op.import_material = [mat for mat in bpy.data.materials if mat.kitops.id and mat.kitops.id == slot.material.kitops.id][0]
                        op.import_material.kitops.material = True
                        break

                    else:
                        op.import_material = slot.material
                        op.import_material.kitops.material = True
                        break

                elif regex.clean_name(strip_num(slot.material.name), use_re=preference.clean_names) in kitops_materials:
                    if strip_num(slot.material.name) in bpy.data.materials:
                        mats = [m for m in sorted(bpy.data.materials[:], key=lambda m: m.name) if m.kitops.material and regex.clean_name(strip_num(slot.material.name)) == regex.clean_name(strip_num(m.name)) and m != slot.material]

                        if mats:
                            op.import_material = mats[0]
                            break

                        op.import_material = slot.material

                    else:
                        op.import_material = slot.material
                    op.import_material.kitops.material = True
                    break

                else:
                    op.import_material = slot.material
                    op.import_material.kitops.material = True
                    break

            elif slot.material and op.material:
                slot.material.name = regex.clean_name(slot.material.name, use_re=preference.clean_names)
                op.import_material = slot.material
                bpy.data.materials[slot.material.name].kitops.material = True
                break

    for obj in op.inserts:
        if regex.clean_name(basename[:-6].title(), use_re=preference.clean_names) not in bpy.data.collections:
            bpy.data.collections['INSERTS'].children.link(bpy.data.collections.new(name=regex.clean_name(basename[:-6].title(), use_re=preference.clean_names)))

        bpy.data.collections[regex.clean_name(basename[:-6].title(), use_re=preference.clean_names)].objects.link(obj)
        obj.kitops.applied = False

        if obj.kitops.main:
            bpy.context.view_layer.objects.active = obj

    if op.boolean_target:
        for obj in op.cutter_objects:
            # if obj.kitops.boolean_type != 'INSERT':
            add_boolean(obj)

    op.main = context.active_object
    # if op.init_active:
    #     op.main.parent = op.init_active

    for obj in op.inserts:
        obj.kitops.main_object = op.main

    if op.init_selected and op.boolean_target:
        update.insert_scale(None, context)

    for scene in imported.scenes:
        bpy.data.scenes.remove(scene, do_unlink=True)

    for material in imported.materials:
        try:
            if not material.kitops.material:
                bpy.data.materials.remove(material, do_unlink=True, do_id_user=True, do_ui_user=True)
        except: continue

    for obj in op.inserts:
        obj.kitops.insert = True
        if obj.data:
            obj.data.kitops.insert = True

    update.insert_scale(None, context)

    return new_id


def add_boolean(obj):
    if obj.kitops.boolean_type == 'INSERT':
        return

    mod = obj.kitops.insert_target.modifiers.new(name='{}: {}'.format(obj.kitops.boolean_type.title(), obj.name), type='BOOLEAN')
    mod.show_expanded = False
    mod.operation = obj.kitops.boolean_type
    mod.object = obj

    if hasattr(mod, 'solver'):
        mod.solver = addon.preference().boolean_solver

    obj.show_all_edges = False

    ignore_vgroup = addon.preference().sort_bevel_ignore_vgroup
    ignore_verts = addon.preference().sort_bevel_ignore_only_verts
    bevels = modifier.bevels(obj.kitops.insert_target, vertex_group=ignore_vgroup, props={'use_only_vertices': True} if ignore_verts else {})
    modifier.sort(obj.kitops.insert_target, option=addon.preference(), ignore=bevels)
    # modifier.sort(obj.kitops.insert_target, option=addon.preference())

def select():
    global operator

    if not hasattr(bpy.context, 'selected_objects'):
        return

    if addon.option().auto_select:
        inserts = collect(bpy.context.selected_objects)
        main_objects = collect(inserts, mains=True)

        for obj in inserts:
            if not operator:
                if obj.kitops.selection_ignore and obj.select_get():
                    addon.option().auto_select = False

                    for deselect in inserts:
                        if deselect != obj:
                           deselect.select_set(False)

                    break

                elif not obj.kitops.selection_ignore:
                    obj.select_set(True)
            else:
                obj.select_set(True)

            if not operator:
                obj.hide_viewport = False

            if bpy.context.active_object and bpy.context.active_object.kitops.insert:
                for main in main_objects:
                    if main.kitops.id == bpy.context.active_object.kitops.id:
                        bpy.context.view_layer.objects.active = main

                        if not operator and main:
                            bpy.context.active_object.hide_viewport = False

def show_solid_objects():
    for obj in collect(solids=True, all=True):
        try:
            if not obj.select_get() and not addon.option().show_solid_objects:
                obj.hide_viewport = True

            elif addon.option().show_solid_objects:
                obj.hide_viewport = False
        except RuntimeError: pass

def show_cutter_objects():
    for obj in collect(cutters=True, all=True):
        try:
            if not obj.select_get() and not addon.option().show_cutter_objects:
                obj.hide_viewport = True

            elif addon.option().show_cutter_objects:
                obj.hide_viewport = False
        except RuntimeError: pass

def show_wire_objects():
    for obj in collect(wires=True, all=True):
        try:
            if not obj.select_get() and not addon.option().show_wire_objects:
                obj.hide_viewport = True

            elif addon.option().show_wire_objects:
                obj.hide_viewport = False
        except RuntimeError: pass

def correct_ids():
    main_objects = collect(mains=True, all=True)

    ids = []
    correct = []
    for obj in main_objects:
        if obj.kitops.id not in ids:
            ids.append(obj.kitops.id)
        else:
            correct.append(obj)

    inserts = collect(all=True)

    for main in correct:
        new_id = id.uuid()
        for obj in inserts:
            if obj.kitops.main_object == main:
                obj.kitops.id = new_id
