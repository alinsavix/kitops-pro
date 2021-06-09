# Collection helper utilities.
import bpy

def init(context):
    """Initialize collections for inserts."""
    if 'INSERTS' not in bpy.data.collections:
        context.scene.collection.children.link(bpy.data.collections.new(name='INSERTS'))
    else:
        old_active = context.active_object

        objects = bpy.data.collections['INSERTS'].objects[:]
        children = bpy.data.collections['INSERTS'].children[:]

        bpy.data.collections.remove(bpy.data.collections['INSERTS'])

        context.scene.collection.children.link(bpy.data.collections.new(name='INSERTS'))

        for obj in objects:
            bpy.data.collections['INSERTS'].objects.link(obj)

        for child in children:
            bpy.data.collections['INSERTS'].children.link(child)
            
        context.view_layer.objects.active = old_active

    for obj in bpy.data.objects:
        for modifier in obj.modifiers:
            if modifier.type == 'BOOLEAN' and not modifier.object:
                obj.modifiers.remove(modifier)