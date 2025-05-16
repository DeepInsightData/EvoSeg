from enum import Enum
import pathlib
import shutil
import slicer
import uuid
import os
import subprocess
import logging
from typing import List
from qt import QObject, Signal, QThread, QMutex, QWaitCondition


class SegTaskStatus(Enum):
    """
    分割任务状态枚举类，定义了所有分割任务共有的状态
    """
    CREATED = 0      # 任务创建但尚未进入队列
    PENDING = 1       # 任务已进入队列，等待执行
    RUNNING = 2     # 任务正在执行
    COMPLETED = 3    # 任务已成功完成
    CANCELLED = 4    # 任务被用户取消
    FAILED = 5       # 任务执行失败

    @classmethod
    def get_description(cls, status):
        """获取状态的描述文本"""
        descriptions = {
            cls.CREATED: "已创建",
            cls.PENDING: "队列等待中",
            cls.RUNNING: "运行中",
            cls.COMPLETED: "已完成",
            cls.CANCELLED: "已取消",
            cls.FAILED: "执行失败",
        }
        return descriptions.get(status, "未知状态")

class SegTaskInfo:
    """
    分割任务信息类，定义了所有分割任务共有的属性和方法
    """
    def __init__(self, volumeNode: slicer.vtkMRMLScalarVolumeNode, model: str, command: list[str]):
        self.id = uuid.uuid4() 
        self.volumeNode = volumeNode
        self.model = model
        self.command = command
        self.status = SegTaskStatus.CREATED
        self.process = None
        self.stdout = None
        self.stderr = None
        self.segmentationNode = None

class SegTaskContext(QObject):
    """
    分割任务上下文类，包含任务执行环境和相关信号
    """
    # 定义信号
    taskStarted = Signal(SegTaskInfo)          # 任务开始执行
    taskProgress = Signal(SegTaskInfo)         # 任务进度更新
    taskCompleted = Signal(SegTaskInfo)  # 任务成功完成
    taskFailed = Signal(SegTaskInfo, Exception) # 任务执行失败
    taskLog = Signal(SegTaskInfo, str)        # 任务日志消息
    taskCancelled = Signal(SegTaskInfo)        # 任务被取消
    allCancelled = Signal()                    # 所有任务被取消
    
    def __init__(self, volumeNode: slicer.vtkMRMLScalarVolumeNode):
        QObject.__init__(self)
        self.fileCachePath = pathlib.Path.home().joinpath(".EvoSeg")
        self.modelDir = self.fileCachePath.joinpath("models")
        self.moduleDir = os.path.dirname(slicer.util.getModule('EvoSeg').path)   # 模块目录
        self.tempDir = slicer.util.tempDirectory()  # 临时目录
        self.pythonExePath = shutil.which("PythonSlicer")   # Python解释器路径

        self.volumeNode = volumeNode
        self.tasks = []                        # 任务列表
        self.taskIndex = -1                    # 当前执行的任务索引

    def getTask(self, taskId: uuid.UUID):
        """
        获取指定ID的任务
        """
        for task in self.tasks:
            if task.taskInfo.id == taskId:
                return task
        return None

    def schedule(self, model: str):
        """
        调度任务，添加一个新任务到任务列表中
        
        参数:
            model: 模型名称，例如 'Airway_nnUnet', 'Artery_nnUnet'
        """
        task = SegTaskFactory.create(self, model)
        self.tasks.append(task)

    def fireNext(self):
        """
        触发下一个任务
        """
        self.taskIndex = self.taskIndex + 1
        if self.taskIndex < 0 or self.taskIndex >= len(self.tasks):
            return
                
        nextTask = self.tasks[self.taskIndex]
        if nextTask is not None and nextTask.taskInfo.status == SegTaskStatus.PENDING:
            try:
                nextTask.taskInfo.status = SegTaskStatus.RUNNING
                nextTask.run(self)
                if nextTask.taskInfo.status == SegTaskStatus.FAILED:
                    self.taskFailed.emit(nextTask.taskInfo, None)
                elif nextTask.taskInfo.status == SegTaskStatus.CANCELLED:
                    self.taskCancelled.emit(nextTask.taskInfo)
                elif nextTask.taskInfo.status == SegTaskStatus.COMPLETED:
                    self.taskCompleted.emit(nextTask.taskInfo)
            except Exception as e:
                logging.error(f"{nextTask.taskInfo.model} segmentation failed: {str(e)}")
                nextTask.taskInfo.status = SegTaskStatus.FAILED
                self.taskLog.emit(nextTask.taskInfo, f"{nextTask.taskInfo.model} segmentation failed: {str(e)}")
                self.taskFailed.emit(nextTask.taskInfo, e)

class SegTask:
    """
    分割任务的基类，定义了所有分割任务共有的属性和方法
    """
    
    def __init__(self, context: SegTaskContext, model: str, command: list[str]):
        self.context = context
        self.taskInfo = SegTaskInfo(context.volumeNode, model, command)

    def run(self, context: SegTaskContext):
        self.taskInfo.process = subprocess.Popen(self.taskInfo.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.taskInfo.stdout, self.taskInfo.stderr = self.taskInfo.process.communicate()
        
        if self.taskInfo.process.returncode == 0:
            self.taskInfo.segmentationNode = slicer.util.getNode(self.taskInfo.volumeNode.GetName() + "_Segmentation")
            self.taskInfo.status = SegTaskStatus.COMPLETED  
        else:
            self.taskInfo.status = SegTaskStatus.FAILED
            
class AirwaySegTask(SegTask):
    """
    气管分割任务类，继承自分割任务基类
    """
    def __init__(self, context: SegTaskContext, model: str, command: list[str]):
        super().__init__(context, model, command)

class SegTaskFactory:
    """
    分割任务工厂类，负责创建分割任务
    """

    @staticmethod
    def defaultCommand(context: SegTaskContext, model: str) -> list[str]:
        """获取脚本的完整路径"""
        command = [
                context.pythonExePath,
                os.path.join(context.moduleDir, "EvoSegLib", "nnunetv2_inference.py"),
                "--model_folder", os.path.join(context.modelDir, model),
                "--image_file", os.path.join(context.tempDir, "input", "input-volume0.nii.gz"),
                "--result_file", os.path.join(context.tempDir, "output", "output-segmentation.nii.gz"),
                "--use_total", "True"
            ]
        return command

    @staticmethod   
    def create(context: SegTaskContext, model: str):
        """
        创建一个分割任务
        
        参数:
            context: 任务上下文
            model: 模型名称，例如 'Airway_nnUnet', 'Artery_nnUnet'
        返回:
            具体的分割任务实例
        """
        # 根据模型类型创建相应的任务实例
        if model.startswith('Airway'):
            return AirwaySegTask(context, model, SegTaskFactory.defaultCommand(context, model))
        else:
            raise ValueError(f"不支持的模型类型: {model}")

class TaskManager(QThread):
    submited = Signal(SegTaskContext)

    def __init__(self, parent=None):
        super(TaskManager, self).__init__(parent)
        self._running = True
        self.contextQueue: List[SegTaskContext] = []

        self._mutex = QMutex()
        self._wait_condition = QWaitCondition()
        self.submited.connect(self.onContextSubmited)

    def stop(self):
        self._running = False
        self._wait_condition.wakeAll()  # 唤醒等待中的线程

    def onContextSubmited(self, context: SegTaskContext):
        self._mutex.lock()
        self.contextQueue.append(context)
        self._mutex.unlock()
        self._wait_condition.wakeAll()  # 唤醒任务线程立即执行

    def run(self):
        while self._running:
            self._mutex.lock()
            try:
                if not self._running:
                    break
                if not self.contextQueue:
                    self._wait_condition.wait(self._mutex, 100)  # 无任务时挂起等待
                
                if self.contextQueue:
                    context = self.contextQueue.pop(0)
                    for task in context.tasks:
                        task.taskInfo.status = SegTaskStatus.PENDING

                    while context.taskIndex + 1 < len(context.tasks):
                        context.fireNext()

                    logging.info("任务上下文完成")
            except Exception as e:
                logging.error(f"获取任务上下文失败: {str(e)}")
            finally:
                self._mutex.unlock()
        