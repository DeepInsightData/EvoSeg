#!/usr/bin/env python3
"""
肺部分割推理脚本
整合自 inference.ipynb，用于批量处理肺部CT图像的动脉、静脉、气道和肺段分割
"""

import os
import glob
import numpy as np
import nibabel as nib
from scipy import ndimage
import torch
from batchgenerators.utilities.file_and_folder_operations import join
from nnunetv2.paths import nnUNet_results, nnUNet_raw
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor


def initialize_predictors(model_path):
    """初始化所有预测器"""
    print("正在初始化预测器...")
    
    # 动脉预测器
    predictor_artery = nnUNetPredictor(
        tile_step_size=0.5,
        use_gaussian=True,
        use_mirroring=True,
        perform_everything_on_device=True,
        device=torch.device('cuda', 0),
        verbose=False,
        verbose_preprocessing=False,
        allow_tqdm=True
    )
    
    predictor_artery.initialize_from_trained_model_folder(
        join(model_path, 'Artery_nnUnet'),
        use_folds=('1', ),
        checkpoint_name='checkpoint_best.pth',
    )
    
    # 静脉预测器
    predictor_vein = nnUNetPredictor(
        tile_step_size=0.5,
        use_gaussian=True,
        use_mirroring=True,
        perform_everything_on_device=True,
        device=torch.device('cuda', 0),
        verbose=False,
        verbose_preprocessing=False,
        allow_tqdm=True
    )
    
    predictor_vein.initialize_from_trained_model_folder(
        join(model_path, 'Vein_nnUnet'),
        use_folds=('1', ),
        checkpoint_name='checkpoint_best.pth',
    )
    
    # 气道预测器
    predictor_airway = nnUNetPredictor(
        tile_step_size=0.5,
        use_gaussian=True,
        use_mirroring=True,
        perform_everything_on_device=True,
        device=torch.device('cuda', 0),
        verbose=False,
        verbose_preprocessing=False,
        allow_tqdm=True
    )
    
    predictor_airway.initialize_from_trained_model_folder(
        join(model_path, 'Airway_nnUnet'),
        use_folds=('1', ),
        checkpoint_name='checkpoint_best.pth',
    )
    
    # 肺段预测器
    predictor_lung_segments = nnUNetPredictor(
        tile_step_size=0.5,
        use_gaussian=True,
        use_mirroring=True,
        perform_everything_on_device=True,
        device=torch.device('cuda', 0),
        verbose=False,
        verbose_preprocessing=False,
        allow_tqdm=True
    )
    
    predictor_lung_segments.initialize_from_trained_model_folder(
        join(model_path, 'LungLobe_nnUnet'),
        use_folds=('all', ),
        checkpoint_name='checkpoint_best.pth',
    )
    
    print("所有预测器初始化完成！")
    return predictor_artery, predictor_vein, predictor_airway, predictor_lung_segments


def prepare_input_files(input_path):
    """准备输入文件列表和输出文件名"""
    input_files = glob.glob(input_path+'/*.nii.gz')
    input_files = [f for f in input_files if f.endswith('.nii.gz')]
    
    artery_output_files = [f.replace('.nii.gz', '_artery_pred.nii.gz') for f in input_files]
    vein_output_files = [f.replace('.nii.gz', '_vein_pred.nii.gz') for f in input_files]
    airway_output_files = [f.replace('.nii.gz', '_airway_pred.nii.gz') for f in input_files]
    
    input_files = [[f] for f in input_files]
    
    print(f"找到 {len(input_files)} 个输入文件:")
    for i, f in enumerate(input_files):
        print(f"  {i+1}: {f[0]}")
    
    return input_files, artery_output_files, vein_output_files, airway_output_files


def run_predictions(predictor_artery, predictor_vein, predictor_airway, predictor_lung_segments,
                   input_files, artery_output_files, vein_output_files, airway_output_files):
    """运行所有预测"""
    
    # 动脉预测
    print("开始动脉分割预测...")
    predictor_artery.predict_from_files(
        input_files,
        artery_output_files,
        save_probabilities=False, 
        overwrite=False,
        num_processes_preprocessing=2, 
        num_processes_segmentation_export=2,
        folder_with_segs_from_prev_stage=None, 
        num_parts=1, 
        part_id=0
    )
    
    # 静脉预测
    print("开始静脉分割预测...")
    predictor_vein.predict_from_files(
        input_files,
        vein_output_files,
        save_probabilities=False, 
        overwrite=False,
        num_processes_preprocessing=2, 
        num_processes_segmentation_export=2,
        folder_with_segs_from_prev_stage=None, 
        num_parts=1, 
        part_id=0
    )
    
    # 气道预测
    print("开始气道分割预测...")
    predictor_airway.predict_from_files(
        input_files,
        airway_output_files,
        save_probabilities=False, 
        overwrite=False,
        num_processes_preprocessing=2, 
        num_processes_segmentation_export=2,
        folder_with_segs_from_prev_stage=None, 
        num_parts=1, 
        part_id=0
    )
    
    # 准备肺段预测的融合输入
    fused_input = [[p[0], p[0].replace('.nii.gz', '_airway_pred.nii.gz'), 
                   p[0].replace('.nii.gz', '_artery_pred.nii.gz'), 
                   p[0].replace('.nii.gz', '_vein_pred.nii.gz')] for p in input_files]
    
    lung_segment_output = [p[0].replace('_cropped.nii.gz', '_lung_segment_pred.nii.gz') for p in input_files]
    
    print("肺段预测融合输入:")
    for i, f in enumerate(fused_input):
        print(f"  {i+1}: {f}")
    
    # 肺段预测
    print("开始肺段分割预测...")
    predictor_lung_segments.predict_from_files(
        fused_input, 
        lung_segment_output,
        save_probabilities=False, 
        overwrite=True,
        num_processes_preprocessing=2, 
        num_processes_segmentation_export=2,
        folder_with_segs_from_prev_stage=None, 
        num_parts=1, 
        part_id=0
    )
    
    return lung_segment_output


def _append_suffix_to_filename(path, suffix='_post'):
    """在文件名后添加后缀"""
    if path.endswith('.nii.gz'):
        return path[:-7] + suffix + '.nii.gz'
    base, ext = os.path.splitext(path)
    return base + suffix + ext


def postprocess_lung_segments(nifti_path, out_path=None, suffix='_post'):
    """
    后处理肺段分割结果：将所有非零区域视为一个整体，仅保留最大的连通域，移除其它不连通的小区域。
    可以指定 out_path（完整输出路径），否则在原文件名后添加 suffix（默认 '_post'）并保存为新文件。
    """
    if out_path is None:
        out_path = _append_suffix_to_filename(nifti_path, suffix)

    img = nib.load(nifti_path)
    data = img.get_fdata()

    # 二值化所有非零区域
    binary = (data != 0)
    if not np.any(binary):
        print(f"No non-zero voxels in {nifti_path}. Saving a copy to {out_path}.")
        # 直接保存原始图像到输出路径（不覆盖原文件）
        nib.save(img, out_path)
        return

    # 连通域标记（所有非零区域一起处理）
    labeled, num_components = ndimage.label(binary)
    if num_components <= 1:
        print(f"{nifti_path}: only {num_components} component(s), copying to {out_path} without changes.")
        nib.save(img, out_path)
        return

    # 计算每个连通域大小并保留最大连通域
    component_sizes = np.bincount(labeled.ravel())
    component_sizes[0] = 0  # 忽略背景
    largest_label = int(component_sizes.argmax())
    largest_size = int(component_sizes[largest_label])
    print(f"Processing {nifti_path}: {num_components} components found, keeping largest (label {largest_label}) with {largest_size} voxels.")

    largest_mask = (labeled == largest_label)
    # 保留最大连通域的原始标签值，其余设为0
    output_data = np.where(largest_mask, data, 0)

    # 保持数据类型一致
    try:
        target_dtype = img.get_data_dtype()
    except Exception:
        target_dtype = data.dtype
    output_data = output_data.astype(target_dtype)

    # 使用原始affine和header保存（保存为新文件）
    out_img = nib.Nifti1Image(output_data, img.affine, img.header.copy())
    nib.save(out_img, out_path)
    print(f"Saved processed result to {out_path}")


def postprocess_results(lung_segment_output):
    """对所有肺段预测结果进行后处理"""
    print("开始后处理肺段分割结果（输出添加后缀 '_post'）...")
    for pred_result in lung_segment_output:
        if pred_result is not None and os.path.exists(pred_result):
            out_path = _append_suffix_to_filename(pred_result, '_post')
            postprocess_lung_segments(pred_result, out_path=out_path, suffix='_post')
        else:
            print(f"文件不存在或预测结果为空: {pred_result}")
    
    print("肺段后处理完成！")


def lung_inference0825_main(model_folder, input_path, result_path):
    """主函数"""
    print("开始肺部分割推理流程...")
    
    # print("-----------------------------")
    # print("---", model_folder)
    # print("---", input_path)
    # print("---", result_path)
    # print("-----------------------------")
    # print("-----------------------------")
    # print("---", os.path.dirname(model_folder))
    # print("---", os.path.dirname(input_path))
    # print("---", os.path.dirname(result_path))
    # print("-----------------------------")
    
    # # 初始化预测器
    predictor_artery, predictor_vein, predictor_airway, predictor_lung_segments = initialize_predictors(os.path.dirname(model_folder))
    
    # 准备输入文件
    input_files, artery_output_files, vein_output_files, airway_output_files = prepare_input_files(os.path.dirname(input_path))
    
    if not input_files:
        print("未找到输入文件！请确保 "+os.path.dirname(input_path)+" 目录下有 *.nii.gz 文件。")
        return
    
    # 运行预测
    lung_segment_output = run_predictions(
        predictor_artery, predictor_vein, predictor_airway, predictor_lung_segments,
        input_files, artery_output_files, vein_output_files, airway_output_files
    )

    # lung_segment_output = ['C:/Users/P14s/AppData/Local/Temp/Slicer/__SlicerTemp__2025-08-26_09+04+49.843/input\\input-volume0.nii.gz']
    # print("-----------------------------")
    # print("------>",lung_segment_output)
    # print("-----------------------------")

    # 后处理
    postprocess_results(lung_segment_output)
    
    print("肺部分割推理流程完成！")

    # 复制预测结果到指定的输出路径
    import shutil
    if lung_segment_output and len(lung_segment_output) > 0:
        # 确保输出目录存在
        output_dir = os.path.dirname(result_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")
        
        # 复制第一个预测结果文件到指定的result_path
        if os.path.exists(lung_segment_output[0]):
            try:
                shutil.copy2(lung_segment_output[0], result_path)
                print(f"成功复制预测结果到: {result_path}")
            except Exception as e:
                print(f"复制文件时出错: {e}")
        else:
            print(f"预测结果文件不存在: {lung_segment_output[0]}")
    else:
        print("没有预测结果文件需要复制")

# def main():
#     """主函数"""
#     print("开始肺部分割推理流程...")
    
#     # 初始化预测器
#     predictor_artery, predictor_vein, predictor_airway, predictor_lung_segments = initialize_predictors()
    
#     # 准备输入文件
#     input_files, artery_output_files, vein_output_files, airway_output_files = prepare_input_files()
    
#     if not input_files:
#         print("未找到输入文件！请确保 ./sample_scans_cropped/ 目录下有 *_cropped.nii.gz 文件。")
#         return
    
#     # 运行预测
#     lung_segment_output = run_predictions(
#         predictor_artery, predictor_vein, predictor_airway, predictor_lung_segments,
#         input_files, artery_output_files, vein_output_files, airway_output_files
#     )
    
#     # 后处理
#     postprocess_results(lung_segment_output)
    
#     print("肺部分割推理流程完成！")


# if __name__ == "__main__":
#     main()
