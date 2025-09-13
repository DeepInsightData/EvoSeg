import SimpleITK as sitk
import numpy as np
import os


def mask_with_lobe_region(input_raw_mask_path, lobe_mask_path, output_path, preserve_labels=True, add_value=0):
    """
    使用肺叶mask来过滤输入图像，只保留肺叶区域内的部分。
    可以应用在任何需要去除肺外区域，气管、血管、肺段都可以用该函数来后处理
    Parameters:
    -----------
    input_raw_mask_path : str
        输入的nifti图像路径
    lobe_mask_path : str
        肺叶mask路径（来自TotalSegmentator等）
    output_path : str
        输出文件路径
    preserve_labels : bool, default=True
        是否保留原始标签值。如果为False，则将所有非零区域设为1
    add_value : int, default=0
        对保留的非零区域加上该值，常用于调整标签范围
    Returns:
    --------
    bool
        处理是否成功
    """
    try:
        # 读取输入图像和肺叶mask
        print(f"Reading input image: {input_raw_mask_path}")
        input_image = sitk.ReadImage(input_raw_mask_path)

        print(f"Reading lobe mask: {lobe_mask_path}")
        lobe_mask = sitk.ReadImage(lobe_mask_path)
        
        # 检查图像尺寸是否一致
        if input_image.GetSize() != lobe_mask.GetSize():
            print(f"Warning: Image sizes don't match. Input: {input_image.GetSize()}, Mask: {lobe_mask.GetSize()}")
            print("Resampling mask to match input image...")
            
            # 重采样mask以匹配输入图像
            resampler = sitk.ResampleImageFilter()
            resampler.SetReferenceImage(input_image)
            resampler.SetInterpolator(sitk.sitkNearestNeighbor)
            resampler.SetDefaultPixelValue(0)
            lobe_mask = resampler.Execute(lobe_mask)
        
        # 转换为numpy数组进行处理
        input_array = sitk.GetArrayFromImage(input_image)
        mask_array = sitk.GetArrayFromImage(lobe_mask)
        
        # 创建二值化的肺叶mask（所有非零区域）
        binary_lobe_mask = mask_array != 0
        
        print(f"Input image shape: {input_array.shape}")
        print(f"Lobe mask shape: {mask_array.shape}")
        print(f"Number of non-zero voxels in input: {np.sum(input_array != 0)}")
        print(f"Number of non-zero voxels in lobe mask: {np.sum(binary_lobe_mask)}")
        
        # 应用mask：只保留肺叶区域内的像素
        if preserve_labels:
            # 保留原始标签值
            output_array = np.where(binary_lobe_mask, input_array, 0)
        else:
            # 将所有非零区域设为1
            output_array = np.where(binary_lobe_mask & (input_array != 0), 1, 0)
        
        print(f"Number of non-zero voxels in output: {np.sum(output_array != 0)}")

        # 让output_array非零部分+add_value
        output_array[output_array != 0] += add_value

        # 转换回SimpleITK图像，保持原始图像的空间信息
        output_image = sitk.GetImageFromArray(output_array)
        output_image.CopyInformation(input_image)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存结果
        print(f"Saving masked result to: {output_path}")
        sitk.WriteImage(output_image, output_path)
        
        print("Processing completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        return False


def remove_non_lobe_regions_batch(input_dir, lobe_mask_path, output_dir, file_pattern="*.nii.gz", preserve_labels=True):
    """
    批量处理：对输入目录中的所有文件应用肺叶mask
    
    Parameters:
    -----------
    input_dir : str
        输入文件目录
    lobe_mask_path : str
        肺叶mask路径
    output_dir : str
        输出目录
    file_pattern : str, default="*.nii.gz"
        文件匹配模式
    preserve_labels : bool, default=True
        是否保留原始标签值
    """
    import glob
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    pattern_path = os.path.join(input_dir, file_pattern)
    input_files = glob.glob(pattern_path)
    
    print(f"Found {len(input_files)} files matching pattern: {file_pattern}")
    
    success_count = 0
    for input_file in input_files:
        filename = os.path.basename(input_file)
        output_file = os.path.join(output_dir, filename)
        
        print(f"\nProcessing: {filename}")
        if mask_with_lobe_region(input_file, lobe_mask_path, output_file, preserve_labels):
            success_count += 1
        else:
            print(f"Failed to process: {filename}")
    
    print(f"\nBatch processing completed: {success_count}/{len(input_files)} files processed successfully")


def create_combined_lobe_mask(lobe_mask_path, output_path=None):
    """
    创建合并的肺叶mask（将所有肺叶标签合并为一个二值mask）
    
    Parameters:
    -----------
    lobe_mask_path : str
        原始肺叶mask路径（可能包含多个标签）
    output_path : str, optional
        输出路径，如果不指定则在原文件名后添加'_binary'
    
    Returns:
    --------
    str
        输出文件路径
    """
    if output_path is None:
        base, ext = os.path.splitext(lobe_mask_path)
        if ext == '.gz':
            base, ext2 = os.path.splitext(base)
            output_path = f"{base}_binary{ext2}{ext}"
        else:
            output_path = f"{base}_binary{ext}"
    
    try:
        # 读取肺叶mask
        lobe_mask = sitk.ReadImage(lobe_mask_path)
        mask_array = sitk.GetArrayFromImage(lobe_mask)
        
        # 创建二值mask
        binary_array = (mask_array != 0).astype(np.uint8)
        
        # 转换回SimpleITK图像
        binary_mask = sitk.GetImageFromArray(binary_array)
        binary_mask.CopyInformation(lobe_mask)
        
        # 保存
        sitk.WriteImage(binary_mask, output_path)
        print(f"Binary lobe mask saved to: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"Error creating binary mask: {str(e)}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="使用肺叶mask来过滤输入图像，只保留肺叶区域内的部分。可以应用在任何需要去除肺外区域的场景，如气管、血管、肺段等分割结果的后处理。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            示例用法:
            python remove_non_lobe_region.py -i input.nii.gz -l lobe_mask.nii.gz -o output.nii.gz
            python remove_non_lobe_region.py -i input.nii.gz -l lobe_mask.nii.gz -o output.nii.gz --no-preserve-labels
            python remove_non_lobe_region.py --batch -d input_dir -l lobe_mask.nii.gz -od output_dir
        """
    )
    
    # 添加互斥组：单文件处理 vs 批量处理
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '-i', '--input',
        type=str,
        help='输入的nifti格式Raw Mask路径'
    )
    mode_group.add_argument(
        '--batch',
        action='store_true',
        help='批量处理模式'
    )
    
    parser.add_argument(
        '-l', '--lobe-mask',
        type=str,
        required=True,
        help='肺叶mask路径（来自TotalSegmentator等）'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='输出文件路径（单文件模式必需）'
    )
    
    # 批量处理参数
    parser.add_argument(
        '-d', '--input-dir',
        type=str,
        help='输入文件目录（批量模式必需）'
    )
    
    parser.add_argument(
        '-od', '--output-dir',
        type=str,
        help='输出目录（批量模式必需）'
    )
    
    parser.add_argument(
        '-p', '--pattern',
        type=str,
        default='*.nii.gz',
        help='文件匹配模式（批量模式，默认: *.nii.gz）'
    )
    
    parser.add_argument(
        '--no-preserve-labels',
        action='store_true',
        help='不保留原始标签值，将所有非零区域设为1（默认保留原始标签值）'
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if not args.batch:
        # 单文件模式
        if not args.output:
            parser.error("单文件模式需要指定输出路径 (-o/--output)")
        
        if not os.path.exists(args.input):
            parser.error(f"输入文件不存在: {args.input}")
        
        if not os.path.exists(args.lobe_mask):
            parser.error(f"肺叶mask文件不存在: {args.lobe_mask}")
        
        print("=== 单文件处理模式 ===")
        success = mask_with_lobe_region(
            input_raw_mask_path=args.input,
            lobe_mask_path=args.lobe_mask,
            output_path=args.output,
            preserve_labels=not args.no_preserve_labels
        )
        
        if success:
            print("处理完成！")
        else:
            print("处理失败！")
            exit(1)
    
    else:
        # 批量处理模式
        if not args.input_dir:
            parser.error("批量模式需要指定输入目录 (-d/--input-dir)")
        
        if not args.output_dir:
            parser.error("批量模式需要指定输出目录 (-od/--output-dir)")
        
        if not os.path.exists(args.input_dir):
            parser.error(f"输入目录不存在: {args.input_dir}")
        
        if not os.path.exists(args.lobe_mask):
            parser.error(f"肺叶mask文件不存在: {args.lobe_mask}")
        
        print("=== 批量处理模式 ===")
        remove_non_lobe_regions_batch(
            input_dir=args.input_dir,
            lobe_mask_path=args.lobe_mask,
            output_dir=args.output_dir,
            file_pattern=args.pattern,
            preserve_labels=not args.no_preserve_labels
        )