from pathlib import Path
import tempfile
import threading
import logging

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