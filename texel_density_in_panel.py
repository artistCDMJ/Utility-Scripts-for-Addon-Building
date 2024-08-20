import bpy
import math
from bpy.types import Panel, Operator

def calculate_texel_density(obj, desired_texel_density):
    # Calculate the surface area of the object
    obj_surface_area = sum(p.area for p in obj.data.polygons)
    
    # Calculate the required number of pixels (texels)
    required_texels = desired_texel_density * math.sqrt(obj_surface_area)
    
    # Determine the appropriate texture resolution
    # We assume square textures and round to the nearest power of two
    texture_size = 2 ** math.ceil(math.log2(required_texels))
    
    return texture_size

class D2P_OT_CalculateTexelDensity(Operator):
    """Selected Object is Examined for Surface Area and Suggests Power of 2 Texture Size"""
    bl_idname = "object.calculate_texel_density"
    bl_label = "Calculate Texel Density"
    
    
    result: bpy.props.StringProperty(name="Result", default="")
    
    def execute(self, context):
        obj = context.active_object
        
        # Ensure object has valid data
        if not obj or obj.type != 'MESH':
            self.result = "Please select a valid mesh object."
            return {'FINISHED'}
        
        # Desired texel density (texels per meter)
        desired_texel_density = 1024  # Modify this value as needed
        
        # Calculate ideal texture size
        texture_size = calculate_texel_density(obj, desired_texel_density)
        
        self.result = f"Suggested Texture Size: {texture_size}x{texture_size}"
        
        # Store the result in the context scene to display in the panel
        context.scene.texel_density_result = self.result
        
        return {'FINISHED'}

class PaintPanel(Panel):
    bl_label = "Texel Density Calculator"
    bl_idname = "PAINT_PT_texel_density"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paint'
    
    def draw(self, context):
        layout = self.layout
        layout.operator("object.calculate_texel_density", icon='TEXTURE')
        if context.scene.get("texel_density_result"):
            layout.label(text=context.scene["texel_density_result"])

def register():
    bpy.utils.register_class(D2P_OT_CalculateTexelDensity)
    bpy.utils.register_class(PaintPanel)
    bpy.types.Scene.texel_density_result = bpy.props.StringProperty(name="Texel Density Result", default="")

def unregister():
    bpy.utils.unregister_class(D2P_OT_CalculateTexelDensity)
    bpy.utils.unregister_class(PaintPanel)
    del bpy.types.Scene.texel_density_result

if __name__ == "__main__":
    register()
