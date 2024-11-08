import bpy
import json
import os
from bpy.types import Panel, Operator, Menu, PropertyGroup
from bl_operators.presets import AddPresetBase

# Color Set
preset_colors = [
        [0.4,0.08,0.08],[0.4,0.25,0.0],[0.4,0.4,0.0],
        [0.15,0.4,0.08],[0.08,0.4,0.4],[0.08,0.2,0.4],
        [0.2,0.08,0.4],[0.45,0.09,0.3],[0.3,0.3,0.3]
]

# [ Props ]
class FRAMEFOCUS_ColorEdit_Props(bpy.types.PropertyGroup):
    def define_color_prop(id):
        return bpy.props.FloatVectorProperty(name=f'color_{id-1}',
                                      min=0.0,max=1.0,subtype='COLOR_GAMMA',
                                      default=preset_colors[id-1])


    color_1 : define_color_prop(1)
    color_2 : define_color_prop(2)
    color_3 : define_color_prop(3)
    color_4 : define_color_prop(4)
    color_5 : define_color_prop(5)
    color_6 : define_color_prop(6)
    color_7 : define_color_prop(7)
    color_8 : define_color_prop(8)
    color_9 : define_color_prop(9)

    open_perference : bpy.props.BoolProperty(name='Open Preference',default=False)
    frames_only : bpy.props.BoolProperty(name='use all node',default=True)


# [ Preset ]
#  --- Preset ---
class FRAMEFOCUS_MT_Palette_Preset(Menu):
    bl_label = "Focus Color Settings"
    preset_subdir = "scene/frame_color"
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset

class FRAMEFOCUS_OT_Palette_Preset(AddPresetBase, bpy.types.Operator):
    """Palette Preset Add & Remove"""
    bl_idname = "frame_color.palette"
    bl_label = "Palette Presets"
    preset_menu = "FRAMEFOCUS_MT_Palette_Preset"
    preset_defines = ["frame_color = bpy.context.scene.frame_color"]
    preset_values = [f"frame_color.color_{str(i)}" for i in range(1,10)]
    preset_subdir = "scene/frame_color"

class FRAMEFOCUS_OT_Palette_Reset(bpy.types.Operator):
    """Reset Color Set"""
    bl_idname = "frame_color.palette_reset"
    bl_label = "Reset Palette"
    def execute(self, context):
        Props = context.scene.frame_color
        Props.color_1 = [0.4,0.08,0.08]
        Props.color_2 = [0.4,0.25,0.0]
        Props.color_3 = [0.4,0.4,0.0]
        Props.color_4 = [0.15,0.4,0.08]
        Props.color_5 = [0.08,0.4,0.4]
        Props.color_6 = [0.08,0.2,0.4]
        Props.color_7 = [0.2,0.08,0.4]
        Props.color_8 = [0.45,0.09,0.3]
        Props.color_9 = [0.3,0.3,0.3]
        return {'FINISHED'}

def node_list(context,frame_only):
    Tree = context.space_data.edit_tree
    if not Tree:
        return None
    Nodes = Tree.nodes
    if not Nodes:
        return None
    if not frame_only:
        return [ nd for nd in Nodes if nd.select]
    return [ nd for nd in Nodes if nd.select and nd.type=='FRAME']

#[ Operator ]
class FRAMEFOCUS_OT_Color_Set_Default(bpy.types.Operator):
    """Reset Selected Frames Color To Default"""
    bl_idname = "frame_color.color_set_default"
    bl_label = "Set Default Color"
    def execute(self, context):
        colorEditor = context.scene.frame_color
        Nodes = node_list(context,colorEditor.frames_only)
        for nd in Nodes:
            nd.color = [0.327964, 0.327964, 0.327964]#[0.188, 0.188, 0.188]
        return {'FINISHED'}

class FRAMEFOCUS_OT_Color_Enabled(bpy.types.Operator):
    """Selected Nodes (Not) Use Custom Color"""
    bl_idname = "frame_color.color_enabled"
    bl_label = "Node\'s Color Enable"
    use_custom_color : bpy.props.BoolProperty(default=True)
    def execute(self, context):
        colorEditor = context.scene.frame_color
        Nodes = node_list(context,colorEditor.frames_only)
        for nd in Nodes:
            nd.use_custom_color = self.use_custom_color
        return {'FINISHED'}
    

class FRAMEFOCUS_OT_Color_Set(bpy.types.Operator):
    """Set Selected Nodes Color"""
    bl_idname = "frame_color.set_color"
    bl_label = "Set Color "
    setColor : bpy.props.FloatVectorProperty(default=[0,0,0])
    def execute(self, context):
        colorEditor = context.scene.frame_color
        Nodes = node_list(context,colorEditor.frames_only)
        for nd in Nodes:
            nd.color = self.setColor
        return {'FINISHED'}

# Color Set Panel
class FRAMEFOCUS_OT_Color_panel(bpy.types.Operator):
    """Node Color Panel"""
    bl_idname = "frame_color.color_panel"
    bl_label = "Set Selected Frames Color Panel"

    def execute(self, context):
        return {'FINISHED'}
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)
        
    def draw(self, context):
        Layout = self.layout
        Props = context.scene.frame_color
        # Preset 
        Preset_row = Layout.row(align=True)
        Preset_row.menu(FRAMEFOCUS_MT_Palette_Preset.__name__,text =FRAMEFOCUS_MT_Palette_Preset.bl_label)
        Preset_row.operator(FRAMEFOCUS_OT_Palette_Preset.bl_idname, text="", icon='ZOOM_IN')
        Preset_row.operator(FRAMEFOCUS_OT_Palette_Preset.bl_idname, text="", icon='ZOOM_OUT').remove_active = True
        Preset_row.operator("frame_color.palette_reset",text='',icon='LOOP_BACK')
        
        # Frames Only
        LowRow = Layout.row()
        pie_L = LowRow.menu_pie()
        pie_L.alignment='LEFT'
        pie_L.prop(Props,'frames_only',text='Frames Only')

        # Use Custom Color
        Layout.separator(factor=1.0,type='LINE')
        row_useCol = Layout.row(align=True)
        row_useCol.alignment='LEFT'
        row_useCol.label(text='Custom Color')
        row_useCol.operator("frame_color.color_enabled",text='',icon='CHECKBOX_HLT').use_custom_color = True
        row_useCol.operator("frame_color.color_enabled",text='',icon='CHECKBOX_DEHLT').use_custom_color = False
        
        # Colors
        Layout.separator(factor=1.0)
        colorsRow = Layout.row()
        for i in range(1,10):
            col = colorsRow.column(align=True)
            col.prop(context.scene.frame_color,f'color_{i}',text='')
            Color = getattr(Props, f"color_{str(i)}", [0,0,0])
            btn_setColor =col.operator("frame_color.set_color",icon='EYEDROPPER')
            btn_setColor.setColor=Color
        
        # Clear Color
        pie_cleanColor = Layout.menu_pie()
        pie_cleanColor.alignment = 'RIGHT'
        pie_cleanColor.operator("frame_color.color_set_default",text='Default Color',icon='LOOP_BACK')#.frameOnly = useFrameOnly


classes = [
    FRAMEFOCUS_MT_Palette_Preset,
    FRAMEFOCUS_OT_Palette_Preset,
    FRAMEFOCUS_OT_Palette_Reset,
    FRAMEFOCUS_OT_Color_Set_Default,
    FRAMEFOCUS_OT_Color_Enabled,
    FRAMEFOCUS_OT_Color_Set,
    FRAMEFOCUS_OT_Color_panel, 
    ]

def register():
    bpy.utils.register_class(FRAMEFOCUS_ColorEdit_Props)
    bpy.types.Scene.frame_color = bpy.props.PointerProperty(type= FRAMEFOCUS_ColorEdit_Props)
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.frame_color
    bpy.utils.unregister_class(FRAMEFOCUS_ColorEdit_Props)
