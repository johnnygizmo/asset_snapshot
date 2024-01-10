import bpy, math

from bpy.types import (Panel,
                       # Menu,
                       Operator,
                       PropertyGroup,
                       )
from bpy.props import (
        FloatProperty,
        IntProperty,
        BoolProperty,
        # StringProperty,
        FloatVectorProperty,
        PointerProperty,
        )
from bpy import context
import os
import random

bl_info = {
    "name": "Asset Snapshot",
    "author": "Johnny Matthews (guitargeek), Draise, Daniel Ayala",
    "category": "View3d",
    "location": "View3D > N Panel / Asset Browser Tab",
    "version": (2, 0, 2),
    "blender": (4, 0, 0),
    "description": "Mark active object as asset and render the current view as the asset preview",
}

def is_in_collection(col, obj):
    for o in col.all_objects:
        if obj is o:
            return True
    return False

def snapshot_all_selected(self, context):
    selected_objects = bpy.context.selected_objects
    for asset_object in selected_objects:
        snapshot(self, context, asset_object, False)
    for asset_object in selected_objects:
        asset_object.select_set(True)

def snapshot(self,context,ob,is_collection):
    scene = context.scene
    tool = scene.asset_snapshot
    hold_camera = bpy.context.scene.camera
    # Make sure we have a camera
    if(tool.create_camera):
        camera_data = bpy.data.cameras.new("Camera AS")
        camera = bpy.data.objects.new("Camera AS", camera_data)
        bpy.context.scene.collection.objects.link(camera)
        bpy.context.scene.camera = camera
    else:
        camera = bpy.context.scene.camera
    
    #Save some basic settings
    hold_film = scene.render.film_transparent
    hold_cameratype = camera.data.type
    hold_camerapos = camera.location.copy()
    hold_camerarot = camera.rotation_euler.copy()
    hold_x = bpy.context.scene.render.resolution_x
    hold_y = bpy.context.scene.render.resolution_y 
    hold_filepath = bpy.context.scene.render.filepath

    if(tool.use_ortho):
        camera.data.type = 'ORTHO'

    if(tool.transparent_background):
        scene.render.film_transparent=True
    
    # Find objects that are hidden in viewport and hide them in render
    tempHidden = []
    for o in bpy.data.objects:
        o.select_set(False)
        if (tool.isolate_object and o.type in ['MESH','FONT','CURVE','VOLUME','SURFACE','META','CURVES','GREASEPENCIL','POINTCLOUD']) or o.hide_get() == True:
            if((not is_collection and (o != ob)) or (is_collection and (not is_in_collection(ob, o)))):
                o.hide_render = True
                tempHidden.append(o)
            else:
                o.select_set(True)

    if(tool.use_ortho):
        camera.rotation_euler = (tool.ortho_rotation)
        bpy.context.view_layer.update()
    if(tool.auto_position):
        bpy.ops.view3d.camera_to_view_selected()
        bpy.context.view_layer.update()
    if(tool.use_ortho):
        camera.data.ortho_scale = camera.data.ortho_scale * tool.ortho_scale_multiplier
    if(tool.auto_focus):
        if not is_collection:
            camera.data.dof.focus_object = ob
        else:
            camera.data.dof.focus_object = ob.all_objects[0]

    # Change Settings
    bpy.context.scene.render.resolution_y = tool.resolution
    bpy.context.scene.render.resolution_x = tool.resolution
    switchback = False
    if not tool.auto_position and bpy.ops.view3d.camera_to_view.poll():
        bpy.ops.view3d.camera_to_view()
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
    
    ### Draise - Removed due to not working with 4.0.0
        
    #context_override = bpy.context.copy()
    #context_override['id'] = ob
    #bpy.ops.ed.lib_id_load_custom_preview(context_override,filepath=filepath)

    ### Draise - Added to work with 4.0.0
    with context.temp_override(id=ob): 
        bpy.ops.ed.lib_id_load_custom_preview(filepath=filepath) #
    
    # Unhide the objects hidden for the render
    for o in tempHidden:
        o.hide_render = False
    # Reset output file format
    scene.render.image_settings.file_format = previousFileFormat
    
    #Cleanup
    os.unlink(filepath)
    scene.render.film_transparent = hold_film
    bpy.context.scene.render.resolution_y = hold_y
    bpy.context.scene.render.resolution_x = hold_x
    camera.data.type = hold_cameratype
    camera.location = hold_camerapos
    camera.rotation_euler = hold_camerarot
    bpy.context.scene.render.filepath = hold_filepath
    if tool.use_ortho:
        camera.data.ortho_scale = camera.data.ortho_scale / tool.ortho_scale_multiplier
    if tool.create_camera:
        bpy.data.objects.remove(camera, do_unlink=True)
    if switchback and not tool.create_camera:
        bpy.ops.view3d.view_camera()
    bpy.context.scene.camera = hold_camera


class properties(PropertyGroup):
    resolution : IntProperty(
            name="Preview Resolution",
            description="Resolution to render the preview",
            min=1,
            soft_max=500,
            default=256
            )
    ortho_rotation : FloatVectorProperty(
        name="Orthographic Rotation",
        subtype="EULER",
        unit="ROTATION",
        description="Rotation to use when the orthographic perspective setting is activated. Default value corresponds to isometric view",
        min=0,
        max=359,
        default=[math.radians(60.0), math.radians(0.0), math.radians(45.0)]
    )
    transparent_background : BoolProperty(
        name="Transparent Background",
        description="Whether or not to set the background to transparent",
        default=True
    )
    isolate_object : BoolProperty(
        name="Isolate Object",
        description="Whether or not to hide all other mesh objects in the scene before rendering",
        default=True
    )
    create_camera : BoolProperty(
        name="Create Camera",
        description="Whether or not to use a new camera that is deleted after rendering. If not, the active camera is used",
        default=True
    )
    auto_position : BoolProperty(
        name="Auto Position Camera",
        description="Whether or not to automatically center the object on the camera.",
        default=True
    )
    auto_focus : BoolProperty(
        name="Auto Focus",
        description="Whether or not to automatically focus on the object. Useful when using a camera with depth of field.",
        default=True
    )
    use_ortho : BoolProperty(
        name="Use Orthographic Perspective",
        description="Whether or not to set the camera to orthographic mode. If so, the orthographic rotation property is used for the rotation",
        default=True
    )
    ortho_scale_multiplier : FloatProperty(
            name="Orthographic Scale Multiplier",
            description="The multipication factor applied to the orthographic scale when the orthographic perspective setting is activated. Greater values result in wider fields of view.",
            min=0,
            soft_max=500,
            default=1.25
    )


class AssetSnapshotCollection(Operator):
    """Create a preview of a collection"""
    bl_idname = "view3d.asset_snaphot_collection"
    bl_label = "Asset Snapshot - Collection"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    #def poll(cls, context):
    def poll(cls, context):
        if context.area.type != 'VIEW_3D':
            return False
        if context.collection == None:
            return False
        return True
    def execute(self, context):
        snapshot(self, context, context.collection, True)
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
        snapshot(self, context, bpy.context.view_layer.objects.active, False)
        return {'FINISHED'}

class AssetSnapshotSelected(Operator):
    """Create an asset preview of every selected object"""
    bl_idname = "view3d.asset_snaphot_selected"
    bl_label = "Asset Snapshot - Selected"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        if context.area.type != 'VIEW_3D':
            return False
        if len(bpy.context.selected_objects) == 0:
            return False
        return True
    def execute(self, context):
        snapshot_all_selected(self, context)
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
        layout.prop(tool, "transparent_background")
        layout.prop(tool, "isolate_object")
        layout.prop(tool, "create_camera")
        layout.prop(tool, "auto_position")
        layout.prop(tool, "auto_focus")
        layout.prop(tool, "use_ortho")
        layout.prop(tool, "ortho_rotation")
        layout.prop(tool, "ortho_scale_multiplier")
        layout.operator("view3d.object_preview")
        layout.operator("view3d.asset_snaphot_collection")
        layout.operator("view3d.asset_snaphot_selected")


def register():
    bpy.utils.register_class(properties)
    bpy.utils.register_class(AssetSnapshotCollection)
    bpy.utils.register_class(AssetSnapshotSelected)
    bpy.utils.register_class(AssetSnapshotObject)
    bpy.utils.register_class(OBJECT_PT_panel)
    
    bpy.types.Scene.asset_snapshot = PointerProperty(type=properties)

def unregister():
    bpy.utils.unregister_class(properties)
    bpy.utils.unregister_class(AssetSnapshotCollection)
    bpy.utils.unregister_class(AssetSnapshotSelected)
    bpy.utils.unregister_class(AssetSnapshotObject)
    bpy.utils.unregister_class(OBJECT_PT_panel)
    
    del bpy.types.Scene.asset_snapshot

if __name__ == "__main__":
    register()
