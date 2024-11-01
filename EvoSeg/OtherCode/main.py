import numpy as np
import nibabel as nib
import nrrd
from data import DataModule
from display import DisplayModule
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RangeSlider, CheckButtons

# Load the NIfTI image
nii_image = nib.load('demo data/image.nii.gz')  # Replace with your file path
ct_data = nii_image.get_fdata()
ct_data = ct_data - ct_data.min() * 1.0
ct_data = ct_data / ct_data.max()

# Load the predicted probability and the segmentation mask
data, options = nrrd.read("demo data/Selected segmentation.nrrd")
segmentation_masks = {
    "airway" : data[0, :, :, :] == 1, 
    "artery": data[2, :, :, :] == 1, 
    "vein": data[2, :, :, :] == 2
}
display_colors = {
    "airway" : [0.854902, 0.0823529, 0.768627], 
    "artery" : [0, 0.478431, 0.670588], 
    "vein": [0.729412, 0.301961, 0.25098]
}
probability_maps = {
    "airway": segmentation_masks["airway"].astype(np.float32),
    "artery": segmentation_masks["artery"].astype(np.float32),
    "vein": segmentation_masks["vein"].astype(np.float32),
}

data_module = DataModule(ct_data, segmentation_masks, probability_maps)
display_module = DisplayModule(data_module, display_colors)
display_module.show()

