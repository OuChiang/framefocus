import bpy
import json
import os


# [ Props ]
class FRAMEFOCUS_Props(bpy.types.PropertyGroup):
    is_color_panel : bpy.props.BoolProperty(name='use color panel', default=False)
    picker_mode : bpy.props.IntProperty(name='use mode', default=0)
    panel_mode : bpy.props.EnumProperty(items =[('0','None','None','NONE',0),
                                                ('1','Look','Look','HIDE_OFF',1),
                                                ('2','Word','Word','OUTLINER_OB_FONT',2)],
                                        name='panel mode',default = 0)

class FRAMEFOCUS_OT_SelectAll(bpy.types.Operator):
    """Select All Frames / Deselect"""
    bl_idname = "frame_focus.select_all"
    bl_label = "Select All Frames / Deselect"
    def execute(self, context):
        snode = context.space_data
        Nodes = snode.edit_tree.nodes
        Fms = [fm for fm in Nodes if fm.type == 'FRAME']

        # Check is no frame selected
        isNoSel = True
        for Fm in Fms:
            if Fm.select:
                isNoSel = False
                break
        
        bpy.ops.node.select_all(action='DESELECT')
        for Fm in Fms:
            Fm.select = isNoSel
            Nodes.active = None if isNoSel else Fms[0]

        return {'FINISHED'}


class FRAMEFOCUS_OT_Focus(bpy.types.Operator):
    """Focus Frames"""
    bl_idname = "frame_focus.frame_focus"
    bl_label = "Frame Focus"
    frame : bpy.props.StringProperty(default="")
    def execute(self, context):
        snode = context.space_data
        Nodes = snode.edit_tree.nodes
        Sels = [nd for nd in Nodes if nd.select]

        bpy.ops.node.select_all(action='DESELECT')

        Nodes[self.frame].select=1
        bpy.ops.node.view_selected()
        Nodes[self.frame].select=0

        for Node in Nodes[:]:
            Node.select= Node in Sels

        return {'FINISHED'}
    
class FRAMEFOCUS_OT_Reorder(bpy.types.Operator):
    """Reorder Frames By Label / Color( Hue ) / Reverse"""
    bl_idname = "frame_focus.reorder"
    bl_label = "Reorder Frames By Label / Color(Hue)"
    useType : bpy.props.EnumProperty(items = [('0','Label',''),('1','Color(Hue)',''),('2','Reverse','')],default='0')
    is_invert :  bpy.props.BoolProperty(default=False)
    def execute(self, context):
        snode = context.space_data
        Nodes = snode.edit_tree.nodes
        Frames = sorted([fm.name for fm in Nodes if (fm.type=='FRAME')])
        sel_fms = sorted([fm for fm in Frames  if Nodes[fm].select ])
        unSel_fms= [fm for fm in Frames  if not Nodes[fm].select ]

        if self.useType=='0':
            sel_fms.sort(key=lambda x :Nodes[x].label,reverse=self.is_invert)
        if self.useType=='1':
            def color_value(Col):
                H,S,V = Col.hsv
                H,S,V = 1-H,1-S,1-V
                HSV = int(H*255)*(10**6)+int(V*255)*(10**3)+int(S*255)
                return HSV
            sel_fms.sort(key=lambda x :color_value(Nodes[x].color),reverse=not self.is_invert)
        
        if self.useType=='2':
            sel_fms.sort(reverse=True)

        for i,fm in enumerate(Frames):
            if fm in unSel_fms:
                sel_fms.insert(i,fm)
        # Rename
        newList = []
        Length = len(str(len(sel_fms)))
        for i,Node in enumerate(sel_fms):
            newName = '_fm_'+str(i).rjust(Length,'0')
            Nodes[Node].name = newName
            newList.append(newName)
        for fm in newList:
            Nodes[fm].name =fm[1:]
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self,'useType',text='Order By')
        if self.useType =='2':
            return None
        row = layout.row()
        row.alignment = 'RIGHT'
        row.prop(self,'is_invert',text='Use Invert')

class FRAMEFOCUS_OT_Walk(bpy.types.Operator):
    """Frames Order Walk"""
    bl_idname = "frame_focus.frame_walk"
    bl_label = "Frames Order Walk"
    walk_type : bpy.props.StringProperty(default='WALK_UP')
    def execute(self, context):
        snode = context.space_data
        Nodes = snode.edit_tree.nodes

        Frames = sorted([ fm.name for fm in Nodes[:] if fm.type=='FRAME'])
        selected_frames = sorted([fm.name for fm in Nodes if (fm.type=='FRAME')and(fm.select) ])
        

        def id_walk(item,upDown):
            fm_id = Frames.index(item)
            walk_id = fm_id-1 if upDown else fm_id+1
            Frames.remove(item)
            Frames.insert(walk_id,item)

        def WALK_UP():
            Frames.insert(0,'frame_focus_TEMP_FOR_WALK_TOP')
            Frames.append('frame_focus_TEMP_FOR_WALK_BTM')
            for fm in selected_frames:
                id_walk(fm,True)
            Frames.remove('frame_focus_TEMP_FOR_WALK_TOP')
            Frames.remove('frame_focus_TEMP_FOR_WALK_BTM')

        def WALK_DOWN():
            Frames.insert(0,'frame_focus_TEMP_FOR_WALK_TOP')
            Frames.append('frame_focus_TEMP_FOR_WALK_BTM')
            selected_frames.reverse()
            for fm in selected_frames:
                id_walk(fm,False)
            Frames.remove('frame_focus_TEMP_FOR_WALK_TOP')
            Frames.remove('frame_focus_TEMP_FOR_WALK_BTM')
        
        def TO_TOP():
            for fm in selected_frames[::-1]:
                Frames.remove(fm)
                Frames.insert(0,fm)
        
        def TO_BOTTOM():
            for fm in selected_frames:
                Frames.remove(fm)
                Frames.append(fm)
        WALK_TYPE = {
            'WALK_UP':WALK_UP,
            'WALK_DOWN':WALK_DOWN,
            'TO_TOP':TO_TOP,
            'TO_BOTTOM':TO_BOTTOM
            }
        WALK_TYPE[self.walk_type]()

        Length = len(str(len(Frames)))
        newList = []
        for i,Node in enumerate(Frames):
            newName = '_fm_'+str(i).rjust(Length,'0')
            Nodes[Node].name = newName
            newList.append(newName)
        for fm in newList:
            Nodes[fm].name =fm[1:]

        return {'FINISHED'}

class FRAMEFOCUS_OT_Batch_UseCustomColor(bpy.types.Operator):
    """Batch Set Use Color Of Selected Frames"""
    bl_idname = "frame_focus.frame_batch_use_custom_color"
    bl_label = "Batch Custom Color"
    frame : bpy.props.StringProperty(default="")
    def execute(self, context):
        snode = context.space_data
        #Tree = snode.edit_tree
        Nodes = snode.edit_tree.nodes
        
        Fms = [Node for Node in Nodes if (Node.select) and (Node.type=='FRAME')]
        isAllTrue = False if False in [Fm.use_custom_color for Fm in Fms] else True
        for Fm in Fms:
            Fm.use_custom_color = not isAllTrue
            
        return {'FINISHED'}

class FRAMEFOCUS_OT_Batch_Shrink(bpy.types.Operator):
    """Batch Set Shrink Of Selected Frames"""
    bl_idname = "frame_focus.frame_batch_shrink"
    bl_label = "Batch Set Shrink"
    frame : bpy.props.StringProperty(default="")
    def execute(self, context):
        snode = context.space_data
        Nodes = snode.edit_tree.nodes
        
        Fms = [Node for Node in Nodes if (Node.select) and (Node.type=='FRAME')]
        isAllTrue = False if False in [Fm.shrink for Fm in Fms] else True
        for Fm in Fms:
            Fm.shrink = not isAllTrue
            
        return {'FINISHED'}
    
# [ Panel ]

def frames_list(context):
    try :
        Nodes = context.space_data.edit_tree.nodes
        frames = [ fm for fm in Nodes if fm.type=='FRAME']
        return frames
    except:
        return None

# Main 
class FRAMEFOCUS_PT_Main(bpy.types.Panel):
    bl_idname = "FRAMEFOCUS_PT_Main"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Frames"
    bl_label = ''
    bl_options = {'HEADER_LAYOUT_EXPAND',}

    def draw_header(self, context):
        layout =self.layout
        row=layout.row()
        row.alignment='LEFT'
        row.label( text="Frames Focus",icon = "IMAGE_ZDEPTH")
    def draw(self, context):
        layout = self.layout
        Tree = context.space_data.edit_tree
        
        if not Tree:
            row = layout.row()
            row.enabled = False
            row.label(text='No Any Node Tree Actived' , icon = 'ERROR')
            return None
        frames = frames_list(context)
        fm_col = context.scene.frame_focus
        box_main = layout.box()
        row = box_main.row()
        draw_function_bar_L(row, frames)

        pie_M = row.menu_pie()
        pie_M.alignment='CENTER'
        row_M = pie_M.row(align=True)
        row_M.prop(fm_col,'panel_mode',text='')

        pie_R = row.menu_pie()
        pie_R.alignment='RIGHT'
        pie_R.enabled = len(frames)>0
        draw_function_bar_R(pie_R)

def draw_function_bar_L(layout,frames):
    hasFrame = len(frames)>0
    isNoSelected = True in [fm.select for fm in frames]
    isAllCustomColor= False not in [fm.use_custom_color for fm in frames if fm.select]
    isAllShrink= False not in [fm.shrink for fm in frames if fm.select]

    row = layout.row()
    pie_L = row.menu_pie()
    pie_L.alignment='LEFT'
    row_L = pie_L.row(align=True)
    
    pie_L_0 = row_L.menu_pie()
    pie_L_0.enabled = hasFrame
    selAll_icon = 'RADIOBUT_OFF' if isNoSelected else 'RADIOBUT_ON'
    pie_L_0.operator("frame_focus.select_all",text='',icon=selAll_icon)
    
    pie_L_1 = row_L.menu_pie()
    pie_L_1.operator("frame_color.color_panel",text='',icon="GROUP_VCOL")

    pie_L_2 = row_L.menu_pie()
    pie_L_2.enabled = hasFrame
    cusCol_icon = 'RESTRICT_COLOR_OFF' if isAllCustomColor else 'RESTRICT_COLOR_ON'
    pie_L_2.operator("frame_focus.frame_batch_use_custom_color",text='',icon=cusCol_icon)

    pie_L_3 = row_L.menu_pie()
    pie_L_3.enabled = hasFrame
    shrink_icon = 'FULLSCREEN_EXIT' if isAllShrink else "MOD_LENGTH"
    pie_L_3.operator("frame_focus.frame_batch_shrink",text='',icon=shrink_icon)

    pie_L_4 = row_L.menu_pie()
    pie_L_4.operator('node.view_selected',icon='ZOOM_SELECTED',text='')


def draw_function_bar_R(Layout):
    row_R = Layout.row(align=True)
    row_R.operator("frame_focus.reorder",text='',icon='SEQ_STRIP_DUPLICATE')
    walk_types = {'TO_TOP':'TRIA_UP_BAR',
                  'WALK_UP' :'TRIA_UP',
                  'WALK_DOWN':'TRIA_DOWN',
                  'TO_BOTTOM':'TRIA_DOWN_BAR'
                  }
    for key ,item in walk_types.items():
        btn =row_R.operator("frame_focus.frame_walk",text='',icon=item)
        btn.walk_type=key

    return Layout



class FRAMEFOCUS_PT_Frame_Bar(bpy.types.Panel):
    bl_idname = "FRAMEFOCUS_PT_Frame_Bar"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Frames"
    bl_label = ''
    bl_options = {'HIDE_HEADER'}
    bl_parent_id = "FRAMEFOCUS_PT_Main"
    @classmethod
    def poll(cls, context):
        return frames_list(context)
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        PANEL_TYPE = {
            '0':panelMode_none,
            '1':panelMode_look,
            '2':panelMode_word
        }
        panelMode_id = context.scene.frame_focus.get('panel_mode',0)
        frames = frames_list(context)
        if not frames:
            return None
        frames.sort(key = lambda x : x.name)
        for fm in frames:
            box = col.box()
            boxRow = box.row(align=True)
            PANEL_TYPE[str(panelMode_id)](boxRow,fm)

def panelMode_none(Layout,Node):
    select_icon = 'RADIOBUT_ON' if Node.select else 'RADIOBUT_OFF'
    Layout.prop(Node,'select',text='',emboss=False,icon=select_icon)
    Layout.prop(Node, "color", text="",icon='DOT')
    Layout.operator("frame_focus.frame_focus",text=Node.label,emboss=True).frame=Node.name

def panelMode_look(Layout,Node):
    select_icon = 'RADIOBUT_ON' if Node.select else 'RADIOBUT_OFF'
    Layout.prop(Node,'select',text='',emboss=False,icon=select_icon)
    Layout.prop(Node, "color", text="",icon='DOT')
    Layout.prop(Node, "use_custom_color", text="",icon='RESTRICT_COLOR_ON',emboss=True)
    Layout.prop(Node, "shrink", text="",icon='MOD_LENGTH')
    Layout.operator("frame_focus.frame_focus",text=Node.label,emboss=True).frame=Node.name

def panelMode_word(Layout,Node):
    select_icon = 'RADIOBUT_ON' if Node.select else 'RADIOBUT_OFF'
    Layout.prop(Node,'select',text='',emboss=False,icon=select_icon)
    Layout.prop(Node, "color", text="",icon='DOT')
    split = Layout.split(factor=0.25,align=True)
    split.prop(Node, "label_size", text="",icon='NONE',slider=False) 
    split.prop(Node, "label", text="")
    split.prop(Node, "text", text="",icon='TEXT')
    pie = Layout.menu_pie()
    pie.operator("frame_focus.frame_focus",text='',icon='ZOOM_SELECTED').frame=Node.name


classes = (
    FRAMEFOCUS_OT_Focus,
    FRAMEFOCUS_OT_SelectAll,
    FRAMEFOCUS_OT_Walk,
    FRAMEFOCUS_OT_Reorder,
    FRAMEFOCUS_OT_Batch_UseCustomColor,
    FRAMEFOCUS_OT_Batch_Shrink,
    FRAMEFOCUS_PT_Main,
    FRAMEFOCUS_PT_Frame_Bar,
)

def register():
    bpy.utils.register_class(FRAMEFOCUS_Props)
    bpy.types.Scene.frame_focus = bpy.props.PointerProperty(type= FRAMEFOCUS_Props)
    for cls in classes:
        bpy.utils.register_class(cls)
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.frame_focus
    bpy.utils.unregister_class(FRAMEFOCUS_Props)

