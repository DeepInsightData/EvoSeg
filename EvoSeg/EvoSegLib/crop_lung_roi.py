#!/usr/bin/env python3

import os
import numpy as np
import SimpleITK as sitk
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Tuple, List
import sys

def get_bounding_box(mask_image: sitk.Image, margin: Tuple[int, int, int] = (10, 10, 10)) -> Optional[Tuple[int, int, int, int, int, int]]:
    """
    获取mask的边界框，并添加边距

    Parameters:
    mask_image: SimpleITK Image
    margin: 三个方向上的边距 (x, y, z) - 注意SimpleITK使用XYZ顺序

    Returns:
    bbox: (x_start, y_start, z_start, x_size, y_size, z_size)
    """
    # 获取mask的数组数据
    mask_array = sitk.GetArrayFromImage(mask_image)

    # SimpleITK使用XYZ坐标，但数组是ZYX顺序，需要转换
    # 找到非零元素的坐标 (返回的是(Z,Y,X)坐标)
    coords = np.nonzero(mask_array)

    if len(coords[0]) == 0:  # 如果没有非零元素
        return None

    # 获取边界框 (注意数组索引是(Z,Y,X)顺序)
    z_min, z_max = coords[0].min(), coords[0].max()
    y_min, y_max = coords[1].min(), coords[1].max()
    x_min, x_max = coords[2].min(), coords[2].max()

    # 添加边距 (注意SimpleITK的顺序是(X,Y,Z))
    x_min = max(0, x_min - margin[0])
    y_min = max(0, y_min - margin[1])
    z_min = max(0, z_min - margin[2])

    x_max = min(mask_array.shape[2], x_max + margin[0])
    y_max = min(mask_array.shape[1], y_max + margin[1])
    z_max = min(mask_array.shape[0], z_max + margin[2])

    # 计算尺寸
    x_size = x_max - x_min
    y_size = y_max - y_min
    z_size = z_max - z_min

    return (int(x_min), int(y_min), int(z_min), int(x_size), int(y_size), int(z_size))

def generate_lung_mask(ct_path: Path, mask_output_path: Path) -> bool:
    """
    使用TotalSegmentator生成肺叶mask

    Parameters:
    ct_path: CT图像路径
    mask_output_path: mask输出路径

    Returns:
    bool: 是否成功生成mask
    """
    # 肺叶类别列表
    lung_lobe_classes = [
        "lung_lower_lobe_left",
        "lung_lower_lobe_right",
        "lung_middle_lobe_right",
        "lung_upper_lobe_left",
        "lung_upper_lobe_right"
    ]

    # 构建TotalSegmentator命令
    cmd = [
        "TotalSegmentator",
        "-i", str(ct_path),
        "-o", str(mask_output_path),
        "--ml",  # 保存为多标签图像
        "--roi_subset"  # 指定要分割的类别
    ] + lung_lobe_classes

    try:
        print(f"Running TotalSegmentator for {ct_path.name}...")
        # 不捕获输出，让TotalSegmentator的输出实时显示
        result = subprocess.run(cmd, check=True, text=True)
        print(f"Successfully generated mask for {ct_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating mask for {ct_path.name}: {e}")
        return False

def crop_image_with_mask(ct_path: Path, mask_path: Path, output_path: Path, margin: Tuple[int, int, int] = (10, 10, 10)) -> bool:
    """
    使用mask裁剪CT图像

    Parameters:
    ct_path: 原始CT图像路径
    mask_path: mask图像路径
    output_path: 裁剪后图像输出路径
    margin: 边界框边距

    Returns:
    bool: 是否成功裁剪
    """
    try:
        # 读取CT图像和mask
        ct_image = sitk.ReadImage(str(ct_path))
        mask_image = sitk.ReadImage(str(mask_path))

        # 获取边界框
        bbox = get_bounding_box(mask_image, margin)
        if bbox is None:
            print(f"No valid mask found in {mask_path.name}, skipping crop")
            return False

        x_start, y_start, z_start, x_size, y_size, z_size = bbox

        # 执行裁剪
        cropped_image = ct_image[x_start:x_start+x_size, y_start:y_start+y_size, z_start:z_start+z_size]

        # 设置数据类型为float32（适合CT图像）
        cropped_image = sitk.Cast(cropped_image, sitk.sitkFloat32)

        # 正确设置图像的origin和spacing
        original_spacing = ct_image.GetSpacing()
        original_direction = ct_image.GetDirection()
        original_origin = ct_image.GetOrigin()

        # 计算新的origin
        new_origin = (
            original_origin[0] + x_start * original_spacing[0],
            original_origin[1] + y_start * original_spacing[1],
            original_origin[2] + z_start * original_spacing[2]
        )

        # 设置新的元数据
        cropped_image.SetOrigin(new_origin)
        cropped_image.SetSpacing(original_spacing)
        cropped_image.SetDirection(original_direction)

        # 保存裁剪后的图像
        sitk.WriteImage(cropped_image, str(output_path))
        print(f"Successfully cropped and saved: {output_path.name}")
        return True

    except Exception as e:
        print(f"Error cropping {ct_path.name}: {e}")
        return False

def process_single_file_to_file(ct_path: Path, output_path: Path, temp_dir: Path, margin: Tuple[int, int, int]) -> bool:
    """
    处理单个CT文件并输出到指定文件

    Parameters:
    ct_path: CT文件路径
    output_path: 输出文件路径
    temp_dir: 临时文件目录
    margin: 边界框边距

    Returns:
    bool: 是否成功处理
    """
    try:
        # 提取文件ID
        file_id = ct_path.stem.split('.')[0]

        # 定义临时mask路径
        mask_path = temp_dir / f"mask_{file_id}.nii.gz"

        # 检查输出文件是否已存在
        if output_path.exists():
            print(f"Output file {output_path.name} already exists, skipping...")
            return True

        # 生成肺叶mask
        if not generate_lung_mask(ct_path, mask_path):
            return False

        # 使用mask裁剪图像
        if not crop_image_with_mask(ct_path, mask_path, output_path, margin):
            return False

        # 清理临时mask文件
        if mask_path.exists():
            mask_path.unlink()

        return True

    except Exception as e:
        print(f"Error processing {ct_path.name}: {e}")
        return False

def process_single_file(ct_path: Path, output_dir: Path, temp_dir: Path, margin: Tuple[int, int, int]) -> bool:
    """
    处理单个CT文件

    Parameters:
    ct_path: CT文件路径
    output_dir: 输出目录
    temp_dir: 临时文件目录
    margin: 边界框边距

    Returns:
    bool: 是否成功处理
    """
    try:
        # 提取文件ID
        file_id = ct_path.stem.split('.')[0]

        # 定义输出路径
        mask_path = temp_dir / f"mask_{file_id}.nii.gz"
        cropped_path = output_dir / f"{file_id}_cropped.nii.gz"

        # 检查输出文件是否已存在
        if cropped_path.exists():
            print(f"Cropped file {cropped_path.name} already exists, skipping...")
            return True

        # 生成肺叶mask
        if not generate_lung_mask(ct_path, mask_path):
            return False

        # 使用mask裁剪图像
        if not crop_image_with_mask(ct_path, mask_path, cropped_path, margin):
            return False

        # 清理临时mask文件
        if mask_path.exists():
            mask_path.unlink()

        return True

    except Exception as e:
        print(f"Error processing {ct_path.name}: {e}")
        return False

def process_directory(input_dir: Path, output_dir: Path, temp_dir: Path, margin: Tuple[int, int, int]) -> None:
    """
    处理目录中的所有CT文件

    Parameters:
    input_dir: 输入目录
    output_dir: 输出目录
    temp_dir: 临时文件目录
    margin: 边界框边距
    """
    # 获取所有.nii.gz文件
    ct_files = list(input_dir.glob("*.nii.gz"))

    if not ct_files:
        print(f"No .nii.gz files found in {input_dir}")
        return

    print(f"Found {len(ct_files)} CT files to process")

    # 创建输出和临时目录
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 处理每个文件
    success_count = 0
    for i, ct_file in enumerate(ct_files, 1):
        print(f"\nProcessing {i}/{len(ct_files)}: {ct_file.name}")

        if process_single_file(ct_file, output_dir, temp_dir, margin):
            success_count += 1

    print(f"\nProcessing complete: {success_count}/{len(ct_files)} files processed successfully")

def process_files(input_path, output_path, margin=(10, 10, 10), temp_dir=None):
    """
    处理文件或目录的主函数，可以被其他模块调用
    
    Args:
        input_path (str or Path): 输入文件或目录路径
        output_path (str or Path): 输出文件或目录路径
        margin (tuple): 边界框边距 (x, y, z), 默认为(10, 10, 10)
        temp_dir (str or Path, optional): 临时文件目录，默认为输出目录下的temp文件夹
    
    Returns:
        bool: 处理是否成功
    """
    # 转换路径
    input_path = Path(input_path)
    output_path = Path(output_path)

    # 验证输入路径
    if not input_path.exists():
        print(f"Error: Input path {input_path} does not exist")
        return False

    # 处理文件或目录
    if input_path.is_file():
        if not input_path.name.lower().endswith('.nii.gz'):
            print("Error: Input file must be a .nii.gz file")
            return False

        # 输入是文件，输出也应该是文件
        if output_path.exists() and output_path.is_dir():
            print("Error: When input is a file, output should also be a file path, not a directory")
            return False

        print(f"Processing single file: {input_path.name}")

        # 设置临时目录
        if temp_dir:
            temp_dir = Path(temp_dir)
        else:
            temp_dir = output_path.parent / "temp"

        temp_dir.mkdir(parents=True, exist_ok=True)

        success = process_single_file_to_file(input_path, output_path, temp_dir, margin)
        if success:
            print("Single file processing completed successfully")
            return True
        else:
            print("Single file processing failed")
            return False

    elif input_path.is_dir():
        # 输入是目录，输出也应该是目录
        if output_path.exists() and output_path.is_file():
            print("Error: When input is a directory, output should also be a directory path, not a file")
            return False

        print(f"Processing directory: {input_path}")

        # 设置临时目录
        if temp_dir:
            temp_dir = Path(temp_dir)
        else:
            temp_dir = output_path / "temp"

        process_directory(input_path, output_path, temp_dir, margin)
        return True

    else:
        print(f"Error: {input_path} is neither a file nor a directory")
        return False

def main():
    """
    主函数 - 命令行接口
    """
    parser = argparse.ArgumentParser(description="使用TotalSegmentator预测mask并裁剪CT图像")
    parser.add_argument('-i', "--input", type=str, required=True, help="输入文件或目录路径")
    parser.add_argument('-o', "--output", type=str, required=True, help="输出文件或目录路径")
    parser.add_argument("--margin", type=int, nargs=3, default=[10, 10, 10],
                       help="边界框边距 (x y z), 默认为10 10 10")
    parser.add_argument("--temp_dir", type=str, default=None,
                       help="临时文件目录，默认为输出目录下的temp文件夹")

    args = parser.parse_args()

    # 调用处理函数
    success = process_files(
        input_path=args.input,
        output_path=args.output,
        margin=tuple(args.margin),
        temp_dir=args.temp_dir
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()