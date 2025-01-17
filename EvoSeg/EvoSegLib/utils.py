import slicer
import SegmentStatistics
import numpy as np

def obbDiameterMm(segmentationNode : slicer.vtkMRMLSegmentationNode, segmentId : str):
    segStatLogic = SegmentStatistics.SegmentStatisticsLogic()
    segStatLogic.getParameterNode().SetParameter("Segmentation", segmentationNode.GetID())
    segStatLogic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.obb_diameter_mm.enabled",str(True))
    segStatLogic.computeStatistics()
    stats = segStatLogic.getStatistics()
    obb_diameter_mm = np.array(stats[segmentId,"LabelmapSegmentStatisticsPlugin.obb_diameter_mm"])
    return obb_diameter_mm