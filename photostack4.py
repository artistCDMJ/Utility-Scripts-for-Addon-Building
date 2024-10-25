import bpy

class PhotoStackProperties(bpy.types.PropertyGroup):
    uv_map_name: bpy.props.StringProperty(
        name="UV Map Name",
        default="UVMap"
    )


class PhotoStack(bpy.types.Operator):
    """Add or extend a 'Photostack' with Multiple Image Textures inside a Node Group"""
    bl_idname = "object.add_photostack"
    bl_label = "Add to or Create Photostack"

    def execute(self, context):
        scene = context.scene
        num_textures = scene.num_textures
        obj = context.object

        # Ensure the object has a material
        if not obj.data.materials:
            self.report({'ERROR'}, "Object has no material.")
            return {'CANCELLED'}

        material = obj.active_material
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes

        # Find the first Image Texture node (this is the active image node to copy)
        image_node = None
        for node in nodes:
            if node.type == 'TEX_IMAGE':
                image_node = node
                break

        if not image_node or not image_node.image:
            self.report({'ERROR'}, "No valid image texture node found.")
            return {'CANCELLED'}

        original_image = image_node.image  # This is the original image to copy

        # Check if a '_photostack' group node already exists in the material
        group_node = None
        for node in nodes:
            if node.type == 'GROUP' and "_photostack" in node.node_tree.name:
                group_node = node
                break

        # If no group node exists, create a new one
        if not group_node:
            nodegroup_name = f"{original_image.name}_photostack"
            nodegroup = bpy.data.node_groups.new(type='ShaderNodeTree', name=nodegroup_name)

            # Prepare links for adding more layers
            links = nodegroup.links  # Initialize the links for the nodegroup here

            # Create input and output nodes in the node group
            group_input = nodegroup.nodes.new("NodeGroupInput")
            group_output = nodegroup.nodes.new("NodeGroupOutput")
            group_output.location = (600, 0)

            # Add an output socket to the node group interface in Blender 4.0+
            nodegroup.interface.new_socket(name="Result", socket_type='NodeSocketColor', in_out='OUTPUT')

            # Create a new group node in the material
            group_node = nodes.new(type="ShaderNodeGroup")
            group_node.node_tree = nodegroup

            ### Add a UV Map node for the first image (original image) ###
            uv_node = nodegroup.nodes.new(type='ShaderNodeUVMap')
            uv_node.location = (-300, 400)  # Position for the UV node
            uv_node.uv_map = "UVMap"  # Assuming "UVMap", but this could be dynamic

            # Copy the first image node to the node group as the first layer
            img_tex = nodegroup.nodes.new(type='ShaderNodeTexImage')
            img_tex.location = (-100, 400)
            img_tex.image = original_image

            # Connect the UV map to the original image texture node
            links.new(uv_node.outputs['UV'], img_tex.inputs['Vector'])

            previous_node = img_tex  # Track the first image node

        else:
            # If the group node already exists, retrieve it
            nodegroup = group_node.node_tree  # This retrieves the existing nodegroup
            links = nodegroup.links  # Initialize the links for the existing nodegroup

            # Locate the Group Output node
            group_output_node = None
            for node in nodegroup.nodes:
                if node.type == 'GROUP_OUTPUT':
                    group_output_node = node
                    break

            if not group_output_node:
                self.report({'ERROR'}, "Group output node not found.")
                return {'CANCELLED'}

            # Find the last node connected to the Group Output node
            if group_output_node.inputs[0].is_linked:
                last_link = group_output_node.inputs[0].links[0]
                previous_node = last_link.from_node  # Set the last connected node as previous_node
            else:
                # If there's no Mix node or connection to the Group Output, fallback to the original image node
                previous_node = None
                for node in nodegroup.nodes:
                    if node.type == 'TEX_IMAGE' and node.image == original_image:
                        previous_node = node
                        break

                if not previous_node:
                    self.report({'ERROR'}, "No valid previous node found.")
                    return {'CANCELLED'}


        # Start adding additional blank images (RGBA 0,0,0,0)
        uv_y_offset = 200
        img_y_offset = 400
        mix_x_offset = 200

        # Find the Group Output node
        group_output_node = None
        for node in nodegroup.nodes:
            if node.type == 'GROUP_OUTPUT':
                group_output_node = node
                break

        if not group_output_node:
            self.report({'ERROR'}, "Group output node not found.")
            return {'CANCELLED'}

        # Keep track of existing textures to avoid name conflicts
        num_existing_textures = len([n for n in nodegroup.nodes if n.type == 'TEX_IMAGE'])

        # Add new blank image textures and mix them
        for i in range(num_textures):
            # Create a new blank image for painting with a unique name
            new_image_name = f"PaintLayer_{num_existing_textures + i + 1}"
            new_image = bpy.data.images.new(new_image_name, width=original_image.size[0], height=original_image.size[1], alpha=True)
            new_image.generated_color = (0, 0, 0, 0)  # RGBA 0,0,0,0 for transparency

            # Create a new UV Map node and Image Texture node for the blank image
            uv_node = nodegroup.nodes.new(type='ShaderNodeUVMap')
            uv_node.location = (-300, uv_y_offset)
            uv_node.uv_map = "UVMap"  # Assuming "UVMap", but this could be dynamic

            img_tex = nodegroup.nodes.new(type='ShaderNodeTexImage')
            img_tex.location = (-100, img_y_offset)
            img_tex.image = new_image

            # Connect the UV map to the Image Texture
            links.new(uv_node.outputs['UV'], img_tex.inputs['Vector'])

            # Create a mix node to blend the new image with the previous layer
            mix_node = nodegroup.nodes.new(type='ShaderNodeMix')
            mix_node.location = (mix_x_offset, img_y_offset)
            mix_node.data_type = 'RGBA'  # Mix colors with alpha
            mix_node.inputs["Factor"].default_value = 1.0  # Can be adjusted for blending

            # Connect the previous node (last mix node or first image) to the new mix node
            if previous_node.type == 'ShaderNodeMix':
                # For ShaderNodeMix, use the 'Result' output
                links.new(previous_node.outputs['Result'], mix_node.inputs['A'])  # Previous mix Result goes to A
            else:
                # Check if the 'Color' output exists, else use 'Result' or another output
                if 'Color' in previous_node.outputs:
                    links.new(previous_node.outputs['Color'], mix_node.inputs['A'])  # Previous image's Color goes to A
                elif 'Result' in previous_node.outputs:
                    links.new(previous_node.outputs['Result'], mix_node.inputs['A'])  # Fallback to 'Result' if no 'Color'
                elif 'RGBA' in previous_node.outputs:
                    links.new(previous_node.outputs['RGBA'], mix_node.inputs['A'])  # Some nodes may have 'RGBA'
                else:
                    # If none of these outputs exist, raise an error
                    self.report({'ERROR'}, f"No suitable output found on previous node: {previous_node.name}")
                    return {'CANCELLED'}


            # Connect new image's Color and Alpha to the new mix node
            links.new(img_tex.outputs['Color'], mix_node.inputs['B'])  # New image's Color goes to B
            links.new(img_tex.outputs['Alpha'], mix_node.inputs['Factor'])  # Alpha controls the mix factor

            # Update previous_node to the new mix node for the next iteration
            previous_node = mix_node

            # Adjust positions for the next iteration
            uv_y_offset -= 200
            img_y_offset -= 200
            mix_x_offset += 200

        # Final output connection to the Group Output node
        links.new(previous_node.outputs['Result'], group_output_node.inputs['Result'])  # Connect final mix Result to Group Output

        # Connect the group output to the Material Output's surface
        material_output_node = None
        for node in nodes:
            if node.type == 'OUTPUT_MATERIAL':
                material_output_node = node
                break

        if not material_output_node:
            material_output_node = nodes.new(type='ShaderNodeOutputMaterial')
            material_output_node.location = (800, 0)

        # Connect the group output to the material output
        links = material.node_tree.links
        links.new(group_node.outputs['Result'], material_output_node.inputs['Surface'])

        return {'FINISHED'}


class PhotoPaintPanel(bpy.types.Panel):
    """Creates a Panel in the 3D View's Tool Shelf"""
    bl_label = "PhotoStack Generator"
    bl_idname = "VIEW3D_PT_simple_material"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paint'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Number of textures input
        layout.prop(scene, "num_textures")

        # Add material button
        layout.operator("object.add_photostack", text="Generate/Extend Photostack")


def update_texture_settings(self, context):
    """Update the texture settings collection whenever the number of textures changes."""
    scene = context.scene
    current_num = len(scene.texture_settings)
    requested_num = scene.num_textures

    # Add entries if num_textures is greater than the current number of entries
    if requested_num > current_num:
        for i in range(requested_num - current_num):
            scene.texture_settings.add()
    
    # Remove entries if num_textures is less than the current number of entries
    elif requested_num < current_num:
        for i in range(current_num - requested_num):
            scene.texture_settings.remove(len(scene.texture_settings) - 1)


def register():
    bpy.utils.register_class(PhotoStackProperties)
    bpy.utils.register_class(PhotoStack)
    bpy.utils.register_class(PhotoPaintPanel)

    bpy.types.Scene.num_textures = bpy.props.IntProperty(
        name="Number of Textures",
        default=1,  # Set default to 1
        min=1,
        max=10,
        description="Number of image textures to add",
        update=update_texture_settings  # Ensure we update texture settings on change
    )

    bpy.types.Scene.texture_settings = bpy.props.CollectionProperty(type=PhotoStackProperties)

    # Initialize the collection when the script is run
    update_texture_settings(bpy.context.scene, bpy.context)


def unregister():
    bpy.utils.unregister_class(PhotoStackProperties)
    bpy.utils.unregister_class(PhotoStack)
    bpy.utils.unregister_class(PhotoPaintPanel)

    del bpy.types.Scene.num_textures
    del bpy.types.Scene.texture_settings


if __name__ == "__main__":
    register()
