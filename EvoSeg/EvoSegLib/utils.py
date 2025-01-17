import slicer

def max_diameter_of_segmentation(segmentation_node : slicer.vtkMRMLSegmentationNode, segment_id : str):
    segment = segmentation_node.GetSegmentation().GetSegment(segment_id)
    bounds = [0] * 6
    segment.GetBounds(bounds)
    max_diameter = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
    return max_diameter