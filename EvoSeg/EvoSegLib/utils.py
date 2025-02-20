import slicer
import vtk

def splitSegment(segmentationNode : slicer.vtkMRMLSegmentationNode, segmentID : str):
    segmentationNode.CreateClosedSurfaceRepresentation()
    
    bounds = [0,0,0,0,0,0]
    segmentationNode.GetBounds(bounds)
    centerX = (bounds[1] + bounds[0]) / 2

    segmentation = segmentationNode.GetSegmentation()
    segment = segmentation.GetSegment(segmentID)
    if not segment:
        return

    segmentName=segment.GetName()
    polyData = segmentationNode.GetClosedSurfaceInternalRepresentation(segmentID)
    if not polyData:
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
    segmentationNode.AddSegmentFromClosedSurfaceRepresentation(clipperLeft.GetOutput(), f'{segmentName}_Left', segmentColor)

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
    segmentationNode.AddSegmentFromClosedSurfaceRepresentation(clipperRight.GetOutput(), f'{segmentName}_Right', segmentColor)

    segmentation.RemoveSegment(segmentID)