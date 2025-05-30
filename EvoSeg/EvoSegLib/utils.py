import slicer
import vtk
import os
import logging

# Configure logger
logger = logging.getLogger('EvoSegLib.utils')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)  # Only show warnings and errors
    logger.propagate = False

def splitSegment(segmentationNode : slicer.vtkMRMLSegmentationNode, segmentID : str):
    segmentationNode.CreateClosedSurfaceRepresentation()
    
    bounds = [0,0,0,0,0,0]
    segmentationNode.GetBounds(bounds)
    centerX = (bounds[1] + bounds[0]) / 2

    segmentation = segmentationNode.GetSegmentation()
    segment = segmentation.GetSegment(segmentID)
    if not segment:
        logger.error(f'No segment found for ID: {segmentID}')
        return

    segmentName=segment.GetName()
    polyData = segmentationNode.GetClosedSurfaceInternalRepresentation(segmentID)
    if not polyData:
        logger.error(f'No polydata for segment {segmentID}')
        return

    displayNode=segmentationNode.GetDisplayNode()
    segmentColor=[0, 0, 0]
    displayNode.GetSegmentColor(segmentID, segmentColor)

    plane = vtk.vtkPlane()
    plane.SetOrigin(centerX, 0, 0)
    plane.SetNormal(-1, 0, 0)
    planes=vtk.vtkPlaneCollection()
    planes.AddItem(plane)
    clipperLeft = vtk.vtkClipClosedSurface()
    clipperLeft.SetInputData(polyData)
    clipperLeft.SetClippingPlanes(planes)
    clipperLeft.GenerateOutlineOn()
    clipperLeft.GenerateFacesOn()
    clipperLeft.Update()
    leftSegmentID=segmentationNode.AddSegmentFromClosedSurfaceRepresentation(clipperLeft.GetOutput(), f'{segmentName}_Left', segmentColor, f'{segmentName}_Left')

    plane = vtk.vtkPlane()
    plane.SetOrigin(centerX, 0, 0) 
    plane.SetNormal(1, 0, 0) 
    planes=vtk.vtkPlaneCollection()
    planes.AddItem(plane)
    clipperRight = vtk.vtkClipClosedSurface()
    clipperRight.SetInputData(polyData)
    clipperRight.SetClippingPlanes(planes)
    clipperRight.GenerateOutlineOn()
    clipperRight.GenerateFacesOn()
    clipperRight.Update()
    rightSegmentID=segmentationNode.AddSegmentFromClosedSurfaceRepresentation(clipperRight.GetOutput(), f'{segmentName}_Right', segmentColor, f'{segmentName}_Right')

    displayNode.SetSegmentDisplayPropertiesToDefault(leftSegmentID)
    displayNode.SetSegmentDisplayPropertiesToDefault(rightSegmentID)

    segmentation.RemoveSegment(segmentID)


def mergeSegments(segmentationNode: slicer.vtkMRMLSegmentationNode, segmentID1: str, segmentID2: str):
    segmentation = segmentationNode.GetSegmentation()
    segment1 = segmentation.GetSegment(segmentID1)
    segment2 = segmentation.GetSegment(segmentID2)

    polyData1 = segmentationNode.GetClosedSurfaceInternalRepresentation(segmentID1)
    polyData2 = segmentationNode.GetClosedSurfaceInternalRepresentation(segmentID2)

    appendFilter = vtk.vtkAppendPolyData()
    appendFilter.AddInputData(polyData1)
    appendFilter.AddInputData(polyData2)
    appendFilter.Update()
    displayNode = segmentationNode.GetDisplayNode()
    segmentColor = [0, 0, 0]
    displayNode.GetSegmentColor(segmentID1, segmentColor)

    segmentNameParts = segmentID1.split('_')
    newSegmentID = f"{segmentNameParts[0]}"

    mergedPolyData = appendFilter.GetOutput()
    newSegmentID = segmentationNode.AddSegmentFromClosedSurfaceRepresentation(
        mergedPolyData, newSegmentID, segmentColor, newSegmentID)

    displayNode.SetSegmentDisplayPropertiesToDefault(newSegmentID)

    segmentation.RemoveSegment(segmentID1)
    segmentation.RemoveSegment(segmentID2)

class MaterialPreset:
    def __init__(self, opacity, specular, specularPower, metallic, roughness):
        self.opacity = opacity
        self.specular = specular
        self.specularPower = specularPower
        self.metallic = metallic
        self.roughness = roughness

    @staticmethod
    def fromName(name):
        presets = {
            "airway": MaterialPreset(opacity=0.5, specular=0.2, specularPower=20, metallic=0.0, roughness=0.8),
            "artery": MaterialPreset(opacity=0.7, specular=0.2, specularPower=30, metallic=0.0, roughness=0.7),
            "vein": MaterialPreset(opacity=0.7, specular=0.2, specularPower=20, metallic=0.0, roughness=0.8),
            "lobe": MaterialPreset(opacity=0.5, specular=0.1, specularPower=10, metallic=0.0, roughness=0.9),
            "rib": MaterialPreset(opacity=0.7, specular=0.1, specularPower=10, metallic=0.0, roughness=0.9),
            "nodule": MaterialPreset(opacity=0.8, specular=0.2, specularPower=15, metallic=0.0, roughness=0.8),
        }
        name = name.lower()
        if "airway" in name:
            return presets["airway"]
        elif "artery" in name:
            return presets["artery"]
        elif "vein" in name:
            return presets["vein"]
        elif "lobe" in name:
            return presets["lobe"]
        elif "rib" in name:
            return presets["rib"]
        elif "nodule" in name:
            return presets["nodule"]
        else:
            return presets["default"]
    
def segments_to_assembly(segmentationNode: slicer.vtkMRMLSegmentationNode, material: MaterialPreset):
    """
    Convert segmentation node to VTK assembly with correct material, transform, and normals.
    Args:
        segmentationNode: Slicer segmentation node
        material: Material preset
    Returns:
        tuple: (node name, VTK assembly) or None if failed
    """
    if not segmentationNode:
        logger.error("Segmentation node is None")
        return None
        
    nodeName = segmentationNode.GetName()
    
    assembly = vtk.vtkAssembly()
    if hasattr(assembly, 'SetName'):
        assembly.SetName(nodeName)

    shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
    exportFolderItemId = shNode.CreateFolderItem(shNode.GetSceneItemID(), nodeName)
    
    try:
        segmentationNode.CreateClosedSurfaceRepresentation()
        
        slicer.modules.segmentations.logic().ExportAllSegmentsToModels(segmentationNode, exportFolderItemId)
        childCount = shNode.GetNumberOfItemChildren(exportFolderItemId)
        
        if childCount < 1:
            logger.warning(f"No segments found in node: {nodeName}")
            return None
        
        childIDs = vtk.vtkIdList()
        shNode.GetItemChildren(exportFolderItemId, childIDs)
        
        for i in range(childIDs.GetNumberOfIds()):
            childItemId = childIDs.GetId(i)
            dataNode = shNode.GetItemDataNode(childItemId)
            if not dataNode:
                continue
                
            try:
                if dataNode.IsA("vtkMRMLModelNode"):
                    polyData = dataNode.GetPolyData()
                    if not polyData or polyData.GetNumberOfPoints() == 0:
                        continue
                    
                    # Inline: triangle filter + normals + always flip normals
                    triangle_filter = vtk.vtkTriangleFilter()
                    triangle_filter.SetInputData(polyData)
                    triangle_filter.Update()
                    normals = vtk.vtkPolyDataNormals()
                    normals.SetInputConnection(triangle_filter.GetOutputPort())
                    normals.ConsistencyOn()
                    normals.AutoOrientNormalsOn()
                    normals.Update()
                    consistentPolyData = normals.GetOutput()
                    
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputData(consistentPolyData)
                    
                    actor = vtk.vtkActor()
                    actor.SetMapper(mapper)
                    
                    # Set material properties
                    displayNode = dataNode.GetDisplayNode()
                    if displayNode:
                        color = displayNode.GetColor()
                        actor.GetProperty().SetColor(color)
                        
                    # Set advanced material properties
                    actorProperty = actor.GetProperty()
                    actorProperty.SetOpacity(material.opacity)
                    actorProperty.SetSpecular(material.specular)
                    actorProperty.SetSpecularPower(material.specularPower)
                    if hasattr(actorProperty, 'SetMetallic'):
                        actorProperty.SetMetallic(material.metallic)
                    if hasattr(actorProperty, 'SetRoughness'):
                        actorProperty.SetRoughness(material.roughness)
                    
                    # Get transform matrix
                    try:
                        worldMatrix = vtk.vtkMatrix4x4()
                        transformNode = dataNode.GetParentTransformNode()
                        if transformNode:
                            transformNode.GetMatrixTransformToWorld(worldMatrix)
                            if not worldMatrix.IsIdentity():
                                actorMatrix = vtk.vtkMatrix4x4()
                                actorMatrix.DeepCopy(worldMatrix)
                                actor.SetUserMatrix(actorMatrix)
                    except Exception as e:
                        logger.warning(f"Failed to get transform for node {dataNode.GetName()}: {e}")
                    
                    assembly.AddPart(actor)
            finally:
                if dataNode:
                    slicer.mrmlScene.RemoveNode(dataNode)
    finally:
        shNode.RemoveItem(exportFolderItemId)
        
    return (nodeName, assembly)


def export_segmentations_as_gltf(segmentationNodes: list[slicer.vtkMRMLSegmentationNode], filename: str):
    # Input validation
    if not segmentationNodes:
        logger.error("No segmentation nodes provided")
        return False
        
    if not filename:
        logger.error("No filename provided")
        return False
    
    if not (filename.lower().endswith('.gltf') or filename.lower().endswith('.glb')):
        logger.error("Filename must have .gltf or .glb extension")
        return False
    
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Cannot create output directory {output_dir}: {e}")
            return False
    
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    
    try:
        renderer.SetBackground(0.1, 0.1, 0.1)
        renderer.SetUseFXAA(True)
        renderWindow.SetSize(1024, 1024)

        actorCount = 0
        for segmentationNode in segmentationNodes:
            if not segmentationNode:
                continue
                
            material = MaterialPreset.fromName(segmentationNode.GetName())
            result = segments_to_assembly(segmentationNode, material)
            if result is None:
                continue
            (_, assembly) = result
            renderer.AddActor(assembly)
            actorCount += 1

        if actorCount == 0:
            logger.warning("No valid segmentations in scene")
            return False

        renderer.ResetCamera()
        renderer.GetActiveCamera().Azimuth(45)
        renderer.GetActiveCamera().Elevation(30)

        exporter = vtk.vtkGLTFExporter()
        exporter.SetFileName(filename)
        exporter.SetRenderWindow(renderWindow)
        exporter.InlineDataOn()
        exporter.SaveNormalOn()
        
        try:
            exporter.Write()
            return True
        except Exception as e:
            logger.error(f"Failed to write GLTF file: {e}")
            return False
            
    finally:
        renderWindow.Finalize() 
        del renderWindow 