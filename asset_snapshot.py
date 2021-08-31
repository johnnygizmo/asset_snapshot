import bpy
from bpy.types import Operator
from bpy.props import (
        # FloatProperty,
        IntProperty,
        # BoolProperty,
        # StringProperty,
        # FloatVectorProperty
        )
import os

bl_info = {
    'name': 'Asset Snapshot',
    'category': 'View3d',
    "blender": (3, 0, 0),
}


def snapshot(self,context,ob):
    #Save some basic settings
    areatype = context.area.type
    if bpy.context.scene.camera == None:
        bpy.ops.object.camera_add()
    camera = bpy.context.scene.camera    
    camerapos = camera.location.copy()
    camerarot = camera.rotation_euler.copy()
    hold_x = bpy.context.scene.render.resolution_x
    hold_y = bpy.context.scene.render.resolution_y 
    filepath = bpy.context.scene.render.filepath
    
    
    # Find objects that are hidden in viewport and hide them in render
    tempHidden = []
    for o in bpy.data.objects:
        if o.hide_get() == True:
            o.hide_render = True
            tempHidden.append(o)
    
    
    # Change Settings
    bpy.context.scene.render.resolution_y = self.resolution
    bpy.context.scene.render.resolution_x = self.resolution
    if bpy.ops.view3d.camera_to_view.poll():
        bpy.ops.view3d.camera_to_view()  
    bpy.context.scene.render.filepath = os.path.join("/tmp", ob.name) 
    file = os.path.join("/tmp", ob.name)+".png"
    
    
    #Render File, Mark Asset and Set Image
    bpy.ops.render.render(write_still = True)
    ob.asset_mark()
    override = bpy.context.copy()
    context.area.type = 'FILE_BROWSER'
    override['id'] = ob
    bpy.ops.ed.lib_id_load_custom_preview(override,filepath=file)
    
    
    # Unhide the objects hidden for the render
    for o in tempHidden:
        o.hide_render = False
    
    
    #Cleanup
    context.area.type = areatype
    os.unlink(file)
    bpy.context.scene.render.resolution_y = hold_y
    bpy.context.scene.render.resolution_x = hold_x
    camera.location = camerapos
    camera.rotation_euler = camerarot
    bpy.context.scene.render.filepath = filepath
    bpy.ops.view3d.view_camera()


class AssetSnapshotCollection(Operator):
    """Create a preview of a collection"""
    bl_idname = "view3d.asset_snaphot_collection"
    bl_label = "Asset Snapshot - Collection"
    bl_options = {'REGISTER', 'UNDO'}
    resolution: IntProperty(
            name="Preview Resolution",
            description="Resolution to render the preview",
            min=1,
            soft_max=500,
            default=256
            )
    @classmethod
    def poll(cls, context):
        if context.area.type != 'VIEW_3D':
            return False
        if context.collection == None:
            return False
        return True
    def execute(self, context):
        snapshot(self, context,context.collection)
        return {'FINISHED'}


class AssetSnapshotObject(Operator):
    """Create an asset preview of an object"""
    bl_idname = "view3d.object_preview"
    bl_label = "Asset Snapshot - Object"
    bl_options = {'REGISTER', 'UNDO'}
    resolution: IntProperty(
            name="Preview Resolution",
            description="Resolution to render the preview",
            min=1,
            soft_max=500,
            default=250
            )
    @classmethod
    def poll(cls, context):
        if context.area.type != 'VIEW_3D':
            return False
        if context.view_layer.objects.active == None:
            return False
        return True
    def execute(self, context):
        snapshot(self, context, bpy.context.view_layer.objects.active)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(AssetSnapshotCollection)
    bpy.utils.register_class(AssetSnapshotObject)

def unregister():
    bpy.utils.unregister_class(AssetSnapshotCollection)
    bpy.utils.unregister_class(AssetSnapshotObject)

if __name__ == "__main__":
    register()
