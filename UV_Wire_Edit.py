bl_info = {
    "name": "UV Wire Color Customizer",
    "blender": (3, 0, 0),
    "category": "UV",
}

import bpy

class UVWireColor(bpy.types.Panel):
    """Creates a Panel in the UV Editor to change the UV wire color"""
    bl_label = "UV Wire Color"
    bl_idname = "UV_PT_wire_color"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'

    def draw(self, context):
        layout = self.layout
        prefs = bpy.context.preferences
        theme = prefs.themes[0].image_editor
        
        # Display the color picker for UV wire color
        layout.prop(theme, "wire_edit", text="UV Wire Color")

def register():
    bpy.utils.register_class(UVWireColor)

def unregister():
    bpy.utils.unregister_class(UVWireColor)

if __name__ == "__main__":
    register()
