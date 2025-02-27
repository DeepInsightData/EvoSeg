import SimpleITK as sitk
from scipy.ndimage import label, binary_dilation
import numpy as np
from skimage.measure import label, regionprops
import argparse

def detect_small_regions(slice_2d, area_threshold):
    labeled_slice = label(slice_2d)
    regions = regionprops(labeled_slice)
    small_regions_mask = np.zeros_like(slice_2d)
    for region in regions:
        if region.area < area_threshold:
            coords = region.coords
            small_regions_mask[coords[:, 0], coords[:, 1]] = 1
    return small_regions_mask

def dilate_3d(voxels, kernel_size=3):
    kernel = np.ones((kernel_size, kernel_size, kernel_size))
    dilated_voxels = binary_dilation(voxels, structure=kernel)
    return dilated_voxels

def process_mask_3d(mask_3d, area_threshold=1, kernel_size=2):
    """
    处理3D分割mask的三视角连通域膨胀
    
    参数：
    mask_3d: 3D binary numpy array (H x W x D)
    area_threshold: 连通域面积阈值
    dilation_iter: 膨胀次数
    
    返回：
    处理后的3D mask
    """
    # 初始化结果
    total_mask = np.zeros_like(mask_3d)

    # 轴向处理 (axis 0)
    for z in range(mask_3d.shape[0]):
        slide = mask_3d[z]
        slide_mask = detect_small_regions(slide, area_threshold)
        total_mask[z] = total_mask[z] | slide_mask

    # 冠状面处理 (axis 1)
    for y in range(mask_3d.shape[1]):
        # process_slice(mask_3d[:, y, :], coronal_result[:, y, :], area_threshold, struct, dilation_iter)
        slide = mask_3d[:, y, :]
        slide_mask = detect_small_regions(slide, area_threshold)
        total_mask[:, y, :] = total_mask[:, y, :] | slide

    # 矢状面处理 (axis 2)
    for x in range(mask_3d.shape[2]):
        # process_slice(mask_3d[:, :, x], sagittal_result[:, :, x], area_threshold, struct, dilation_iter)
        slide = mask_3d[:, :, x]
        slide_mask = detect_small_regions(slide, area_threshold)
        total_mask[:, :, x] = total_mask[:, :, x] | slide

    # 进行膨胀操作
    final_mask = dilate_3d(total_mask, kernel_size=kernel_size)
    return final_mask | mask_3d

if __name__ == "__main__":
    # 解析输入参数
    parser = argparse.ArgumentParser(description="Post-process 3D segmentation mask")
    parser.add_argument("--mask_path", type=str, required=True, help="Path to the input mask file")
    parser.add_argument("--output_path", type=str, required=True, help="Path to save the processed mask file")
    parser.add_argument("--kernel_size", type=int, default=2, help="Kernel size for dilation")
    args = parser.parse_args()

    # 读取mask
    mask = sitk.ReadImage(args.mask_path)
    mask_3d = sitk.GetArrayFromImage(mask)

    # 后处理
    final_mask = process_mask_3d(mask_3d, area_threshold=1, kernel_size=args.kernel_size)

    # 保存mask
    final_mask = sitk.GetImageFromArray(final_mask)
    final_mask.CopyInformation(mask)
    sitk.WriteImage(final_mask, args.output_path)