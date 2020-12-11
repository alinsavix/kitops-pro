import bpy


def save_file(context):
    versions = context.preferences.filepaths.save_version
    context.preferences.filepaths.save_version = 0

    try: bpy.ops.wm.save_mainfile()
    except: print('KITOPS: Background save file exception')

    context.preferences.filepaths.save_version = versions


bpy.ops.file.pack_all()
save_file(bpy.context)
