from pathlib import Path
import tempfile
import threading
import logging
from scipy import ndimage
import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
import multiprocessing as mp
import nibabel as nib
import numpy as np

# Get logger for this module
logger = logging.getLogger(__name__)

class EvoSegmentator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(EvoSegmentator, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._case_path = None
        self._case_dir = None
    
    def __del__(self):
        """Destructor - cleanup as last resort (not recommended to rely on)"""
        try:
            self._terminate_processes()
            self._remove_case_dirs()
        except Exception as e:
            # Print to stderr as logger might be destroyed
            import sys
            print(f"EvoSegmentator destructor error: {e}", file=sys.stderr)
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    # Create instance if it doesn't exist
                    cls._instance = super(EvoSegmentator, cls).__new__(cls)
                    cls._instance.__init__()
                    logger.info("EvoSegmentator instance created")
        return cls._instance
    
    def reset(self, case_dir: str = None):
        """Reset singleton instance state without destroying the instance"""
        with self._lock:
            # Execute cleanup work
            try:
                self._terminate_processes()
                self._remove_case_dirs()
                logger.info("EvoSegmentator resources cleaned up")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            
            # If new case_dir is provided, reinitialize state
            if case_dir:
                self._case_path = Path(case_dir)
                self._case_dir = None
                self._create_case_dirs()
                logger.info(f"EvoSegmentator reset with new case_dir: {case_dir}")
            else:
                self._case_path = None
                self._case_dir = None
                logger.info("EvoSegmentator reset (no new case_dir)")
    
    def submit(self, case_dir: str, model_dir: str):
        pass

    def _terminate_processes(self):
        """Clean up related processes (to be implemented)"""
        # Here you can add process cleanup logic
        # For example: terminate inference processes, clean up child processes, etc.
        logger.info("Cleaning up processes...")

    def _create_case_dirs(self):
        """Create case directory structure (caller must hold lock)"""
        if self._case_dir is None and self._case_path is not None:
            self._case_dir = tempfile.TemporaryDirectory(prefix=f'{self._case_path}_')
            dirs = ["input", "preprocess", "predict", "output"]
            for dir_name in dirs:
                (Path(self._case_dir.name) / dir_name).mkdir(exist_ok=True, parents=True)
            logger.info(f"Created case directories in: {self._case_dir.name}")
        return self
    
    def _remove_case_dirs(self):
        """Clean up case directories (caller must hold lock)"""
        try:
            if self._case_dir is not None:
                self._case_dir.cleanup()
                self._case_dir = None
                logger.info("Cleaned up case directories")
        except Exception as e:
            logger.error(f"❌ remove case directory error: {e}")

    @property
    def case_dir(self):
        """Get current temporary directory name"""
        with self._lock:
            return self._case_dir.name if self._case_dir else None

    def get_subdir(self, subdir: str):
        """Get subdirectory path"""
        with self._lock:
            return Path(self._case_dir.name) / subdir if self._case_dir else None
    
    @property
    def input_dir(self):
        """Get input directory path"""
        return self.get_subdir("input")
    
    @property
    def preprocess_dir(self):
        """Get preprocess directory path"""
        return self.get_subdir("preprocess")
    
    @property
    def predict_dir(self):
        """Get predict directory path"""
        return self.get_subdir("predict")
    
    @property
    def output_dir(self):
        """Get output directory path"""
        return self.get_subdir("output")
    
class LungSegmentPredictor:
    def __init__(self, model_folder:str, 
        device = torch.device('cuda', 0) if torch.cuda.is_available() else torch.device('cpu'), 
        use_folds=('all', ),
        checkpoint_name='checkpoint_best.pth'):
        self._model_folder:str = model_folder
        self._device = device
        self._use_folds = use_folds
        self._checkpoint_name:str = checkpoint_name

    def predict(self, volume_file: str, airway_pred: str, artery_pred: str, 
                vein_pred: str, output_dir: str):
        predictor = nnUNetPredictor(
            tile_step_size=0.5,
            use_gaussian=True,
            use_mirroring=True,
            perform_everything_on_device=True,
            device=self._device,
            verbose=False,
            verbose_preprocessing=False,
            allow_tqdm=True
        )
        
        predictor.initialize_from_trained_model_folder(
            self._model_folder,
            use_folds=self._use_folds,
            checkpoint_name=self._checkpoint_name,
        )

        print(f"predict output directory: {[output_dir]}")
        predictor.predict_from_files(
            [[volume_file, airway_pred, artery_pred, vein_pred]], 
            [output_dir],
            save_probabilities=False, 
            overwrite=True,
            num_processes_preprocessing=2, 
            num_processes_segmentation_export=2,
            folder_with_segs_from_prev_stage=None, 
            num_parts=1, 
            part_id=0
        )

    def postprocess(self, predict_file:str, output_file: str):
        img = nib.load(predict_file)
        data = img.get_fdata()

        # 二值化所有非零区域
        binary = (data != 0)
        if not np.any(binary):
            print(f"No non-zero voxels in {predict_file}. Saving a copy to {output_file}.")
            # 直接保存原始图像到输出路径（不覆盖原文件）
            nib.save(img, output_file)
            return

        # map label value from 1~18 to 31~48
        data[binary] = data[binary] + 30

        # 连通域标记（所有非零区域一起处理）
        labeled, num_components = ndimage.label(binary)
        if num_components <= 1:
            print(f"{predict_file}: only {num_components} component(s), copying to {output_file} without changes.")
            nib.save(img, output_file)
            return

        # 计算每个连通域大小并保留最大连通域
        component_sizes = np.bincount(labeled.ravel())
        component_sizes[0] = 0  # 忽略背景
        largest_label = int(component_sizes.argmax())
        largest_size = int(component_sizes[largest_label])
        print(f"Processing {predict_file}: {num_components} components found, keeping largest (label {largest_label}) with {largest_size} voxels.")

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
        nib.save(out_img, output_file)
        print(f"Saved processed result to {output_file}")