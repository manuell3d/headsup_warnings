import bpy

from .utils import *
from .properties import *
from .preferences import *

class HEADSUP_OT_Select_Highlight(bpy.types.Operator):
    bl_idname = "wm.headsup_select_highlight"         # Unique identifier
    bl_label = ""                 # Label for the operator button
    bl_description = "Select and highlight in Outliner"  # Tooltip description
    bl_options = {'UNDO'}          # Allows for undo functionality

    object_name: bpy.props.StringProperty(     # Property to hold the object name
        name="Object Name",
        description="Name of the object to select",
        default="Cube"
    )

    def get_outliner_area_and_region(self):
        """Finds and returns the Outliner area and its region."""
        for area in bpy.context.screen.areas:
            if area.type == 'OUTLINER':
                for region in area.regions:
                    if region.type == 'WINDOW':  # Ensure the region is of type 'WINDOW'
                        return area, region
        return None, None

    def execute(self, context):
        # Attempt to get the object by the provided name
        obj = bpy.context.scene.objects.get(self.object_name)
        
        if obj:
            if bpy.context.mode == 'OBJECT':   
                # Deselect all objects first
                bpy.ops.object.select_all(action='DESELECT')
                
                # Select the specified object and make it active
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                # Find the Outliner area and region
                area, region = self.get_outliner_area_and_region()
                if area and region:
                    # Use temp_override with the correct area and region
                    with bpy.context.temp_override(area=area, region=region):
                        space = bpy.context.space_data
                        space.filter_text = ""
                        bpy.ops.outliner.show_active()
                        space.show_restrict_column_holdout = True
                        space.show_restrict_column_viewport = True
                        space.show_restrict_column_render = True
                        space.show_restrict_column_select = True
                        space.show_restrict_column_hide = True
                        space.show_restrict_column_enable = True
                        space.show_restrict_column_indirect_only = True
                    self.report({'INFO'}, "Object successfully highlighted in Outliner!")
            else:
                self.report({'WARNING'}, "Highlighting only works in Object Mode!")
                return {'CANCELLED'}


            return {'FINISHED'}
        else:
            return {'CANCELLED'}
    
class HEADSUP_OT_Select_Highlight_Collection(bpy.types.Operator):
    """Highlight a collection in the Outliner and search for it's name"""
    bl_idname = "wm.headsup_highlight_collection"
    bl_label = "Highlight Collection"
    bl_options = {'UNDO'}
    
    collection_name: bpy.props.StringProperty(
        name="Collection Name",
        description="Name of the collection to highlight",
        default=""
    )
    
    def execute(self, context):
        # Check if the collection exists
        collection = bpy.data.collections.get(self.collection_name)
        if not collection:
            self.report({'ERROR'}, f"Collection '{self.collection_name}' not found")
            return {'CANCELLED'}
        
        # Set the active collection
        context.view_layer.active_layer_collection = self.find_layer_collection(
            context.view_layer.layer_collection, self.collection_name
        )
        
        if context.view_layer.active_layer_collection is None:
            self.report({'ERROR'}, f"Collection '{self.collection_name}' could not be highlighted")
            return {'CANCELLED'}
        
        # Set the Outliner search filter to the collection name
        self.set_outliner_filter(context, self.collection_name)

        self.report({'INFO'}, f"Collection '{self.collection_name}' highlighted")
        return {'FINISHED'}
    
    def find_layer_collection(self, layer_collection, name):
        """Recursively find the layer collection with the specified name"""
        if layer_collection.collection.name == name:
            return layer_collection
        for child in layer_collection.children:
            found = self.find_layer_collection(child, name)
            if found:
                return found
        return None
    
    def set_outliner_filter(self, context, name):
        """Set the Outliner search filter text to the specified name"""
        for area in context.screen.areas:
            if area.type == 'OUTLINER':
                for space in area.spaces:
                    if space.type == 'OUTLINER':
                        space.filter_text = name
                        #space.use_filter_complete = True # This turns on 'Exact Match' in the Outliner, but it stays turned on which might be undesired...
                        space.show_restrict_column_holdout = True
                        space.show_restrict_column_viewport = True
                        space.show_restrict_column_render = True
                        space.show_restrict_column_select = True
                        space.show_restrict_column_hide = True
                        space.show_restrict_column_enable = True
                        space.show_restrict_column_indirect_only = True

class HEADSUP_OT_Store_Color(bpy.types.Operator):
    bl_idname = "wm.headsup_store_color"
    bl_label = "Store the current theme color in the Original Theme Color preference."

    def execute(self, context):
        store_original_theme_color()
        self.report({'INFO'}, "HeadsUp: Stored current theme color!")
        return {'FINISHED'}

class HEADSUP_OT_OpenPreferences(bpy.types.Operator):
    """Open Preferences in Add-Ons Tab with 'HeadsUp' in Search"""
    bl_idname = "wm.headsup_open_preferences"
    bl_label = "Open HeadsUp Preferences"

    def execute(self, context):
        open_headsup_prefs()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(HEADSUP_OT_Store_Color)
    bpy.utils.register_class(HEADSUP_OT_Select_Highlight)
    bpy.utils.register_class(HEADSUP_OT_Select_Highlight_Collection)
    bpy.utils.register_class(HEADSUP_OT_OpenPreferences)

def unregister():
    bpy.utils.unregister_class(HEADSUP_OT_Store_Color)
    bpy.utils.unregister_class(HEADSUP_OT_Select_Highlight)
    bpy.utils.unregister_class(HEADSUP_OT_Select_Highlight_Collection)
    bpy.utils.unregister_class(HEADSUP_OT_OpenPreferences)