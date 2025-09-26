import bpy

class HEADSUP_Props:
    handler = None 
    handler_sequencer = None 
    handler_comp = None
    handler_gradient = None
    warn_state = None
    warning_message = ""
    warnings = []
    old_warnings = []
    modifier_mismatches = set()
    system = bpy.context.preferences.system
    dpi = int(system.dpi * (1 / system.pixel_size))
    actual_text_size = 11
    object_mismatches = []
    collection_mismatches = []
    undefined_nodes = []
    load_up_done = False
    startup_done = False
    problematic_materials = set()
    problematic_objects = set()
    problematic_collections = set()
    collection_check_bool = True
    compositor_check_bool = True
    view_layer_visible_collections = {}
    view_layer_visibilities = {}
    saved_just_now = False
    current_scene = None
    old_warn_state = None
    viewlayer_count = None

class HEADSUP_WarnInfoProperties(bpy.types.PropertyGroup):
    def get_pass(self):
        pass
    
    def set_pass(self, value):
        pass

#    1 Lock Camera to View
    warn_info_1: bpy.props.BoolProperty(
        name="Viewport: Lock Camera to View",
        description="'Lock Camera To View’ is active in one of your 3D Viewports. This setting might destructively change your camera position and might not be undone. ▶▶▶ Disable via 3D Viewports Right Sidebar → View → Lock → Camera To View",
        default=False, 
    )
#    2 Viewport/Render Visibility Mismatch
    warn_info_2: bpy.props.BoolProperty(
        name="Viewport/Render: Visibility Mismatch",
        description="A Collection or Object has different settings for Viewport and Rendering. This can cause unexpected outcomes in Rendering, ▶▶▶ Use HeadsUp “Collection/Object Mismatch” Panels to resolve visiblity issues",
        default=False
    )
#    3 Shapekey Warning in Sculpt Mode
    warn_info_3: bpy.props.BoolProperty(
        name="Sculpt: Shapekey Value not 1",
        description="You are trying to sculpt on a Shape Key, but that Shape Key is not fully applied, therefore the Viewport is not „What you see is what you get“. ▶▶▶ Go to Properties → Mesh → Shape Keys → Set Active Shape Key Value to 1.0",
        default=False
    )
#    4 Auto Keying
    warn_info_4: bpy.props.BoolProperty(
        name="Animation: Auto Keying",
        description="„Auto-Keying“ is active. This can potentially be destructive by inserting unwanted Keyframes or overwriting existing ones. ▶▶▶ Disable via the Timeline UI Button (⏺)",
        default=False
    )
#    5 Proportional Editing
    warn_info_5: bpy.props.BoolProperty(
        name="General: Proportional Editing",
        description="Proportional Editing is active and might unintentionally change off-screen data. ▶▶▶ Press ‘o’ in the affected editor type or use the UI Button",
        default=False
    )
#    6 Affect only Origins/Locations/Parents 
    warn_info_6: bpy.props.BoolProperty(
        name="General: Affect Only",
        description="'Affect only Origins/Locations/Parents’ is active in your 3D Viewport.  ▶▶▶ Go to the 3D Viewport → Right Sidebar → Tool → Options → Transform → Affect",
        default=False
    )
#    7 Snapping
    warn_info_7: bpy.props.BoolProperty(
        name="General: Snapping",
        description="Snapping is activated. ▶▶▶ Go to the affected editor type and press on the Top Bar UI Button (Magnet)",
        default=False
    )
#    8 Scaling Issues 
    warn_info_8: bpy.props.BoolProperty(
        name="Active Object: Scaling Issues",
        description="Scaling issues detected for your active object. ▶▶▶ Check the scaling values and consider applying scale (Ctrl+A → Scale)",
        default=False
    )
#    9 Mirror Options
    warn_info_9: bpy.props.BoolProperty(
        name="Edit: Mirror Options",
        description="Mirror options are active in your 3D Viewport. ▶▶▶ Go to the 3D Viewport (Edit Mode) → Right Sidebar → Tool → Options → Transform → Mirror X/Y/Z",
        default=False
    )
#    10 Simplify 
    warn_info_10: bpy.props.BoolProperty(
        name="Render: Simplify",
        description="Simplify is turned on and the subdivision level is below your chosen threshold. Rendering with low Simplify settings can lead to unsatisfying results. ▶▶▶ Change the Simplify Settings in the Render Properties",
        default=False
    )
#    11 Sequencer
    warn_info_11: bpy.props.BoolProperty(
        name="Sequencer: Sequencer contains Strips",
        description="The Sequencer is turned on in the Output Properties and the Sequencer does contain image data. That might result in “Render” not working as expected. ▶▶▶ Consider turning off Output Properties → Post Processing → Sequencer",
        default=False
    )
#    12 Render Border
    warn_info_12: bpy.props.BoolProperty(
        name="Render: Render Region",
        description="Render Region is turned on in the Output Properties. Double check that render result is as expected. ▶▶▶ Consider turning off Output Properties → Format → Render Region",
        default=False
    )
#    13 Auto-Merge Vertices	     
    warn_info_13: bpy.props.BoolProperty(
        name="Edit: Auto-Merge Vertices",
        description="'Auto Merge Vertices’ is active in your 3d Viewport.  ▶▶▶ Go to the 3D Viewport → Right Sidebar → Tool → Options → Transform → ‘Auto Merge’",
        default=False
    )
#    14 UV Select Sync
    warn_info_14: bpy.props.BoolProperty(
        name="UV: Select Sync",
        description="'UV Sync Selection’ is turned on, you are only seeing UV for selected Geometry. Watch out for hidden Geometry. ▶▶▶ Consider disabling ‘UV Sync Selection’ in the UV Editor Top Bar or check if there is Geometry to unhide in the Edit-Mode (Alt+H)",
        default=False
    )
#    15 Live Unwrapping
    warn_info_15: bpy.props.BoolProperty(
        name="UV: Live Unwrap",
        description="UV ‘Live Unwrap’ is turned on. Changing the Geometry or Seams will change the UV Layout. ▶▶▶ Go to the 3D Viewport → Right Sidebar → Tool → Options → Transform → Uvs Live Unwrap",
        default=False
    )
#    16 Correct Face Attributes
    warn_info_16: bpy.props.BoolProperty(
        name="UV: Correct Face Attributes",
        description="'Correct Face Attributes’ is turned on. Changing the Geometry will change the UV Layout. ▶▶▶ Go to the 3D Viewport → Right Sidebar → Tool → Options → Correct Face Attributes",
        default=False
    )
#    17 Multiple Image Sequence Nodes with same datablock
    warn_info_17: bpy.props.BoolProperty(
        name="Shader: Img-Sequence not unique",
        description="Multiple Image Sequence nodes refer to the same datablock but have different settings, that is not really supported. Expect weird behavior. ▶▶▶ Create a unique datablock for your Image Sequence Nodes",
        default=False
    )
#    18 Sculpt Mode and Corrective Smooth
    warn_info_18: bpy.props.BoolProperty(
        name="Sculpt: Corrective Smooth active",
        description="Sculpt Mode + Corrective Smooth can lead to Geometry looking extremely different than expected once Corrective Smooth is turned off ▶▶▶Temporarily disable the modifier if needed",
        default=False
    )
#    19 Automatically Pack Ressources
    warn_info_19: bpy.props.BoolProperty(
        name="General: Autopack Ressources",
        description="Auto-Pack is activated, the Blender File will automatically pack all images and might become very large. ▶▶▶ File → External Data → Automatically Pack Ressources",
        default=False
    )
#    20 LocalView
    warn_info_20: bpy.props.BoolProperty(
        name="Viewport: Local View",
        description="'Local View’ is activated in one of your 3D Viewports. ▶▶▶ Press Numpad Slash (/) or go to the View menu in the 3D Viewport and select Local View → Toggle Local View",
        default=False
    )
#    21 Clipping Borders (Alt+B)
    warn_info_21: bpy.props.BoolProperty(
        name="Viewport: Clipping Border",
        description="'Clipping Borders’ are active in one of your 3D Viewports. ▶▶▶ Alt+B to clear Clipping Borders",
        default=False
    )
#    22 Active Object is Shadow Catcher/Holdout
    warn_info_22: bpy.props.BoolProperty(
        name="Active Object: Shadow Catcher/Holdout",
        description="Active Object is a Shadow Catcher or Holdout Object ▶▶▶ Check Object Properties → Visbility → Shadow Catcher / Holdout and change if needed", 
        default=False
    )
#    23 Render Resolution Percentage not 100%
    warn_info_23: bpy.props.BoolProperty(
        name="Render: Resolution not 100%",
        description="Render Resolution has been changed from 100% to another value. This is often done for test rendering and can lead to final render mistakes. ▶▶▶ In the Output Properties, reset the resolution to 100% if needed",
        default=False
    )
#    24 Render: Filter Size not 1.5
    warn_info_24: bpy.props.BoolProperty(
        name="Render: Filter Size",
        description="The Filter Size is changed from its default value. This can lead to pixelated or blurry renders. ▶▶▶ Consider changing the Filter Size back to 1.5px in the Render Properties → Film",
        default=False
    )
#    25 Viewport/Render Modifier Mismatch
    warn_info_25: bpy.props.BoolProperty(
        name="Viewport/Render: Modifier Mismatch",
        description="There is a mismatch for the Render/Viewport visibilities of some modifier. ▶▶▶ Check the modifiers and change if needed",
        default=False
    )
#    26 Sample Override 
    warn_info_26: bpy.props.BoolProperty(
        name="Render: Sample Override",
        description="There is an active Sample override for a Viewlayer. If this was done for test render purposes, this could be unwanted. ▶▶▶ Check Viewlayer Properties → Overrides and disable if needed",
        default=False
    )
#    27 Render Samples Low or High
    warn_info_27: bpy.props.BoolProperty(
        name="Render: Samples lower than threshold",
        description="This scene has either very high or low render samples. ▶▶▶ Check the sample numbers and change if needed",
        default=False
    )
#    28 Active Object: Array with relative Offset not first in stack
    warn_info_28: bpy.props.BoolProperty(
        name="Active Object: Relative Array",
        description="The active Object has an Array modifier with Relative offset with other modifiers in the stack before it. This might lead to changing positions between Render and Viewport. ▶▶▶ Double Check the Modifier Stack",
        default=False
    )
#    29 Viewport: Hidden Object Types    
    warn_info_29: bpy.props.BoolProperty(
        name="Viewport: Hidden Object Types",
        description="One of your 3D Viewports has Hidden Object Types. ▶▶▶ Toggle the Visibilities of the affected Viewport via the Top Bar Dropdown ’View Object Types’",
        default=False
    )
#    30 Viewport: Unselectable Object Types
    warn_info_30: bpy.props.BoolProperty(
        name="Viewport: Unselectable Object Types",
        description="One of your 3D Viewports has Unselectable Object Types. ▶▶▶ Toggle the Selectabilities of the affected Viewport via the Top Bar Dropdown ’View Object Types’",
        default=False
    )
#    31 Render: Preview Range is used
    warn_info_31: bpy.props.BoolProperty(
        name="Render: Use Preview Range",
        description="A Preview Range is used, that means not the whole timeline will play/render. ▶▶▶ Consider disabling via the Timeline → ‘Stopwatch’ Button in the Top Bar",
        default=False
    )
#    32 Cycles: Render Device
    warn_info_32: bpy.props.BoolProperty(
        name="Cycles: Render Device",
        description="The Cycles Render Device is not set to your chosen preference. ▶▶▶ Change in the Render Properties → Device",
        default=False
    )
#    33 Active Object: Locked Transforms
    warn_info_33: bpy.props.BoolProperty(
        name="Active Object: Locked Transforms",
        description="Active Object has locked Transforms ▶▶▶ In the 3D Viewport → Right Sidebar → Item → Lock/Unlock Icons",
        default=False
    )
#    34 Active Object: Rig in Rest Position
    warn_info_34: bpy.props.BoolProperty(
        name="Active Object: Rig in Rest Position",
        description="The Active Rig is set to Rest Position, so no animation can be seen or rendered right now ▶▶▶ In the Rig Properties → Skeleton → Pose Position",
        default=False
    )
#    35 Render: Material Override
    warn_info_35: bpy.props.BoolProperty(
        name="Render: Material Override",
        description="A Material Override has been set up for a Viewlayer ▶▶▶ Check Viewlayer Properties → Overrides and disable if needed",
        default=False
    )
#    36 Compositing: Use Nodes
    warn_info_36: bpy.props.BoolProperty(
        name="Compositing: 'Use Nodes' OFF",
        description="In the Compositor ‘Use Nodes’ is turned OFF but the Compositor contains Nodes ▶▶▶ Double Check and enable ‘Use Nodes’ in a Compositor if needed",
        default=False
    )
#    37 Render: Output to video
    warn_info_37: bpy.props.BoolProperty(
        name="Render: Output to Video",
        description="The Render Output has been set to a video format, that can cause issues, e.g. it won’t work on distributed rendering etc. ▶▶▶ Check Output Properties → Output → File Format and change If needed",
        default=False
    )
#    38 Render: Film Transparent
    warn_info_38: bpy.props.BoolProperty(
        name="Render: Film Transparent",
        description="The Transparency setting of the Render Output is different to your chosen preference. ▶▶▶ Check Render Properties → Film → Transparent and change If needed",
        default=False
    )
#    39 Sequencer: Loud audio
    warn_info_39: bpy.props.BoolProperty(
        name="Sequencer: Loud Audio",
        description="The Sequencer contains Audio Strips that are louder than your chosen threshold value. ▶▶▶ Check the Sequencer",
        default=False
    )
#    40 Active Object: Render < Viewport Subdiv
    warn_info_40: bpy.props.BoolProperty(
        name="SubSurf: Render < Viewport",
        description="The Active Object has a higher Viewport subdivision than Render subdivision. ▶▶▶ Check the Subdivision Surface modifier",
        default=False
    )
#    41 Material: Undefined Nodes
    warn_info_41: bpy.props.BoolProperty(
        name="Shader: 'Undefined' Nodes'",
        description="Materials contain Undefined Nodes, those are usually caused by Blendfiles being opened in lower versions than they were saved in. ▶▶▶ Use Headsup “Undefined” Panel to find problematic materials",
        default=False
    )
#    42 Data: Missing Textures
    warn_info_42: bpy.props.BoolProperty(
        name="Data: Missing Textures",
        description="Missing Textures found ▶▶▶ Go to File → External Data → Report Missing Files and check the Log printed to the Console",
        default=False
    )
#    43 Data: Missing Libraries
    warn_info_43: bpy.props.BoolProperty(
        name="Data: Missing Libraries",
        description="Missing Libraries found ▶▶▶ Go to File → External Data → Report Missing Files and check the Log printed to the Console",
        default=False
    )
#    44 Blender Version
    warn_info_44: bpy.props.BoolProperty(
        name="Data: Blender Version",
        description="The file was saved with another Blender Version. ▶▶▶ Make sure that you are aware of the differing versions, consider the limitations and save the file with this version to resolve the Warning",
        default=False
    )
#    45 Blender Version
    warn_info_45: bpy.props.BoolProperty(
        name="Compositing: Renderlayer Node Issue",
        description="In the Compositor a Renderlayer Node is either Muted or connected to a muted File Output Saver although the RenderLayer is active. ▶▶▶ Go to the Compositor and check",
        default=False
    )
#    46 Active Object: In Front
    warn_info_46: bpy.props.BoolProperty(
        name="Active Object: In Front",
        description="The Active Object is set to 'In Front', being shown in Front of all other objects in the 3D viewport. This might be confusing sometimes. ▶▶▶ Go to Object Properties → Viewport Display → 'In Front' ",
        default=False
    )
#    Custom: Custom Text
    warn_info_custom: bpy.props.BoolProperty(
        name="CUSTOM Warning",
        description="A custom HeadsUp warning was set up. ▶▶▶ To change or delete the warning, go to the text editor and find the text file that starts with ‘Headsup:’ in the first line",
        default=False
    )

WarnInfoIconMap = {
    1: 'VIEW_CAMERA',
    2: 'RESTRICT_RENDER_OFF',
    3: 'SCULPTMODE_HLT',
    4: 'RADIOBUT_ON',
    5: 'PROP_ON',
    6: 'TOOL_SETTINGS',
    7: 'SNAP_ON',
    8: 'CON_SIZELIKE',
    9: 'MOD_MIRROR',
    11: 'SEQUENCE',
    12: 'OUTPUT',
    13: 'AUTOMERGE_ON',
    14: 'UV_SYNC_SELECT',
    15: 'UV_DATA',
    16: 'UV_FACESEL',
    17: 'NODE_MATERIAL',
    18: 'SCULPTMODE_HLT',
    19:'PACKAGE',
    20:'VIEW3D',
    21:'VIEW3D',
    22:'OBJECT_DATA',
    23:'OUTPUT',
    24:'SCENE',
    25:'MODIFIER',
    26:'RENDERLAYERS',
    27:'SCENE',
    28:'MODIFIER',
    29:'VIS_SEL_01',
    30:'VIS_SEL_10',
    31:'PREVIEW_RANGE',
    32:'SCENE',
    33:'LOCKED',
    34:'ARMATURE_DATA',
    35:'RENDERLAYERS',
    36:'NODE_COMPOSITING',
    37:'OUTPUT',
    38:'SCENE',
    39:'PLAY_SOUND',
    40:'MOD_SUBSURF',
    41:'MATERIAL',
    42:'LIBRARY_DATA_BROKEN',
    43:'LIBRARY_DATA_BROKEN',
    44:'BLENDER',
    45:'NODE_COMPOSITING',
    46:'XRAY',
}

def register():
    HEADSUP_Props.load_up_done = False
    HEADSUP_Props.startup_done = False
    bpy.utils.register_class(HEADSUP_WarnInfoProperties)
    bpy.types.Scene.HEADSUP_WarnInfoProperties = bpy.props.PointerProperty(type=HEADSUP_WarnInfoProperties) 

def unregister():
    del bpy.types.Scene.HEADSUP_WarnInfoProperties
    bpy.utils.unregister_class(HEADSUP_WarnInfoProperties)