import argparse
import os
import sys
import traceback
import numpy as np
import nibabel as nib
from scipy import ndimage
import torch
from batchgenerators.utilities.file_and_folder_operations import join
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

class LungSegmentPredictor:
    def __init__(self, model_dir, 
                 tile_step_size=0.5, 
                 use_gaussian=True, 
                 use_mirroring=True,
                 perform_everything_on_device=True, 
                 device= torch.device("cuda", 0) if torch.cuda.is_available() else torch.device('cpu'),
                 verbose_preprocessing=False, 
                 allow_tqdm=True):
        self.model_dir = model_dir
        
        # Initialize lung segment predictor
        self.nnUNetPredictor = nnUNetPredictor(
            tile_step_size=tile_step_size,
            use_gaussian=use_gaussian,
            use_mirroring=use_mirroring,
            perform_everything_on_device=perform_everything_on_device,
            device=device,
            verbose=False,
            verbose_preprocessing=verbose_preprocessing,
            allow_tqdm=allow_tqdm
        )
        
        self.nnUNetPredictor.initialize_from_trained_model_folder(
            model_dir,
            use_folds=('all', ),
            checkpoint_name='checkpoint_best.pth',
        )
    
    def predict(self, preprocessed_file, airway_file, artery_file, vein_file, pred_file, output_file, verbose=False):
        """Run lung segment prediction"""
        
        if verbose:
            print(f"Model directory: {self.model_dir}")
            print(f"Preprocessed file: {preprocessed_file}")
            print(f"Airway file: {airway_file}")
            print(f"Artery file: {artery_file}")
            print(f"Vein file: {vein_file}")
            print(f"Prediction file: {pred_file}")
            print(f"Output file: {output_file}")
        
        self.nnUNetPredictor.predict_from_files(
            [[preprocessed_file, airway_file, artery_file, vein_file]],
            [pred_file],
            save_probabilities=False,
            overwrite=True,
            num_processes_preprocessing=2,
            num_processes_segmentation_export=2,
            folder_with_segs_from_prev_stage=None,
            num_parts=1,
            part_id=0
        )
        
        if os.path.exists(pred_file):
            self.postprocess(pred_file, output_file, verbose)
        else:
            print(f"Warning: Prediction file not found: {pred_file}")

    def postprocess(self, pred_file, output_file, verbose):
        """
        后处理肺段分割结果：将所有非零区域视为一个整体，仅保留最大的连通域，移除其它不连通的小区域。
        """
        pred_nib = nib.load(pred_file)
        data = pred_nib.get_fdata()

        # 二值化所有非零区域
        binary = (data != 0)
        if not np.any(binary):
            if verbose:
                print(f"No non-zero voxels in {pred_file}. Saving a copy to {output_file}.")
            nib.save(pred_nib, output_file)
            return

        # 连通域标记（所有非零区域一起处理）
        labeled, num_components = ndimage.label(binary)
        if num_components <= 1:
            if verbose:
                print(f"{pred_file}: only {num_components} component(s), copying to {output_file} without changes.")
            nib.save(pred_nib, output_file)
            return

        # 计算每个连通域大小并保留最大连通域
        component_sizes = np.bincount(labeled.ravel())
        component_sizes[0] = 0  # 忽略背景
        largest_label = int(component_sizes.argmax())
        largest_size = int(component_sizes[largest_label])
        if verbose:
            print(f"Processing {pred_file}: {num_components} components found, keeping largest (label {largest_label}) with {largest_size} voxels.")
        largest_mask = (labeled == largest_label)
        # 保留最大连通域的原始标签值，其余设为0
        output_data = np.where(largest_mask, data, 0)

        # 保持数据类型一致
        try:
            target_dtype = pred_nib.get_data_dtype()
        except Exception:
            target_dtype = data.dtype
        output_data = output_data.astype(target_dtype)

        # 使用原始affine和header保存（保存为新文件）
        out_img = nib.Nifti1Image(output_data, pred_nib.affine, pred_nib.header.copy())
        nib.save(out_img, output_file)
        if verbose:
            print(f"Saved processed result to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Lung segment segmentation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--work-dir', '-w', type=str, default='.', 
                       help='Working directory path (optional, defaults to current directory)')
    parser.add_argument('--model', '-m', type=str, required=True,
                       help='Model directory path (should contain LungLobe_nnUnet folder)')
    parser.add_argument('--input', '-i', type=str, required=True,
                       help='Preprocessed file path (.nii.gz format)')
    parser.add_argument('--output', '-o', type=str,
                       help='Output file path (optional)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show verbose output')
    
    args = parser.parse_args()
    work_dir = os.path.abspath(args.work_dir)
    model_dir = os.path.abspath(args.model)
    preprocessed_file = os.path.abspath(args.input)
    
    # Construct prediction file paths based on preprocessed file
    base_filename = os.path.basename(preprocessed_file).replace('.nii.gz', '')
    artery_file = os.path.join(work_dir, f"{base_filename}_artery_pred.nii.gz")
    vein_file = os.path.join(work_dir, f"{base_filename}_vein_pred.nii.gz")
    airway_file = os.path.join(work_dir, f"{base_filename}_airway_pred.nii.gz")
    pred_file = os.path.join(work_dir, f"{base_filename}_lung_segment_pred.nii.gz")
    output_file = args.output or os.path.join(work_dir, f"{base_filename}_lung_segment_pred.nii.gz")
    
    # Check if all input files exist
    for file_path in [preprocessed_file, airway_file, artery_file, vein_file]:
        if not os.path.exists(file_path):
            print(f"Error: Missing input file: {file_path}")
            sys.exit(1)
    
    predictor = LungSegmentPredictor(model_dir=model_dir)
    
    # Run prediction
    verbose = args.verbose
    try:
        predictor.predict(preprocessed_file, airway_file, artery_file, vein_file, pred_file, output_file, verbose)
        if verbose:
            print(f"Lung segment prediction result saved to: {output_file}")
    except Exception as e:
        print(f"Error during lung segment prediction: {e}")
        traceback.print_exc()
        sys.exit(1)
