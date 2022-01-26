import bpy

from bpy.types import (Panel,
                       # Menu,
                       Operator,
                       PropertyGroup,
                       )
from bpy.props import (
        FloatProperty,
        IntProperty,
        # BoolProperty,
        # StringProperty,
        # FloatVectorProperty,
        PointerProperty,
        )
import os
import random

bl_info = {
    "name": "Asset Snapshot",
    "author": "Johnny Matthews (guitargeek)",
    "category": "View3d",
    "location": "View3D > N Panel / Asset Browser Tab",
    "version": (1, 0, 2),
    "blender": (3, 0, 0),
    "description": "Mark active object as asset and render the current view as the asset preview",
}

def snapshot(self,context,ob):
    scene = context.scene
    tool = scene.asset_snapshot
    # Make sure we have a camera
    if bpy.context.scene.camera == None:
        bpy.ops.object.camera_add()
    
    #Save some basic settings
    camera = bpy.context.scene.camera    
    hold_camerapos = camera.location.copy()
    hold_camerarot = camera.rotation_euler.copy()
    hold_x = bpy.context.scene.render.resolution_x
    hold_y = bpy.context.scene.render.resolution_y 
    hold_filepath = bpy.context.scene.render.filepath
    
    
    
    # Find objects that are hidden in viewport and hide them in render
    tempHidden = []
    for o in bpy.data.objects:
        if o.hide_get() == True:
            o.hide_render = True
            tempHidden.append(o)
    
    # Change Settings
    bpy.context.scene.render.resolution_y = tool.resolution
    bpy.context.scene.render.resolution_x = tool.resolution
    switchback = False
    if bpy.ops.view3d.camera_to_view.poll():
        bpy.ops.view3d.camera_to_view()
        #Add Lights
        bpy.ops.object.light_add(type='AREA', radius=tool.lightradius, align='VIEW', location=(camera.location), scale=(1, 1, 1))
        light = bpy.context.active_object
        light.data.energy = tool.lightstrength
        switchback = True
    
    # Ensure outputfile is set to png (temporarily, at least)
    previousFileFormat = scene.render.image_settings.file_format
    if scene.render.image_settings.file_format != 'PNG':
        scene.render.image_settings.file_format = 'PNG'
    
    filename = str(random.randint(0,100000000000))+".png"
    filepath = str(os.path.abspath(os.path.join(os.sep, 'tmp', filename)))
    bpy.context.scene.render.filepath = filepath
    
    #Render File, Mark Asset and Set Image
    bpy.ops.render.render(write_still = True)
    ob.asset_mark()
    override = bpy.context.copy()
    override['id'] = ob
    bpy.ops.ed.lib_id_load_custom_preview(override,filepath=filepath)
    
    # Unhide the objects hidden for the render
    for o in tempHidden:
        o.hide_render = False
    # Reset output file format
    scene.render.image_settings.file_format = previousFileFormat
    
    #Cleanup
    os.unlink(filepath)
    bpy.context.scene.render.resolution_y = hold_y
    bpy.context.scene.render.resolution_x = hold_x
    camera.location = hold_camerapos
    camera.rotation_euler = hold_camerarot
    #remove light
    bpy.ops.object.delete()
    bpy.context.scene.render.filepath = hold_filepath
    if switchback:
        bpy.ops.view3d.view_camera()


class properties(PropertyGroup):
    resolution : IntProperty(
            name="Preview Resolution",
            description="Resolution to render the preview",
            min=1,
            soft_max=500,
            default=256
            )    
                 
    lightstrength : IntProperty(
            name="Light Strength",
            description="Change the stregth of the light sorce",
            min=1,
            soft_max=10000,
            default=1000
            )
            
    lightradius : FloatProperty(
            name="Light Radius",
            description="Change the radius of the light sorce",
            min=0.1,
            soft_max=100,
            default=3
            )

class AssetSnapshotCollection(Operator):
    """Create a preview of a collection"""
    bl_idname = "view3d.asset_snaphot_collection"
    bl_label = "Asset Snapshot - Collection"
    bl_options = {'REGISTER', 'UNDO'}
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


class OBJECT_PT_panel(Panel):
    bl_label = "Asset Snapshot"
    bl_idname = "OBJECT_PT_asset_snapshot_panel"
    bl_category = "Asset Snapshot"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    @classmethod
    def poll(self,context):
        return context.mode
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        tool = scene.asset_snapshot
        layout.prop(tool, "resolution")
        layout.prop(tool, "lightstrength")
        layout.prop(tool, "lightradius")
        layout.operator("view3d.object_preview")
        layout.operator("view3d.asset_snaphot_collection")


def register():
    bpy.utils.register_class(properties)
    bpy.utils.register_class(AssetSnapshotCollection)
    bpy.utils.register_class(AssetSnapshotObject)
    bpy.utils.register_class(OBJECT_PT_panel)
    
    bpy.types.Scene.asset_snapshot = PointerProperty(type=properties)

def unregister():
    bpy.utils.unregister_class(properties)
    bpy.utils.unregister_class(AssetSnapshotCollection)
    bpy.utils.unregister_class(AssetSnapshotObject)
    bpy.utils.unregister_class(OBJECT_PT_panel)
    
    del bpy.types.Scene.asset_snapshot

if __name__ == "__main__":
    register()
