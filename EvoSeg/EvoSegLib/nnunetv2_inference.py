import os
import numpy as np
import fire
import time
import torch
from collections import OrderedDict
#from flask import Flask, request, jsonify
import torch
import numpy as np
from batchgenerators.utilities.file_and_folder_operations import join
from nnunetv2.imageio.simpleitk_reader_writer import SimpleITKIO
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
import SimpleITK as sitk

import nrrd
import nibabel as nib
from resampling import change_spacing

from post_process import *

def write_prob_maps(seg: np.ndarray, output_fname: str, properties: dict) -> None:
    assert seg.ndim == 3, 'segmentation must be 3d. If you are exporting a 2d segmentation, please provide it as shape 1,x,y'
    output_dimension = len(properties['sitk_stuff']['spacing'])
    assert 1 < output_dimension < 4
    if output_dimension == 2:
        seg = seg[0]

    itk_image = sitk.GetImageFromArray(seg.astype(np.float32, copy=False))
    itk_image.SetSpacing(properties['sitk_stuff']['spacing'])
    itk_image.SetOrigin(properties['sitk_stuff']['origin'])
    itk_image.SetDirection(properties['sitk_stuff']['direction'])

    sitk.WriteImage(itk_image, output_fname, True)

simulated_data=False

@torch.no_grad()
def main(model_folder,
         image_file,
         result_file,
         save_prob_maps=False,
         resample=None,
         use_total=False,
         **kwargs):

    if simulated_data:
        print("->copy:"+model_folder+"/output-segmentation.nii.gz to"+result_file)
        output_dir = os.path.dirname(result_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(model_folder+"/output-segmentation.nii.gz", 'rb') as f_src:  # 以二进制模式打开源文件
            with open(result_file, 'wb') as f_dest:  # 以二进制模式写入目标文件
                while True:
                    # 每次读取 1024 字节
                    chunk = f_src.read(1024)
                    if not chunk:
                        break
                    f_dest.write(chunk)
        print(f'ALL DONE, result saved in {result_file}')
        return

    if use_total:
        from modify_total_python_api import modifiy_totalsegmentator

        input_img = nib.load(image_file)
        output_img = modifiy_totalsegmentator(model_folder, input_img)#, fast=True)

        val = output_img.dataobj[:]
        # 特殊处理
        if os.path.basename(model_folder) == "LungLobe_nnUnet":
            val[(val < 10) | (val > 14)] = 0 
        elif os.path.basename(model_folder) == "Rib_nnUnet":
            val[(val < 1) | (val > 24)] = 0
            val[val != 0] = 20
        elif os.path.basename(model_folder) == "Vein_nnUnet":
            val[val != 3] = 0

        output_img = nib.Nifti1Image(val, output_img.affine)

        output_dir = os.path.dirname(result_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        nib.save(output_img, result_file)

        return

    if resample is not None: # 目前resample下对prob_maps该如何处理未知
        save_prob_maps=False

    start_time = time.time()
    timing_checkpoints = []  # list of (operation, time) tuples
    
    # check if model_folder exists
    if not os.path.isdir(model_folder):
        raise ValueError(f"model_folder {model_folder} does not exist")

    # check if image_file exists
    if not os.path.isfile(image_file):
        raise ValueError(f"image_file {image_file} does not exist")
    
    use_folds = (1, )
    device = torch.device('cuda', 0)

    if resample is not None and resample < 3.0:
        # overall speedup for 15mm model roughly 11% (GPU) and 100% (CPU)
        # overall speedup for  3mm model roughly  0% (GPU) and  10% (CPU)
        # (dice 0.001 worse on test set -> ok)
        # (for lung_trachea_bronchia somehow a lot lower dice)
        step_size = 0.8
    else:
        step_size = 0.5
    
    predictor = nnUNetPredictor(
        tile_step_size=step_size,
        use_gaussian=True,
        use_mirroring=False,
        perform_everything_on_device=True,
        device=device,
        verbose=False,
        verbose_preprocessing=True,
        allow_tqdm=True
    )
    
    # load model
    print(f"Loading model from {model_folder}")
    predictor.initialize_from_trained_model_folder(
        model_folder,
        use_folds=use_folds,
        checkpoint_name='checkpoint_best.pth',
    )
    timing_checkpoints.append(('model loading', time.time()))
    
    
    print(f"Loading image from {image_file}")
    input_image = nib.load(image_file)
    if type(resample) is float:
        resample = [resample, resample, resample]
    if resample is not None:
        print("Resampling...")
        st = time.time()
        img_in_shape = input_image.shape
        img_in_zooms = input_image.header.get_zooms()
        img_in_rsp = change_spacing(input_image, resample, order=3, dtype=np.int32, nr_cpus=1)  # 4 cpus instead of 1 makes it a bit slower
        print(f"  from shape {input_image.shape} to shape {img_in_rsp.shape}")
        print(f"  Resampled in {time.time() - st:.2f}s")
    else:
        img_in_rsp = input_image
    img_in_rsp_data = np.asanyarray(img_in_rsp.dataobj).transpose(2, 1, 0)[None,...].astype(np.float32)
    spacing = img_in_rsp.header.get_zooms()
    affine = img_in_rsp.affine
    # Do i have to transpose spacing? does not matter because anyways isotropic at this point.
    spacing = (spacing[2], spacing[1], spacing[0])
    prop = {"spacing": spacing}
    timing_checkpoints.append(('image loading', time.time()))


    print(f"Predicting")    
    seg_results = predictor.predict_single_npy_array(img_in_rsp_data, prop,
                                             None, None,
                                             save_prob_maps)
    # 结果的特殊处理
    if save_prob_maps:
        # 带prob的输出是一个()需要拆开再合起来, 其中val相当于不带prob输出的seg_results纯numpy
        val, val_prob = seg_results
        val = val.transpose(2, 1, 0)
        if os.path.basename(model_folder)=="Airway_nnUnet":
            val = process_mask_3d(val, 1, 2)
        if os.path.basename(model_folder)=="Artery_nnUnet":
            # 特殊处理1, Artery_nnUnet执行结果*2
            val=val*2
        #else: 
        seg_results=(val, val_prob)

        # 转成nii
        seg_results_nib = nib.Nifti1Image(seg_results[0].astype(np.uint8), affine)

    else:
        seg_results = seg_results.transpose(2, 1, 0)
        if os.path.basename(model_folder)=="Airway_nnUnet":
            seg_results = process_mask_3d(seg_results, 1, 2)
        if os.path.basename(model_folder)=="Artery_nnUnet":
            # 特殊处理1, Artery_nnUnet执行结果*2
            seg_results=seg_results*2
        #else: 其它

        # 转成nii
        seg_results_nib = nib.Nifti1Image(seg_results.astype(np.uint8), affine)

    if resample is not None:
        print("Resampling...")
        print(f"  back to original shape: {img_in_shape}")
        # Use force_affine otherwise output affine sometimes slightly off (which then is even increased
        # by undo_canonical)
        end_seg_results = change_spacing(seg_results_nib, resample, img_in_shape,
                                order=0, dtype=np.uint8, nr_cpus=1,
                                force_affine=input_image.affine)
    else:
        end_seg_results = seg_results_nib
    # import pdb; pdb.set_trace()
    timing_checkpoints.append(('Inference', time.time()))

    # TODO:多模态分割结果保存
    
    if save_prob_maps:
        if resample is not None:
            # 已在41行处理
            pass
        else:
            # 这个 prob_maps 即118行val_prob
            prob_maps = seg_results[1][1]
            # normalize prob_maps to 0-255
            prob_maps = (prob_maps - prob_maps.min()) / (prob_maps.max() - prob_maps.min()) * 255
            SimpleITKIO().write_seg({'sitk_stuff':np.expand_dims(prob_maps, axis=0)}, result_file.replace('.nii.gz', '_prob.nii.gz'), prop)
    
    output_dir = os.path.dirname(result_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 统一用nib保存nii.gz
    nib.save(end_seg_results, result_file)
    timing_checkpoints.append(("Save", time.time()))
    
    # Print computation time log
    print("Computation time log:")
    previous_start_time = start_time
    for timing_checkpoint in timing_checkpoints:
        print(f"  {timing_checkpoint[0]}: {timing_checkpoint[1] - previous_start_time:.2f} seconds")
        previous_start_time = timing_checkpoint[1]

    print(f'ALL DONE, result saved in {result_file}')

if __name__ == '__main__':
    fire.Fire(main)
