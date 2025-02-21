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
        print('splitSegment no segment found')
        return

    segmentName=segment.GetName()
    polyData = segmentationNode.GetClosedSurfaceInternalRepresentation(segmentID)
    if not polyData:
        print('splitSegment no polyData found')
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