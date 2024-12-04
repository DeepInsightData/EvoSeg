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

simulated_data=True

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

@torch.no_grad()
def main(model_folder,
         image_file,
         result_file,
         save_prob_maps=True,
         **kwargs):
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
    
    predictor = nnUNetPredictor(
        tile_step_size=0.5,
        use_gaussian=True,
        use_mirroring=True,
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
    img, prop = SimpleITKIO().read_images([image_file])
    timing_checkpoints.append(('image loading', time.time()))
    
    print(f"Predicting")
    # predict
    # seg_results = predictor.predict_from_list_of_npy_arrays([img],
    #                                                 None,
    #                                                 [prop],
    #                                                 None, 3, save_probabilities=False,
    #                                                 num_processes_segmentation_export=2)
    if not simulated_data:
        seg_results = predictor.predict_single_npy_array(img, prop, None, None, save_prob_maps)
        # TODO: 根据model_folder->确定当前模型->修改mask值
        if os.path.basename(model_folder)=="Airway_nnUnet":
            pass
        else: # 注意之后添加vein模型
            #print(seg_results)
            seg_results*=2
    # import pdb; pdb.set_trace()
    timing_checkpoints.append(('Inference', time.time()))

    # TODO:多模态分割结果保存
    # save result by copying all image metadata from the input, just replacing the voxel data
    # nrrd_header = nrrd.read_header(image_file)
    # nrrd.write(result_file, seg_results, nrrd_header)
    
    # load NIFTI header
    if simulated_data:
        print("->copy:"+model_folder+"/output-segmentation.nrrd to"+result_file)
        with open(model_folder+"/output-segmentation.nrrd", 'rb') as f_src:  # 以二进制模式打开源文件
            with open(result_file, 'wb') as f_dest:  # 以二进制模式写入目标文件
                while True:
                    # 每次读取 1024 字节
                    chunk = f_src.read(1024)
                    if not chunk:
                        break
                    f_dest.write(chunk)
        if os.path.basename(model_folder)=="Artery_nnUnet":
            data, header = nrrd.read(result_file)
            data = data * 2
            nrrd.write(result_file, data, header)
            print("-> Done")
        if save_prob_maps:
            print("->copy:"+model_folder+"/output-segmentation_prob.nrrd to"+result_file.replace('.nrrd', '_prob.nrrd'))
            with open(model_folder+"/output-segmentation_prob.nrrd", 'rb') as f_src:  # 以二进制模式打开源文件
                with open(result_file.replace('.nrrd', '_prob.nrrd'), 'wb') as f_dest:  # 以二进制模式写入目标文件
                    while True:
                        # 每次读取 1024 字节
                        chunk = f_src.read(1024)
                        if not chunk:
                            break
                        f_dest.write(chunk)
    else:
        if save_prob_maps:
            SimpleITKIO().write_seg(seg_results[0], result_file, prop)
            prob_maps = seg_results[1][1]
            # normalize prob_maps to 0-255
            prob_maps = (prob_maps - prob_maps.min()) / (prob_maps.max() - prob_maps.min()) * 255
            SimpleITKIO().write_seg(prob_maps, result_file.replace('.nrrd', '_prob.nrrd'), prop)
            # write_prob_maps(seg_results[1][1], result_file.replace('.nrrd', '_prob.nrrd'), prop)
            # prob_maps = (prob_mps - prob_maps.min()) / (prob_maps.max() - prob_maps.min()) * 255
            # SimpleITKIO().writea_seg(prob_maps, result_file.replace('.nii.gz', '_prob.nii.gz'), prop)
            # # write_prob_maps(seg_results[1][1], result_file.replace('.nii.gz', '_prob.nii.gz'), prop)
        else:
            SimpleITKIO().write_seg(seg_results, result_file, prop)
    
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