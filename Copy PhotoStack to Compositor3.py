
### Copy PhotoStack works for going to Compositor, and Generate/Edit PhotoStack works as well so we need to combine this into one
### working addon for now
### We need to go back and add functionality to other operators before fully introducing to D2P
###
### Flatten Images - needs to work from either inside or outside group node on selected images and mix nodes only for consolidating parts of a project
### Image2Compositor - check if we can add to it to work with PhotoStack2Compositor
### Image2Scene - borrow or adapt some of PhotoStack for it, but it SHOULD work as a main image then PhotoStack it


import bpy

def copy_photostack_nodes_to_compositor():
    # Ensure an object is selected
    obj = bpy.context.active_object
    if not obj:
        print("No active object selected.")
        return

    # Ensure the object has an active material
    if not obj.active_material:
        print("The selected object has no active material.")
        return

    material = obj.active_material

    # Ensure the material uses nodes
    if not material.use_nodes:
        print("The active material does not use nodes.")
        return

    # Access the node tree of the active material
    node_tree = material.node_tree
    active_node = node_tree.nodes.active  # Get the active node in the node editor

    # Check if the active node is a group node
    if not active_node or active_node.type != 'GROUP':
        print("The active node is not a group node.")
        return

    shader_node_group = active_node.node_tree

    # Enable Compositor Nodes
    bpy.context.scene.use_nodes = True
    compositor_nodes = bpy.context.scene.node_tree.nodes
    compositor_links = bpy.context.scene.node_tree.links

    # Create a Viewer Node if not already present
    viewer_node = None
    for node in compositor_nodes:
        if node.type == 'VIEWER':
            viewer_node = node
            break

    if not viewer_node:
        viewer_node = compositor_nodes.new(type="CompositorNodeViewer")
        viewer_node.location = (500, 300)

    # Keep track of added image and mix nodes for connections
    image_nodes = []
    node_offset_x = 0
    node_offset_y = 0
    
    # Iterate through nodes in photoStack, copying Image Texture and Mix nodes
    mix_nodes = [node for node in shader_node_group.nodes if node.type == 'MIX']  # Updated to 'MIX'
    if not mix_nodes:
        print("No Mix nodes found in the PhotoStack group.")
        return

    # Print the blend types found in shader Mix nodes
    for i, mix_node in enumerate(mix_nodes):
        print(f"Shader Mix Node {i} blend type: {mix_node.blend_type}")

    # Copy Image Texture nodes
    for node in shader_node_group.nodes:
        if node.type == 'TEX_IMAGE':
            new_node = compositor_nodes.new(type="CompositorNodeImage")
            new_node.location = (node_offset_x, node_offset_y)
            new_node.label = "PhotoStack Image"
            new_node.name = node.name
            if node.image:
                new_node.image = node.image
            image_nodes.append(new_node)
            node_offset_x += 300

    if len(image_nodes) >= 2:
        # First Mix node setup
        first_mix = compositor_nodes.new(type="CompositorNodeMixRGB")
        first_mix.location = (node_offset_x, node_offset_y)
        first_mix.use_alpha = True
        first_mix.blend_type = mix_nodes[0].blend_type
        print(f"Set first compositor mix node blend type to: {first_mix.blend_type}")
        
        compositor_links.new(image_nodes[0].outputs[0], first_mix.inputs[1])
        compositor_links.new(image_nodes[1].outputs[0], first_mix.inputs[2])
        node_offset_x += 300

        # Additional Mix nodes
        previous_mix = first_mix
        for i in range(2, len(image_nodes)):
            mix_node = compositor_nodes.new(type="CompositorNodeMixRGB")
            mix_node.location = (node_offset_x, node_offset_y)
            mix_node.use_alpha = True
            if i - 1 < len(mix_nodes):
                blend_type = mix_nodes[i - 1].blend_type
                mix_node.blend_type = blend_type
                print(f"Set compositor mix node {i} blend type to: {blend_type}")
            
            # Link previous Mix node output to the current Mix node input 1
            compositor_links.new(previous_mix.outputs[0], mix_node.inputs[1])
            compositor_links.new(image_nodes[i].outputs[0], mix_node.inputs[2])
            previous_mix = mix_node
            node_offset_x += 300

    else:
        print("Insufficient image nodes to perform mixing.")

    compositor_links.new(previous_mix.outputs[0], viewer_node.inputs[0])
    print("PhotoStack nodes copied to the Compositor with alpha blending and blend types applied.")



# Define the UI Panel to add the button
class NODE_PT_photostack_copy(bpy.types.Panel):
    bl_label = "PhotoStack Copier"
    bl_idname = "NODE_PT_photostack_copy"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout
        layout.operator('node.copy_photostack_to_compositor', text="Copy PhotoStack to Compositor")

# Define the Operator that is triggered by the button
class NODE_OT_copy_photostack_to_compositor(bpy.types.Operator):
    bl_idname = "node.copy_photostack_to_compositor"
    bl_label = "Copy PhotoStack to Compositor"
    
    def execute(self, context):
        copy_photostack_nodes_to_compositor()
        return {'FINISHED'}

# Register the panel and operator
def register():
    bpy.utils.register_class(NODE_PT_photostack_copy)
    bpy.utils.register_class(NODE_OT_copy_photostack_to_compositor)

def unregister():
    bpy.utils.unregister_class(NODE_PT_photostack_copy)
    bpy.utils.unregister_class(NODE_OT_copy_photostack_to_compositor)

if __name__ == "__main__":
    register()
