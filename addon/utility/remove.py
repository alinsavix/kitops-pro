# Helper package for object removal.

import bpy

# TODO KNOWN ISSUE: It seems that the call to bpy.data.<ref>.remove() gets longer after each SYNTH run.  This is a known issue but appears inherent to Blender.

def object(obj, data=False):
    if data:
        object_data(obj)

    try:
        bpy.data.objects.remove(obj, do_unlink=True, do_id_user=True, do_ui_user=True)
    except: pass


def object_data(obj):
    try:
        if obj.data:
            if obj.type == 'MESH':
                bpy.data.meshes.remove(obj.data, do_unlink=True, do_id_user=True, do_ui_user=True)
            elif obj.type not in {'FONT', 'META', 'SURFACE', 'CURVE'}:
                getattr(bpy.data, '{}s'.format(obj.type.lower())).remove(obj.data, do_unlink=True, do_id_user=True, do_ui_user=True)

            elif obj.type in {'FONT', 'SURFACE', 'CURVE'}:
                bpy.data.curves.remove(obj.data, do_unlink=True, do_id_user=True, do_ui_user=True)

            else:
                bpy.data.metaballs.remove(obj.data, do_unlink=True, do_id_user=True, do_ui_user=True)
    except: pass
