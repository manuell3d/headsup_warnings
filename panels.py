import bpy

from .operators import *
from .preferences import *
from .properties import *

class VIEW3D_PT_HeadsUpPanel:
    bl_label = "HeadsUp"          # Panel title
   # bl_idname = "VIEW3D_PT_headsup_panel" # Unique ID for the panel
    bl_space_type = 'VIEW_3D'              # Specify the space type (3D View)
    bl_region_type = 'UI'                  # Place it in the UI sidebar
    bl_category = "HeadsUp"                # Tab name in the sidebar
   
    @classmethod
    def poll(cls, context):
        # Ensure the panel is only displayed when a 3D view is active
        return context.area.type == 'VIEW_3D'

class VIEW3D_PT_HeadsUpPanel_HeadsUp_Warnings(VIEW3D_PT_HeadsUpPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_warnings_panel"
    bl_label = "HeadsUp Warnings"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        prefs = bpy.context.preferences.addons[__package__].preferences
        props = bpy.context.scene.HEADSUP_WarnInfoProperties

        if not HEADSUP_Props.warn_state:
            row.label(text="No warnings to display :)")
            row = layout.row()
            row.operator("wm.headsup_open_preferences", text="HeadsUp Preferences", icon='PREFERENCES')
            return

        row.label(text="Read tooltips for more info", icon='INFO')
        row = layout.row()
        box=row.box()
        for i in range(1, 52):
            prop_name = f"warn_info_{i}"
            
            if getattr(props, prop_name, None):  
                prop_def = props.bl_rna.properties[prop_name]
                prop_name_display = prop_def.name
                row = box.row()
                icon = WarnInfoIconMap.get(i, 'QUESTION')
        
                row.prop(props, prop_name, icon=icon, text=prop_name_display)

        if getattr(props, "warn_info_custom", None):  
            prop_def = props.bl_rna.properties["warn_info_custom"]
            prop_name_display = prop_def.name
            row = box.row()
            row.prop(props, "warn_info_custom", icon='TEXT', text=prop_name_display)
        
        row = layout.row()
        row.operator("wm.headsup_open_preferences", text="HeadsUp Preferences", icon='PREFERENCES')

class VIEW3D_PT_HeadsUpPanel_Object_Mismatch(VIEW3D_PT_HeadsUpPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_object_mismatch_panel"
    bl_label = "Object Visibilities"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        prefs = bpy.context.preferences.addons[__package__].preferences
        
        if not prefs.warn_2:
            row.label(text="Mismatch Checks disabled in Preferences")
            return

        # Filter mismatches
        visible_mismatches = []
        non_visible_mismatches = []

        # Get the current view layer
        current_view_layer = bpy.context.view_layer

        # Separate mismatches into visible and non-visible in the current view layer
        for mismatch in HEADSUP_Props.object_mismatches:
            object = mismatch['object']
            visibility = mismatch['view_layers']  # A list of view layers the object is visible in

            # Check if the object is visible in the current view layer
            if current_view_layer.name in visibility:
                visible_mismatches.append(mismatch)
            # Check if visible in any other view layer
            elif any(visibility):  # Check if visible in any view layer from the list
                non_visible_mismatches.append(mismatch)

        # Sort the mismatches alphabetically by object name
        visible_mismatches.sort(key=lambda x: x['object'].name.lower())
        non_visible_mismatches.sort(key=lambda x: x['object'].name.lower())

        # Create UI layout for mismatches
        if not visible_mismatches and not non_visible_mismatches:
            row.label(text="No Object Mismatches")
        else:
            row.label(text="Viewport/Rendering Mismatch:")

            # Boxes for visible and non-visible objects
            visible_box = layout.box()
            non_visible_box = layout.box()

            # Labels for the boxes
            visible_box.label(text="In Current View Layer:")
            non_visible_box.label(text="In Other View Layer:")

            # Add objects to their respective boxes
            self.add_objects_to_box(visible_box, visible_mismatches, box_type='visible_box')
            self.add_objects_to_box(non_visible_box, non_visible_mismatches, box_type='non_visible_box')

    @staticmethod
    def add_objects_to_box(box, object_list, box_type):
        """Add objects and their mismatch details to the specified box."""
        if len(object_list) > 0:
            for mismatch in object_list:
                obj = mismatch['object']
                row = box.row()
                row.label(text=obj.name)

                # Display viewport and render icons
                icon_viewport = 'RESTRICT_VIEW_ON' if obj.hide_viewport else 'RESTRICT_VIEW_OFF'
                icon_render = 'RESTRICT_RENDER_ON' if obj.hide_render else 'RESTRICT_RENDER_OFF'
                row.label(icon=icon_viewport)
                row.label(icon=icon_render)

                # Add operator for selection only for visible box
                if box_type == 'visible_box':
                    op = row.operator("wm.headsup_select_highlight", text="", icon='OUTLINER')
                    op.object_name = obj.name

class VIEW3D_PT_HeadsUpPanel_Collection_Mismatch(VIEW3D_PT_HeadsUpPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_collection_mismatch_panel"
    bl_label = "Collection Visibilities"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        prefs = bpy.context.preferences.addons[__package__].preferences         

        if not prefs.warn_2:
            row.label(text="Mismatch Checks disabled in Preferences")
            return

        # Filter mismatches
        visible_mismatches = []
        non_visible_mismatches = []

        # Get the current view layer
        current_view_layer = bpy.context.view_layer

        # Separate mismatches into visible and non-visible in the current view layer
        for mismatch in HEADSUP_Props.collection_mismatches:
            collection_name = mismatch['collection_name']
            visibility = mismatch['view_layers']  # A list of view layers the object is visible in

            # Check if the object is visible in the current view layer
            if current_view_layer.name in visibility:
                visible_mismatches.append(mismatch)
            # Check if visible in any other view layer
            elif any(visibility):  # Check if visible in any view layer from the list
                non_visible_mismatches.append(mismatch)

        # Sort the mismatches alphabetically for consistent display
        visible_mismatches.sort(key=lambda x: x['collection_name'])
        non_visible_mismatches.sort(key=lambda x: x['collection_name'])

        # Create UI layout for mismatches
        if not visible_mismatches and not non_visible_mismatches:
            row.label(text="No Collection Mismatches")
        else:
            row.label(text="Viewport/Rendering Mismatch:")

            # Boxes for visible and non-visible objects
            visible_box = layout.box()
            non_visible_box = layout.box()

            # Labels for the boxes
            visible_box.label(text="In Current View Layer:")
            non_visible_box.label(text="In Other View Layer:")

            # Add objects to their respective boxes
            self.add_objects_to_box(visible_box, visible_mismatches, box_type='visible_box')
            self.add_objects_to_box(non_visible_box, non_visible_mismatches, box_type='non_visible_box')

    @staticmethod
    def add_objects_to_box(box, object_list, box_type):
        """Add objects and their mismatch details to the specified box."""
        if len(object_list) > 0:
            for mismatch in object_list:
                col_name = mismatch['collection_name']
                col = bpy.data.collections.get(col_name)
                row = box.row()
                row.label(text=col_name)

                # Display viewport and render icons
                icon_viewport = 'RESTRICT_VIEW_ON' if col.hide_viewport else 'RESTRICT_VIEW_OFF'
                icon_render = 'RESTRICT_RENDER_ON' if col.hide_render else 'RESTRICT_RENDER_OFF'
                row.label(icon=icon_viewport)
                row.label(icon=icon_render)

                # Add operator for selection 
                op = row.operator("wm.headsup_highlight_collection", text="", icon='BORDERMOVE')
                op.collection_name = col_name

class VIEW3D_PT_HeadsUpPanel_Modifier_Mismatch(VIEW3D_PT_HeadsUpPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_modifier_mismatch_panel"
    bl_label = "Modifier Visibilities"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        prefs = bpy.context.preferences.addons[__package__].preferences
        
        row = layout.row()
        row.prop(prefs, "warn_25_a", text="Check")
        row = layout.row()

        if prefs.warn_25_a == 'ACTIVE_ONLY':
            row.label(text="'Active Only' reports to 3d viewport")
            return

        # Filter mismatches
        visible_mismatches = []
        non_visible_mismatches = []

        # Get the current view layer
        current_view_layer = bpy.context.view_layer

        # Separate mismatches into visible and non-visible in the current view layer
        for mismatch in HEADSUP_Props.modifier_mismatches:
            object = mismatch['object']
            visibility = mismatch['view_layers']  # A list of view layers the object is visible in

            # Check if the object is visible in the current view layer
            if current_view_layer.name in visibility:
                visible_mismatches.append(mismatch)
            # Check if visible in any other view layer
            elif any(visibility):  # Check if visible in any view layer from the list
                non_visible_mismatches.append(mismatch)

        # Sort the mismatches alphabetically for consistent display
        visible_mismatches.sort(key=lambda x: x['object'].name.lower())
        non_visible_mismatches.sort(key=lambda x: x['object'].name.lower())

        # Create UI layout for mismatches
        if not visible_mismatches and not non_visible_mismatches:
            row.label(text="No Modifier Mismatches")
        else:
            row.label(text="Viewport/Rendering Mismatch:")

            # Boxes for visible and non-visible objects
            visible_box = layout.box()
            non_visible_box = layout.box()

            # Labels for the boxes
            visible_box.label(text="In Current View Layer:")
            non_visible_box.label(text="In Other View Layer:")

            # Add objects to their respective boxes
            self.add_objects_to_box(visible_box, visible_mismatches, box_type='visible_box')
            self.add_objects_to_box(non_visible_box, non_visible_mismatches, box_type='non_visible_box')

    @staticmethod
    def add_objects_to_box(box, object_list, box_type):
        """Add objects and their mismatch details to the specified box."""
        if len(object_list) > 0:
            for mismatch in object_list:
                obj = mismatch['object']
                row = box.row()
                row.label(text=obj.name)

                # Display viewport and render icons
                icon_viewport = 'RESTRICT_VIEW_ON' if obj.hide_viewport else 'RESTRICT_VIEW_OFF'
                icon_render = 'RESTRICT_RENDER_ON' if obj.hide_render else 'RESTRICT_RENDER_OFF'
                row.label(icon=icon_viewport)
                row.label(icon=icon_render)

                # Add operator for selection only for visible box
                if box_type == 'visible_box':
                    op = row.operator("wm.headsup_select_highlight", text="", icon='OUTLINER')
                    op.object_name = obj.name

class VIEW3D_PT_HeadsUpPanel_Undefined_Nodes(VIEW3D_PT_HeadsUpPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_undefined_nodes_panel"
    bl_label = "Undefined Nodes"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        prefs = bpy.context.preferences.addons[__package__].preferences

        if not prefs.warn_41:
            row.label(text="Check for 'Undefined' nodes disabled in Preferences")
            return

        # Create UI layout for mismatches
        if not HEADSUP_Props.undefined_nodes:
            row.label(text="No 'Undefined' nodes found")
        else:
            row.label(text="Materials contain 'Undefined' nodes:")

            # Boxes for visible and non-visible objects
            box = layout.box()
            for material in HEADSUP_Props.undefined_nodes:
                row = box.row()
                row.label(text=material)

def register():
    bpy.utils.register_class(VIEW3D_PT_HeadsUpPanel_HeadsUp_Warnings)
    bpy.utils.register_class(VIEW3D_PT_HeadsUpPanel_Collection_Mismatch)
    bpy.utils.register_class(VIEW3D_PT_HeadsUpPanel_Object_Mismatch)
    bpy.utils.register_class(VIEW3D_PT_HeadsUpPanel_Modifier_Mismatch)
    bpy.utils.register_class(VIEW3D_PT_HeadsUpPanel_Undefined_Nodes)
    

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_HeadsUpPanel_HeadsUp_Warnings)
    bpy.utils.unregister_class(VIEW3D_PT_HeadsUpPanel_Collection_Mismatch)
    bpy.utils.unregister_class(VIEW3D_PT_HeadsUpPanel_Object_Mismatch)  
    bpy.utils.unregister_class(VIEW3D_PT_HeadsUpPanel_Modifier_Mismatch)  
    bpy.utils.unregister_class(VIEW3D_PT_HeadsUpPanel_Undefined_Nodes)