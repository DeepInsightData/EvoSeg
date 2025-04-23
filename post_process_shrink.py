import SimpleITK as sitk
import numpy as np
import argparse
from skimage.measure import label, regionprops
from scipy.ndimage import binary_dilation, binary_propagation, binary_erosion
import denseCRF3D
import sys
import nibabel


if __name__ == "__main__":
    # 解析输入参数
    parser = argparse.ArgumentParser(description="Post-process shrink 3D segmentation mask")
    parser.add_argument("--mask_path", type=str, required=True, help="Path to the input mask file")
    parser.add_argument("--output_path", type=str, required=True, help="Path to save the processed mask file")
    parser.add_argument("--kernel_size", type=int, default=2, help="Kernel size for erosion")
    args = parser.parse_args()

    # 读取mask
    mask = sitk.ReadImage(args.mask_path)
    mask = sitk.Cast(mask, sitk.sitkUInt8)  # 确保mask是uint8类型
    # import pdb; pdb.set_trace()
    mask_3d = sitk.GetArrayFromImage(mask)

    # 后处理
    kernel = np.ones((args.kernel_size, args.kernel_size, args.kernel_size))

    # 进行腐蚀操作
    eroded_mask = binary_erosion(mask_3d, structure=kernel, iterations=1).astype(np.uint8)

    # 保存mask
    final_mask = sitk.GetImageFromArray(eroded_mask)
    final_mask.CopyInformation(mask)
    sitk.WriteImage(final_mask, args.output_path)

    print(f"Processed mask saved to {args.output_path}")

