import bpy
import blf

# Global variables to store the draw handlers
draw_text_handler = None
draw_hex_handler = None
last_mode = None

def search_keymap_item(identifier, keymap_name):
    keyconfigs = [bpy.context.window_manager.keyconfigs.addon, bpy.context.window_manager.keyconfigs.user]
    
    for keyconfig in keyconfigs:
        if keyconfig:
            keymap = keyconfig.keymaps.get(keymap_name)
            if keymap:
                for keymap_item in keymap.keymap_items:
                    if keymap_item.idname == identifier:
                        print(f"Keymap: {keymap.name}")
                        print(f"  Keymap Item: {keymap_item.idname}, Key: {keymap_item.type}, Action: {keymap_item.value}")
                        return keymap_item
                print(f"Identifier '{identifier}' not found in keymap '{keymap_name}'.")
            else:
                print(f"Keymap '{keymap_name}' not found in keyconfig '{keyconfig.name}'.")
    
    return None

def format_keymap_item(kmi):
    if kmi:
        keys = []
        if kmi.ctrl:
            keys.append("Ctrl")
        if kmi.alt:
            keys.append("Alt")
        if kmi.shift:
            keys.append("Shift")
        if kmi.oskey:
            keys.append("Cmd")  # MacOS specific
        keys.append(kmi.type)
        return "+".join(keys)
    return "Unassigned"

def draw_text_callback():
    global last_mode
    current_mode = bpy.context.object.mode if bpy.context.object else None
    
    if current_mode != last_mode:
        print(f"Current mode: {current_mode}")
        last_mode = current_mode
    
    if current_mode == 'TEXTURE_PAINT':
        x = bpy.context.scene.text_x
        y = bpy.context.scene.text_y
        color = bpy.context.scene.text_color

        font_id = 0  # Blender default font
        blf.position(font_id, x, y, 0)
        blf.size(font_id, 16)  # Set the font size
        blf.color(font_id, color[0], color[1], color[2], color[3])  # Set text color from the scene property

        keymap_items = [
            ("Image Paint", "paint.toggle_add_multiply", "Toggle Multiply/Add"),
            ("Image Paint", "paint.init_blend_mode", "Return Mix"),
            ("Image Paint", "paint.toggle_color_soft_light_screen", "Toggle Color/Soft Light/Screen"),
            ("Image Paint", "paint.toggle_alpha_mode", "Toggle Erase Alpha/Add Alpha"),
            ("Image Paint", "view3d.projectpaint", "Slots Menu popup"),
            ("Image Paint", "view3d.texture_popup", "Brush Tex/Mask Popup"),
            ("Image Paint", "view3d.brush_popup", "Brush Popup")
        ]

        for i, (keymap_name, operator_name, display_name) in enumerate(keymap_items):
            kmi = search_keymap_item(operator_name, keymap_name)
            hotkey = format_keymap_item(kmi)
            blf.position(font_id, x, y + i * 20, 0)
            blf.draw(font_id, f'{display_name} - {hotkey}')

        blf.position(font_id, x, y + len(keymap_items) * 20, 0)
        blf.draw(font_id, 'Draw2Paint Hotkeys')

# Function to draw the brush color hex code in the 3D View
def draw_hex_callback():
    global last_mode
    current_mode = bpy.context.object.mode if bpy.context.object else None
    
    if current_mode != last_mode:
        print(f"Current mode: {current_mode}")
        last_mode = current_mode
    
    if current_mode == 'TEXTURE_PAINT':
        x = bpy.context.scene.hex_x
        y = bpy.context.scene.hex_y
        brush_color_hex = bpy.context.scene.brush_color_hex

        font_id = 0  # Blender default font
        blf.position(font_id, x, y, 0)
        blf.size(font_id, 16)  # Set the font size
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)  # Set text color to white
        blf.draw(font_id, f'Brush Color Hex: {brush_color_hex}')

class VIEW3D_OT_toggle_draw_text(bpy.types.Operator):
    bl_idname = "view3d.toggle_draw_text"
    bl_label = "Toggle Draw Text"

    def execute(self, context):
        global draw_text_handler

        if draw_text_handler is None:
            # Add the draw handler
            print("Adding draw text handler")
            draw_text_handler = bpy.types.SpaceView3D.draw_handler_add(draw_text_callback, (), 'WINDOW', 'POST_PIXEL')
        else:
            # Remove the draw handler
            print("Removing draw text handler")
            bpy.types.SpaceView3D.draw_handler_remove(draw_text_handler, 'WINDOW')
            draw_text_handler = None

        # Redraw the area to reflect changes
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}

class VIEW3D_OT_toggle_draw_hex(bpy.types.Operator):
    bl_idname = "view3d.toggle_draw_hex"
    bl_label = "Toggle Draw Hex Code"

    def execute(self, context):
        global draw_hex_handler

        if draw_hex_handler is None:
            # Add the draw handler
            print("Adding draw hex handler")
            draw_hex_handler = bpy.types.SpaceView3D.draw_handler_add(draw_hex_callback, (), 'WINDOW', 'POST_PIXEL')
        else:
            # Remove the draw handler
            print("Removing draw hex handler")
            bpy.types.SpaceView3D.draw_handler_remove(draw_hex_handler, 'WINDOW')
            draw_hex_handler = None

        # Redraw the area to reflect changes
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}

class D2P_PT_toggle_draw_panel(bpy.types.Panel):
    bl_label = "HotKey2Screen"
    bl_idname = "D2P_PT_toggle_draw_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout        
        row = layout.row()
        
        row.operator("view3d.toggle_draw_text", text="HUD")
        row.prop(context.scene, "text_color", text="")
        
        row = layout.row()
        row.prop(context.scene, "text_x", text="Text X")
        row.prop(context.scene, "text_y", text="Text Y")
        
        row = layout.row()
        row.operator("view3d.toggle_draw_hex", text="HEXCODE")
        
        row = layout.row() 
        row.prop(context.scene, "hex_x", text="Hex Code X")
        row.prop(context.scene, "hex_y", text="Hex Code Y")

def hex_from_color(color):
    r, g, b = [int(c * 255) for c in color]
    return f'#{r:02X}{g:02X}{b:02X}'

def update_brush_color_hex(scene):
    brush = bpy.context.tool_settings.image_paint.brush
    if brush and brush.use_paint_image:
        color = brush.color
        scene.brush_color_hex = hex_from_color(color)

def list_keymaps():
    wm = bpy.context.window_manager
    keyconfigs = wm.keyconfigs
    kc = keyconfigs.active

    keymap_names = ["Image Paint", "Image Paint (Global)"]
    for keymap_name in keymap_names:
        km = kc.keymaps.get(keymap_name)
        if km:
            print(f"Listing keymap: {keymap_name}")
            for kmi in km.keymap_items:
                print(f"Keymap Item: {kmi.idname}, Key: {kmi.type}")
        else:
            print(f"Keymap {keymap_name} not found")

def register():
    bpy.utils.register_class(VIEW3D_OT_toggle_draw_text)
    bpy.utils.register_class(VIEW3D_OT_toggle_draw_hex)
    bpy.utils.register_class(D2P_PT_toggle_draw_panel)
    bpy.types.Scene.text_x = bpy.props.IntProperty(name="Text X Position", default=100, min=0, max=2000)
    bpy.types.Scene.text_y = bpy.props.IntProperty(name="Text Y Position", default=100, min=0, max=2000)
    bpy.types.Scene.text_color = bpy.props.FloatVectorProperty(
        name="Text Color",
        subtype='COLOR',
        default=(0.906, 0.549, 0.192, 1.0),
        min=0.0, max=1.0,
        size=4,
        description="Color of the text"
    )
    bpy.types.Scene.brush_color_hex = bpy.props.StringProperty(
        name="Brush Color Hex",
        default="#E78C31",
        description="Hex code of the brush color"
    )
    bpy.types.Scene.hex_x = bpy.props.IntProperty(name="Hex Code X Position", default=100, min=0, max=2000)
    bpy.types.Scene.hex_y = bpy.props.IntProperty(name="Hex Code Y Position", default=300, min=0, max=2000)
    bpy.app.handlers.depsgraph_update_post.append(update_brush_color_hex)

    # List the keymaps for debugging
    list_keymaps()

def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_toggle_draw_text)
    bpy.utils.unregister_class(VIEW3D_OT_toggle_draw_hex)
    bpy.utils.unregister_class(D2P_PT_toggle_draw_panel)
    del bpy.types.Scene.text_x
    del bpy.types.Scene.text_y
    del bpy.types.Scene.text_color
    del bpy.types.Scene.brush_color_hex
    del bpy.types.Scene.hex_x
    del bpy.types.Scene.hex_y
    bpy.app.handlers.depsgraph_update_post.remove(update_brush_color_hex)

if __name__ == "__main__":
    register()
