import bpy
import bmesh
from math import degrees
from math import radians
from mathutils import Vector
from . import DUV_Utils

def unwrapisland():

    bpy.ops.view3d.dreamuv_uvboxmap()

    obj = bpy.context.view_layer.objects.active
    bm = bmesh.from_edit_mesh(obj.data)

    #GET LARGEST FACE

    #set initial face
    largest_face = bm.faces[0]
    for f in bm.faces:
        if f.select is True:
            largest_face = f
    #grab largest
    for f in bm.faces:
        if f.select is True:
            if f.calc_area() > largest_face.calc_area():
                largest_face = f
        #print(f.calc_area())

    #make largest active
    bm.faces.active = largest_face
    uv_layer = bm.loops.layers.uv.active
    bpy.ops.uv.select_all(action='DESELECT')

    #select largest face island
    for l in largest_face.loops:
        #print(l)
        l[uv_layer].select = True
        
    #select linked, and pin
    #THIS IS OPTIONAL! but gives results closer to box map
    bpy.ops.uv.select_linked()

                
    bpy.ops.uv.pin(clear=False)
    bpy.ops.uv.unwrap(method='CONFORMAL', margin=0.001)
    bpy.ops.uv.pin(clear=True)

    print("wrapped island!")

    return None

def main(context):
    
    #check for object or edit mode:
    objectmode = False
    if bpy.context.object.mode == 'OBJECT':
        objectmode = True
        #switch to edit and select all
        bpy.ops.object.editmode_toggle() 
        bpy.ops.mesh.select_all(action='SELECT')
        
    #CREATE WORKING DUPLICATE!
    object_original = bpy.context.view_layer.objects.active
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.duplicate()

    bpy.ops.object.editmode_toggle()
    bpy.context.view_layer.objects.active.name = "dreamuv_temp"
    object_temporary = bpy.context.view_layer.objects.active
        
    #PREPROCESS - save seams and hard edges

    #first apply hard edges? might have to duplicate object for this
    #temp apply hard edges, return them back later
    bpy.ops.object.modifier_copy(modifier="Smooth by Angle")
    bpy.context.view_layer.objects.active.modifiers.active.name = "boxmapedges"
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.modifier_apply(modifier="boxmapedges")
    bpy.ops.object.editmode_toggle()

    obj = bpy.context.view_layer.objects.active
    bm = bmesh.from_edit_mesh(obj.data)

    faces = list()
    for face in bm.faces:
        if face.select:
            faces.append(face)

    backupseams = list()
    for edge in bm.edges:
        isSeam = edge.seam
        backupseams.append(isSeam)

    bpy.ops.mesh.select_all(action='DESELECT')

    obj = bpy.context.view_layer.objects.active
    bm = bmesh.from_edit_mesh(obj.data)

    for edge in bm.edges:
        if edge.smooth is False:
            edge.select = True

    bpy.ops.mesh.mark_seam(clear=False)
    bpy.ops.mesh.select_all(action='DESELECT')

    #select all faces to be hotspotted again:
    #obj = bpy.context.view_layer.objects.active
    #bm = bmesh.from_edit_mesh(obj.data)
    for face in faces:
        face.select = True

    #PREPROCESS - find islands
    #save a backup of UV
    uv_layer = bm.loops.layers.uv.verify()
    uv_backup = list();
    for face in bm.faces:
        backupface = list()
        for vert in face.loops:
            backupuv = list()
            backupuv.append(vert[uv_layer].uv.x)
            backupuv.append(vert[uv_layer].uv.y)
            backupface.append(backupuv)
        uv_backup.append(backupface)

    #create islands
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.uv.unwrap(method='CONFORMAL', margin=1.0)
    obj = bpy.context.view_layer.objects.active
    bm = bmesh.from_edit_mesh(obj.data)
    #list islands
    #iterate using select linked uv

    islands = list()        
    tempfaces = list()
    updatedfaces = list()
    #MAKE FACE LIST
    for face in bm.faces:
        if face.select:
            updatedfaces.append(face)
            tempfaces.append(face)
            face.select = False
        

    while len(tempfaces) > 0:

        updatedfaces[0].select = True

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_linked(delimit={'UV'})
        obj = bpy.context.view_layer.objects.active
        bm = bmesh.from_edit_mesh(obj.data)

        islandfaces = list()
        for face in bm.faces:
            if face.select:
                islandfaces.append(face)

        islands.append(islandfaces)

        #create updated list
        tempfaces.clear()
        for face in updatedfaces:
            if face.select == False:
                tempfaces.append(face)
            else:
                face.select = False 
        #make new list into updated list
        updatedfaces.clear()
        updatedfaces = tempfaces.copy()

    print(islands)
    print(len(islands))

    #now iterate and boxwrap each island
    for island in islands:
        for face in island:
            face.select = True
        print("unwrapping!")
        unwrapisland()
        for face in island:
            face.select = False

    #NOW RETURN UV DATA AND DELETE temp object

    #transfer UV maps back to original mesh
        
    obj = bpy.context.view_layer.objects.active
    bm = bmesh.from_edit_mesh(obj.data) 
    uv_layer = bm.loops.layers.uv.verify()
    uv_backup = list();
    #print("new UV:")
    for face in bm.faces:
        backupface = list()
        for vert in face.loops:
            backupuv = list()
            backupuv.append(vert[uv_layer].uv.x)
            backupuv.append(vert[uv_layer].uv.y)
            backupface.append(backupuv)
            #print(backupuv)
        uv_backup.append(backupface)
        
    #now apply to original mesh
    bpy.ops.object.editmode_toggle()
    object_temporary.select_set(False)
    object_original.select_set(True)
    bpy.ops.object.editmode_toggle()

    obj = object_original
    bm = bmesh.from_edit_mesh(obj.data) 
    uv_layer = bm.loops.layers.uv.verify()
    #uv_backup = list();
    #print("new UV:")
    for face, backupface in zip(bm.faces, uv_backup):
        for vert, backupuv in zip(face.loops, backupface):
            vert[uv_layer].uv.x = backupuv[0]
            vert[uv_layer].uv.y = backupuv[1]
    bmesh.update_edit_mesh(obj.data)
        
    bpy.ops.object.editmode_toggle() 
        
    object_original.select_set(False)
    object_temporary.select_set(True)
    bpy.ops.object.delete(use_global=False)
    object_original.select_set(True)
    context.view_layer.objects.active=object_original

    #unwrapisland()
    
    if objectmode is False:
        print("switch to object mode")
        bpy.ops.object.editmode_toggle() 
        
    #normalize islands:
    DUV_Utils.normalize_islands(context)

class DREAMUV_OT_uv_boxwrap(bpy.types.Operator):
    """Unwrap using a box shape"""
    bl_idname = "view3d.dreamuv_uvboxwrap"
    bl_label = "box wrap"
    
    def execute(self, context):
        #remember selected uv
        uv_index = bpy.context.view_layer.objects.active.data.uv_layers.active_index
        if context.scene.duv_boxmap_uv1 == True:
            bpy.context.view_layer.objects.active.data.uv_layers.active_index = 0
            main(context)
        if context.scene.duv_boxmap_uv2 == True:    
            bpy.context.view_layer.objects.active.data.uv_layers.active_index = 1
            main(context)
        if context.scene.duv_boxmap_uv1 == False and context.scene.duv_boxmap_uv2 == False:
            #just uv selected uv
            main(context)
        #reset selected uv
        bpy.context.view_layer.objects.active.data.uv_layers.active_index = uv_index

        return {'FINISHED'}