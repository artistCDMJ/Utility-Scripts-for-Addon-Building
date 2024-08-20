import bpy

class BRUSH_OT_flip_gradient(bpy.types.Operator):
    bl_idname = "brush.flip_gradient"
    bl_label = "Flip Brush Gradient"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        brush = self.get_active_brush(context)
        if not brush:
            self.report({'WARNING'}, "No active brush found.")
            return {'CANCELLED'}
        
        if not hasattr(brush, "gradient") or brush.gradient is None:
            self.report({'WARNING'}, "The active brush does not use a gradient.")
            return {'CANCELLED'}

        self.flip_color_ramp(brush.gradient)
        
        return {'FINISHED'}
    
    def get_active_brush(self, context):
        tool_settings = context.tool_settings

        if context.sculpt_object:
            return tool_settings.sculpt.brush
        elif context.vertex_paint_object:
            return tool_settings.vertex_paint.brush
        elif context.weight_paint_object:
            return tool_settings.weight_paint.brush
        elif context.image_paint_object:
            return tool_settings.image_paint.brush
        else:
            return None

    def flip_color_ramp(self, color_ramp):
        elements = color_ramp.elements
        n = len(elements)
        
        # Create lists to hold the positions and colors temporarily
        positions = [e.position for e in elements]
        colors = [e.color[:] for e in elements]  # Use slicing to copy the color values
        
        for i in range(n):
            elements[i].position = 1.0 - positions[n-1-i]
            elements[i].color = colors[n-1-i]

def register():
    bpy.utils.register_class(BRUSH_OT_flip_gradient)

def unregister():
    bpy.utils.unregister_class(BRUSH_OT_flip_gradient)

if __name__ == "__main__":
    register()

    # Test call
    bpy.ops.brush.flip_gradient()
