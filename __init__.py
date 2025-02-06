# ====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ======================= END GPL LICENSE BLOCK ========================


bl_info = {
    "name": "HeadsUp Warnings",
    "description": "Temporarily change UI colors and overlay a text with warnings about potentially destructive Blender settings",
    "author": "Manuel Lüllau",
    "version": (1, 0),
    "blender": (3, 3, 0),
    'location': 'Somewhere',
    'category': '3D View',
    'support': 'COMMUNITY',
    }

import bpy
import blf  # Blender Font Library for text drawing
import re
import math
import time
import os
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent
from math import cos, sin, pi

warn_state = None
warning_message = ""
warnings = []
old_warnings = []
mismatch_list = []
original_theme_color = None
handler = None
handler_comp = None
handler_gradient = None
blender_version = bpy.app.version
visibilities_list = []
modifier_mismatches = set()
system = bpy.context.preferences.system
dpi = int(system.dpi * system.pixel_size)
actual_text_size = 11
object_mismatches = []
collection_mismatches = []
visible_objects = []
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

#Current Warn List:
#    1 Lock Camera to View
#    2 Viewport/Render Visibility Mismatch
#    3 Shapekey Warning in Sculpt Mode
#    4 Auto Keying
#    5 Proportional Editing
#    6 Affect only Origins/Locations/Parents 
#    7 Snapping
#    8 Scaling Issues 
#    9 Mirror Options
#    10 Simplify 
#    11 Sequencer
#    12 Render Border
#    13 Auto-Merge Vertices	     
#    14 UV Select Sync
#    15 Live Unwrapping
#    16 Correct Face Attributes
#    17 Multiple Image Sequence Nodes with same datablock
#    18 Sculpt Mode and Corrective Smooth
#    19 Automatically Pack Ressources
#    20 LocalView
#    21 Clipping Borders (Alt+B)
#    22 Active Object: Shadow Catcher / Holdout
#    23 Render Resolution Percentage not 100%
#    24 Render: Filter Size not 1.5
#    25 Viewport/Render Modifier Mismatch
#    26 Sample Override 
#    27 Render Samples Low or High
#    28 Active Object: Array with relative Offset not first in stack
#    29 Viewport: Hidden Object Types
#    30 Viewport: Unselectable Object Types
#    31 Render: Preview Range is used
#    32 Cycles: Render Device
#    33 Active Object: Locked Transforms
#    34 Active Object: Rig in Rest Position
#    35 Render: Material Override
#    36 Compositing: Use Nodes
#    37 Render: Output to video
#    38 Render: Film Transparent
#    39 Sequencer: Loud audio
#    40 Active Object: Render < Viewport Subdiv
#    41 Material: Undefined Nodes
#    42 Missing: Textures
#    43 Missing: Libraries
#    44 Blender Version
#    45 Compositing: Renderlayer Node Issues

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
        name="Render: Render Border",
        description="Render Border is turned on in the Output Properties. Double check that render result is as expected. ▶▶▶ Consider turning off Output Properties → Format → Render Region",
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
#    Custom: Custom Text
    warn_info_custom: bpy.props.BoolProperty(
        name="CUSTOM Warning",
        description="A custom HeadsUp warning was set up. ▶▶▶ To change or delete the warning, go to the text editor and find the text file that starts with ‘Headsup:’ in the first line",
        default=False
    )

WarnInfoIconMap = {
    1: 'CAMERA',
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
    45:'NODE_COMPOSITING'
}

class HEADSUP_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    # Callback function for certain property changes
    def prop_update_callback(self, context):
        global load_up_done
        load_up_done = False

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
        description="Warn me about 'Camera to View' being active, as it can be destructive and is not undo-able",
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
        name="Render: Render Border",
        description="Warn me about a Render Border being used",
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
        name="Shader: Img-Sequence not unique",
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
        name="Render: Use Preview Range",
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
        name="Active Object: Armature is in Rest Position",
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
        name="Compositing: Renderlayer Node Issue",
        description="Show a central warning in the 3D View to remind me of the Version mismatch",
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
        if bpy.context.preferences.addons[__name__].preferences.toggle_with_overlays:
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
        row.operator("headsup_warnings.store_color", text="Store current theme color")
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
        grid.prop(self, "warn_31")  # Render: Sample Override
        grid.prop(self, "warn_41")  # Material: Undefined nodes
        grid.prop(self, "warn_36")  # Compositing: Use Nodes
        grid.prop(self, "warn_45")  # Compositing: Renderlayer Node Issues
        grid.prop(self, "warn_11")  # Sequencer: Use Sequencer
        row = grid.row()
        split = row.split(factor=0.8)
        split.prop(self, "warn_39")  # Sequencer: Audio louder than 
        split.prop(self, "warn_39_a")# threshold
        row = grid.row()
        split = row.split(factor=0.8)
        split.prop(self, "warn_32")  # Cycles: Not using 
        split.prop(self, "warn_32_a")# CPU/GPU
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
        grid.prop(self, "warn_3")   # Sculpt: Shapekey
        grid.prop(self, "warn_18")  # Sculpt: Corrective
        grid.prop(self, "warn_14")  # UV: Select Sync
        grid.prop(self, "warn_15")  # UV: Live Unwrap
        grid.prop(self, "warn_16")  # UV: Correct Face Attributes
        grid.prop(self, "warn_9")   # Edit: Mirror Options
        grid.prop(self, "warn_13")  # Edit: Auto-Merge Vertices
        grid.prop(self, "warn_17")  # Shader: Image Sequence Nodes
        row = grid.row()
        split = row.split(factor=0.7)
        split.prop(self, "warn_4")  # Animation: Auto Keying
        split.prop(self, "warn_4_a")  
        grid.prop(self, "warn_22")  # Active Object: Shadow Catcher/Holdout
        grid.prop(self, "warn_28")  # Active Object: Relative Array
        grid.prop(self, "warn_33")  # Active Object: Locked Transforms
        grid.prop(self, "warn_34")  # Active Object: Rig in Rest Position
        grid.prop(self, "warn_40")  # Active Object: Render < Viewport SubDiv
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
        if bpy.context.preferences.addons[__name__].preferences.warn_10:
            inner_box1.label(text="┗▶ Settings: (Warn if equal or lower than)")
            inner_box1.prop(self, "simplify_viewport", text="Viewport")
            inner_box1.prop(self, "simplify_render", text="Render")
            inner_box1.prop(self, "warn_10_a")
        
        # Scaling Issues section
        row = inner_box2.row(align=True)
        inner_box2.prop(self, "warn_8")
        if bpy.context.preferences.addons[__name__].preferences.warn_8:
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
        if blender_version >= (4, 0, 0):
            prefs = bpy.context.preferences.addons[__package__].preferences
        else:
            prefs = bpy.context.preferences.addons[__name__].preferences
        props = bpy.context.scene.HEADSUP_WarnInfoProperties

        if not warn_state:
            row.label(text="No warnings to display :)")
            row = layout.row()
            row.operator("headsup_warnings.open_preferences", text="HeadsUp Preferences", icon='PREFERENCES')
            return

        row.label(text="Read tooltips to get info", icon='INFO')
        row = layout.row()
        box=row.box()
        #box.enabled = False  # Disable editing
        for i in range(1, 46):
            prop_name = f"warn_info_{i}"
            
            if getattr(props, prop_name):  # Check if the property is True
                prop_def = props.bl_rna.properties[prop_name]
                prop_name_display = prop_def.name
                row = box.row()
                icon = WarnInfoIconMap.get(i, 'QUESTION')
        
                row.prop(props, prop_name, icon=icon, text=prop_name_display)

        if props.warn_info_custom:
            prop_def = props.bl_rna.properties["warn_info_custom"]
            prop_name_display = prop_def.name
            row = box.row()
            row.prop(props, warn_info_custom, icon='TEXT', text=prop_name_display)
        
        row = layout.row()
        row.operator("headsup_warnings.open_preferences", text="HeadsUp Preferences", icon='PREFERENCES')

class VIEW3D_PT_HeadsUpPanel_Object_Mismatch(VIEW3D_PT_HeadsUpPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_object_mismatch_panel"
    bl_label = "Object Visibilities"

    def draw(self, context):
        # Access the global object_mismatches list
        global object_mismatches 

        layout = self.layout
        row = layout.row()
        if blender_version >= (4, 0, 0):
            prefs = bpy.context.preferences.addons[__package__].preferences
        else:
            prefs = bpy.context.preferences.addons[__name__].preferences

        if not prefs.warn_2:
            row.label(text="Mismatch Checks disabled in Preferences")
            return

        # Filter mismatches
        visible_mismatches = []
        non_visible_mismatches = []

        # Get the current view layer
        current_view_layer = bpy.context.view_layer

        # Separate mismatches into visible and non-visible in the current view layer
        for mismatch in object_mismatches:
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
                    op = row.operator("headsup_warnings.select_highlight", text="", icon='OUTLINER')
                    op.object_name = obj.name

class VIEW3D_PT_HeadsUpPanel_Collection_Mismatch(VIEW3D_PT_HeadsUpPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_collection_mismatch_panel"
    bl_label = "Collection Visibilities"

    def draw(self, context):
        global collection_mismatches
        layout = self.layout
        row = layout.row()
        if blender_version >= (4, 0, 0):
            prefs = bpy.context.preferences.addons[__package__].preferences
        else:
            prefs = bpy.context.preferences.addons[__name__].preferences            

        if not prefs.warn_2:
            row.label(text="Mismatch Checks disabled in Preferences")
            return

        # Filter mismatches
        visible_mismatches = []
        non_visible_mismatches = []

        # Get the current view layer
        current_view_layer = bpy.context.view_layer

        # Separate mismatches into visible and non-visible in the current view layer
        for mismatch in collection_mismatches:
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
                op = row.operator("headsup_warnings.highlight_collection", text="", icon='BORDERMOVE')
                op.collection_name = col_name

class VIEW3D_PT_HeadsUpPanel_Modifier_Mismatch(VIEW3D_PT_HeadsUpPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_modifier_mismatch_panel"
    bl_label = "Modifier Visibilities"

    def draw(self, context):
        global modifier_mismatches
        layout = self.layout
        row = layout.row()
        if blender_version >= (4, 0, 0):
            prefs = bpy.context.preferences.addons[__package__].preferences
        else:
            prefs = bpy.context.preferences.addons[__name__].preferences            
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
        for mismatch in modifier_mismatches:
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
                    op = row.operator("headsup_warnings.select_highlight", text="", icon='OUTLINER')
                    op.object_name = obj.name

class VIEW3D_PT_HeadsUpPanel_Undefined_Nodes(VIEW3D_PT_HeadsUpPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_undefined_nodes_panel"
    bl_label = "Undefined Nodes"

    def draw(self, context):
        # Access the global object_mismatches list
        global undefined_nodes

        layout = self.layout
        row = layout.row(align=True)
        if blender_version >= (4, 0, 0):
            prefs = bpy.context.preferences.addons[__package__].preferences
        else:
            prefs = bpy.context.preferences.addons[__name__].preferences

        if not prefs.warn_41:
            row.label(text="Check for 'Undefined' nodes disabled in Preferences")
            return

        # Create UI layout for mismatches
        if not undefined_nodes:
            row.label(text="No 'Undefined' nodes found")
        else:
            row.label(text="Materials contain 'Undefined' nodes:")

            # Boxes for visible and non-visible objects
            box = layout.box()
            for material in undefined_nodes:
                row = box.row()
                row.label(text=material)

class HEADSUP_OT_Select_Highlight(bpy.types.Operator):
    bl_idname = "headsup_warnings.select_highlight"         # Unique identifier
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
    bl_idname = "headsup_warnings.highlight_collection"
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
                        space.show_restrict_column_holdout = True
                        space.show_restrict_column_viewport = True
                        space.show_restrict_column_render = True
                        space.show_restrict_column_select = True
                        space.show_restrict_column_hide = True
                        space.show_restrict_column_enable = True
                        space.show_restrict_column_indirect_only = True

class HEADSUP_OT_Store_Color(bpy.types.Operator):
    bl_idname = "headsup_warnings.store_color"
    bl_label = "Store the current theme color in the Original Theme Color preference."

    def execute(self, context):
        store_original_theme_color()
        self.report({'INFO'}, "HeadsUp: Stored current theme color!")
        return {'FINISHED'}

class HEADSUP_OT_OpenPreferences(bpy.types.Operator):
    """Open Preferences in Add-Ons Tab with 'HeadsUp' in Search"""
    bl_idname = "headsup_warnings.open_preferences"
    bl_label = "Open HeadsUp Preferences"

    def execute(self, context):
        open_headsup_prefs()
        return {'FINISHED'}

def open_headsup_prefs():
    bpy.ops.screen.userpref_show(section='ADDONS')
    bpy.context.preferences.active_section  = "ADDONS"
    bpy.data.window_managers["WinMan"].addon_search = "HeadsUp"
    bpy.ops.preferences.addon_expand(module=__package__)
    bpy.ops.preferences.addon_show(module=__package__)
    
def check_startup_time():
    global startup_done

    # Check if 1 second has passed since Blender started
    if time.time() - bpy.app.timers._startup_time > 2:
        draw_warning_text()
        # Set the variable to indicate that the check is done
        startup_done = True
        bpy.context.window_manager.update_tag()
        print("HeadsUp: Startup Done")
        
        # Remove the timer by returning None
        return None

    # Continue the timer with a short delay if the condition is not yet met
    return 1  # Check again in 0.1 seconds 

def store_original_theme_color():
    if blender_version >= (4, 0, 0):
        prefs = bpy.context.preferences.addons[__package__].preferences
    else:
       prefs = bpy.context.preferences.addons[__name__].preferences
    theme = bpy.context.preferences.themes[0]

    if blender_version >= (4, 3, 0):
        prefs.original_theme_color = theme.user_interface.editor_border
    else:
        prefs.original_theme_color = theme.user_interface.editor_outline

    if not prefs.first_setup_bool:
        print("HeadsUp: Stored current theme color!")
        prefs.first_setup_bool = True
    
def is_redo_panel_visible():
    if bpy.context.window_manager.operators:
        recent_operator = bpy.context.window_manager.operators[-1]
        if hasattr(recent_operator, "bl_options") and 'REGISTER' in recent_operator.bl_options and hasattr(recent_operator, "rna_type"):
            try:
                for prop in recent_operator.properties.rna_type.properties:
                    if not prop.is_readonly:
                        return True  # The operator has adjustable properties
            except:
                return True
    return False
    
def multiple_sequence_nodes(check_materials):
    # Store image sequence nodes with their properties
    image_sequences = {}

    # Loop through all materials in the blend file
    for material in check_materials:
        # Check if the material is valid and uses nodes
        if material and material.use_nodes:  
            if material.users == 0 or not material.use_nodes or material.library:
                continue
            # Check if the material has a node tree
            node_tree = material.node_tree
            if node_tree:
                for node in node_tree.nodes:
                    try:
                        # Check if the node is an Image Texture node
                        if "undefined" in node.bl_idname.lower():
                            continue
                        if node and hasattr(node, 'type'):
                            if node.type == 'TEX_IMAGE' and \
                            hasattr(node, 'image') and node.image and node.image.source == 'SEQUENCE':
                                
                                image_name = node.image.name
                                # Safely access image user properties
                                if node.image_user:
                                    frame_start = node.image_user.frame_start
                                    frame_offset = node.image_user.frame_offset
                                    frame_duration = node.image_user.frame_duration
                                    settings = (frame_start, frame_offset, frame_duration)

                                    # Check if the image has already been added to the dictionary
                                    if image_name in image_sequences:
                                        # Compare settings
                                        if image_sequences[image_name] != settings:
                                            problematic_materials.add(material)
                                            return True  # Found a match with different settings
                                    else:
                                        # Add the image and its settings to the dictionary
                                        image_sequences[image_name] = settings
                    except:
                        continue

    return False  # No matching cases found

def clean_viewport_warnings(strings, target_number):
    processed_list = []
    viewport_warnings_found = False
    for s in strings:
        # Check if the string starts with a number inside question marks
        match = re.match(r"^\?(-?\d+)\?", s)
        if match:
            # Extract the number
            found_number = int(match.group(1))
            if found_number == target_number:
                # Remove the ?number? part
                viewport_warnings_found = True
                processed_list.append(s[match.end():].strip())
        else:
            # If no ?number? is found, keep the string as is
            processed_list.append(s)
    
    return processed_list, viewport_warnings_found

def is_in_ortho_view(region_data):
    if region_data.view_perspective != 'ORTHO':
        return False  # Not in orthographic mode
    
    # View direction (rounded for precision)
    direction = tuple(round(v, 3) for v in region_data.view_matrix.col[2][:3])

    # Known orthographic directions
    ortho_directions = {
        (0.0, 0.0, 1.0),   # Top
        (0.0, 0.0, -1.0),  # Bottom
        (1.0, 0.0, 0.0),   # Right
        (-1.0, 0.0, 0.0),  # Left
        (0.0, 1.0, 0.0),   # Front
        (0.0, -1.0, 0.0)   # Back
    }
    return direction in ortho_directions

def rgb_to_rgba(rgb, alpha=1.0):
    """
    Convert an RGB tuple to RGBA by adding an alpha value.

    """
    if len(rgb) != 3:
        raise ValueError("Input must be an RGB tuple with 3 values.")
    
    return (*rgb, alpha)

def calculate_text_size(prefs):
    """Calculate the actual text size based on preferences and UI scaling."""
    text_size = prefs.text_size if prefs else 11  # Default to 11 if preferences are missing
    system_pixel_size = bpy.context.preferences.system.pixel_size
    ui_scale = bpy.context.preferences.view.ui_scale
    text_scale = system_pixel_size * ui_scale
    return round(text_size * text_scale)

def draw_highlight_border(border_thickness, border_color=None):
    """Draws a border with rounded corners."""
    context = bpy.context
    width = context.region.width
    height = context.region.height

    # Determine preferences based on Blender version
    if blender_version >= (4, 0, 0):
        prefs = bpy.context.preferences.addons[__package__].preferences
    else:
        prefs = bpy.context.preferences.addons[__name__].preferences

    # Use the provided border_color or fall back to prefs.highlight_color
    if border_color is None:
        border_color = rgb_to_rgba(prefs.highlight_color, 1)  # (RGBA tuple)

    # Select the appropriate shader
    if blender_version >= (4, 0, 0):
        HIGHLIGHT_BORDER_SHADER = gpu.shader.from_builtin('UNIFORM_COLOR')
    else:
        HIGHLIGHT_BORDER_SHADER = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

    # Set GPU state for line drawing
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(border_thickness)

    # Generate the rounded rectangle positions
    corner_radius = 8
    positions = [
        (0, 0 + corner_radius),  # Bottom-left
        (0 + corner_radius, 0),  # Bottom-left
        (width - corner_radius, 0),  # Bottom-right
        (width, 0 + corner_radius),  # Bottom-right
        (width, height - corner_radius),  # Top-right
        (width - corner_radius, height),  # Top-right
        (0 + corner_radius, height),  # Top-left
        (0, height - corner_radius),  # Top-left
    ]

    # Create the batch for the border
    batch = batch_for_shader(HIGHLIGHT_BORDER_SHADER, 'LINE_LOOP', {"pos": positions})

    # Set the shader color and draw
    HIGHLIGHT_BORDER_SHADER.bind()
    HIGHLIGHT_BORDER_SHADER.uniform_float("color", border_color)
    batch.draw(HIGHLIGHT_BORDER_SHADER)

    # Restore GPU state to defaults
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')

def draw_filled_red_circle():
    if blender_version >= (4, 0, 0):
        prefs = bpy.context.preferences.addons[__package__].preferences
    else:
        prefs = bpy.context.preferences.addons[__name__].preferences
    if bpy.context.space_data is not None and bpy.context.space_data.type == 'VIEW_3D':
        if bpy.context.space_data.overlay.show_overlays:
            if blender_version >= (4, 0, 0):
                RED_CIRCLE_SHADER = gpu.shader.from_builtin('SMOOTH_COLOR')
            else:
                RED_CIRCLE_SHADER = gpu.shader.from_builtin('2D_SMOOTH_COLOR')

            # Define the circle vertices and colors for TRI_FAN
            segments = 16
            radius = 9 * bpy.context.preferences.view.ui_scale  # Radius in pixels
            vertices = [(0, 0)]  # Center of the circle
            colors = [(1.0, 0.0, 0.0, 1.0)]  # Red color for the center

            vertices += [
                (
                    radius * math.cos(2 * math.pi * i / segments),
                    radius * math.sin(2 * math.pi * i / segments)
                )
                for i in range(segments)
            ]
            colors += [(1.0, 0.0, 0.0, 0.0) for _ in range(segments)]  # Same red for all vertices
            vertices.append(vertices[1])  # Close the circle
            colors.append(colors[1])

            # Create a batch for the filled circle
            batch = batch_for_shader(RED_CIRCLE_SHADER, 'TRI_FAN', {"pos": vertices, "color": colors})
            gpu.state.blend_set('ALPHA')

            # Get viewport dimensions
            viewport = gpu.state.viewport_get()
            width, height = viewport[2], viewport[3]

            # Position the circle in the top-left corner (with a margin)
            margin = 40 * bpy.context.preferences.view.ui_scale 
            
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    tools_region = next((region for region in area.regions if region.type == 'TOOLS'), None)
                    if tools_region:
                        toolshelf = tools_region.width

                        x_pos = 10 * bpy.context.preferences.view.ui_scale + radius + toolshelf   
                        y_pos = height - 40 * bpy.context.preferences.view.ui_scale - radius
                        if blender_version >= (4, 0, 0):
                            y_pos = y_pos - 25 * bpy.context.preferences.view.ui_scale 
                        if not bpy.context.space_data.show_region_header:
                            y_pos = y_pos + 25 * bpy.context.preferences.view.ui_scale
                        if bpy.context.space_data.show_region_header and not bpy.context.space_data.show_region_tool_header: 
                            y_pos = y_pos + 25 * bpy.context.preferences.view.ui_scale
                        if bpy.context.space_data.overlay.show_text:
                            y_pos = y_pos - 35 * bpy.context.preferences.view.ui_scale 
                        if bpy.context.space_data.overlay.show_stats:
                            y_pos = y_pos - 100 * bpy.context.preferences.view.ui_scale 
                        if is_in_ortho_view(bpy.context.space_data.region_3d):
                            y_pos = y_pos - 16 * bpy.context.preferences.view.ui_scale 
                        if bpy.context.scene.render.engine  == "CYCLES":
                            if bpy.context.space_data.shading.type == 'RENDERED':
                                y_pos = y_pos - 16 * bpy.context.preferences.view.ui_scale 
                    header_region = next((region for region in area.regions if region.type == 'HEADER'), None) 
                    if header_region:
                        if header_region.alignment == 'BOTTOM':
                            y_pos = y_pos + 27 * bpy.context.preferences.view.ui_scale

            gpu.matrix.push()
            gpu.matrix.load_identity()
            gpu.matrix.translate((x_pos, y_pos, 0))  # Top-left corner position
            RED_CIRCLE_SHADER.bind()
            for i in range(1,14):
                batch.draw(RED_CIRCLE_SHADER)
            gpu.matrix.pop()
            gpu.state.blend_set('NONE')


            # Draw "REC" text next to the circle
            text_margin = 4 * bpy.context.preferences.view.ui_scale # Distance between the circle and the text
            text_x = x_pos + radius + text_margin
            text_y = y_pos - 3 * bpy.context.preferences.view.ui_scale   # Slight adjustment to vertically center the text
        
            # Set the font and size
            blf.position(0, text_x, text_y, 0)
            blf.color(0, *prefs.highlight_color, 1.0)  # White text
            # Enable shadow
            blf.enable(0, blf.SHADOW)
            if blender_version >= (4,0,0):
                blf.shadow_offset(0, 0, 0)  # Offset shadow
                blf.shadow(0, 6, 0.0, 0.0, 0.0, 0.8)
            else:
                blf.shadow_offset(0, 1, -1)  # Offset shadow
                blf.shadow(0, 3, 0.0, 0.0, 0.0, 0.9)  # Blur level and shadow color (black with 70% opacity)

            blf.draw(0, "[REC] (Auto-Keyframe)")
            blf.disable(0, blf.SHADOW)

            draw_highlight_border(8, (1, 0, 0, 0.5))

@persistent
def on_file_load(dummy):
    global load_up_done, collection_check_bool, saved_just_now
    # Reset the flag on file load
    load_up_done = False
    collection_check_bool = True
    saved_just_now = False

@persistent
def on_file_save(dummy):
    global saved_just_now, load_up_done
    saved_just_now = True
    load_up_done = False

@persistent
def warning(warn):
    """Change editor outline color based on warning state."""
    global warn_state
    warn_state = warn
    theme = bpy.context.preferences.themes[0]
    if blender_version >= (4, 0, 0):
        prefs = bpy.context.preferences.addons[__package__].preferences
    else:
        prefs = bpy.context.preferences.addons[__name__].preferences
    
    if prefs.first_setup_bool == False:
        store_original_theme_color()
        prefs.highlight_color = theme.view_3d.space.text_hi
        
    else:    
        if warn and not prefs.UI_color_change_bool:
            if blender_version >= (4, 3, 0):
                theme.user_interface.editor_border = prefs.warn_color
            else:
                theme.user_interface.editor_outline = prefs.warn_color
        else: 
            if blender_version >= (4, 3, 0):
                theme.user_interface.editor_border = prefs.original_theme_color
            else:
                theme.user_interface.editor_outline = prefs.original_theme_color
 
def draw_warning_text():
    """Draw warning text in the 3D viewport if warn_state is True, with white text and brackets within [ ] and orange outside."""
    if blender_version >= (4, 0, 0):
        prefs = bpy.context.preferences.addons[__package__].preferences
    else:
        prefs = bpy.context.preferences.addons[__name__].preferences
    x_position = 10
    y_position = 10
    header_bottom = False

    if warn_state:
        # Starting positions for text warnings, starting from lower left corner 
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                # Set default positions for each VIEW_3D area
                x_position = 10
                y_position = 10  # Reset y_position to 10 for each VIEW_3D area

                # Check for TOOLS region and set x_position if found
                tools_region = next((region for region in area.regions if region.type == 'TOOLS'), None)
                if tools_region:
                    toolshelf = tools_region.width
                    x_position = 9 + toolshelf 
                header_region = next((region for region in area.regions if region.type == 'HEADER'), None) 
                if header_region:
                    if header_region.alignment == 'BOTTOM':
                        header_bottom = True
                        y_position = y_position + 27 * bpy.context.preferences.view.ui_scale
                shelf_region = next((region for region in area.regions if region.type == 'ASSET_SHELF'), None)
                if shelf_region:
                    if shelf_region.height > 1:
                        y_position = y_position + shelf_region.height + 27 * bpy.context.preferences.view.ui_scale

        if bpy.context.space_data is not None and bpy.context.space_data.show_region_header == False:
            if header_bottom:
                y_position = y_position - 27 * bpy.context.preferences.view.ui_scale

        if is_redo_panel_visible():
            y_position = y_position + 25 * bpy.context.preferences.view.ui_scale
        
        
        warning_message = " , ".join(warnings) if warnings else ""
        warning_message_full = f"HeadsUp: {warning_message}"
        
        # For viewport specific options, remove the warning text if it does not apply.
        if bpy.context.space_data is not None and bpy.context.space_data.type == 'VIEW_3D':
            area_identifier = hash(bpy.context.space_data)
            clean_warnings = clean_viewport_warnings(warnings, area_identifier)
            warning_message = " , ".join(clean_warnings[0]) if clean_warnings else ""
            warning_message_full = f"HeadsUp: {warning_message}"
            if clean_warnings[1] and prefs.viewport_highlighting and prefs.toggle_with_overlays and not bpy.context.space_data.overlay.show_overlays:
                draw_highlight_border(8)
            
            prev_message = warning_message_full
            warning_message_full = re.sub(r"^\s*HeadsUp:\s*$", "", prev_message)

            # Remove the string if Overlays are deactivated 
            if not bpy.context.space_data.overlay.show_overlays and prefs.toggle_with_overlays:
                warning_message_full = ""
            
        
        # Initialize color state and buffer to store characters for drawing
        inside_brackets = False
        current_word = ""
    
        # Calculate and set text size
        actual_text_size = calculate_text_size(prefs)
        if blender_version >= (4, 0, 0):
            blf.size(0, actual_text_size)
        else: 
            blf.size(0, actual_text_size, bpy.context.preferences.system.dpi)

        # Enable shadow
        blf.enable(0, blf.SHADOW)
        if blender_version >= (4,0,0):
            blf.shadow_offset(0, 0, 0)  # Offset shadow
            blf.shadow(0, 6, 0.0, 0.0, 0.0, 0.8)
        else:
            blf.shadow_offset(0, 1, -1)  # Offset shadow (x=2, y=-2)
            blf.shadow(0, 3, 0.0, 0.0, 0.0, 0.9)  # Blur level and shadow color (black with 70% opacity)


        for char in warning_message_full:
            if char == "[":
                # Draw any accumulated text in orange before entering brackets
                if current_word:
                    blf.color(0, *prefs.warn_color, 1.0)  # Orange for text outside brackets
                    blf.position(0, x_position, y_position, 0)
                    blf.draw(0, current_word)
                    x_position += blf.dimensions(0, current_word)[0]
                    current_word = ""
                
                # Draw the "[" bracket in white
                blf.color(0, *prefs.highlight_color, 1.0)  # White for brackets
                blf.position(0, x_position, y_position, 0)
                blf.draw(0, "[")
                x_position += blf.dimensions(0, "[")[0]
                
                inside_brackets = True
            
            elif char == "]":
                # Draw any accumulated text in white before exiting brackets
                if current_word:
                    blf.color(0, *prefs.highlight_color, 1.0)  # White for text inside brackets
                    blf.position(0, x_position, y_position, 0)
                    blf.draw(0, current_word)
                    x_position += blf.dimensions(0, current_word)[0]
                    current_word = ""
                
                # Draw the "]" bracket in white
                blf.color(0, *prefs.highlight_color, 1.0)  # White for brackets
                blf.position(0, x_position, y_position, 0)
                blf.draw(0, "]")
                x_position += blf.dimensions(0, "]")[0]
                
                inside_brackets = False
            
            else:
                # Accumulate characters for the current section
                current_word += char

        # Draw any remaining text in the appropriate color
        if current_word:
            color = (*prefs.highlight_color, 1.0) if inside_brackets else (*prefs.warn_color, 1.0)
            blf.color(0, *color)
            blf.position(0, x_position, y_position, 0)
            blf.draw(0, current_word)
        
        warning_message_old = warning_message_full

        if prefs.warn_4 and prefs.warn_4_a and bpy.context.scene.tool_settings.use_keyframe_insert_auto:
            if bpy.context.mode == 'OBJECT' or bpy.context.mode == 'POSE':
                draw_filled_red_circle()   
       
        # "Fullscreen" Version warning in the center of the 3D View
        if prefs.warn_44_a and not saved_just_now:
            if bpy.data.filepath != '':
                current_version = bpy.app.version_file[:2]
                file_version = bpy.data.version[:2]

                if file_version != current_version:
                    font_id = 0  
                    area_width = bpy.context.area.width
                    area_height = bpy.context.area.height

                    # Set warning text
                    blf.color(font_id, *prefs.warn_color, 1.0)
                    if bpy.app.version >= (4, 0, 0):
                        blf.size(font_id, 33)
                    else:
                        blf.size(font_id, 30, bpy.context.preferences.system.dpi)

                    # Enable shadow effect
                    blf.enable(font_id, blf.SHADOW)
                    blf.shadow_offset(font_id, 0, 0)  
                    if bpy.app.version >= (4, 0, 0):
                        blf.shadow(font_id, 6, 0.0, 0.0, 0.0, 0.9)
                    else:
                        blf.shadow(font_id, 5, 0.0, 0.0, 0.0, 0.9)

                    warning_text = "Attention:"
                    text_width, _ = blf.dimensions(font_id, warning_text)
                    blf.position(font_id, (area_width - text_width) / 2, area_height / 2 + 35, 0)
                    blf.draw(font_id, warning_text)

                    # Set file version text
                    blf.color(font_id, *prefs.highlight_color, 1.0)
                    file_version_text = f"File created in Blender {file_version[0]}.{file_version[1]}"
                    text_width, _ = blf.dimensions(font_id, file_version_text)
                    blf.position(font_id, (area_width - text_width) / 2, area_height / 2, 0)
                    blf.draw(font_id, file_version_text)

                    # Set save file reminder text
                    if bpy.app.version >= (4, 0, 0):
                        blf.size(font_id, 15)
                    else:
                        blf.size(font_id, 15, bpy.context.preferences.system.dpi)

                    reminder_text = "HeadsUp: Save file to confirm and remove the warning."
                    text_width, _ = blf.dimensions(font_id, reminder_text)
                    blf.position(font_id, (area_width - text_width) / 2, area_height / 2 - 20, 0)
                    blf.draw(font_id, reminder_text)
        # Reset color to default after drawing
        blf.color(0, 1.0, 1.0, 1.0, 1.0)
        blf.disable(0, blf.SHADOW)
    
def draw_warning_text_comp():
    """Draw warning text in the compositor if warn_state is True, with white text and brackets within [ ] and orange outside."""
    if blender_version >= (4, 0, 0):
        prefs = bpy.context.preferences.addons[__package__].preferences
    else:
        prefs = bpy.context.preferences.addons[__name__].preferences
    x_position = 10
    y_position = 10

    if warn_state and prefs.compositor_warnings:
        # Starting positions for text warnings, starting from lower left corner 
        for area in bpy.context.screen.areas:
            if area.type == 'NODE_EDITOR':
                x_position = 10
                y_position = 10  

        warning_message = " , ".join(warnings) if warnings else ""
        warning_message_full = f"HeadsUp: {warning_message}"
        
        # For viewport specific options, remove the warning text if it does not apply.
        if bpy.context.space_data is not None and bpy.context.space_data.type == 'NODE_EDITOR':
            if bpy.context.space_data.tree_type == 'CompositorNodeTree':
                area_identifier = hash(bpy.context.space_data)
                clean_warnings = clean_viewport_warnings(warnings, area_identifier)
                warning_message = " , ".join(clean_warnings[0]) if clean_warnings else ""
                warning_message_full = f"HeadsUp: {warning_message}"
                
                prev_message = warning_message_full
                warning_message_full = re.sub(r"^\s*HeadsUp:\s*$", "", prev_message)

                # Remove the string if Overlays are deactivated 
                if not bpy.context.space_data.overlay.show_overlays and prefs.toggle_with_overlays:
                    warning_message_full = ""
            else:
                warning_message_full = ""
        
        # Initialize color state and buffer to store characters for drawing
        inside_brackets = False
        current_word = ""

        # Calculate and set text size
        actual_text_size = calculate_text_size(prefs)
        if blender_version >= (4, 0, 0):
            blf.size(0, actual_text_size)
        else: 
            blf.size(0, actual_text_size, bpy.context.preferences.system.dpi)


        # Enable shadow
        blf.enable(0, blf.SHADOW)
        if blender_version >= (4,0,0):
            blf.shadow_offset(0, 0, 0)  # Offset shadow
            blf.shadow(0, 6, 0.0, 0.0, 0.0, 0.8)
        else:
            blf.shadow_offset(0, 1, -1)  # Offset shadow (x=2, y=-2)
            blf.shadow(0, 3, 0.0, 0.0, 0.0, 0.9)  # Blur level and shadow color (black with 70% opacity)
        
        for char in warning_message_full:
            if char == "[":
                # Draw any accumulated text in orange before entering brackets
                if current_word:
                    blf.color(0, *prefs.warn_color, 1.0)  # Orange for text outside brackets
                    blf.position(0, x_position, y_position, 0)
                    blf.draw(0, current_word)
                    x_position += blf.dimensions(0, current_word)[0]
                    current_word = ""
                
                # Draw the "[" bracket in white
                blf.color(0, *prefs.highlight_color, 1.0)  # White for brackets
                blf.position(0, x_position, y_position, 0)
                blf.draw(0, "[")
                x_position += blf.dimensions(0, "[")[0]
                
                inside_brackets = True
            
            elif char == "]":
                # Draw any accumulated text in white before exiting brackets
                if current_word:
                    blf.color(0, *prefs.highlight_color, 1.0)  # White for text inside brackets
                    blf.position(0, x_position, y_position, 0)
                    blf.draw(0, current_word)
                    x_position += blf.dimensions(0, current_word)[0]
                    current_word = ""
                
                # Draw the "]" bracket in white
                blf.color(0, *prefs.highlight_color, 1.0)  # White for brackets
                blf.position(0, x_position, y_position, 0)
                blf.draw(0, "]")
                x_position += blf.dimensions(0, "]")[0]
                
                inside_brackets = False
            
            else:
                # Accumulate characters for the current section
                current_word += char

        # Draw any remaining text in the appropriate color
        if current_word:
            color = (*prefs.highlight_color, 1.0) if inside_brackets else (*prefs.warn_color, 1.0)
            blf.color(0, *color)
            blf.position(0, x_position, y_position, 0)
            blf.draw(0, current_word)

        # "Fullscreen" Version warning in the center of the Compositor
        if prefs.warn_44_a and not saved_just_now:
            if bpy.data.filepath != '':
                current_version = bpy.app.version_file[:2]
                file_version = bpy.data.version[:2]

                if file_version != current_version:
                    font_id = 0  
                    area_width = bpy.context.area.width
                    area_height = bpy.context.area.height

                    # Set warning text
                    blf.color(font_id, *prefs.warn_color, 1.0)
                    if bpy.app.version >= (4, 0, 0):
                        blf.size(font_id, 33)
                    else:
                        blf.size(font_id, 30, bpy.context.preferences.system.dpi)

                    # Enable shadow effect
                    blf.enable(font_id, blf.SHADOW)
                    blf.shadow_offset(font_id, 0, 0)  # Offset shadow
                    if bpy.app.version >= (4, 0, 0):
                        blf.shadow(font_id, 6, 0.0, 0.0, 0.0, 1)
                    else:
                        blf.shadow(font_id, 5, 0.0, 0.0, 0.0, 1)

                    warning_text = "Attention:"
                    text_width, _ = blf.dimensions(font_id, warning_text)
                    blf.position(font_id, (area_width - text_width) / 2, area_height / 2 + 35, 0)
                    blf.draw(font_id, warning_text)

                    # Set file version text
                    blf.color(font_id, *prefs.highlight_color, 1.0)
                    file_version_text = f"File created in Blender {file_version[0]}.{file_version[1]}"
                    text_width, _ = blf.dimensions(font_id, file_version_text)
                    blf.position(font_id, (area_width - text_width) / 2, area_height / 2, 0)
                    blf.draw(font_id, file_version_text)

                    # Set save file reminder text
                    if bpy.app.version >= (4, 0, 0):
                        blf.size(font_id, 15)
                    else:
                        blf.size(font_id, 15, bpy.context.preferences.system.dpi)

                    reminder_text = "HeadsUp: Save file to confirm and remove the warning."
                    text_width, _ = blf.dimensions(font_id, reminder_text)
                    blf.position(font_id, (area_width - text_width) / 2, area_height / 2 - 20, 0)
                    blf.draw(font_id, reminder_text)
        
        # Reset color to default after drawing
        blf.color(0, 1.0, 1.0, 1.0, 1.0)
        blf.disable(0, blf.SHADOW)

def draw_circular_gradient():
    """Draw a circular gradient over the 3D viewport."""
    props = bpy.context.scene.HEADSUP_WarnInfoProperties
    if not props.warn_info_44:
        return
    
    region = bpy.context.region
    width, height = region.width, region.height

    # Center of the viewport
    center_x, center_y = width / 2, height / 2

    # Define the number of segments for the circle
    segments = 64
    angle_step = 2 * math.pi / segments

    # Radius of the gradient (diagonal length for full coverage)
    radius = math.sqrt(width ** 2 + height ** 2) / 2

    # Create vertices for the circular gradient
    vertices = [(center_x, center_y)]  # Add the center vertex
    vertices.extend([
        (center_x + radius * math.cos(i * angle_step),
         center_y + radius * math.sin(i * angle_step))
        for i in range(segments + 1)  # Close the circle
    ])

    # Define colors for the gradient
    colors = [(0.1, 0.1, 0.1, 1.0)]  # Dark grey center
    colors.extend([(0.1, 0.1, 0.1, 0.0) for _ in range(segments + 1)])  # Transparent edges

    # Create a shader for drawing
    if blender_version >= (4,0,0):
        shader = gpu.shader.from_builtin('SMOOTH_COLOR')
    else:
        shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')

    # Enable blending for transparency
    gpu.state.blend_set('ALPHA')

    # Create a batch for the gradient
    batch = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices, "color": colors})

    # Draw the gradient
    shader.bind()
    batch.draw(shader)

    # Restore the default blend state
    gpu.state.blend_set('NONE')

def update_visible_collections():
    global view_layer_visible_collections
    view_layer_visible_collections = {}

    for layer in bpy.context.scene.view_layers:
        visible_collections = set()  # Use a set to avoid duplicates
        if not layer.use:
            continue
        def check_layer_collection(layer_coll):
            # Skip checking this collection and its children if it is hidden in render
            if layer_coll.collection.hide_render:
                return

            # Add the collection name if it is not excluded
            if not layer_coll.exclude:
                visible_collections.add(layer_coll.collection.name)

            # Recursively check child collections
            for child in layer_coll.children:
                check_layer_collection(child)

        # Start checking from the root layer collection
        check_layer_collection(layer.layer_collection)
        # Map the layer name to the list of visible collection names
        view_layer_visible_collections[layer.name] = list(visible_collections)

def check_object_mismatches(check_objects):
    """Find objects with mismatched hide_render and hide_viewport statuses."""
    SKIPPED_TYPES = {'CAMERA', 'IMAGE', 'LATTICE', 'ARMATURE', 'SPEAKER', 'FORCE_FIELD'}

    global problematic_objects

    object_view_layer_map = {}

    for obj in check_objects:
        if not obj or obj.type in SKIPPED_TYPES:
            continue

        # Initialize the object in the map
        object_view_layer_map[obj] = []

        # Find collection names the object belongs to
        obj_collection_names = {coll.name for coll in obj.users_collection}

        # Check if these collection names appear in the view_layer_visible_collections
        for layer_name, visible_collections in view_layer_visible_collections.items():
            if obj_collection_names.intersection(visible_collections):
                # If the object has a mismatch, add it to the map and problematic_objects
                if obj.hide_render != obj.hide_viewport:
                    object_view_layer_map[obj].append(layer_name)
                    problematic_objects.add(obj)

    # Build mismatch list
    mismatch_list = [
        {"object": obj, "view_layers": view_layers}
        for obj, view_layers in object_view_layer_map.items()
        if view_layers
    ]

    return mismatch_list

def check_modifier_mismatches(check_objects):
    """Find objects with mismatched modifier visibility (show_viewport vs show_render)."""
    CHECKED_TYPES = {'MESH', 'CURVE', 'LATTICE', 'FONT', 'GPENCIL'}

    global problematic_objects

    mismatch_dict = {}

    for obj in check_objects:
        if not obj or obj.type not in CHECKED_TYPES:
            continue

        # Skip objects fully hidden
        if obj.hide_viewport and obj.hide_render:
            continue

        # Check for mismatched modifiers
        modifier_mismatch = any(
            modifier.show_viewport != modifier.show_render for modifier in obj.modifiers
        )

        if modifier_mismatch:
            if obj not in mismatch_dict:
                mismatch_dict[obj] = []

            # Get the collections the object belongs to
            obj_collection_names = {coll.name for coll in obj.users_collection}

            # Check if these collections intersect with visible collections for any view layer
            for layer_name, visible_collections in view_layer_visible_collections.items():
                if obj_collection_names.intersection(visible_collections):
                    mismatch_dict[obj].append(layer_name)
                    problematic_objects.add(obj)

    mismatch_list = [
        {"object": obj, "view_layers": view_layers}
        for obj, view_layers in mismatch_dict.items()
        if view_layers
    ]
    return mismatch_list

def check_collection_mismatches():
    """Find collections with mismatched hide_render and hide_viewport attributes."""
    mismatch_dict = {}

    def check_layer_collection(layer_coll, view_layer_name):
        """Recursively check layer collections for mismatches."""
        collection = layer_coll.collection

        # Skip collection if it is excluded (this applies to the collection itself)
        if layer_coll.exclude:
            # Only skip the current collection, but still check its children
            pass
        else:
            # Determine visibility based on hide_render (should it be visible in the renderer?)
            collection_visible = not collection.hide_render

            # Check for mismatches between hide_render and hide_viewport
            if collection.hide_render != collection.hide_viewport:
                if collection.name not in mismatch_dict:
                    mismatch_dict[collection.name] = []
                mismatch_dict[collection.name].append(view_layer_name)

        # Recursively check child collections, regardless of the parent's exclusion (unless the child is excluded)
        for child_layer_coll in layer_coll.children:
            check_layer_collection(
                child_layer_coll,
                view_layer_name=view_layer_name
            )

    # Iterate through all view layers
    for layer in bpy.context.scene.view_layers:
        check_layer_collection(
            layer.layer_collection,
            view_layer_name=layer.name
        )

    # Convert the dictionary to a list of mismatches
    mismatch_list = [{"collection_name": coll_name, "view_layers": view_layers}
                     for coll_name, view_layers in mismatch_dict.items()]
    return mismatch_list

def on_any_collection_or_layer_change():
    """Callback when any collection or layer property changes."""
    global collection_check_bool, problematic_objects, compositor_check_bool
    collection_check_bool = True
    compositor_check_bool = True
    update_visible_collections()
    for obj in bpy.context.scene.objects:
        problematic_objects.add(obj)

def compositor_callback():
    global compositor_check_bool
    compositor_check_bool = True

def subscribe_to_global_visibility_and_exclusion():
    """Subscribe globally to visibility and exclusion property changes."""
    # Subscribe to Collection visibility properties
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Collection, "hide_viewport"),
        owner=subscribe_to_global_visibility_and_exclusion,
        args=(),
        notify=on_any_collection_or_layer_change,
    )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Collection, "hide_render"),
        owner=subscribe_to_global_visibility_and_exclusion,
        args=(),
        notify=on_any_collection_or_layer_change,
    )
    
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.LayerCollection, "exclude"),
        owner=subscribe_to_global_visibility_and_exclusion,
        args=(),
        notify=on_any_collection_or_layer_change,
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.LayerCollection, "name"),
        owner=subscribe_to_global_visibility_and_exclusion,
        args=(),
        notify=on_any_collection_or_layer_change,
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "hide_viewport"),
        owner=subscribe_to_global_visibility_and_exclusion,
        args=(),
        notify=on_obj_visibility_change,
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "hide_render"),
        owner=subscribe_to_global_visibility_and_exclusion,
        args=(),
        notify=on_obj_visibility_change,
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "name"),
        owner=subscribe_to_global_visibility_and_exclusion,
        args=(),
        notify=on_obj_visibility_change,
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Material, "name"),
        owner=subscribe_to_global_visibility_and_exclusion,
        args=(),
        notify=on_material_change,
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Scene, "use_nodes"),
        owner=subscribe_to_global_visibility_and_exclusion,
        args=(),
        notify=compositor_callback,
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.RenderSettings, "use_compositing"),
        owner=subscribe_to_global_visibility_and_exclusion,
        args=(),
        notify=compositor_callback,
    )

def on_material_change():
    for mat in bpy.data.materials:
        if not mat.library:
            problematic_materials.add(mat)

def on_obj_visibility_change():
    """Callback when any collection or layer property changes."""
    global problematic_objects
    for obj in bpy.context.scene.objects:
        problematic_objects.add(obj)

def check_renderlayer_compositing_conditions():
    def is_connected_to_file_output(node, visited):
        if node in visited:
            return False, False  # Avoid infinite loops
        visited.add(node)

        if node.type == 'OUTPUT_FILE':
            return True, node.mute

        for output in node.outputs:
            if output.is_linked:
                for link in output.links:
                    connected_node = link.to_node
                    connected, muted = is_connected_to_file_output(connected_node, visited)
                    if connected:
                        return True, muted

        return False, False

    scene = bpy.context.scene
    if not scene.render.use_compositing or not scene.use_nodes or scene.node_tree is None:
        return []
    
    node_tree = scene.node_tree
    compositor_nodes = node_tree.nodes
    warnings = []

    for view_layer in scene.view_layers:
        if not view_layer.use:
            continue

        render_layer_node = next((node for node in compositor_nodes if node.type == 'R_LAYERS' and node.layer == view_layer.name), None)
        
        if not render_layer_node:
            warnings.append("Renderlayer Node(s) missing")
            continue
        
        if render_layer_node.mute:
            warnings.append("Renderlayer Node(s) muted")
            
        connected, muted = is_connected_to_file_output(render_layer_node, set())
        if muted:
            warnings.append("File Output Node(s) muted")
    
    return warnings

@persistent
def headsup_check_warnings(scene, depsgraph):
    """Check auto keyframe settings and warn if necessary."""
    global warnings, mismatch_list, old_warnings, collection_mismatches, object_mismatches, viewlayer_count
    global modifier_mismatches, undefined_nodes, load_up_done, problematic_materials, problematic_objects
    global collection_check_bool, view_layer_visibilities, compositor_check_bool, current_scene, old_warn_state
        
    scene = bpy.context.scene
    if blender_version >= (4, 2):
        if len(bpy.context.window.modal_operators) > 0:
            if load_up_done:
                load_up_done = False
            return

    if bpy.context.screen and bpy.context.screen.is_animation_playing:
        if load_up_done:
            load_up_done = False
        return

    mismatch_list = []
    new_warnings = []
    active_obj = bpy.context.active_object
    if blender_version >= (4, 0, 0):
        prefs = bpy.context.preferences.addons[__package__].preferences
    else:
        prefs = bpy.context.preferences.addons[__name__].preferences
    props = bpy.context.scene.HEADSUP_WarnInfoProperties
    
    # Reset all warn_info properties
    props.warn_info_custom = False
    for i in range(1, 46):  # From 1 to 45
        setattr(props, f"warn_info_{i}", False)

    for view_layer in bpy.context.scene.view_layers:
        current_state = view_layer.use
        previous_state = view_layer_visibilities.get(view_layer.name, None)
        
        # Compare with the stored state
        if previous_state is None:
            view_layer_visibilities[view_layer.name] = current_state
        elif current_state != previous_state:
            load_up_done = False
            view_layer_visibilities[view_layer.name] = current_state

    # Do a full check after loading a blender file, otherwise only check relevant updates and known problematic items
    if current_scene is None or bpy.context.scene != current_scene:
        load_up_done = False
        current_scene = bpy.context.scene

    if load_up_done == False:
        check_objects = set()
        check_materials = set()        

        for obj in bpy.context.scene.objects:
            check_objects.add(obj)
        for mat in bpy.data.materials:
            if not mat.library:
                check_materials.add(mat)
        collection_check_bool = True
        compositor_check_bool = True
        update_visible_collections()
    else: 
        check_objects = set()
        check_materials = set()        

        for obj in problematic_objects:
            check_objects.add(obj)
        
        for mat in problematic_materials:
            check_materials.add(mat)
        if depsgraph is not None:
            for update in depsgraph.updates:
                if isinstance(update.id, bpy.types.Material):
                    mat = update.id
                    check_materials.add(mat)
                if isinstance(update.id, bpy.types.Object):
                    obj = update.id
                    check_objects.add(obj)
                if isinstance(update.id, bpy.types.Collection):
                    collection_check_bool = True
                    update_visible_collections()
                    for obj in bpy.context.scene.objects:
                        check_objects.add(obj)
                if isinstance(update.id, bpy.types.CompositorNodeTree):
                    compositor_check_bool = True
        if viewlayer_count != len(bpy.context.scene.view_layers):
            viewlayer_count = len(bpy.context.scene.view_layers)
            compositor_check_bool = True
            
        # Problematic items have been added to the check-lists, if they are still problematic, they'll be added again
        problematic_materials = set()
        problematic_objects = set()

    try:
        if prefs.warn_1:
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        if area.spaces is not None:
                            for space in area.spaces: 
                                if space.type == 'VIEW_3D':
                                    area_identifier = hash(space)
                                    if space.lock_camera:
                                        new_warnings.append(f"?{area_identifier}?[Camera to View] is ON!")
                                        props.warn_info_1 = True

        if prefs.warn_2:
            if len(check_objects) > 0:
                object_mismatches = check_object_mismatches(check_objects)
            if collection_check_bool:
                collection_mismatches = check_collection_mismatches()                

            if len(collection_mismatches) > 0 and len(object_mismatches) == 0:
               new_warnings.append(f"[Collection Render/Viewport Mismatch] check HeadsUp SidePanel")
               props.warn_info_2 = True
            if len(object_mismatches) > 0 and len(collection_mismatches) == 0:
               new_warnings.append(f"[Object Render/Viewport Mismatch] check HeadsUp SidePanel")
               props.warn_info_2 = True
            if len(object_mismatches) > 0 and len(collection_mismatches) > 0:
               new_warnings.append(f"[Object & Collection Render/Viewport Mismatches] check HeadsUp SidePanel")
               props.warn_info_2 = True

            if len(collection_mismatches) == 0:
                collection_check_bool = False

        if prefs.warn_3:
            if active_obj and active_obj.type == 'MESH':
                    if bpy.context.mode == 'SCULPT':
                        if active_obj.data.shape_keys:
                            active_shape_key_index = active_obj.active_shape_key_index
                            if active_shape_key_index != 0:
                                active_shape_key = active_obj.data.shape_keys.key_blocks[active_shape_key_index]
                                if round(active_shape_key.value, 3) != 1.0:
                                    new_warnings.append(f"Active [Shape Key] is not 1.0! Set to: {round(active_shape_key.value, 3)}!")
                                    props.warn_info_3 = True
        
        if prefs.warn_4:
            if bpy.context.mode == 'OBJECT' or bpy.context.mode == 'POSE':
                if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
                    new_warnings.append("[Auto Keying] is ON!")
                    props.warn_info_4 = True
        
        if prefs.warn_5:        
            if bpy.context.mode == 'EDIT_MESH':
                if bpy.context.scene.tool_settings.use_proportional_edit:
                    new_warnings.append("[Proportional Editing (Edit Mode/UV)] is ON!")
                    props.warn_info_5 = True
            if bpy.context.mode == 'OBJECT':    
                if bpy.context.scene.tool_settings.use_proportional_edit_objects:
                    new_warnings.append("[Proportional Editing (Object Mode)] is ON!")
                    props.warn_info_5 = True
            
            fcurve_checked = False
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'GRAPH_EDITOR':
                        if bpy.context.scene.tool_settings.use_proportional_fcurve:
                            new_warnings.append("[Proportional Editing (Graph Editor)] is ON!")
                            props.warn_info_5 = True
                        fcurve_checked = True
                        break  # Exit the areas loop for this screen
                if fcurve_checked:
                    break 
            
            dopesheet_checked = False
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'DOPESHEET_EDITOR':
                        if bpy.context.scene.tool_settings.use_proportional_action:
                            new_warnings.append("[Proportional Editing (Dopesheet)] is ON!")
                            props.warn_info_5 = True
                        dopesheet_checked = True
                        break 
                if dopesheet_checked:
                    break  
        
        if prefs.warn_6:        
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.tool_settings.use_transform_data_origin:
                    new_warnings.append("[Affect Only >Origins<] is ON!")
                    props.warn_info_6 = True
                            
                if bpy.context.scene.tool_settings.use_transform_pivot_point_align:
                    new_warnings.append("[Affect Only >Locations<] is ON!")
                    props.warn_info_6 = True
                    
                if bpy.context.scene.tool_settings.use_transform_skip_children:
                    new_warnings.append("[Affect Only >Parents<] is ON!")
                    props.warn_info_6 = True
   
        if prefs.warn_7:    
            if bpy.context.mode == 'OBJECT' or bpy.context.mode == 'EDIT_MESH':
                if bpy.context.scene.tool_settings.use_snap:
                    new_warnings.append("[Snapping] is ON!")
                    props.warn_info_7 = True
            if bpy.context.mode == 'EDIT_MESH':
                if bpy.context.scene.tool_settings.use_snap_uv:
                    new_warnings.append("[Snapping (UV)] is ON!")
                    props.warn_info_7 = True

        if prefs.warn_8:    
            if active_obj:
                if not round(bpy.context.object.scale[0],3) == round(bpy.context.object.scale[1],3) == round(bpy.context.object.scale[2],3):
                    if any(axis <= 0 for axis in bpy.context.object.scale):
                        if prefs.warn_8_a:
                            new_warnings.append("[Non-Uniform Scale (Zero or Negative Axis!)] for active Object!")
                            props.warn_info_8 = True
                    else:
                        if prefs.warn_8_b and active_obj.type not in ("LIGHT","META","CAMERA","LIGHT_PROBE"):
                            new_warnings.append("[Non-Uniform Scale] for active Object!") 
                            props.warn_info_8 = True
                    
                else: 
                    if bpy.context.object.scale[0] != 1.0: 
                        if bpy.context.object.scale[0] < 0:
                            if prefs.warn_8_a:
                                new_warnings.append("[Negative Scale] for active Object!")
                                props.warn_info_8 = True
                        else:
                            if prefs.warn_8_c and active_obj.type not in ("LIGHT","META","CAMERA","LIGHT_PROBE"): 
                                new_warnings.append("[Scale is not 1] for active Object!")
                                props.warn_info_8 = True

        if prefs.warn_9:            
            if bpy.context.mode != 'OBJECT':
                if active_obj and active_obj.type == 'MESH':    
                    mirror_warnings = []

                    if bpy.context.object.data.use_mirror_x:
                        mirror_warnings.append("'X'")

                    if bpy.context.object.data.use_mirror_y:
                        mirror_warnings.append("'Y'")

                    if bpy.context.object.data.use_mirror_z:
                        mirror_warnings.append("'Z'")

                    if bpy.context.object.data.use_mirror_topology:
                        mirror_warnings.append("'Topology'")

                    if mirror_warnings:
                        new_warnings.append(f"[Mirror {', '.join(mirror_warnings)}] is ON!")
                        props.warn_info_9 = True
  
        if prefs.warn_10:        
            if bpy.context.mode == 'OBJECT':   
                if bpy.context.scene.render.use_simplify:
                    sub_v = bpy.context.scene.render.simplify_subdivision
                    sub_r = bpy.context.scene.render.simplify_subdivision_render
                    if not prefs.warn_10_a:
                        if sub_v <= prefs.simplify_viewport and not sub_r <= prefs.simplify_render:
                            new_warnings.append(f"[Simplify] is ON! Viewport: {sub_v}, Render: {sub_r}")
                            props.warn_info_10 = True
                    if sub_r <= prefs.simplify_render:
                        new_warnings.append(f"[Simplify] is ON! Render Subdivision is low: {sub_r}!")
                        props.warn_info_10 = True
   
        if prefs.warn_11:   
            if bpy.context.mode == 'OBJECT':         
                if bpy.context.scene.render.use_sequencer:
                    has_non_audio_strips = any(
                        strip.type != 'SOUND' for strip in scene.sequence_editor.sequences_all
                    ) if scene.sequence_editor else False
                    if has_non_audio_strips:
                        new_warnings.append("[Sequencer] is ON and contains Data!")
                        props.warn_info_11 = True
       
        if prefs.warn_12:  
            if bpy.context.mode == 'OBJECT':                  
                if bpy.context.scene.render.use_border:
                    border_x = bpy.context.scene.render.border_max_x - bpy.context.scene.render.border_min_x
                    border_y = bpy.context.scene.render.border_max_y - bpy.context.scene.render.border_min_y
                    
                    if border_x != 1.0 or border_y != 1.0:
                        if bpy.context.scene.render.use_crop_to_border:
                            new_warnings.append("[Render Border with Crop] is ON!")
                        else:
                            new_warnings.append("[Render Border] is ON!")
                        props.warn_info_12 = True
        
        if prefs.warn_13:                
            if bpy.context.mode == 'EDIT_MESH':
                if bpy.context.scene.tool_settings.use_mesh_automerge:
                    new_warnings.append("[Automerge Vertices] is ON!")
                    props.warn_info_13 = True
        
        if prefs.warn_14:        
            if bpy.context.mode == 'EDIT_MESH':
                if bpy.context.scene.tool_settings.use_uv_select_sync:
                    new_warnings.append("[UV Sync Selection] is ON!")
                    props.warn_info_14 = True
        
        if prefs.warn_15:
            if bpy.context.mode == 'EDIT_MESH':        
                if bpy.context.scene.tool_settings.use_edge_path_live_unwrap:
                    new_warnings.append("[Live Unwrap] is ON!")
                    props.warn_info_15 = True
                    
        if prefs.warn_16:
            if bpy.context.mode == 'EDIT_MESH':    
                if bpy.context.scene.tool_settings.use_transform_correct_face_attributes:
                    new_warnings.append("[Correct Face Attributes] is ON!(UVs change with Editmode Transforms)!")
                    props.warn_info_16 = True
                
        if prefs.warn_17:
            if multiple_sequence_nodes(check_materials):
                new_warnings.append("Several [Image Sequence] nodes with different settings refer to the same datablock, expect issues!")
                props.warn_info_17 = True
        
        if prefs.warn_18:
            if active_obj and active_obj.type == 'MESH':
                if bpy.context.mode == 'SCULPT':
                    if any(mod.type == 'CORRECTIVE_SMOOTH' and mod.show_viewport for mod in active_obj.modifiers):
                        new_warnings.append("Sculpting with an active [Corrective Smooth] modifier!")
                        props.warn_info_18 = True
                             
        if prefs.warn_19:
            if bpy.context.blend_data.use_autopack:
                new_warnings.append("[Autopack Ressources] is ON!")
                props.warn_info_19 = True
                
        if prefs.warn_20:
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        if area.spaces is not None:
                            for space in area.spaces: 
                                if space.type == 'VIEW_3D':
                                    area_identifier = hash(space)
                                    if space.local_view:
                                        new_warnings.append(f"?{area_identifier}?[Local View] is ON!")
                                        props.warn_info_20 = True

        if prefs.warn_21:
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        if area.spaces is not None:
                            for space in area.spaces: 
                                if space.type == 'VIEW_3D':
                                    area_identifier = hash(space)
                                    for region in area.regions:
                                        if region.type == 'WINDOW':
                                            if region.data.use_clip_planes == True:
                                                new_warnings.append(f"?{area_identifier}?[Clipping Border] is ON! Alt+B to reset")
                                                props.warn_info_21 = True
                                
        if prefs.warn_22:
            if bpy.context.mode == 'OBJECT':
                if active_obj and active_obj.type == 'MESH':
                    if active_obj.is_shadow_catcher and not active_obj.is_holdout:
                        new_warnings.append("Active Object is [Shadow Catcher]") 
                        props.warn_info_22 = True   
                    if active_obj.is_holdout and not active_obj.is_shadow_catcher:
                        new_warnings.append("Active Object is [Holdout]")    
                        props.warn_info_22 = True
                    if active_obj.is_holdout and active_obj.is_shadow_catcher:
                        new_warnings.append("Active Object is [Holdout & Shadow Catcher]") 
                        props.warn_info_22 = True   
                
        if prefs.warn_23:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.resolution_percentage != 100:
                    resolution_percentage = bpy.context.scene.render.resolution_percentage
                    new_warnings.append(f"[Render Resolution Percentage] is: {resolution_percentage}%!")
                    props.warn_info_23 = True
                
        if prefs.warn_24:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.engine  == "CYCLES": 
                    if bpy.context.scene.cycles.filter_width != 1.5:
                        pixel_filter = round(bpy.context.scene.cycles.filter_width,2)
                        new_warnings.append(f"[Pixel Filter(Cycles)]: {pixel_filter} px!(Default 1.5px)")
                        props.warn_info_24 = True
                if bpy.context.scene.render.engine  == "BLENDER_EEVEE" or bpy.context.scene.render.engine == "BLENDER_EEVEE_NEXT":
                    if bpy.context.scene.render.filter_size != 1.5:
                        pixel_filter = round(bpy.context.scene.render.filter_size,2)
                        new_warnings.append(f"[Pixel Filter(EEVEE):] {pixel_filter} px!(Default 1.5px)")
                        props.warn_info_24 = True
                                       
        if prefs.warn_25:
            if bpy.context.mode == 'OBJECT':
                if prefs.warn_25_a == 'ACTIVE_ONLY':
                    if active_obj:
                        modifier_list = []
                        if not active_obj.hide_render and not active_obj.hide_viewport:
                            for modifier in active_obj.modifiers:
                                if modifier.show_viewport != modifier.show_render:
                                    modifier_list.append(modifier.name)
                        if len(modifier_list) > 0:
                            modifier_string = " & ".join(sorted(modifier_list))
                            new_warnings.append(f"[Modifier Visibility Mismatch] for [{modifier_string}]")
                            props.warn_info_25=True
                else:
                    modifier_mismatches = check_modifier_mismatches(check_objects)
                    if len(modifier_mismatches) > 0:
                        new_warnings.append(f"[Modifier Render/Viewport Mismatch] check HeadsUp SidePanel")
                        props.warn_info_25=True

        if prefs.warn_26:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.engine  == "CYCLES":
                    view_layer_list = []
                    for view_layer in bpy.context.scene.view_layers:
                        if view_layer.samples != 0: 
                            view_layer_list.append(f"'{view_layer.name}': {view_layer.samples}")
                    
                    if len(view_layer_list) > 0:
                        override_sample_string = f"[Sample Override] for ViewLayer(s): {' | '.join(view_layer_list)}"
                        props.warn_info_26 = True
                        new_warnings.append(override_sample_string)


                     
        if prefs.warn_27:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.engine  == "CYCLES":
                    if bpy.context.scene.cycles.samples <= prefs.sample_limit_lower :
                        new_warnings.append(f"[Low Samples(Cycles)]: {bpy.context.scene.cycles.samples} samples!")
                        props.warn_info_27 = True
                if bpy.context.scene.render.engine == "BLENDER_EEVEE":
                    if bpy.context.scene.eevee.taa_render_samples <= prefs.sample_limit_lower :
                        new_warnings.append(f"[Low Samples(EEVEE)]: {bpy.context.scene.eevee.taa_render_samples} samples!")
                        props.warn_info_27 = True
                
        if prefs.warn_27_a:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.engine  == "CYCLES":
                    if bpy.context.scene.cycles.samples >= prefs.sample_limit_upper :
                        new_warnings.append(f"[High Samples(Cycles)]: {bpy.context.scene.cycles.samples} samples!")
                        props.warn_info_27 = True
                if bpy.context.scene.render.engine == "BLENDER_EEVEE":
                    if bpy.context.scene.eevee.taa_render_samples >= prefs.sample_limit_upper :
                        new_warnings.append(f"[High Samples(EEVEE)]: {bpy.context.scene.eevee.taa_render_samples} samples!")
                        props.warn_info_27 = True
                                                       
        if prefs.warn_28:
            if bpy.context.mode == 'OBJECT':
                if active_obj and active_obj.modifiers:
                    array_modifier = None
                    for i, mod in enumerate(active_obj.modifiers):
                        if mod.type == 'ARRAY' and mod.use_relative_offset:
                            if i != 0:
                                new_warnings.append(f"Modifiers before [Array] with Relative Offset!")
                                props.warn_info_28 = True

        if prefs.warn_29:
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        if area.spaces is not None:
                            for space in area.spaces: 
                                if space.type == 'VIEW_3D':
                                    visibilities_list = set()
                                    area_identifier = hash(space)
                                    if not space.show_object_viewport_armature:
                                        visibilities_list.add("Armatures")
                                    if not space.show_object_viewport_camera:
                                        visibilities_list.add("Cameras")
                                    if not space.show_object_viewport_curve:
                                        visibilities_list.add("Curves")
                                    if not space.show_object_viewport_curves:
                                        visibilities_list.add("Hair Curves")
                                    if not space.show_object_viewport_empty:
                                        visibilities_list.add("Empties")
                                    if not space.show_object_viewport_font:
                                        visibilities_list.add("Fonts")
                                    if not space.show_object_viewport_grease_pencil:
                                        visibilities_list.add("Grease Pencil")
                                    if not space.show_object_viewport_lattice:
                                        visibilities_list.add("Lattices")
                                    if not space.show_object_viewport_light:
                                        visibilities_list.add("Lights")
                                    if not space.show_object_viewport_light_probe:
                                        visibilities_list.add("Light Probes")
                                    if not space.show_object_viewport_mesh:
                                        visibilities_list.add("Meshes")
                                    if not space.show_object_viewport_meta:
                                        visibilities_list.add("Meta Balls")
                                    if not space.show_object_viewport_pointcloud:
                                        visibilities_list.add("Pointclouds")
                                    if not space.show_object_viewport_speaker:
                                        visibilities_list.add("Speakers")
                                    if not space.show_object_viewport_surf:
                                        visibilities_list.add("Surfaces")
                                    if not space.show_object_viewport_volume:
                                        visibilities_list.add("Volumes")

                                    visibilities_string = ", ".join(sorted(visibilities_list)) if visibilities_list else ""
                                    if visibilities_list:
                                        new_warnings.append(f"?{area_identifier}?[Viewport doesn't show: {visibilities_string}]")
                                        props.warn_info_29 = True

        if prefs.warn_30:
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        if area.spaces is not None:
                            for space in area.spaces: 
                                if space.type == 'VIEW_3D':
                                    selectabilities_list = set()
                                    area_identifier = hash(space)
                                    if not space.show_object_select_armature:
                                        selectabilities_list.add("Armatures")
                                    if not space.show_object_select_camera:
                                        selectabilities_list.add("Cameras")
                                    if not space.show_object_select_curve:
                                        selectabilities_list.add("Curves")
                                    if not space.show_object_select_curves:
                                        selectabilities_list.add("Hair Curves")
                                    if not space.show_object_select_empty:
                                        selectabilities_list.add("Empties")
                                    if not space.show_object_select_font:
                                        selectabilities_list.add("Fonts")
                                    if not space.show_object_select_grease_pencil:
                                        selectabilities_list.add("Grease Pencil")
                                    if not space.show_object_select_lattice:
                                        selectabilities_list.add("Lattices")
                                    if not space.show_object_select_light:
                                        selectabilities_list.add("Lights")
                                    if not space.show_object_select_light_probe:
                                        selectabilities_list.add("Light Probes")
                                    if not space.show_object_select_mesh:
                                        selectabilities_list.add("Meshes")
                                    if not space.show_object_select_meta:
                                        selectabilities_list.add("Meta Balls")
                                    if not space.show_object_select_pointcloud:
                                        selectabilities_list.add("Pointclouds")
                                    if not space.show_object_select_speaker:
                                        selectabilities_list.add("Speakers")
                                    if not space.show_object_select_surf:
                                        selectabilities_list.add("Surfaces")
                                    if not space.show_object_select_volume:
                                        selectabilities_list.add("Volumes")

                                    selectabilities_string = ", ".join(sorted(selectabilities_list)) if selectabilities_list else ""
                                    if selectabilities_list:
                                        new_warnings.append(f"?{area_identifier}?[Viewport can't select: {selectabilities_string}]")
                                        props.warn_info_30 = True

        if prefs.warn_31:
            if bpy.context.scene.use_preview_range:
                if bpy.context.scene.frame_preview_start != bpy.context.scene.frame_start or bpy.context.scene.frame_preview_end != bpy.context.scene.frame_end:
                    new_warnings.append(f"[Render Preview Range]: {bpy.context.scene.frame_preview_start}-{bpy.context.scene.frame_preview_end}!")
                    props.warn_info_31 = True

        if prefs.warn_32:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.engine  == "CYCLES":
                    if prefs.warn_32_a == 'GPU':
                        if bpy.context.scene.cycles.device == 'CPU':
                            new_warnings.append(f"[Cycles not using GPU]")
                            props.warn_info_32 = True
                    else:
                        if bpy.context.scene.cycles.device == 'GPU':
                            new_warnings.append(f"[Cycles not using CPU]")
                            props.warn_info_32 = True

        if prefs.warn_33:
            if active_obj and bpy.context.mode == 'OBJECT':
                lock_warnings = []
                if any(bpy.context.object.lock_scale):
                    locked_axes = ",".join(axis for axis, locked in zip("XYZ", bpy.context.object.lock_scale) if locked)
                    lock_warnings.append(f"Scale({locked_axes})")
                    props.warn_info_33 = True
                if any(bpy.context.object.lock_location):
                    locked_axes = ",".join(axis for axis, locked in zip("XYZ", bpy.context.object.lock_location) if locked)
                    lock_warnings.append(f"Location({locked_axes})")
                    props.warn_info_33 = True
                if any(bpy.context.object.lock_rotation):
                    locked_axes = ",".join(axis for axis, locked in zip("XYZ", bpy.context.object.lock_rotation) if locked)
                    lock_warnings.append(f"Rotation({locked_axes})")
                    props.warn_info_33 = True
                if len(lock_warnings) > 0:
                    lock_message = ", ".join(lock_warnings)
                    new_warnings.append(f"[Lock {lock_message}] for Active Object")
                    props.warn_info_33 = True

        if prefs.warn_34:
            if active_obj and active_obj.type == 'ARMATURE':
                if active_obj.data.pose_position == 'REST':
                    new_warnings.append(f"Active Rig is in [Rest Position]")
                    props.warn_info_34 = True

        if prefs.warn_35:
            if bpy.context.scene.render.engine  == "CYCLES":
                if bpy.context.mode == 'OBJECT':
                    view_layer_list = []
                    for view_layer in bpy.context.scene.view_layers:
                        if view_layer.material_override:
                            view_layer_list.append(f"'{view_layer.name}'")
                    if len(view_layer_list) > 0:
                            override_material_string = f"[Material Override] for ViewLayer(s): {' | '.join(view_layer_list)}"
                            props.warn_info_35 = True
                            new_warnings.append(override_material_string)
       
        if prefs.warn_36:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.use_compositing and not bpy.context.scene.use_nodes:
                    if bpy.context.scene.node_tree is not None:
                        if len(bpy.context.scene.node_tree.nodes) > 0:
                            new_warnings.append(f"[Compositor]: 'Use Nodes' is OFF, but contains nodes!")
                            props.warn_info_36 = True

                if not bpy.context.scene.render.use_compositing and bpy.context.scene.use_nodes:
                    if bpy.context.scene.node_tree is not None:
                        if len(bpy.context.scene.node_tree.nodes) > 0:
                            new_warnings.append(f"[Compositor]: 'Use Nodes' is ON, but Postprocessing is OFF!")
                            props.warn_info_36 = True

        if prefs.warn_37:
            if bpy.context.mode == 'OBJECT':
                try:
                    if bpy.context.scene.render.image_settings.file_format == 'FFMPEG': 
                        new_warnings.append(f"[File Output] is set to FFMPEG video!")
                        props.warn_info_37 = True
                    if bpy.context.scene.render.image_settings.file_format == 'AVI_RAW':
                        new_warnings.append(f"[File Output] is set to AVI_RAW video!")
                        props.warn_info_37 = True
                    if bpy.context.scene.render.image_settings.file_format == 'AVI_JPEG': 
                        new_warnings.append(f"[File Output] is set to AVI_JPEG video!")
                        props.warn_info_37 = True
                except:
                    print("HeadUp: Skipping File Output Check")

        if prefs.warn_38:
            if bpy.context.mode == 'OBJECT':
                if prefs.warn_38_a == "OFF":
                    if not bpy.context.scene.render.film_transparent: 
                        new_warnings.append(f"[Film 'Transparent'] is OFF!")
                        props.warn_info_38 = True
                else:
                    if bpy.context.scene.render.film_transparent:
                        new_warnings.append(f"[Film 'Transparent'] is ON!")
                        props.warn_info_38 = True

        if prefs.warn_39:
            has_loud_audio_strips = any(
                strip.type == 'SOUND' and strip.volume > prefs.warn_39_a for strip in scene.sequence_editor.sequences_all
            ) if scene.sequence_editor else False
            if has_loud_audio_strips:
                new_warnings.append("[Sequencer] contains LOUD audio strip(s)!")
                props.warn_info_39 = True

        if prefs.warn_40:
            if bpy.context.mode == 'OBJECT':
                if active_obj:
                    for modifier in active_obj.modifiers:
                        if modifier.show_render:
                            if modifier.type == 'SUBSURF' and modifier.render_levels < modifier.levels:
                                new_warnings.append(f"[{modifier.name}] Render subdivisions lower than viewport")
                                props.warn_info_40 = True
                            if modifier.type == 'MULTIRES' and modifier.render_levels < modifier.levels:
                                new_warnings.append(f"[{modifier.name}] Render subdivisions lower than viewport")
                                props.warn_info_40 = True

        if prefs.warn_41:
            undefined_nodes = []
            for material in check_materials:
                if material.users == 0 or not material.use_nodes or material.library:
                    continue
                for node in material.node_tree.nodes:
                    if "undefined" in node.bl_idname.lower():
                        undefined_nodes.append(material.name)
                        problematic_materials.add(material)
            if undefined_nodes and bpy.context.mode == 'OBJECT':
                new_warnings.append(f"[Undefined Nodes found] check HeadsUp SidePanel")
                props.warn_info_41 = True

        if prefs.warn_42:
            missing_files = False
            for image in bpy.data.images:
                if image.packed_file or image.users == 0:
                    continue
                if image.filepath: 
                    abs_path = bpy.path.abspath(image.filepath)
                    if not os.path.exists(abs_path):
                        new_warnings.append(f"[Missing Textures] found")
                        props.warn_info_42 = True
                        break                

        if prefs.warn_43:
            broken_libraries = []
            for library in bpy.data.libraries:
                library_path = bpy.path.abspath(library.filepath)
                if not os.path.exists(library_path):
                    broken_libraries.append(library.filepath)
            if broken_libraries:
                new_warnings.append(f"[Missing Libraries] found")
                props.warn_info_43 = True

        if prefs.warn_44:
            if not saved_just_now:
                if bpy.app.version_file[:2] != bpy.data.version[:2]:
                    if not bpy.data.filepath == '':
                        new_warnings.append(f"[Blender Version] File was last saved with Blender {bpy.data.version[0]}.{bpy.data.version[1]}!")
                        props.warn_info_44 = True

        if prefs.warn_45:
            if compositor_check_bool:
                compositor_warnings = check_renderlayer_compositing_conditions()
                if compositor_warnings:
                    new_warnings.append(f"[Compositor]: {', '.join(set(compositor_warnings))}")
                    props.warn_info_45 = True
                    compositor_check_bool = True
                else:
                    compositor_check_bool = False

        if prefs.custom_warn:
            for text_block in bpy.data.texts:
                if text_block.lines:
                    first_line = text_block.lines[0].body.strip()
                    if first_line.lower().startswith("headsup:"):
                        message = first_line[8:].strip()  # Skip the first 8 characters ("Headsup:")
                        new_warnings.append(f"[CUSTOM] {message}")
                        props.warn_info_custom = True
        
        if new_warnings != warnings:
            warnings = new_warnings
        warn_state = bool(warnings)
        if old_warn_state != warn_state:
            warning(warn_state)
            old_warn_state = warn_state 
        if not load_up_done:
            warnings = new_warnings
            warn_state = bool(warnings)
            warning(warn_state)
            old_warn_state = warn_state
            load_up_done = True
        if not startup_done:
            warnings = new_warnings
            warn_state = bool(warnings)
            warning(warn_state)
            old_warn_state = warn_state

    except Exception as e:
        print(f"HeadsUp Error: {e}")

def register_draw_handler():
    global handler, handler_comp, handler_gradient
    if handler_gradient is None:
        handler_gradient = bpy.types.SpaceView3D.draw_handler_add(draw_circular_gradient, (), 'WINDOW', 'POST_PIXEL')
    if handler is None:
        handler = bpy.types.SpaceView3D.draw_handler_add(draw_warning_text, (), 'WINDOW', 'POST_PIXEL')
    if handler_comp is None:
        handler_comp = bpy.types.SpaceNodeEditor.draw_handler_add(draw_warning_text_comp, (), 'WINDOW', 'POST_PIXEL')

def unregister_draw_handler():
    global handler, handler_comp, handler_gradient
    if handler_gradient is not None:
        bpy.types.SpaceView3D.draw_handler_remove(handler_gradient, 'WINDOW')
        handler_gradient = None 
    if handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
        handler = None 
    if handler_comp is not None:
        bpy.types.SpaceNodeEditor.draw_handler_remove(handler_comp, 'WINDOW')
        handler_comp = None

def register():
    global load_up_done, startup_done
    load_up_done = False
    startup_done = False
    bpy.utils.register_class(HEADSUP_WarnInfoProperties)
    bpy.types.Scene.HEADSUP_WarnInfoProperties = bpy.props.PointerProperty(type=HEADSUP_WarnInfoProperties) 
    bpy.utils.register_class(HEADSUP_Preferences)
    bpy.utils.register_class(HEADSUP_OT_Store_Color)
    bpy.utils.register_class(HEADSUP_OT_Select_Highlight)
    bpy.utils.register_class(HEADSUP_OT_Select_Highlight_Collection)
    bpy.utils.register_class(HEADSUP_OT_OpenPreferences)
    bpy.utils.register_class(VIEW3D_PT_HeadsUpPanel_HeadsUp_Warnings)
    bpy.utils.register_class(VIEW3D_PT_HeadsUpPanel_Collection_Mismatch)
    bpy.utils.register_class(VIEW3D_PT_HeadsUpPanel_Object_Mismatch)
    bpy.utils.register_class(VIEW3D_PT_HeadsUpPanel_Modifier_Mismatch)
    bpy.utils.register_class(VIEW3D_PT_HeadsUpPanel_Undefined_Nodes)
    register_draw_handler()
    subscribe_to_global_visibility_and_exclusion()
    bpy.app.handlers.depsgraph_update_post.append(headsup_check_warnings)
    bpy.app.handlers.load_post.append(headsup_check_warnings)
    bpy.app.handlers.load_factory_startup_post.append(headsup_check_warnings)
    bpy.app.handlers.load_post.append(on_file_load)
    bpy.app.handlers.save_post.append(on_file_save)
    bpy.app.timers._startup_time = time.time()
    bpy.app.timers.register(check_startup_time)

def unregister():
    warning(False)
    del bpy.types.Scene.HEADSUP_WarnInfoProperties
    bpy.utils.unregister_class(HEADSUP_WarnInfoProperties)
    bpy.utils.unregister_class(HEADSUP_Preferences)
    bpy.utils.unregister_class(HEADSUP_OT_Store_Color)
    bpy.utils.unregister_class(HEADSUP_OT_Select_Highlight)
    bpy.utils.unregister_class(HEADSUP_OT_Select_Highlight_Collection)
    bpy.utils.unregister_class(HEADSUP_OT_OpenPreferences)
    bpy.utils.unregister_class(VIEW3D_PT_HeadsUpPanel_HeadsUp_Warnings)
    bpy.utils.unregister_class(VIEW3D_PT_HeadsUpPanel_Collection_Mismatch)
    bpy.utils.unregister_class(VIEW3D_PT_HeadsUpPanel_Object_Mismatch)  
    bpy.utils.unregister_class(VIEW3D_PT_HeadsUpPanel_Modifier_Mismatch)  
    bpy.utils.unregister_class(VIEW3D_PT_HeadsUpPanel_Undefined_Nodes)
    unregister_draw_handler()
    bpy.msgbus.clear_by_owner(subscribe_to_global_visibility_and_exclusion)
    bpy.app.handlers.depsgraph_update_post.remove(headsup_check_warnings)
    bpy.app.handlers.load_post.remove(headsup_check_warnings)
    bpy.app.handlers.load_factory_startup_post.remove(headsup_check_warnings)
    bpy.app.handlers.load_post.remove(on_file_load)
    bpy.app.handlers.save_post.remove(on_file_save)

if __name__ == "__main__":
    register()