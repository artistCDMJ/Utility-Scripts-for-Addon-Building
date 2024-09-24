import bpy
from bpy.props import FloatProperty, PointerProperty, EnumProperty
from bpy.types import Panel, Operator, PropertyGroup

def update_alpha(self, context):
    """Function to update the alpha of all objects in the selected collection."""
    collection_name = self.collection
    alpha_value = self.alpha_value

    if collection_name:
        collection = bpy.data.collections.get(collection_name)
        if collection:
            for obj in collection.objects:
                if obj.type == 'MESH':  # Only affect mesh objects
                    for mat_slot in obj.material_slots:
                        if mat_slot.material:
                            mat = mat_slot.material
                            if mat.use_nodes:  # Make sure material uses nodes
                                node_tree = mat.node_tree
                                bsdf = node_tree.nodes.get('Principled BSDF')
                                if bsdf:
                                    bsdf.inputs['Alpha'].default_value = alpha_value
                                    
            # Ensure correct alpha blending settings for transparency
            for obj in collection.objects:
                if obj.type == 'MESH':  # Only affect mesh objects
                    for mat_slot in obj.material_slots:
                        if mat_slot.material:
                            mat_slot.material.blend_method = 'BLEND'

def collection_items(self, context):
    """Returns available collections for dropdown."""
    return [(col.name, col.name, "") for col in bpy.data.collections]

class CollectionAlphaProperties(PropertyGroup):
    collection: EnumProperty(
        name="Collection",
        description="Select a collection to control alpha",
        items=collection_items
    )
    
    alpha_value: FloatProperty(
        name="Alpha",
        description="Set the alpha for the selected collection's objects",
        min=0.0,
        max=1.0,
        default=1.0,
        update=update_alpha
    )

class VIEW3D_PT_CollectionAlphaPanel(Panel):
    """Panel to control the alpha of all objects in a collection"""
    bl_label = "Collection Alpha Control"
    bl_idname = "VIEW3D_PT_collection_alpha"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Collection Alpha'

    def draw(self, context):
        layout = self.layout
        props = context.scene.collection_alpha_props
        
        layout.prop(props, "collection")
        layout.prop(props, "alpha_value")

class WM_OT_ResetAlpha(Operator):
    """Operator to reset alpha of selected collection to 1"""
    bl_label = "Reset Alpha"
    bl_idname = "wm.reset_alpha"

    def execute(self, context):
        props = context.scene.collection_alpha_props
        props.alpha_value = 1.0
        return {'FINISHED'}

def register():
    bpy.utils.register_class(CollectionAlphaProperties)
    bpy.utils.register_class(VIEW3D_PT_CollectionAlphaPanel)
    bpy.utils.register_class(WM_OT_ResetAlpha)
    bpy.types.Scene.collection_alpha_props = PointerProperty(type=CollectionAlphaProperties)

def unregister():
    del bpy.types.Scene.collection_alpha_props
    bpy.utils.unregister_class(CollectionAlphaProperties)
    bpy.utils.unregister_class(VIEW3D_PT_CollectionAlphaPanel)
    bpy.utils.unregister_class(WM_OT_ResetAlpha)

if __name__ == "__main__":
    register()
