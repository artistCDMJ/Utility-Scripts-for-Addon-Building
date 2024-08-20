import bpy

def create_compositor_node_tree(image1, image2, blend_mode):
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree

    for node in tree.nodes:
        tree.nodes.remove(node)

    image_node1 = tree.nodes.new(type='CompositorNodeImage')
    image_node1.image = image1
    image_node1.location = -300, 200

    image_node2 = tree.nodes.new(type='CompositorNodeImage')
    image_node2.image = image2
    image_node2.location = -300, -200

    mix_node = tree.nodes.new(type='CompositorNodeMixRGB')
    mix_node.blend_type = blend_mode
    mix_node.location = 200, 0

    tree.links.new(image_node1.outputs[0], mix_node.inputs[1])
    tree.links.new(image_node2.outputs[1], mix_node.inputs[0])
    tree.links.new(image_node2.outputs[0], mix_node.inputs[2])

    composite_node = tree.nodes.new(type='CompositorNodeComposite')
    composite_node.location = 400, 0

    tree.links.new(mix_node.outputs[0], composite_node.inputs[0])

def render_and_extract_image(output_name, width, height):
    bpy.context.scene.render.resolution_x = width
    bpy.context.scene.render.resolution_y = height
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = f'/tmp/{output_name}.png'
    bpy.ops.render.render(write_still=True)
    combined_image = bpy.data.images.load(bpy.context.scene.render.filepath)
    return combined_image

class NODE_OT_flatten_images(bpy.types.Operator):
    bl_idname = "node.flatten_images"
    bl_label = "Flatten Images"
    bl_description = "Flatten selected image nodes using a mix node and create a composite image"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Ensure we are in the Shader Editor
        if context.area.type != 'NODE_EDITOR' or context.space_data.tree_type != 'ShaderNodeTree':
            self.report({'ERROR'}, "This operator must be run in the Shader Editor")
            return {'CANCELLED'}

        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        material = obj.active_material
        if not material:
            self.report({'ERROR'}, "Active object has no active material")
            return {'CANCELLED'}

        if not material.use_nodes:
            self.report({'ERROR'}, "Active material does not use nodes")
            return {'CANCELLED'}

        node_tree = material.node_tree
        nodes = node_tree.nodes

        # Get selected nodes from the node tree
        selected_nodes = [node for node in nodes if node.select]
        
        # Debug print to verify selected nodes
        print("Selected nodes:", [(node.name, node.type) for node in selected_nodes])

        image_nodes = [node for node in selected_nodes if node.type == 'TEX_IMAGE']
        mix_nodes = [node for node in selected_nodes if node.type == 'MIX']

        # Debug print to verify filtered nodes
        print("Selected image nodes:", [node.name for node in image_nodes])
        print("Selected mix nodes:", [node.name for node in mix_nodes])

        # Debug print the actual types of all selected nodes to diagnose the issue
        for node in selected_nodes:
            print(f"Node {node.name} has type {node.type}")

        if len(image_nodes) != 2 or len(mix_nodes) != 1:
            self.report({'ERROR'}, "Select exactly two image nodes and one mix node")
            return {'CANCELLED'}

        image_node1, image_node2 = image_nodes
        mix_node = mix_nodes[0]

        blend_mode = mix_node.blend_type

        image1 = image_node1.image
        image2 = image_node2.image

        if not image1.has_data or not image2.has_data:
            self.report({'ERROR'}, "One or both images are not loaded")
            return {'CANCELLED'}

        width1, height1 = image1.size
        width2, height2 = image2.size

        if (width1, height1) != (width2, height2):
            self.report({'ERROR'}, "Images must be the same size")
            return {'CANCELLED'}

        render_width, render_height = width1, height1
        create_compositor_node_tree(image1, image2, blend_mode)
        combined_image = render_and_extract_image("CombinedImage", render_width, render_height)

        bpy.context.area.ui_type = 'ShaderNodeTree'

        # Create a group from the selected nodes
        bpy.ops.node.group_make()
        
        # Find the newly created group node
        group_node = None
        for node in nodes:
            if node.type == 'GROUP' and node.name not in [n.name for n in selected_nodes]:
                group_node = node
                break

        if group_node:
            group_node.label = "Flatten Input"

        # Add the new image texture node
        new_image_node = nodes.new('ShaderNodeTexImage')
        new_image_node.image = combined_image
        new_image_node.label = "Flatten result"
        new_image_node.location = group_node.location.x + 300, group_node.location.y

        return {'FINISHED'}

class NODE_PT_flattener_panel(bpy.types.Panel):
    bl_label = "Flattener"
    bl_idname = "NODE_PT_flattener_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout
        layout.operator("node.flatten_images")

def register():
    bpy.utils.register_class(NODE_OT_flatten_images)
    bpy.utils.register_class(NODE_PT_flattener_panel)

def unregister():
    bpy.utils.unregister_class(NODE_OT_flatten_images)
    bpy.utils.unregister_class(NODE_PT_flattener_panel)

if __name__ == "__main__":
    register()
