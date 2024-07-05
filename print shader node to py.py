import bpy
import os
import mathutils

# Get the active object
obj = bpy.context.active_object

# Check if the object has any materials
if not obj or not obj.active_material:
    raise Exception("The active object has no material.")

# Get the active material
mat = obj.active_material

# Check if the material uses nodes
if not mat.use_nodes:
    raise Exception("The active material does not use nodes.")

# Get the node tree
node_tree = mat.node_tree

def node_to_script(node):
    script = ""
    
    # Create node
    script += f'node = nodes.new(type="{node.bl_idname}")\n'
    script += f'node.location = ({node.location[0]}, {node.location[1]})\n'
    
    # Set node properties
    for prop_name in node.bl_rna.properties.keys():
        if prop_name not in {'rna_type', 'location', 'select', 'type', 'name', 'inputs', 'outputs', 'internal_links', 'parent', 'dimensions'}:
            value = getattr(node, prop_name)
            if isinstance(value, str):
                script += f'node.{prop_name} = "{value}"\n'
            elif isinstance(value, mathutils.Vector):
                script += f'node.{prop_name} = mathutils.Vector(({value[0]}, {value[1]}))\n'
            elif isinstance(value, mathutils.Color):
                script += f'node.{prop_name} = mathutils.Color(({value[0]}, {value[1]}, {value[2]}))\n'
            else:
                script += f'node.{prop_name} = {value}\n'
    
    # Check and set input values
    for input in node.inputs:
        if input.type == 'RGBA' and input.default_value:
            color = input.default_value
            script += f'node.inputs["{input.name}"].default_value = ({color[0]}, {color[1]}, {color[2]}, {color[3]})\n'
        elif input.name == 'Blend' and input.default_value:
            blend_value = input.default_value
            script += f'node.inputs["{input.name}"].default_value = {blend_value}\n'
    
    return script

script_lines = [
    "import bpy",
    "import mathutils",
    "obj = bpy.context.active_object",
    "mat = obj.active_material",
    "mat.use_nodes = True",
    "nodes = mat.node_tree.nodes",
    "links = mat.node_tree.links",
    "nodes.clear()"
]

for node in node_tree.nodes:
    script_lines.append(node_to_script(node))

# Add links between nodes
for link in node_tree.links:
    from_node = link.from_node.name
    from_socket = link.from_socket.name
    to_node = link.to_node.name
    to_socket = link.to_socket.name
    script_lines.append(f'links.new(nodes["{from_node}"].outputs["{from_socket}"], nodes["{to_node}"].inputs["{to_socket}"])')

full_script = "\n".join(script_lines)

# Define the file path
file_path = "C:/tmp/generated_shader.py"

# Ensure the directory exists
os.makedirs(os.path.dirname(file_path), exist_ok=True)

# Write the script to the file
with open(file_path, 'w') as file:
    file.write(full_script)

print(f"Script saved to {file_path}")
