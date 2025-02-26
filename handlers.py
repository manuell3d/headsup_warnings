import bpy
import blf
import os
import re
import time
from bpy.app.handlers import persistent
from math import cos, sin, pi

from .utils import *
from .preferences import *
from .properties import *
from .properties import HEADSUP_Props

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
#    31 Animation: Preview Range is used
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
#    45 Compositing: Renderlayer Node 
#    46 Active Object: In Front

def check_startup_time():
    # Check if 1 second has passed since Blender started
    if time.time() - bpy.app.timers._startup_time > 2:
        draw_warning_text()
        # Set the variable to indicate that the check is done
        HEADSUP_Props.startup_done = True
        bpy.context.window_manager.update_tag()
        print("HeadsUp: Startup Done")
        
        # Remove the timer by returning None
        return None

    # Continue the timer with a short delay if the condition is not yet met
    return 1  # Check again in 0.1 seconds 

def draw_warning_text():
    """Draw warning text in the 3D viewport if warn_state is True, with white text and brackets within [ ] and orange outside."""
    prefs = bpy.context.preferences.addons[__package__].preferences
    x_position = 10  * bpy.context.preferences.view.ui_scale 
    y_position = 10  * bpy.context.preferences.view.ui_scale 
    header_bottom = False

    if HEADSUP_Props.warn_state:
        # Starting positions for text warnings, starting from lower left corner 
        for area in bpy.context.screen.areas:
            if area.type != 'VIEW_3D':
                continue  # Skip non-3D areas

            # Ensure the text is drawn only in the active 3D viewport
            if area != bpy.context.area:
                continue  # Skip if this is not the active area
            
            # Set default positions for each VIEW_3D area
            x_position = 10  * bpy.context.preferences.view.ui_scale 
            y_position = 10   * bpy.context.preferences.view.ui_scale # Reset y_position to 10 for each VIEW_3D area

            # Check for TOOLS region and set x_position if found
            tools_region = next((region for region in area.regions if region.type == 'TOOLS'), None)
            if tools_region:
                toolshelf = tools_region.width
                x_position = 9 * bpy.context.preferences.view.ui_scale  + toolshelf 
            
            header_region = next((region for region in area.regions if region.type == 'HEADER'), None) 
            if header_region:
                if header_region.alignment == 'BOTTOM':
                    header_bottom = True
                    if bpy.app.version >= (4, 0, 0):
                        y_position = y_position + 27 * bpy.context.preferences.view.ui_scale
            shelf_region = next((region for region in area.regions if region.type == 'ASSET_SHELF'), None)
            if shelf_region:
                if shelf_region.height > 1:
                    y_position = y_position + shelf_region.height + 27 * bpy.context.preferences.view.ui_scale

            if bpy.context.space_data is not None and bpy.context.space_data.show_region_header == False:
                if bpy.app.version >= (4, 0, 0):
                    if header_bottom:
                        y_position = y_position - 27 * bpy.context.preferences.view.ui_scale
            # Detection method that finally seems to work to find out if the HUD element (redo panel) is open or not
            hud_region = next((region for region in area.regions if region.type == 'HUD'), None) 
            if hud_region:
                if tools_region:
                    if hud_region.x - area.x - toolshelf > 0:
                        y_position = y_position + 25 * bpy.context.preferences.view.ui_scale
            
            HEADSUP_Props.warning_message = " , ".join(HEADSUP_Props.warnings) if HEADSUP_Props.warnings else ""
            warning_message_full = f"HeadsUp: {HEADSUP_Props.warning_message}"
            
            # For viewport specific options, remove the warning text if it does not apply.
            if bpy.context.space_data is not None and bpy.context.space_data.type == 'VIEW_3D':
                area_identifier = hash(bpy.context.space_data)
                clean_warnings = clean_viewport_warnings(HEADSUP_Props.warnings, area_identifier)
                HEADSUP_Props.warning_message = " , ".join(clean_warnings[0]) if clean_warnings else ""
                warning_message_full = f"HeadsUp: {HEADSUP_Props.warning_message}"
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
            HEADSUP_Props.actual_text_size = calculate_text_size(prefs)
            if bpy.app.version >= (4, 0, 0):
                blf.size(0, HEADSUP_Props.actual_text_size)
            else: 
                blf.size(0, HEADSUP_Props.actual_text_size, bpy.context.preferences.system.dpi)

            # Enable shadow
            blf.enable(0, blf.SHADOW)
            if bpy.app.version >= (4,0,0):
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
                    draw_highlight_border(8, (1, 0, 0, 0.5))
        
            # "Fullscreen" Version warning in the center of the 3D View
            if prefs.warn_44_a and not HEADSUP_Props.saved_just_now:
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
    prefs = bpy.context.preferences.addons[__package__].preferences
    x_position = 10
    y_position = 10

    if HEADSUP_Props.warn_state and prefs.compositor_warnings:
        # Starting positions for text warnings, starting from lower left corner 
        for area in bpy.context.screen.areas:
            if area.type == 'NODE_EDITOR':
                x_position = 10
                y_position = 10  

        HEADSUP_Props.warning_message = " , ".join(HEADSUP_Props.warnings) if HEADSUP_Props.warnings else ""
        warning_message_full = f"HeadsUp: {HEADSUP_Props.warning_message}"
        
        # For viewport specific options, remove the warning text if it does not apply.
        if bpy.context.space_data is not None and bpy.context.space_data.type == 'NODE_EDITOR':
            if bpy.context.space_data.tree_type == 'CompositorNodeTree':
                area_identifier = hash(bpy.context.space_data)
                clean_warnings = clean_viewport_warnings(HEADSUP_Props.warnings, area_identifier)
                HEADSUP_Props.warning_message = " , ".join(clean_warnings[0]) if clean_warnings else ""
                warning_message_full = f"HeadsUp: {HEADSUP_Props.warning_message}"
                
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
        HEADSUP_Props.actual_text_size = calculate_text_size(prefs)
        if bpy.app.version >= (4, 0, 0):
            blf.size(0, HEADSUP_Props.actual_text_size)
        else: 
            blf.size(0, HEADSUP_Props.actual_text_size, bpy.context.preferences.system.dpi)


        # Enable shadow
        blf.enable(0, blf.SHADOW)
        if bpy.app.version >= (4,0,0):
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
        if prefs.warn_44_a and not HEADSUP_Props.saved_just_now:
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

@persistent
def on_file_load(dummy):
    # Reset the flag on file load
    HEADSUP_Props.load_up_done = False
    HEADSUP_Props.collection_check_bool = True
    HEADSUP_Props.saved_just_now = False

@persistent
def on_file_save(dummy):
    HEADSUP_Props.saved_just_now = True
    HEADSUP_Props.load_up_done = False

@persistent
def warning(warn):
    """Change editor outline color based on warning state."""
    HEADSUP_Props.warn_state = warn
    theme = bpy.context.preferences.themes[0]
    prefs = bpy.context.preferences.addons[__package__].preferences
    
    if prefs.first_setup_bool == False:
        store_original_theme_color()
        prefs.highlight_color = theme.view_3d.space.text_hi
        
    else:    
        if warn and not prefs.UI_color_change_bool:
            if bpy.app.version >= (4, 3, 0):
                theme.user_interface.editor_border = prefs.warn_color
            else:
                theme.user_interface.editor_outline = prefs.warn_color
        else: 
            if bpy.app.version >= (4, 3, 0):
                theme.user_interface.editor_border = prefs.original_theme_color
            else:
                theme.user_interface.editor_outline = prefs.original_theme_color

@persistent
def headsup_check_warnings(scene, depsgraph):
    """Check auto keyframe settings and warn if necessary."""
        
    scene = bpy.context.scene
    if bpy.app.version >= (4, 2):
        if len(bpy.context.window.modal_operators) > 0:
            if HEADSUP_Props.load_up_done:
                HEADSUP_Props.load_up_done = False
            return

    if bpy.context.screen and bpy.context.screen.is_animation_playing:
        if HEADSUP_Props.load_up_done:
            HEADSUP_Props.load_up_done = False
        return

    new_warnings = []
    active_obj = bpy.context.active_object
    prefs = bpy.context.preferences.addons[__package__].preferences
    props = bpy.context.scene.HEADSUP_WarnInfoProperties
    
    # Reset all warn_info properties
    setattr(props, "warn_info_custom", False)
    for i in range(1, 47):  # From 1 to 46
        setattr(props, f"warn_info_{i}", False)

    for view_layer in bpy.context.scene.view_layers:
        current_state = view_layer.use
        previous_state = HEADSUP_Props.view_layer_visibilities.get(view_layer.name, None)
        
        # Compare with the stored state
        if previous_state is None:
            HEADSUP_Props.view_layer_visibilities[view_layer.name] = current_state
        elif current_state != previous_state:
            HEADSUP_Props.load_up_done = False
            HEADSUP_Props.view_layer_visibilities[view_layer.name] = current_state

    # Do a full check after loading a blender file, otherwise only check relevant updates and known problematic items
    if HEADSUP_Props.current_scene is None or bpy.context.scene != HEADSUP_Props.current_scene:
        HEADSUP_Props.load_up_done = False
        HEADSUP_Props.current_scene = bpy.context.scene

    if HEADSUP_Props.load_up_done == False:
        check_objects = set()
        check_materials = set()        

        for obj in bpy.context.scene.objects:
            check_objects.add(obj)
        for mat in bpy.data.materials:
            if not mat.library:
                check_materials.add(mat)
        HEADSUP_Props.collection_check_bool = True
        HEADSUP_Props.compositor_check_bool = True
        update_visible_collections()
    else: 
        check_objects = set()
        check_materials = set()        

        for obj in HEADSUP_Props.problematic_objects:
            check_objects.add(obj)
        
        for mat in HEADSUP_Props.problematic_materials:
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
                    HEADSUP_Props.collection_check_bool = True
                    update_visible_collections()
                    for obj in bpy.context.scene.objects:
                        check_objects.add(obj)
                if isinstance(update.id, bpy.types.CompositorNodeTree):
                    HEADSUP_Props.compositor_check_bool = True
        if HEADSUP_Props.viewlayer_count != len(bpy.context.scene.view_layers):
            HEADSUP_Props.viewlayer_count = len(bpy.context.scene.view_layers)
            check_objects = set()
            check_materials = set()        

            for obj in bpy.context.scene.objects:
                check_objects.add(obj)
            for mat in bpy.data.materials:
                if not mat.library:
                    check_materials.add(mat)
            HEADSUP_Props.collection_check_bool = True
            HEADSUP_Props.compositor_check_bool = True
            update_visible_collections()
            
        # Problematic items have been added to the check-lists, if they are still problematic, they'll be added again
        HEADSUP_Props.problematic_materials = set()
        HEADSUP_Props.problematic_objects = set()

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
                                        setattr(props, "warn_info_1", True)

        if prefs.warn_2:
            if len(check_objects) > 0:
                HEADSUP_Props.object_mismatches = check_object_mismatches(check_objects)
            if HEADSUP_Props.collection_check_bool:
                HEADSUP_Props.collection_mismatches = check_collection_mismatches()                

            if len(HEADSUP_Props.collection_mismatches) > 0 and len(HEADSUP_Props.object_mismatches) == 0:
               new_warnings.append(f"[Collection Render/Viewport Mismatch] check HeadsUp SidePanel")
               setattr(props, "warn_info_2", True)
            if len(HEADSUP_Props.object_mismatches) > 0 and len(HEADSUP_Props.collection_mismatches) == 0:
               new_warnings.append(f"[Object Render/Viewport Mismatch] check HeadsUp SidePanel")
               setattr(props, "warn_info_2", True)
            if len(HEADSUP_Props.object_mismatches) > 0 and len(HEADSUP_Props.collection_mismatches) > 0:
               new_warnings.append(f"[Object & Collection Render/Viewport Mismatches] check HeadsUp SidePanel")
               setattr(props, "warn_info_2", True)

            if len(HEADSUP_Props.collection_mismatches) == 0:
                HEADSUP_Props.collection_check_bool = False

        if prefs.warn_3:
            if active_obj and active_obj.type == 'MESH':
                    if bpy.context.mode == 'SCULPT':
                        if active_obj.data.shape_keys:
                            active_shape_key_index = active_obj.active_shape_key_index
                            if active_shape_key_index != 0:
                                active_shape_key = active_obj.data.shape_keys.key_blocks[active_shape_key_index]
                                if round(active_shape_key.value, 3) != 1.0:
                                    new_warnings.append(f"Active [Shape Key] is not 1.0! Set to: {round(active_shape_key.value, 3)}!")
                                    setattr(props, "warn_info_3", True)
        
        if prefs.warn_4:
            if bpy.context.mode == 'OBJECT' or bpy.context.mode == 'POSE':
                if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
                    new_warnings.append("[Auto Keying] is ON!")
                    setattr(props, "warn_info_4", True)
        
        if prefs.warn_5:        
            if bpy.context.mode == 'EDIT_MESH':
                if bpy.context.scene.tool_settings.use_proportional_edit:
                    new_warnings.append("[Proportional Editing (Edit Mode/UV)] is ON!")
                    setattr(props, "warn_info_5", True)
            if bpy.context.mode == 'OBJECT':    
                if bpy.context.scene.tool_settings.use_proportional_edit_objects:
                    new_warnings.append("[Proportional Editing (Object Mode)] is ON!")
                    setattr(props, "warn_info_5", True)
            
            fcurve_checked = False
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'GRAPH_EDITOR':
                        if bpy.context.scene.tool_settings.use_proportional_fcurve:
                            new_warnings.append("[Proportional Editing (Graph Editor)] is ON!")
                            setattr(props, "warn_info_5", True)
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
                            setattr(props, "warn_info_5", True)
                        dopesheet_checked = True
                        break 
                if dopesheet_checked:
                    break  
        
        if prefs.warn_6:        
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.tool_settings.use_transform_data_origin:
                    new_warnings.append("[Affect Only >Origins<] is ON!")
                    setattr(props, "warn_info_6", True)
                            
                if bpy.context.scene.tool_settings.use_transform_pivot_point_align:
                    new_warnings.append("[Affect Only >Locations<] is ON!")
                    setattr(props, "warn_info_6", True)
                    
                if bpy.context.scene.tool_settings.use_transform_skip_children:
                    new_warnings.append("[Affect Only >Parents<] is ON!")
                    setattr(props, "warn_info_6", True)
   
        if prefs.warn_7:    
            if bpy.context.mode == 'OBJECT' or bpy.context.mode == 'EDIT_MESH':
                if bpy.context.scene.tool_settings.use_snap:
                    new_warnings.append("[Snapping] is ON!")
                    setattr(props, "warn_info_7", True)
            if bpy.context.mode == 'EDIT_MESH':
                if bpy.context.scene.tool_settings.use_snap_uv:
                    new_warnings.append("[Snapping (UV)] is ON!")
                    setattr(props, "warn_info_7", True)

        if prefs.warn_8:    
            if active_obj:
                if not round(bpy.context.object.scale[0],3) == round(bpy.context.object.scale[1],3) == round(bpy.context.object.scale[2],3):
                    if any(axis <= 0 for axis in bpy.context.object.scale):
                        if prefs.warn_8_a:
                            new_warnings.append("[Non-Uniform Scale (Zero or Negative Axis!)] for active Object!")
                            setattr(props, "warn_info_8", True)
                    else:
                        if prefs.warn_8_b and active_obj.type not in ("LIGHT","META","CAMERA","LIGHT_PROBE"):
                            new_warnings.append("[Non-Uniform Scale] for active Object!") 
                            setattr(props, "warn_info_8", True)
                else: 
                    if bpy.context.object.scale[0] != 1.0: 
                        if bpy.context.object.scale[0] < 0:
                            if prefs.warn_8_a:
                                new_warnings.append("[Negative Scale] for active Object!")
                                setattr(props, "warn_info_8", True)
                        else:
                            if prefs.warn_8_c and active_obj.type not in ("LIGHT","META","CAMERA","LIGHT_PROBE"): 
                                new_warnings.append("[Scale is not 1] for active Object!")
                                setattr(props, "warn_info_8", True)

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
                        setattr(props, "warn_info_9", True)
  
        if prefs.warn_10:        
            if bpy.context.mode == 'OBJECT':   
                if bpy.context.scene.render.use_simplify:
                    sub_v = bpy.context.scene.render.simplify_subdivision
                    sub_r = bpy.context.scene.render.simplify_subdivision_render
                    if not prefs.warn_10_a:
                        if sub_v <= prefs.simplify_viewport and not sub_r <= prefs.simplify_render:
                            new_warnings.append(f"[Simplify] is ON! Viewport: {sub_v}, Render: {sub_r}")
                            setattr(props, "warn_info_10", True)
                    if sub_r <= prefs.simplify_render:
                        new_warnings.append(f"[Simplify] is ON! Render Subdivision is low: {sub_r}!")
                        setattr(props, "warn_info_10", True)
   
        if prefs.warn_11:   
            if bpy.context.mode == 'OBJECT':         
                if bpy.context.scene.render.use_sequencer:
                    has_non_audio_strips = any(
                        strip.type != 'SOUND' for strip in scene.sequence_editor.sequences_all
                    ) if scene.sequence_editor else False
                    if has_non_audio_strips:
                        new_warnings.append("[Sequencer] is ON and contains Data!")
                        setattr(props, "warn_info_11", True)
       
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
                        setattr(props, "warn_info_12", True)
        
        if prefs.warn_13:                
            if bpy.context.mode == 'EDIT_MESH':
                if bpy.context.scene.tool_settings.use_mesh_automerge:
                    new_warnings.append("[Automerge Vertices] is ON!")
                    setattr(props, "warn_info_13", True)
        
        if prefs.warn_14:        
            if bpy.context.mode == 'EDIT_MESH':
                if bpy.context.scene.tool_settings.use_uv_select_sync:
                    new_warnings.append("[UV Sync Selection] is ON!")
                    setattr(props, "warn_info_14", True)
        
        if prefs.warn_15:
            if bpy.context.mode == 'EDIT_MESH':        
                if bpy.context.scene.tool_settings.use_edge_path_live_unwrap:
                    new_warnings.append("[Live Unwrap] is ON!")
                    setattr(props, "warn_info_15", True)
                    
        if prefs.warn_16:
            if bpy.context.mode == 'EDIT_MESH':    
                if bpy.context.scene.tool_settings.use_transform_correct_face_attributes:
                    new_warnings.append("[Correct Face Attributes] is ON!(UVs change with Editmode Transforms)!")
                    setattr(props, "warn_info_16", True)
                
        if prefs.warn_17:
            if multiple_sequence_nodes(check_materials):
                new_warnings.append("Several [Image Sequence] nodes with different settings refer to the same datablock, expect issues!")
                setattr(props, "warn_info_17", True)
        
        if prefs.warn_18:
            if active_obj and active_obj.type == 'MESH':
                if bpy.context.mode == 'SCULPT':
                    if any(mod.type == 'CORRECTIVE_SMOOTH' and mod.show_viewport for mod in active_obj.modifiers):
                        new_warnings.append("Sculpting with an active [Corrective Smooth] modifier!")
                        setattr(props, "warn_info_18", True)
                             
        if prefs.warn_19:
            if bpy.context.blend_data.use_autopack:
                new_warnings.append("[Autopack Ressources] is ON!")
                setattr(props, "warn_info_19", True)
                
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
                                        setattr(props, "warn_info_20", True)

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
                                                setattr(props, "warn_info_21", True)
                                
        if prefs.warn_22:
            if bpy.context.mode == 'OBJECT':
                if active_obj and active_obj.type == 'MESH':
                    if active_obj.is_shadow_catcher and not active_obj.is_holdout:
                        new_warnings.append("Active Object is [Shadow Catcher]") 
                        setattr(props, "warn_info_22", True)
                    if active_obj.is_holdout and not active_obj.is_shadow_catcher:
                        new_warnings.append("Active Object is [Holdout]")    
                        setattr(props, "warn_info_22", True)
                    if active_obj.is_holdout and active_obj.is_shadow_catcher:
                        new_warnings.append("Active Object is [Holdout & Shadow Catcher]") 
                        setattr(props, "warn_info_22", True) 
                
        if prefs.warn_23:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.resolution_percentage != 100:
                    resolution_percentage = bpy.context.scene.render.resolution_percentage
                    new_warnings.append(f"[Render Resolution Percentage] is: {resolution_percentage}%!")
                    setattr(props, "warn_info_23", True)
                
        if prefs.warn_24:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.engine  == "CYCLES": 
                    if bpy.context.scene.cycles.filter_width != 1.5:
                        pixel_filter = round(bpy.context.scene.cycles.filter_width,2)
                        new_warnings.append(f"[Pixel Filter(Cycles)]: {pixel_filter} px!(Default 1.5px)")
                        setattr(props, "warn_info_24", True)
                if bpy.context.scene.render.engine  == "BLENDER_EEVEE" or bpy.context.scene.render.engine == "BLENDER_EEVEE_NEXT":
                    if bpy.context.scene.render.filter_size != 1.5:
                        pixel_filter = round(bpy.context.scene.render.filter_size,2)
                        new_warnings.append(f"[Pixel Filter(EEVEE):] {pixel_filter} px!(Default 1.5px)")
                        setattr(props, "warn_info_24", True)
                                       
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
                            setattr(props, "warn_info_25", True)
                else:
                    HEADSUP_Props.modifier_mismatches = check_modifier_mismatches(check_objects)
                    if len(HEADSUP_Props.modifier_mismatches) > 0:
                        new_warnings.append(f"[Modifier Render/Viewport Mismatch] check HeadsUp SidePanel")
                        setattr(props, "warn_info_25", True)

        if prefs.warn_26:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.engine  == "CYCLES":
                    view_layer_list = []
                    for view_layer in bpy.context.scene.view_layers:
                        if view_layer.samples != 0: 
                            view_layer_list.append(f"'{view_layer.name}': {view_layer.samples}")
                    
                    if len(view_layer_list) > 0:
                        override_sample_string = f"[Sample Override] for ViewLayer(s): {' | '.join(view_layer_list)}"
                        setattr(props, "warn_info_26", True)
                        new_warnings.append(override_sample_string)


                     
        if prefs.warn_27:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.engine  == "CYCLES":
                    if bpy.context.scene.cycles.samples <= prefs.sample_limit_lower :
                        new_warnings.append(f"[Low Samples(Cycles)]: {bpy.context.scene.cycles.samples} samples!")
                        setattr(props, "warn_info_27", True)
                if bpy.context.scene.render.engine == "BLENDER_EEVEE":
                    if bpy.context.scene.eevee.taa_render_samples <= prefs.sample_limit_lower :
                        new_warnings.append(f"[Low Samples(EEVEE)]: {bpy.context.scene.eevee.taa_render_samples} samples!")
                        setattr(props, "warn_info_27", True)
                
        if prefs.warn_27_a:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.engine  == "CYCLES":
                    if bpy.context.scene.cycles.samples >= prefs.sample_limit_upper :
                        new_warnings.append(f"[High Samples(Cycles)]: {bpy.context.scene.cycles.samples} samples!")
                        setattr(props, "warn_info_27", True)
                if bpy.context.scene.render.engine == "BLENDER_EEVEE":
                    if bpy.context.scene.eevee.taa_render_samples >= prefs.sample_limit_upper :
                        new_warnings.append(f"[High Samples(EEVEE)]: {bpy.context.scene.eevee.taa_render_samples} samples!")
                        setattr(props, "warn_info_27", True)
                                                       
        if prefs.warn_28:
            if bpy.context.mode == 'OBJECT':
                if active_obj and active_obj.modifiers:
                    array_modifier = None
                    for i, mod in enumerate(active_obj.modifiers):
                        if mod.type == 'ARRAY' and mod.use_relative_offset:
                            if i != 0:
                                new_warnings.append(f"Modifiers before [Array] with Relative Offset!")
                                setattr(props, "warn_info_28", True)

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
                                        setattr(props, "warn_info_29", True)

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
                                        setattr(props, "warn_info_30", True)

        if prefs.warn_31:
            if bpy.context.scene.use_preview_range:
                if bpy.context.scene.frame_preview_start != bpy.context.scene.frame_start or bpy.context.scene.frame_preview_end != bpy.context.scene.frame_end:
                    new_warnings.append(f"[Preview Range]: {bpy.context.scene.frame_preview_start}-{bpy.context.scene.frame_preview_end}!")
                    setattr(props, "warn_info_31", True)

        if prefs.warn_32:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.engine  == "CYCLES":
                    if prefs.warn_32_a == 'GPU':
                        if bpy.context.scene.cycles.device == 'CPU':
                            new_warnings.append(f"[Cycles not using GPU]")
                            setattr(props, "warn_info_32", True)
                    else:
                        if bpy.context.scene.cycles.device == 'GPU':
                            new_warnings.append(f"[Cycles not using CPU]")
                            setattr(props, "warn_info_32", True)

        if prefs.warn_33:
            if active_obj and bpy.context.mode == 'OBJECT':
                lock_warnings = []
                if any(bpy.context.object.lock_scale):
                    locked_axes = ",".join(axis for axis, locked in zip("XYZ", bpy.context.object.lock_scale) if locked)
                    lock_warnings.append(f"Scale({locked_axes})")
                    setattr(props, "warn_info_33", True)
                if any(bpy.context.object.lock_location):
                    locked_axes = ",".join(axis for axis, locked in zip("XYZ", bpy.context.object.lock_location) if locked)
                    lock_warnings.append(f"Location({locked_axes})")
                    setattr(props, "warn_info_33", True)
                if any(bpy.context.object.lock_rotation):
                    locked_axes = ",".join(axis for axis, locked in zip("XYZ", bpy.context.object.lock_rotation) if locked)
                    lock_warnings.append(f"Rotation({locked_axes})")
                    setattr(props, "warn_info_33", True)
                if len(lock_warnings) > 0:
                    lock_message = ", ".join(lock_warnings)
                    new_warnings.append(f"[Lock {lock_message}] for Active Object")
                    setattr(props, "warn_info_33", True)

        if prefs.warn_34:
            if active_obj and active_obj.type == 'ARMATURE':
                if active_obj.data.pose_position == 'REST':
                    new_warnings.append(f"Active Rig is in [Rest Position]")
                    setattr(props, "warn_info_34", True)

        if prefs.warn_35:
            if bpy.context.scene.render.engine  == "CYCLES":
                if bpy.context.mode == 'OBJECT':
                    view_layer_list = []
                    for view_layer in bpy.context.scene.view_layers:
                        if view_layer.material_override:
                            view_layer_list.append(f"'{view_layer.name}'")
                    if len(view_layer_list) > 0:
                            override_material_string = f"[Material Override] for ViewLayer(s): {' | '.join(view_layer_list)}"
                            setattr(props, "warn_info_35", True)
                            new_warnings.append(override_material_string)
                    view_layer_list = []
                    for view_layer in bpy.context.scene.view_layers:
                        if bpy.app.version >= (4, 3, 0):
                            if view_layer.world_override:
                                view_layer_list.append(f"'{view_layer.name}'")
                    if len(view_layer_list) > 0:
                            override_world_string = f"[World Override] for ViewLayer(s): {' | '.join(view_layer_list)}"
                            setattr(props, "warn_info_35", True)
                            new_warnings.append(override_world_string)
       
        if prefs.warn_36:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.scene.render.use_compositing and not bpy.context.scene.use_nodes:
                    if bpy.context.scene.node_tree is not None:
                        if len(bpy.context.scene.node_tree.nodes) > 0:
                            new_warnings.append(f"[Compositor]: 'Use Nodes' is OFF, but contains nodes!")
                            setattr(props, "warn_info_36", True)

                if not bpy.context.scene.render.use_compositing and bpy.context.scene.use_nodes:
                    if bpy.context.scene.node_tree is not None:
                        if len(bpy.context.scene.node_tree.nodes) > 0:
                            new_warnings.append(f"[Compositor]: 'Use Nodes' is ON, but Postprocessing is OFF!")
                            setattr(props, "warn_info_36", True)

        if prefs.warn_37:
            if bpy.context.mode == 'OBJECT':
                try:
                    if bpy.context.scene.render.image_settings.file_format == 'FFMPEG': 
                        new_warnings.append(f"[File Output] is set to FFMPEG video!")
                        setattr(props, "warn_info_37", True)
                    if bpy.context.scene.render.image_settings.file_format == 'AVI_RAW':
                        new_warnings.append(f"[File Output] is set to AVI_RAW video!")
                        setattr(props, "warn_info_37", True)
                    if bpy.context.scene.render.image_settings.file_format == 'AVI_JPEG': 
                        new_warnings.append(f"[File Output] is set to AVI_JPEG video!")
                        setattr(props, "warn_info_37", True)
                except:
                    print("HeadUp: Skipping File Output Check")

        if prefs.warn_38:
            if bpy.context.mode == 'OBJECT':
                if prefs.warn_38_a == "OFF":
                    if not bpy.context.scene.render.film_transparent: 
                        new_warnings.append(f"[Film 'Transparent'] is OFF!")
                        setattr(props, "warn_info_38", True)
                else:
                    if bpy.context.scene.render.film_transparent:
                        new_warnings.append(f"[Film 'Transparent'] is ON!")
                        setattr(props, "warn_info_38", True)

        if prefs.warn_39:
            has_loud_audio_strips = any(
                strip.type == 'SOUND' and strip.volume > prefs.warn_39_a for strip in scene.sequence_editor.sequences_all
            ) if scene.sequence_editor else False
            if has_loud_audio_strips:
                new_warnings.append("[Sequencer] contains LOUD audio strip(s)!")
                setattr(props, "warn_info_39", True)

        if prefs.warn_40:
            if bpy.context.mode == 'OBJECT':
                if active_obj:
                    for modifier in active_obj.modifiers:
                        if modifier.show_render:
                            if modifier.type == 'SUBSURF' and modifier.render_levels < modifier.levels:
                                new_warnings.append(f"[{modifier.name}] Render subdivisions lower than viewport")
                                setattr(props, "warn_info_40", True)
                            if modifier.type == 'MULTIRES' and modifier.render_levels < modifier.levels:
                                new_warnings.append(f"[{modifier.name}] Render subdivisions lower than viewport")
                                setattr(props, "warn_info_40", True)

        if prefs.warn_41:
            HEADSUP_Props.undefined_nodes = []
            for material in check_materials:
                if material.users == 0 or not material.use_nodes or material.library:
                    continue
                for node in material.node_tree.nodes:
                    if "undefined" in node.bl_idname.lower():
                        HEADSUP_Props.undefined_nodes.append(material.name)
                        HEADSUP_Props.problematic_materials.add(material)
            if HEADSUP_Props.undefined_nodes and bpy.context.mode == 'OBJECT':
                new_warnings.append(f"[Undefined Nodes found] check HeadsUp SidePanel")
                setattr(props, "warn_info_41", True)

        if prefs.warn_42:
            missing_files = False
            for image in bpy.data.images:
                if image.packed_file or image.users == 0:
                    continue
                if image.filepath: 
                    abs_path = bpy.path.abspath(image.filepath)
                    abs_path = abs_path.replace("<UDIM>", "1001")
                    if not os.path.exists(abs_path):
                        new_warnings.append(f"[Missing Textures] found")
                        setattr(props, "warn_info_42", True)
                        break                

        if prefs.warn_43:
            broken_libraries = []
            for library in bpy.data.libraries:
                library_path = bpy.path.abspath(library.filepath)
                if not os.path.exists(library_path):
                    broken_libraries.append(library.filepath)
            if broken_libraries:
                new_warnings.append(f"[Missing Libraries] found")
                setattr(props, "warn_info_43", True)

        if prefs.warn_44:
            if not HEADSUP_Props.saved_just_now:
                if bpy.app.version_file[:2] != bpy.data.version[:2]:
                    if not bpy.data.filepath == '':
                        new_warnings.append(f"[Blender Version] File was last saved with Blender {bpy.data.version[0]}.{bpy.data.version[1]}!")
                        setattr(props, "warn_info_44", True)

        if prefs.warn_45:
            if HEADSUP_Props.compositor_check_bool:
                compositor_warnings = check_renderlayer_compositing_conditions()
                if compositor_warnings:
                    new_warnings.append(f"[Compositor]: {', '.join(set(compositor_warnings))}")
                    setattr(props, "warn_info_45", True)
                    HEADSUP_Props.compositor_check_bool = True
                else:
                    HEADSUP_Props.compositor_check_bool = False
        
        if prefs.warn_46:
            if active_obj and active_obj.show_in_front:
                new_warnings.append(f"Active Object is [In Front]")
                setattr(props, "warn_info_46", True)

        if prefs.custom_warn:
            for text_block in bpy.data.texts:
                if text_block.lines:
                    first_line = text_block.lines[0].body.strip()
                    if first_line.lower().startswith("headsup:"):
                        message = first_line[8:].strip()  # Skip the first 8 characters ("Headsup:")
                        new_warnings.append(f"[CUSTOM] {message}")
                        setattr(props, "warn_info_custom", True)
        
        if new_warnings != HEADSUP_Props.warnings:
            HEADSUP_Props.warnings = new_warnings
        HEADSUP_Props.warn_state = bool(HEADSUP_Props.warnings)
        if HEADSUP_Props.old_warn_state != HEADSUP_Props.warn_state:
            warning(HEADSUP_Props.warn_state)
            HEADSUP_Props.old_warn_state = HEADSUP_Props.warn_state 
        if not HEADSUP_Props.load_up_done:
            HEADSUP_Props.warnings = new_warnings
            HEADSUP_Props.warn_state = bool(HEADSUP_Props.warnings)
            warning(HEADSUP_Props.warn_state)
            HEADSUP_Props.old_warn_state = HEADSUP_Props.warn_state
            HEADSUP_Props.load_up_done = True
        if not HEADSUP_Props.startup_done:
            HEADSUP_Props.warnings = new_warnings
            HEADSUP_Props.warn_state = bool(HEADSUP_Props.warnings)
            warning(HEADSUP_Props.warn_state)
            HEADSUP_Props.old_warn_state = HEADSUP_Props.warn_state

    except Exception as e:
        print(f"HeadsUp Error: {e}")
        
def check_object_mismatches(check_objects):
    """Find objects with mismatched hide_render and hide_viewport statuses."""
    SKIPPED_TYPES = {'CAMERA', 'EMPTY', 'LATTICE', 'ARMATURE', 'SPEAKER'}

    object_view_layer_map = {}

    for obj in check_objects:
        if not obj or obj.type in SKIPPED_TYPES:
            continue

        # Initialize the object in the map
        object_view_layer_map[obj] = []

        # Find collection names the object belongs to
        obj_collection_names = {coll.name for coll in obj.users_collection}

        # Check if these collection names appear in the view_layer_visible_collections
        for layer_name, visible_collections in HEADSUP_Props.view_layer_visible_collections.items():
            if obj_collection_names.intersection(visible_collections):
                # If the object has a mismatch, add it to the map and problematic_objects
                if obj.hide_render != obj.hide_viewport:
                    object_view_layer_map[obj].append(layer_name)
                    HEADSUP_Props.problematic_objects.add(obj)

    # Build mismatch list
    mismatch_list = [
        {"object": obj, "view_layers": view_layers}
        for obj, view_layers in object_view_layer_map.items()
        if view_layers
    ]

    return mismatch_list

def check_modifier_mismatches(check_objects):
    """Find objects with mismatched modifier visibility (show_viewport vs show_render)."""
    if bpy.app.version >= (4, 3, 0):
        CHECKED_TYPES = {'MESH', 'CURVE', 'LATTICE', 'FONT', 'GREASEPENCIL'}
    else:
        CHECKED_TYPES = {'MESH', 'CURVE', 'LATTICE', 'FONT', 'GPENCIL'}

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
            for layer_name, visible_collections in HEADSUP_Props.view_layer_visible_collections.items():
                if obj_collection_names.intersection(visible_collections):
                    mismatch_dict[obj].append(layer_name)
                    HEADSUP_Props.problematic_objects.add(obj)

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

def update_visible_collections():
    HEADSUP_Props.view_layer_visible_collections = {}

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
        HEADSUP_Props.view_layer_visible_collections[layer.name] = list(visible_collections)

def on_any_collection_or_layer_change():
    """Callback when any collection or layer property changes."""
    HEADSUP_Props.collection_check_bool = True
    HEADSUP_Props.compositor_check_bool = True
    update_visible_collections()
    for obj in bpy.context.scene.objects:
        HEADSUP_Props.problematic_objects.add(obj)

def compositor_callback():
    HEADSUP_Props.compositor_check_bool = True

def on_material_change():
    for mat in bpy.data.materials:
        if not mat.library:
            HEADSUP_Props.problematic_materials.add(mat)

def on_obj_visibility_change():
    """Callback when any collection or layer property changes."""
    for obj in bpy.context.scene.objects:
        HEADSUP_Props.problematic_objects.add(obj)

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

def register_draw_handler():
    if HEADSUP_Props.handler_gradient is None:
        HEADSUP_Props.handler_gradient = bpy.types.SpaceView3D.draw_handler_add(draw_circular_gradient, (), 'WINDOW', 'POST_PIXEL')
    if HEADSUP_Props.handler is None:
        HEADSUP_Props.handler = bpy.types.SpaceView3D.draw_handler_add(draw_warning_text, (), 'WINDOW', 'POST_PIXEL')
    if HEADSUP_Props.handler_comp is None:
        HEADSUP_Props.handler_comp = bpy.types.SpaceNodeEditor.draw_handler_add(draw_warning_text_comp, (), 'WINDOW', 'POST_PIXEL')

def unregister_draw_handler():
    if HEADSUP_Props.handler_gradient is not None:
        bpy.types.SpaceView3D.draw_handler_remove(HEADSUP_Props.handler_gradient, 'WINDOW')
        HEADSUP_Props.handler_gradient = None 
    if HEADSUP_Props.handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(HEADSUP_Props.handler, 'WINDOW')
        HEADSUP_Props.handler = None 
    if HEADSUP_Props.handler_comp is not None:
        bpy.types.SpaceNodeEditor.draw_handler_remove(HEADSUP_Props.handler_comp, 'WINDOW')
        HEADSUP_Props.handler_comp = None

def register():
    register_draw_handler()
    subscribe_to_global_visibility_and_exclusion()
    bpy.app.handlers.depsgraph_update_post.append(headsup_check_warnings)
    bpy.app.handlers.load_factory_startup_post.append(on_file_load)
    bpy.app.handlers.load_post.append(on_file_load)
    bpy.app.handlers.save_post.append(on_file_save)
    bpy.app.timers._startup_time = time.time()
    bpy.app.timers.register(check_startup_time)

def unregister():
    unregister_draw_handler()
    bpy.msgbus.clear_by_owner(subscribe_to_global_visibility_and_exclusion)
    bpy.app.handlers.depsgraph_update_post.remove(headsup_check_warnings)
    bpy.app.handlers.load_factory_startup_post.remove(on_file_load)
    bpy.app.handlers.load_post.remove(on_file_load)
    bpy.app.handlers.save_post.remove(on_file_save)