import bpy
import blf
import re
import math
import gpu
from gpu_extras.batch import batch_for_shader
from .properties import *
from .preferences import *

def open_headsup_prefs():
    bpy.ops.screen.userpref_show(section='ADDONS')
    bpy.context.preferences.active_section  = "ADDONS"
    bpy.data.window_managers["WinMan"].addon_search = "HeadsUp"
    bpy.ops.preferences.addon_expand(module=__package__)
    bpy.ops.preferences.addon_show(module=__package__)
    
def store_original_theme_color():
    prefs = bpy.context.preferences.addons[__package__].preferences
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
    prefs = bpy.context.preferences.addons[__package__].preferences

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
    prefs = bpy.context.preferences.addons[__package__].preferences
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

