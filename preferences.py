import bpy
from .properties import *

class HEADSUP_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    # Callback function for certain property changes
    def prop_update_callback(self, context):
        HEADSUP_Props.load_up_done = False

    # Customizable properties for colors and text size
    warn_color: bpy.props.FloatVectorProperty(
        name="Warn Color",
        subtype='COLOR_GAMMA',
        default=(1.0, 0.618573, 0.274545),
        size=3,  # Specify size for RGBA
        min=0.0, max=1.0,
        description="Color of the main warning text",
    )
    highlight_color: bpy.props.FloatVectorProperty(
        name="Highlight Color",
        subtype='COLOR_GAMMA',
        default=(1,1,1),
        size=3,  # Specify size for RGBA
        min=0.0, max=1.0,
        description="Color of the text and brackets within [ ]",
    )
    text_size: bpy.props.IntProperty(
        name="",
        default=11,
        min=6, max=72,
        description="Size of the warning text"
    )
    
    original_theme_color: bpy.props.FloatVectorProperty(
        name="Original Theme Color",
        subtype='COLOR_GAMMA',
        size=3,
        default=(0.0, 0.0, 0.0),
    )
    
    UI_color_change_bool: bpy.props.BoolProperty(
        name="Only display text warning",
        description="Do not change the UI border color to warn me",
        default=False
    ) 
    
    warn_1: bpy.props.BoolProperty(
        name="Viewport: Lock Camera to View",
        description="Warn me about 'Camera to View' being active, as it can be destructive and is not undo-able",
        default=True,
    ) 
    
    warn_2: bpy.props.BoolProperty(
        name="Viewport/Render: Visibility Mismatch",
        description="Warn me about mismatches for the Render/Viewport visiblity Settings of collections or objects",
        default=True,
        update=prop_update_callback
    ) 
    
    warn_3: bpy.props.BoolProperty(
        name="Sculpt: Shapekey Value not 1",
        description="Warn me about Sculpting on a Shapekey which is not set to Value 1.0",
        default=True
    ) 
    
    warn_4: bpy.props.BoolProperty(
        name="Animation: Auto Keying",
        description="Warn me about 'Auto Keying' being active",
        default=True
    ) 

    warn_4_a: bpy.props.BoolProperty(
        name="⏺[REC]",
        description="Add a red dot in the corner of the viewport",
        default=True
    ) 
    
    warn_5: bpy.props.BoolProperty(
        name="General: Proportional Editing",
        description="Warn me about Proportional Editing being active",
        default=True
    ) 
    
    warn_6: bpy.props.BoolProperty(
        name="General: Affect Only",
        description="Warn me about any of the Affect Only (Origins/Locations/Parents) being active",
        default=True
    ) 
    
    warn_7: bpy.props.BoolProperty(
        name="General: Snapping",
        description="Warn me about Snapping",
        default=True
    ) 
    
    warn_8: bpy.props.BoolProperty(
        name="Active Object: Scaling Issues",
        description="Warn me about Scaling Issues",
        default=True
    ) 
    
    warn_8_a: bpy.props.BoolProperty(
        name="Negative",
        description="Warn me about Scaling Issues",
        default=True
    ) 
    warn_8_b: bpy.props.BoolProperty(
        name="Non-Uniform",
        description="Warn me about Scaling Issues",
        default=False
    ) 
    warn_8_c: bpy.props.BoolProperty(
        name="Non-1",
        description="Warn me about Scaling Issues",
        default=False
    ) 
    
    warn_9: bpy.props.BoolProperty(
        name="Edit: Mirror Options",
        description="Warn me about Mirror options being active",
        default=True
    ) 
    
    warn_10: bpy.props.BoolProperty(
        name="Render: Simplify",
        description="Warn me about Simplify being active when below treshhold values",
        default=True
    ) 
    
    warn_10_a: bpy.props.BoolProperty(
        name="Only warn for 'Render' subdivisions",
        description="Warn me about Simplify being active when below treshhold values",
        default=True
    ) 
    
    warn_11: bpy.props.BoolProperty(
        name="Sequencer: Sequencer contains Strips",
        description="Warn me about Post Processing 'Use Sequencer' being active while the Sequencer contains strips",
        default=True
    ) 
    
    warn_12: bpy.props.BoolProperty(
        name="Render: Render Region",
        description="Warn me about a Render Region being used",
        default=True
    ) 
    
    warn_13: bpy.props.BoolProperty(
        name="Edit: Auto-Merge Vertices",
        description="Warn me about Auto-merge Vertices being active",
        default=True
    ) 
    
    warn_14: bpy.props.BoolProperty(
        name="UV: Select Sync",
        description="Warn me about UV Select Sync being active, only showing UVs for selected Geometry",
        default=True
    ) 
    
    warn_15: bpy.props.BoolProperty(
        name="UV: Live Unwrap",
        description="Warn me about Live Unwrap being active",
        default=True
    ) 
    
    warn_16: bpy.props.BoolProperty(
        name="UV: Correct Face Attributes",
        description="Warn me about Correct Face Attributes being active. This can change the UVs with transforms done in edit mode",
        default=True
    ) 
    
    warn_17: bpy.props.BoolProperty(
        name="Material: Img-Sequence not unique",
        description="Warn me about Multiple Image Sequence Nodes using the same image datablock with different settings. This will not work",
        default=True,
        update=prop_update_callback
    ) 
      
    warn_18: bpy.props.BoolProperty(
        name="Sculpt: Corrective Smooth active",
        description="Warn me about active Corrective Smooth modifiers when in Sculpt Mode",
        default=True
    ) 
    
    warn_19: bpy.props.BoolProperty(
        name="General: Autopack Ressources",
        description="Warn me when Autopacking is activated for the current file",
        default=True
    )   
    
    warn_20: bpy.props.BoolProperty(
        name="Viewport: Local View",
        description="Warn me about an active Local-View",
        default=True
    )   
    
    warn_21: bpy.props.BoolProperty(
        name="Viewport: Clipping Border",
        description="Warn me about an clipping borders being used",
        default=True
    )  
    
    warn_22: bpy.props.BoolProperty(
        name="Active Object: Shadow Catcher/Holdout",
        description="Warn me if active object is a shadow catcher or holdout",
        default=True
    )  
    
    warn_23: bpy.props.BoolProperty(
        name="Render: Resolution not 100%",
        description="Warn me if the Render Resolution is not set to 100%",
        default=True
    )  
    
    warn_24: bpy.props.BoolProperty(
        name="Render: Filter Size",
        description="Warn me about the Pixel Filter being changed from its 1.50 px default",
        default=True
    )  
    
    warn_25: bpy.props.BoolProperty(
        name="Viewport/Render: Modifier Mismatch",
        description="Warn me about modifiers which have mismatching viewport/render visibilities",
        default=True,
        update=prop_update_callback
    )  
    
    warn_25_a: bpy.props.EnumProperty(
        name="",
        description="Choose to check only the active object or all objects in enabled collections",
        items=[
            ('ACTIVE_ONLY', "Active Only", "Check only the active object"),
            ('ALL_OBJECTS', "All Objects", "Check all objects in enabled collections"),
        ],
        default='ACTIVE_ONLY',
        update=prop_update_callback
    )
    
    warn_26: bpy.props.BoolProperty(
        name="Render: Sample Override",
        description="Warn me about Sample Override being active on a Viewlayer",
        default=True
    )  
    
    warn_27: bpy.props.BoolProperty(
        name="Render: Samples lower than",
        description="Warn me about Cycles samples being lower than this number",
        default=True
    )  
    warn_27_a: bpy.props.BoolProperty(
        name="Render: Samples higher than",
        description="Warn me about Cycles samples being higher than this number",
        default=True
    )  
    
    warn_28: bpy.props.BoolProperty(
        name="Active Object: Relative Array",
        description="Warn me about modifiers before an array modifier mismatching for render and viewport. Might cause changing positions of the array result",
        default=True
    )  

    warn_29: bpy.props.BoolProperty(
        name="Viewport: Hidden Object Types",
        description="Warn me about hidden object types in a visible viewport",
        default=True
    )  

    warn_30: bpy.props.BoolProperty(
        name="Viewport: Unselectable Object Types",
        description="Warn me about unselectable object types in a visible viewport",
        default=True
    )  

    warn_31: bpy.props.BoolProperty(
        name="Animation: Use Preview Range",
        description="Warn me about an active preview range",
        default=True
    )  
    
    warn_32: bpy.props.BoolProperty(
        name="Render: Cycles not using ",
        description="Warn me about the render device for Cycles",
        default=True
    )  

    warn_32_a: bpy.props.EnumProperty(
        name="",
        description="Choose the prefered rendering device for Cycles",
        items=[
            ('GPU', "GPU", "Warn if GPU Rendering is NOT used"),
            ('CPU', "CPU", "Warn if CPU Rendering is NOT used"),
        ],
        default='GPU'
    )

    warn_33: bpy.props.BoolProperty(
        name="Active Object: Locked Transforms ",
        description="Warn me about locked location, rotation or scale",
        default=True
    )  

    warn_34: bpy.props.BoolProperty(
        name="Active Object: Armature in Rest Position",
        description="Warn me about an active Rig being in Rest Position",
        default=True
    )  

    warn_35: bpy.props.BoolProperty(
        name="Render: Material Override",
        description="Cycles: Warn me about a material override",
        default=True
    )  
    
    warn_36: bpy.props.BoolProperty(
        name="Compositing: 'Use Nodes' is OFF",
        description="Warn me if 'Use Nodes' is OFF in the compositor, but the compositor is NOT emtpy",
        default=True
    )  

    warn_37: bpy.props.BoolProperty(
        name="Render: Output as Video",
        description="Warn me about the Output being set to FFMPEG video, which can lead to many issues",
        default=True
    )  

    warn_38: bpy.props.BoolProperty(
        name="Render: Film 'Transparent' is",
        description="Warn me about a the Film 'Transparent' option being turned OFF",
        default=False
    )  

    warn_38_a: bpy.props.EnumProperty(
        name="",
        description="Choose prefered Film 'Transparent' setting",
        items=[
            ('OFF', "OFF", "Warn if Film Transparent is OFF"),
            ('ON', "ON", "Warn if Film Transparent is ON"),
        ],
        default='OFF'
    )

    warn_39: bpy.props.BoolProperty(
        name="Sequencer: Audio Louder than",
        description="Warn me about an audio strip being louder than a threshold",
        default=True
    )  

    warn_39_a: bpy.props.FloatProperty(
        name="",
        default = 1.0,
        min=0.0, max=5.0,
        description="Warn me about an audio strip being louder than a threshold",
    )  

    warn_40: bpy.props.BoolProperty(
        name="Active Object: Render < Viewport SubDiv",
        description="Warn me about a Subdivision or MultiRes being higher for Viewport than for Render",
        default=True
    )  

    warn_41: bpy.props.BoolProperty(
        name="Material: 'Undefined' nodes",
        description="Warn me about 'UNDEFINED' nodes",
        default=True,
        update=prop_update_callback
    )  

    warn_42: bpy.props.BoolProperty(
        name="Data: Missing Textures",
        description="Warn me about missing textures",
        default=True,
        update=prop_update_callback
    )  

    warn_43: bpy.props.BoolProperty(
        name="Data: Missing Libraries",
        description="Warn me about missing libraries",
        default=True,
        update=prop_update_callback
    )  

    warn_44: bpy.props.BoolProperty(
        name="Data: Blender Version",
        description="Warn me when the file was created in another Blender version",
        default=True,
    )  
    
    warn_44_a: bpy.props.BoolProperty(
        name="Fullscreen",
        description="Show a central warning in the 3D View to remind me of the Version mismatch",
        default=True,
    )  

    warn_45: bpy.props.BoolProperty(
        name="Compositing: Renderlayer Node Issues",
        description="Show a warning for Renderlayer Node Issues, like missing Renderlayer nodes or muted savers",
        default=True,
    )
    
    warn_46: bpy.props.BoolProperty(
        name="Active Object: In Front",
        description="Show a warning if the Active Object is set to 'In Front'",
        default=True,
    )  

    custom_warn: bpy.props.BoolProperty(
        name="Enable Custom Warnings",
        description="Enable custom warnings, simply use the text editor and write 'Headsup:', followed by your custom HeadsUp Overlay warning",
        default=True
    )  
       
    sample_limit_lower: bpy.props.IntProperty(
        name="",
        default=16,
        min=1, max=4096,
        description="Warn if Render Samples are EQUAL to or LOWER than this value"
    )

    sample_limit_upper: bpy.props.IntProperty(
        name="",
        default=4097,
        min=1, max=16384,
        description="Warn if Render Samples are EQUAL to or HIGHER than this value"
    )
    
    simplify_render: bpy.props.IntProperty(
        name="",
        default=3,
        min=0, max=20,
        description="Warn if Render Subdivisions are EQUAL to or LOWER than this value"
    )
    
    simplify_viewport: bpy.props.IntProperty(
        name="",
        default=0,
        min=0, max=20,
        description="Warn if Viewport Subdivisions are EQUAL to or LOWER than this value"
    )
    
    toggle_with_overlays:  bpy.props.BoolProperty(
        name="Toggle text warnings together with 'Show Overlays' toggle",
        description="Don't show text warnings if overlays are turned off for a 3D viewport",
        default=True
    ) 
    
    compositor_warnings:  bpy.props.BoolProperty(
        name="Also show warnings in the Compositor",
        description="Also display HeadsUp warnings at the bottom of the Compositor",
        default=True
    ) 

    viewport_highlighting: bpy.props.BoolProperty(
        name="Draw Highlight border around Viewport if there are Viewport Warnings but 'Show Overlays' is OFF",
        description="Draw a highlight border around the Viewport if 'Show Overlays' is OFF but there are viewport specific warnings",
        default=True
    ) 

    first_setup_bool: bpy.props.BoolProperty(
        name="First Setup",
        description="Indicates if this is the first setup for the add-on",
        default=False
    ) 

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        box = row.box()
        row = box.row()
        row.prop(self, "toggle_with_overlays")
        if bpy.context.preferences.addons[__package__].preferences.toggle_with_overlays:
            row = box.row()
            split = row.split(factor=0.06)
            split.label(text="┗▶")
            split.prop(self, "viewport_highlighting")
        row = layout.row()
        box = row.box()
        box.prop(self, "compositor_warnings")
        # Create the main row
        row = layout.row()
        
        # Column 1
        col1 = row.column()
        box1 = col1.box()
        col1_split = box1.split(factor=0.5)
        
        # Add properties in two columns inside the box
        col1_split.column().prop(self, "warn_color")
        col1_split.column().prop(self, "highlight_color")
        
        # Column 2
        col2 = row.column()
        box2 = col2.box()
        
        row = box2.row()
        row.prop(self, "text_size", text="Text Size:")
        row = box2.row()
        row.prop(self, "UI_color_change_bool")
        
        box1.scale_y = 1
        box2.scale_y = 0.81
        
        # Secondary Row
        row = layout.row()
        
        col = row.column()
        box = col.box()
        row = box.row(align=True)
        row.prop(self, "original_theme_color")
        row = box.row(align=True)
        row.operator("wm.headsup_store_color", text="Store current theme color")
        row = box.row(align=True)
        row.label(text="Addon stores your correct theme color automatically. Use button after theme changes.")

        
        box3 = layout.box()
        row = box3.row(align=True)
        row.label(text="Toggle what you would like to be warned about:")
        row = box3.row(align=True)
        
        
            
        box = row.box()
        # Organize properties with a gridflow layout
        #grid = box.grid_flow(columns=2, align=True)
        grid = box.grid_flow(align=True)
        # First section of properties in inner_box1
        grid.prop(self, "warn_5")   # General: Proportional Editing
        grid.prop(self, "warn_6")   # General: Affect Only
        grid.prop(self, "warn_7")   # General: Snapping
        grid.prop(self, "warn_19")  # General: Autopack Ressources
        row = grid.row()
        split = row.split(factor=0.8)
        split.prop(self, "warn_32")  # Cycles: Not using 
        split.prop(self, "warn_32_a")# CPU/GPU
        grid.prop(self, "warn_23")  # Render: Resolution not 100%
        grid.prop(self, "warn_12")  # Render: Render Border
        grid.prop(self, "warn_24")  # Render: Pixel Filter Size
        grid.prop(self, "warn_26")  # Render: Sample Override
        grid.prop(self, "warn_35")  # Render: Material Override
        grid.prop(self, "warn_37")  # Render: FFMPEG video
        row = grid.row()
        split = row.split(factor=0.8)
        split.prop(self, "warn_38")  # Render: Film Transparent
        split.prop(self, "warn_38_a") # Render: Film Transparent ON/OFF
        row = grid.row()
        split = row.split(factor=0.7)
        split.prop(self, "warn_27")  # Render: Samples lower than
        split.prop(self, "sample_limit_lower") 
        row = grid.row()
        split = row.split(factor=0.7)
        split.prop(self, "warn_27_a")  # Render: Samples lower than
        split.prop(self, "sample_limit_upper")  
        grid.prop(self, "warn_2")   # Viewport: Visibility Mismatch
        row = grid.row()
        split = row.split(factor=0.8)
        split.prop(self, "warn_25")  # Viewport: Modifier Mismatch
        split.prop(self, "warn_25_a")
        grid.prop(self, "warn_1")   # Viewport: Camera to View
        grid.prop(self, "warn_20")  # Viewport: Local View
        grid.prop(self, "warn_21")  # Viewport: Clipping Border
        grid.prop(self, "warn_29")  # Viewport: Object Visibilities
        grid.prop(self, "warn_30")  # Viewport: Object Selectabilities
        grid.prop(self, "warn_36")  # Compositing: Use Nodes
        grid.prop(self, "warn_45")  # Compositing: Renderlayer Node Issues
        grid.prop(self, "warn_11")  # Sequencer: Use Sequencer
        row = grid.row()
        split = row.split(factor=0.8)
        split.prop(self, "warn_39")  # Sequencer: Audio louder than 
        split.prop(self, "warn_39_a")# threshold
        
        grid.prop(self, "warn_3")   # Sculpt: Shapekey
        grid.prop(self, "warn_18")  # Sculpt: Corrective
        grid.prop(self, "warn_14")  # UV: Select Sync
        grid.prop(self, "warn_15")  # UV: Live Unwrap
        grid.prop(self, "warn_16")  # UV: Correct Face Attributes
        grid.prop(self, "warn_9")   # Edit: Mirror Options
        grid.prop(self, "warn_13")  # Edit: Auto-Merge Vertices
        grid.prop(self, "warn_41")  # Material: Undefined nodes
        grid.prop(self, "warn_17")  # Material: Image Sequence Nodes
        row = grid.row()
        split = row.split(factor=0.7)
        split.prop(self, "warn_4")  # Animation: Auto Keying
        split.prop(self, "warn_4_a")  
        grid.prop(self, "warn_31")  # Animation: Preview Range
        grid.prop(self, "warn_22")  # Active Object: Shadow Catcher/Holdout
        grid.prop(self, "warn_28")  # Active Object: Relative Array
        grid.prop(self, "warn_33")  # Active Object: Locked Transforms
        grid.prop(self, "warn_34")  # Active Object: Rig in Rest Position
        grid.prop(self, "warn_40")  # Active Object: Render < Viewport SubDiv
        grid.prop(self, "warn_46")  # Active Object: In Front
        grid.prop(self, "warn_42")  # Data: Missing Textures
        grid.prop(self, "warn_43")  # Data: Missing Libraries
        row = grid.row()
        split = row.split(factor=0.6)
        split.prop(self, "warn_44")  # Data: Blender Version
        split.prop(self, "warn_44_a") 

        row = box3.row(align=True)
        row.label(text="Toggle these warnings with more options:")
        inner_split = box3.split(factor=0.5)
        inner_box1 = inner_split.column().box()
        inner_box2 = inner_split.column().box()
        
        # Simplify section
        row = inner_box1.row(align=True)
        inner_box1.prop(self, "warn_10")
        if bpy.context.preferences.addons[__package__].preferences.warn_10:
            inner_box1.label(text="┗▶ Settings: (Warn if equal or lower than)")
            inner_box1.prop(self, "simplify_viewport", text="Viewport")
            inner_box1.prop(self, "simplify_render", text="Render")
            inner_box1.prop(self, "warn_10_a")
        
        # Scaling Issues section
        row = inner_box2.row(align=True)
        inner_box2.prop(self, "warn_8")
        if bpy.context.preferences.addons[__package__].preferences.warn_8:
            inner_box2.label(text="┗▶ Settings:")
            inner_box2.prop(self, "warn_8_a")
            inner_box2.prop(self, "warn_8_b")
            inner_box2.prop(self, "warn_8_c")

        # Custom section
        box = box3.box()
        row = box.row(align=True)
        row.prop(self, "custom_warn")
        row = box.row(align=True)
        row.label(text="When this is activated, any text file in Blender starting with the word 'HeadsUp:' in ")
        row = box.row(align=True)
        row.label(text="the first line will be adding the following part of that line as a HeadsUp Warning.")


        
def register():
    bpy.utils.register_class(HEADSUP_Preferences)
    
def unregister():
    bpy.utils.unregister_class(HEADSUP_Preferences)
