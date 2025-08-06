bl_info = {
    "name": "Measure Set Apply",
    "blender": (4, 4, 0),
    "category": "Mesh",
    "description": "CAD extras for Work",
}

import bpy
import bmesh
from mathutils import Vector

from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import FloatProperty, PointerProperty, EnumProperty, IntProperty, BoolProperty



class SELProperties(PropertyGroup):
    edge_length: FloatProperty(
        name="Edge Length",
        description="Target length for selected edge",
        default=1.0,
        min=0.0,
        subtype='DISTANCE'
    )

    constrain_to_cursor: bpy.props.BoolProperty(
        name="Constrain to Cursor",
        description="Anchor edge to the vertex closest to the 3D cursor",
        default=False
    )

    bevel_width: FloatProperty(
        name="Bevel Width",
        description="Bevel width for selected vertices",
        default=0.01,
        min=0.0,
        subtype='DISTANCE'
    )

    bevel_segments: bpy.props.IntProperty(
        name="Segments",
        description="Number of segments in vertex bevel",
        default=2,
        min=1,
        max=12
    )
    edge_orientation: EnumProperty(
        name="Orientation",
        description="Direction to align the edge primitive",
        items=[
            ('X', "X Axis", "Align edge along the X axis"),
            ('Y', "Y Axis", "Align edge along the Y axis"),
        ],
        default='X'
    )
    
    plane_width: FloatProperty(
    name="Plane Width",
    description="Width (X) of the new plane",
    default=1.0,
    min=0.0,
    subtype='DISTANCE'
    )

    plane_height: FloatProperty(
        name="Plane Height",
        description="Height (Y) of the new plane",
        default=1.0,
        min=0.0,
        subtype='DISTANCE'
    )
    join_plane_to_active: BoolProperty(
    name="Join to Active Object",
    description="Join the new plane to the currently edited object",
    default=True
    )

class KnockoutProperties(bpy.types.PropertyGroup):
    cutter_shape: EnumProperty(
        name="Shape",
        items=[
            ("CIRCLE", "Circle", "Circle profile cutter"),
            ("PLANE", "Plane", "Flat plane cutter"),
        ],
        default="CIRCLE"
    )

    cutter_size: FloatProperty(
        name="Size",
        description="Size of the cutter object",
        default=0.02,
        min=0.001,
        subtype='DISTANCE'
    )

class MESH_OT_add_scaled_plane(bpy.types.Operator):
    bl_idname = "mesh.add_scaled_plane"
    bl_label = "Add Scaled Plane"
    bl_description = "Add a plane with specified X/Y dimensions and set origin to lower-left"
    bl_options = {'REGISTER', 'UNDO'}

    join_to_edit_object: bpy.props.BoolProperty(
        name="Join to Active",
        description="Join new plane to the current object in Edit Mode",
        default=True
    )

    def execute(self, context):
        import bmesh
        from mathutils import Vector

        props = context.scene.sel_props
        width = props.plane_width
        height = props.plane_height
        join_to_edit = context.scene.sel_props.join_plane_to_active


        props = context.scene.sel_props
        join_to_edit = props.join_plane_to_active

        original_obj = context.edit_object

        # Only require Edit Mode if we plan to join to an existing mesh
        if join_to_edit:
            if original_obj is None or original_obj.type != 'MESH':
                self.report({'ERROR'}, "Must be in Edit Mode on a mesh object.")
                return {'CANCELLED'}

        if context.active_object and context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Switch to Object Mode before creating new mesh
        #bpy.ops.object.mode_set(mode='OBJECT')

        # Add plane at cursor location
        bpy.ops.mesh.primitive_plane_add(location=context.scene.cursor.location)
        plane_obj = context.active_object

        # Scale to desired size
        plane_obj.scale = (width / 2.0, height / 2.0, 1)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        # Enter Edit Mode on the new plane to adjust origin
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(plane_obj.data)
        bm.verts.ensure_lookup_table()
        lower_left = min(bm.verts, key=lambda v: (v.co.x, v.co.y))
        origin_pos = lower_left.co.copy()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Offset so origin aligns to lower-left
        plane_obj.location += plane_obj.matrix_world.to_3x3() @ origin_pos
        for v in plane_obj.data.vertices:
            v.co -= origin_pos

        # Snap to cursor
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

        if join_to_edit:
            # Join new plane to original object
            plane_obj.select_set(True)
            original_obj.select_set(True)
            context.view_layer.objects.active = original_obj
            bpy.ops.object.join()

            # Return to Edit Mode
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}






class MESH_OT_add_edge_to_edit_mesh(bpy.types.Operator):
    bl_idname = "mesh.add_edge_to_edit_mesh"
    bl_label = "Add Edge to Current Mesh"
    bl_description = "Adds an edge to the current object in Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object

        if obj.mode != 'EDIT' or obj.type != 'MESH':
            self.report({'WARNING'}, "Must be in Edit Mode on a mesh object.")
            return {'CANCELLED'}

        props = context.scene.sel_props
        length = props.edge_length
        axis = props.edge_orientation

        if axis == 'X':
            dir = Vector((1, 0, 0))
        elif axis == 'Y':
            dir = Vector((0, 1, 0))
        else:
            dir = Vector((1, 0, 0))

        # Use the 3D cursor as insertion point
        base = context.scene.cursor.location
        offset = dir.normalized() * length

        bm = bmesh.from_edit_mesh(obj.data)
        v1 = bm.verts.new(base)
        v2 = bm.verts.new(base + offset)
        bm.edges.new((v1, v2))

        bm.normal_update()
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)

        return {'FINISHED'}



class MESH_OT_vertex_bevel(bpy.types.Operator):
    bl_idname = "mesh.vertex_bevel_custom"
    bl_label = "Vertex Bevel"
    bl_description = "Bevel Selected Vertex with Current Settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.sel_props

        # Perform vertex-only bevel on selected vertices
        bpy.ops.mesh.bevel(
            offset=props.bevel_width,
            segments=props.bevel_segments,
            affect='VERTICES',  # <- Correct keyword
            offset_pct=0,       # <- Disable percentage mode
            profile=0.5         # Optional: standard profile
        )

        return {'FINISHED'}


class MESH_OT_set_edge_length(Operator):
    bl_idname = "mesh.set_edge_length"
    bl_label = "Set Edge Length"
    bl_description = "Set the Edge(s) to the Current Length"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (
            context.object is not None and
            context.object.type == 'MESH' and
            context.mode == 'EDIT_MESH'
        )

    def execute(self, context):
        obj = context.object
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Must be in Edit mode")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        props = context.scene.sel_props
        target_length = props.edge_length
        constrain = props.constrain_to_cursor
        cursor_location = context.scene.cursor.location

        selected_edges = [e for e in bm.edges if e.select]

        if not selected_edges:
            self.report({'WARNING'}, "No edges selected")
            return {'CANCELLED'}

        for edge in selected_edges:
            if len(edge.verts) != 2:
                continue

            v1, v2 = edge.verts
            edge_vec = v2.co - v1.co
            current_length = edge_vec.length

            if current_length == 0:
                self.report({'WARNING'}, "Skipping zero-length edge")
                continue

            direction = edge_vec.normalized()

            if constrain:
                # Constrain one end to the vertex closest to the 3D cursor
                dist_v1 = (v1.co - cursor_location).length
                dist_v2 = (v2.co - cursor_location).length

                if dist_v1 <= dist_v2:
                    anchor = v1
                    moving = v2
                    sign = 1
                else:
                    anchor = v2
                    moving = v1
                    sign = -1

                moving.co = anchor.co + direction * target_length * sign
            else:
                # Scale from midpoint
                center = (v1.co + v2.co) * 0.5
                offset = direction * (target_length * 0.5)
                v1.co = center - offset
                v2.co = center + offset

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


    
class MESH_OT_apply_scale(Operator):
    bl_idname = "mesh.apply_scale"
    bl_label = "Apply Scale of Object"
    bl_description = "Apply Object Scale and Return to Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (
            context.object is not None and
            context.object.type == 'MESH' and
            context.mode == 'EDIT_MESH'
        )

    def execute(self, context):
        obj = context.object
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Must be in Edit mode")
            return {'CANCELLED'}
        
        # Switch to Object Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Apply scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        # Switch back to Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')

        
        return {'FINISHED'}

class MESH_OT_toggle_edge_length(Operator):
    bl_idname = "mesh.toggle_edge"
    bl_label = "Toggle Edge Length Display"
    bl_description = "Toggle Draw Edge Length On or Off"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (
            context.object is not None and
            context.object.type == 'MESH' and
            context.mode == 'EDIT_MESH'
        )

    def execute(self, context):
        obj = context.object
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Must be in Edit mode")
            return {'CANCELLED'}
        
        if bpy.context.space_data.overlay.show_extra_edge_length == False:
            bpy.context.space_data.overlay.show_extra_edge_length = True
        
        else:
            bpy.context.space_data.overlay.show_extra_edge_length = False
        

        
        return {'FINISHED'}
    
    
    
class VIEW3D_OT_snap_cursor_to_selected(bpy.types.Operator):
    bl_idname = "view3d.snap_cursor_quick"
    bl_label = "Snap Cursor to Selected"
    bl_description = "Quickly snap 3D cursor to the Selection"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (
            context.object is not None and
            context.object.type == 'MESH' and
            context.mode == 'EDIT_MESH'
        )

    def execute(self, context):
        bpy.ops.view3d.snap_cursor_to_selected()
        return {'FINISHED'}
    

class VIEW3D_OT_metric_imperial_set(bpy.types.Operator):
    bl_idname = "view3d.metric_imperial_setup"
    bl_label = "Toggle Metric or Imperial UNITS"
    bl_description = "Set to MM or Imperial and Divisions"
    bl_options = {'REGISTER', 'UNDO'}
    
    #@classmethod
    #def poll(cls, context):
        #return (
            #context.object is not None and
            #context.object.type == 'MESH' and
            #context.mode == 'EDIT_MESH'
        #)

    def execute(self, context):
        
        
        #bpy.context.space_data.context = 'SCENE'
        
        if bpy.context.scene.unit_settings.length_unit == 'MILLIMETERS':
            bpy.context.scene.unit_settings.system = 'IMPERIAL'
            bpy.context.scene.unit_settings.length_unit = 'INCHES'
            bpy.context.space_data.overlay.grid_subdivisions = 12
            bpy.context.scene.unit_settings.scale_length = 0.0833

            
        else:
            bpy.context.scene.unit_settings.system = 'METRIC'
            bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
            bpy.context.space_data.overlay.grid_subdivisions = 10 
            bpy.context.space_data.overlay.grid_scale = 0.1

            bpy.context.scene.unit_settings.scale_length = 0.001
        
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements_base = {'GRID'}

        
        return {'FINISHED'}

class VIEW3D_OT_toggle_wire(bpy.types.Operator):
    bl_idname = "view3d.toggle_wire"
    bl_label = "Toggle Wireframe Draw"
    bl_description = "Toggle Draw Wireframe, Allows preview of edges in Object mode for Tracing"
    bl_options = {'REGISTER', 'UNDO'}
    
    

    def execute(self, context):
        if bpy.context.object.show_wire == True:
            bpy.context.object.show_wire = False
        else:
            bpy.context.object.show_wire = True


        return {'FINISHED'}

# ------------------------------------
# Cutter Generator
# ------------------------------------
class OBJECT_OT_generate_cutter_instances(bpy.types.Operator):
    bl_idname = "object.generate_cutter_instances"
    bl_label = "Generate Cutter Instances"
    bl_description = "Place cutter objects at selected vertices"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.knockout_props
        cutter_shape = props.cutter_shape
        cutter_size = props.cutter_size

        obj = context.object

        if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
            self.report({'ERROR'}, "Must be in Edit Mode on a mesh object.")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        # Cache vertex positions before exiting Edit Mode
        selected_positions = [obj.matrix_world @ v.co.copy() for v in bm.verts if v.select]

        if not selected_positions:
            self.report({'WARNING'}, "No vertices selected.")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='OBJECT')  # Now safe

        for world_pos in selected_positions:
            cutter = self.create_cutter_object(context, shape=cutter_shape, size=cutter_size)
            cutter.location = world_pos


        return {'FINISHED'}

    def create_cutter_object(self, context, shape="CIRCLE", size=0.02):
        if shape == "CIRCLE":
            bpy.ops.mesh.primitive_circle_add(
                vertices=32,
                radius=size * 0.5,
                location=(0, 0, 0),
                fill_type='NOTHING'  # ✅ Must be 'NOTHING' to keep as edge-only
            )
        elif shape == "PLANE":
            bpy.ops.mesh.primitive_grid_add(  # ✅ Use grid to ensure edge-only
                size=size,
                x_subdivisions=2,
                y_subdivisions=2,
                location=(0, 0, 0)
            )

        cutter_obj = context.active_object
        cutter_obj.name = f"Cutter_{shape}"
        return cutter_obj



class OBJECT_OT_knife_project_cutters(bpy.types.Operator):
    bl_idname = "object.knife_project_cutters"
    bl_label = "Knife Project from Cutters"
    bl_description = "Use Cutter_ objects to project into the active object using Knife Project"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        view = context.space_data.region_3d

        if view.view_perspective != 'ORTHO':
            self.report({'WARNING'}, "Knife Project requires orthographic view.")
            return {'CANCELLED'}

        main_obj = context.active_object
        if not main_obj or main_obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh (target for projection).")
            return {'CANCELLED'}

        # Get all valid cutter objects (by name prefix)
        view_layer = context.view_layer
        cutter_objs = [
            obj for obj in view_layer.objects
            if obj.name.startswith("Cutter_")
            and obj.type == 'MESH'
            and not obj.hide_get()
            and not obj.hide_viewport
        ]


        if not cutter_objs:
            self.report({'WARNING'}, "No cutter objects named 'Cutter_' found in the scene.")
            return {'CANCELLED'}

                
        #should have already selected main object to work
        # Select main object and make it active
        main_obj.select_set(True)
        context.view_layer.objects.active = main_obj
        
        
        # Enter Edit Mode on main object, select all geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        
        # Select cutters
        for cutter in cutter_objs:
            cutter.select_set(True)      

        try:
            # Attempt Knife Project
            bpy.ops.mesh.knife_project(cut_through=False)
        except RuntimeError as e:
            self.report({'ERROR'}, f"Knife Project failed: {str(e)}")
            bpy.ops.object.mode_set(mode='OBJECT')
            return {'CANCELLED'}
        
        cutter_collection = bpy.data.collections.get("Cutters")
        if not cutter_collection:
            cutter_collection = bpy.data.collections.new("Cutters")
            context.scene.collection.children.link(cutter_collection)

        for cutter in cutter_objs:
            # Remove from all existing collections
            for collection in cutter.users_collection:
                collection.objects.unlink(cutter)
            
            # Link to 'Cutters' collection
            if cutter.name not in cutter_collection.objects:
                cutter_collection.objects.link(cutter)




        
        return {'FINISHED'}

class OBJECT_OT_tag_as_cutter(bpy.types.Operator):
    bl_idname = "object.tag_as_cutter"
    bl_label = "Tag Object as Cutter"
    bl_description = "Rename selected object(s) with 'Cutter_' prefix"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objs = context.selected_objects
        if not selected_objs:
            self.report({'WARNING'}, "No object selected.")
            return {'CANCELLED'}

        for obj in selected_objs:
            if not obj.name.startswith("Cutter_"):
                obj.name = "Cutter_" + obj.name

        return {'FINISHED'}


class VIEW3D_PT_set_edge_length(Panel):
    bl_label = "Set Measure Apply"
    bl_idname = "VIEW3D_PT_set_edge_length"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object
        units = bpy.context.scene.unit_settings.system

        props = context.scene.sel_props
        tool_settings = context.tool_settings

        box = layout.box()  # big buttons aligned
        col = box.column(align=True)
        col.label(text='Edge Settings')

        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        
        if units == 'METRIC':
            row1.operator("view3d.metric_imperial_setup",
                      text = "Set Imperial",
                      icon='FULLSCREEN_EXIT')
            
        else:
            row1.operator("view3d.metric_imperial_setup",
                      text = "Set Metric", 
                      icon ='FULLSCREEN_ENTER')
                      
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        # row2.operator("render.render")
        
        if bpy.context.space_data.overlay.show_extra_edge_length == False:
            
            row2.operator("mesh.toggle_edge",
                          text="Edge Length",
                          icon='HIDE_OFF')
        else:
            row2.operator("mesh.toggle_edge",
                          text="Edge Length",
                          icon='HIDE_ON')
            
        
        
        row = col.row(align=True)
        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row1 = row.split(align=True)
        row1.prop(props, "edge_length")
        row1.operator("mesh.set_edge_length",
                        icon='FILE_ALIAS')


        row = col.row(align=True)
        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row1 = row.split(align=True)
        row1.prop(props, "constrain_to_cursor")
        row1.prop(tool_settings, "use_mesh_automerge",
                      text="Auto Merge",
                      toggle=False)
        
                      
                      
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        # row2.operator("render.render")
        row2.operator("view3d.toggle_wire",
                      text="Toggle Display Wire",
                      icon='MESH_GRID')
        row2.operator("mesh.apply_scale",
                      text="Apply Scale",
                      icon='FILE_3D')
                      
        
        
        
        box = layout.box()  # big buttons aligned
        col = box.column(align=True)
        col.label(text='Edge Primitive:')
        
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        # row2.operator("render.render")
        row2.prop(props, "edge_orientation", text="Axis")
        row2.operator("mesh.add_edge_to_edit_mesh", text="Generate Edge")
        
        
        
        col.label(text="Plane Primitive:")
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.prop(props, "plane_width", text= "Width")
        row2.prop(props, "plane_height", text= "Height")
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        #row2.operator("mesh.add_scaled_plane", icon='UV_ISLANDSEL')
        row2.prop(props, "join_plane_to_active")
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25

        row2.operator("mesh.add_scaled_plane", icon='UV_ISLANDSEL')
        #op.join_to_edit_object = True
        
        box = layout.box()  # big buttons aligned
        col = box.column(align=True)
        col.label(text='Bevel Corner Vertex')
        
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        # row2.operator("render.render")
        row2.prop(props, "bevel_width")
        row2.prop(props, "bevel_segments")
        
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        # row2.operator("render.render")
        row2.operator("mesh.vertex_bevel_custom",
                    icon='MOD_BEVEL')

# ------------------------------------
# UI Panel
# ------------------------------------
class VIEW3D_PT_knockout_panel(bpy.types.Panel):
    bl_label = "Knock-Out Cutter"
    bl_idname = "VIEW3D_PT_knockout_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.knockout_props
        
        box = layout.box()  # big buttons aligned
        col = box.column(align=True)
        #col.label(text='Bevel Corner Vertex')
        row=layout.row()
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25

        row2.prop(props, "cutter_shape")
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.prop(props, "cutter_size")
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("object.generate_cutter_instances", 
                text="Cutter(s) at Selected Vertex", 
                icon='LATTICE_DATA')
        
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        
        row2.operator("object.knife_project_cutters", 
                text="Project Cutters", 
                icon='MOD_BOOLEAN')
        
        row = col.row(align=True)
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("object.tag_as_cutter", icon='FONT_DATA')       
        
        
        
        


classes = (
    KnockoutProperties,
    OBJECT_OT_generate_cutter_instances,    
    OBJECT_OT_knife_project_cutters,
    SELProperties,
    MESH_OT_set_edge_length,
    MESH_OT_apply_scale,
    MESH_OT_toggle_edge_length,
    VIEW3D_PT_set_edge_length,
    VIEW3D_PT_knockout_panel,
    VIEW3D_OT_snap_cursor_to_selected,
    VIEW3D_OT_metric_imperial_set,
    VIEW3D_OT_toggle_wire,
    MESH_OT_vertex_bevel,
    MESH_OT_add_edge_to_edit_mesh,
    MESH_OT_add_scaled_plane,
    OBJECT_OT_tag_as_cutter
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.sel_props = PointerProperty(type=SELProperties)    
    bpy.types.Scene.knockout_props = bpy.props.PointerProperty(type=KnockoutProperties)
    
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new(
            "view3d.snap_cursor_quick",
            type='V',
            value='PRESS',
            shift=True
        )
        
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.sel_props    
    del bpy.types.Scene.knockout_props
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km in kc.keymaps:
            for kmi in km.keymap_items:
                if kmi.idname == "view3d.snap_cursor_quick":
                    km.keymap_items.remove(kmi)


if __name__ == "__main__":
    register()
