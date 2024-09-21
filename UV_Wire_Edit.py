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
        
        if context.area.ui_type == 'UV':
            layout.prop(theme, "wire_edit", text="UV Wire in Edit")
        else:
            layout.prop(theme, "uv_shadow", text="UV Wire in Paint")

class VIEW3DWireColor(bpy.types.Panel):
    """Creates a Panel in the 3D View to change the Edit Mode wire color"""
    bl_label = "3D View Wire Color"
    bl_idname = "VIEW3D_PT_wire_color"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        prefs = bpy.context.preferences
        theme = prefs.themes[0].view_3d
        
        layout.prop(theme, "wire_edit", text="Wire in Edit")
        layout.prop(theme, "edge_width", text = "Edge Width")
        


def register():
    bpy.utils.register_class(UVWireColor)
    bpy.utils.register_class(VIEW3DWireColor)

def unregister():
    bpy.utils.unregister_class(UVWireColor)
    bpy.utils.unregister_class(VIEW3DWireColor)

if __name__ == "__main__":
    register()

