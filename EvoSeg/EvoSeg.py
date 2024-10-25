import logging
import json
import os
from typing import Annotated, Optional

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode

from qt import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QFileDialog

import subprocess
#
# EvoSeg
#


class EvoSeg(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("EvoSeg")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Segmentation")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#EvoSeg">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")
        self.terminologyName = None
        self.anatomicContextName = None

        slicer.app.connect("startupCompleted()", self.configureDefaultTerminology)
        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", self.registerSampleData)

    def configureDefaultTerminology(self):
        moduleDir = os.path.dirname(self.parent.path)
        #terminologyFilePath = os.path.join(moduleDir, "Resources", "SegmentationCategoryTypeModifier-EvoSeg.term.json")
        #anatomicContextFilePath = os.path.join(moduleDir, "Resources", "AnatomicRegionAndModifier-EvoSeg.term.json")
        tlogic = slicer.modules.terminologies.logic()
        #self.terminologyName = tlogic.LoadTerminologyFromFile(terminologyFilePath)
        #self.anatomicContextName = tlogic.LoadAnatomicContextFromFile(anatomicContextFilePath)


    def registerSampleData(self):
        """
        Add data sets to Sample Data module.
        """
        print("~")


#
# EvoSegParameterNode
#


@parameterNodeWrapper
class EvoSegParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# EvoSegWidget
#


class EvoSegWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    PROCESSING_IDLE = 0
    PROCESSING_STARTING = 1
    PROCESSING_IN_PROGRESS = 2
    PROCESSING_IMPORT_RESULTS = 3
    PROCESSING_CANCEL_REQUESTED = 4

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None
        self._updatingGUIFromParameterNode = False
        self._processingState = EvoSegWidget.PROCESSING_IDLE
        self._segmentationProcessInfo = None
        

        with open(os.path.join(os.path.dirname(slicer.util.getModule('EvoSeg').path), "Resources", "AppConfig.json"), 'r') as file:
            app_config = json.load(file)
        self.ui_language = app_config["language"]
        
        self.logic = EvoSegLogic(self.ui_language)

    ##
    # 该临时翻译，仅限于对该插件ui文件中可以搜到字符串的控件进行翻译
    # 
    def translate(self, language="en-US"):
        # 翻译
        en_zh={
            "Advanced": "设置",
            "Apply": "应用",
            "<p>Start segmentation.</p>": "开始分割。",
            "Open models cache folder": "打开模型缓存文件夹",
            "<p>Open the folder that contains all downloaded files for models.</p>":"打开包含所有下载模型文件的文件夹。",
            "<p>Use CPU, even if GPU is available. Useful if the GPU does not have enough memory.</p>": "即使有 GPU 可用，也使用 CPU。如果 GPU 内存不足，则此选项很有用。",
            "<p>Higher value means stronger smoothing during closed surface representation conversion.</p>": "更高的值表示在闭合表面表示转换期间更强的平滑。",
            "Clear cache": "清除缓存",
            "<p>Delete all downloaded files for all models. The files will be automatically downloaded again as needed.</p>": "删除所有模型的所有下载文件。文件会根据需要自动重新下载。",
            "Download": "下载",
            "<p>Download sample data and model set for the current segmentation model</p>": "<p>下载当前分割模型和示例数据集</p>",
            "Full text": "全文",
            "<p>Search in full text of the segmentation model description. Uncheck to search only in the model names.</p>": "在分割模型描述的全文中搜索。取消勾选以仅在模型名称中搜索。",
            "Search...": "搜索...",
            "Input volume:": "输入体积:",
            "Input volume 1:": "输入体积 1：",
            "Input volume 2:": "输入体积 2：",
            "Input volume 3:": "输入体积 3：",
            "Input volume 4:": "输入体积 4：",
            "Inputs": "输入",
            "<p>Translate to chinese</p>": "<p>切换成英文</p>",
            "Force to use CPU: ": "强制使用 CPU：",
            "Segmentation model:": "分割模型：",
            "Show all models:": "显示所有模型：",
            "Segmentation:": "分割：",
            "Manage models:": "管理模型：",
            "Copy to folder":"一键导入",
            "Use standard segment names:": "使用标准分割名称：",
            "EVO Python package:": "EVO Python 包：",
            "<p>List models that contain all the specified words</p>": "列出包含所有指定词的模型",
            "Download model if not saved": "如果未保存则下载模型",
            "<p>Copy it yourself.</p>": "请自行复制。",
            "<p>This will store the segmentation result.</p>": "这将保存分割结果。",
            "Outputs": "输出",
            "Get Python package information": "获取 Python 包信息",
            "<p>Get information on the installed EVO Python package</p>": "获取已安装的 EVO Python 包的信息",
            "Reinstall": "重新安装",
            "<p>Force upgrade of EVO Python package to the version required by this module.</p>": "强制将 EVO Python 包升级到本模块所需的版本。",
            "0.50": "0.50",
            "Show 3D": "显示 3D",
            '<p>Show all models in "Segmentation model" list, including old versions.</p>': "显示“分割模型”列表中的所有模型，包括旧版本。",
            "<p>If enabled (default) then segment names are obtained from Slicer standard terminology files. If disabled then internal identifiers are used as segment names.</p>": "如果启用（默认），则分段名称将从 Slicer 标准术语文件中获取。如果禁用，则使用内部标识符作为分段名称。",
            "<p>Create new segmentation on Apply</p>":"<p>创建新分割</p>",
        }

        if language == "zh-CN":
            for name in dir(self.ui):
                widget = getattr(self.ui, name)
                try:
                    #print(widget.text)
                    widget.setText(en_zh[widget.text])
                except:
                    pass
                try:
                    #print(widget.toolTip)
                    widget.setToolTip(en_zh[widget.toolTip])
                except:
                    pass
            self.ui_language="zh-CN"
        else:
            for name in dir(self.ui):
                widget = getattr(self.ui, name)
                try:
                    #print(widget.text)
                    widget.setText([k for k, v in en_zh.items() if v == widget.text][0])
                except:
                    pass
                try:
                    #print(widget.toolTip)
                    widget.setToolTip([k for k, v in en_zh.items() if v ==widget.toolTip][0])
                except:
                    pass
            self.ui_language="en-US"
        
        save_data={  
            "Name": "EvoSeg",
            "language": "zh-CN"
            }
        save_data["language"] = self.ui_language
        self.logic.ui_language =self.ui_language

        with open(os.path.join(os.path.dirname(slicer.util.getModule('EvoSeg').path), "Resources", "AppConfig.json"), 'w') as file:
            json.dump(save_data, file, indent=4) 
        #print
        # 非官方翻译最后一个版本

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/EvoSeg.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
        
        import qt
        # 下载样本数据按钮设置icon
        self.ui.downloadSampleDataToolButton.setIcon(qt.QIcon(self.resourcePath("Icons/radiology.svg")))
        self.ui.TranslateToolButton.setIcon(qt.QIcon(self.resourcePath("Icons/translate.svg")))
        self.ui.ImportModelToolButton.setIcon(qt.QIcon(self.resourcePath("Icons/import_model.svg")))
        self.ui.ImportModelToolButton.hide() # 进一步明确模型描述信息后启用

        self.inputNodeSelectors = [self.ui.inputNodeSelector0, self.ui.inputNodeSelector1, self.ui.inputNodeSelector2, self.ui.inputNodeSelector3]
        self.inputNodeLabels = [self.ui.inputNodeLabel0, self.ui.inputNodeLabel1, self.ui.inputNodeLabel2, self.ui.inputNodeLabel3]


        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        # EvoSegLogic()直接copy EvoSegLogic()
        self.logic.logCallback = self.addLog
        self.logic.processingCompletedCallback = self.onProcessingCompleted
        self.logic.startResultImportCallback = self.onProcessImportStarted
        self.logic.endResultImportCallback = self.onProcessImportEnded

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

         # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).
        for inputNodeSelector in self.inputNodeSelectors:
            inputNodeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.fullTextSearchCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        # NOTE:已隐藏暂时没有用的选项
        # self.ui.cpuCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        self.ui.showAllModelsCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        self.ui.useStandardSegmentNamesCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)

        self.ui.modelSearchBox.connect("textChanged(QString)", self.updateParameterNodeFromGUI)
        self.ui.modelComboBox.currentTextChanged.connect(self.updateParameterNodeFromGUI)
        self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.ui.segmentationShow3DButton.setSegmentationNode)
        #self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.ui.segmentationEditor_.setSegmentationNode)

        # Buttons
        self.ui.downloadSampleDataToolButton.connect("clicked(bool)", self.onDownloadSampleData)
        self.ui.TranslateToolButton.connect("clicked(bool)", self.tr_ui)
        self.ui.ImportModelToolButton.connect("clicked(bool)", self.onInputLocalModel)
        self.ui.copyModelsButton.connect("clicked(bool)", self.onCopyModel)
        self.ui.packageInfoUpdateButton.connect("clicked(bool)", self.onPackageInfoUpdate)
        self.ui.packageUpgradeButton.connect("clicked(bool)", self.onPackageUpgrade)
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)
        self.ui.browseToModelsFolderButton.connect("clicked(bool)", self.onBrowseModelsFolder)
        self.ui.deleteAllModelsButton.connect("clicked(bool)", self.onClearModelsFolder)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

        self.updateGUIFromParameterNode()

        # Make the model search box in focus by default so users can just start typing to find the model they need
        qt.QTimer.singleShot(0, self.ui.modelSearchBox.setFocus)

        # NOTE: 弃用
        # self.ui.translate_ui.connect("toggled(bool)", self.tr_ui)

        # if cn , language set
        if(self.ui_language=="zh-CN"):
            self.translate("zh-CN")

    def onCopyModel(self):
        
        from qt import QMessageBox 
        if os.path.exists(os.path.join(self.logic.modelsPath(),"Airway_nnUnet(artery)")):
            QMessageBox.warning(None, "不可导入", f"模型Airway nnUnet(artery)路径已存在!\n清除缓存再试")
            return
        import qt
        copy2dir= os.path.join(self.logic.modelsPath())
        print(self.logic.modelsPath())
        if not os.path.exists(copy2dir):
            os.makedirs(copy2dir)
            
        select_file = QFileDialog.getOpenFileNames(None, "选择文件", "", "File (*.7z)")
        
        

        self.logic.extract_7z(select_file[0],copy2dir)
        print("ok?")
        

    def onInputLocalModel(self):
        print("input local model")
        # file_name, _ = QFileDialog.getOpenFileName(None, "选择文件", "", "File (*.7z)")
        # if file_name:
            # text, ok = QInputDialog.getText(None, "输入对话框", "当前版本不允许自定义模型导入:",text="Airway nnUnet(artery)")
            # if ok and text:
            #     print(f"你输入了: {text}")
            # else:
            #     print("你取消了输入")
        # else:
        #     return

    def tr_ui(self):
        #if self.ui.translate_ui.checked:
        if self.ui_language=="en-US":
            self.translate("zh-CN")
            #self.ui.translate_ui.setEnabled(False)
        else:
            self.translate()

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        # if self._parameterNode:
        #     self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
        #     self._parameterNodeGuiTag = None
        #     self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        # if not self._parameterNode.inputVolume:
        #     firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
        #     if firstVolumeNode:
        #         self._parameterNode.inputVolume = firstVolumeNode
        if not self._parameterNode.GetNodeReference("InputNode0"):
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.SetNodeReferenceID("InputNode0", firstVolumeNode.GetID())

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()


        # if self._parameterNode:
        #     self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
        #     self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        # self._parameterNode = inputParameterNode
        # if self._parameterNode:
        #     # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
        #     # ui element that needs connection.
        #     self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
        #     self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        #     self._checkCanApply()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """
        import qt

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True
        try:

            self.ui.modelSearchBox.text = self._parameterNode.GetParameter("ModelSearchText")

            searchWords = self._parameterNode.GetParameter("ModelSearchText").lower().split()
            fullTextSearch = self._parameterNode.GetParameter("FullTextSearch") == "true"
            showAllModels = self._parameterNode.GetParameter("ShowAllModels") == "true"
            self.ui.modelComboBox.clear()
            for model in self.logic.models:

                if model.get("deprecated"):
                    if showAllModels:
                        modelTitle = f"{model['title']} (v{model['version']}) -- deprecated"
                    else:
                        # Do not show deprecated models
                        continue
                else:
                    if showAllModels:
                        modelTitle = f"{model['title']} (v{model['version']})"
                    else:
                        modelTitle = model['title']

                if searchWords:
                    textToSearchIn = modelTitle.lower()
                    if fullTextSearch:
                        textToSearchIn += " " + model.get("description").lower() + " " + model.get("imagingModality").lower()
                        segmentNames = model.get("segmentNames")
                        if segmentNames:
                            segmentNames = " ".join(segmentNames)
                            textToSearchIn += " " + segmentNames.lower()
                    if not all(word in textToSearchIn for word in searchWords):
                        continue

                itemIndex = self.ui.modelComboBox.count
                self.ui.modelComboBox.addItem(modelTitle)
                item = self.ui.modelComboBox.item(itemIndex)
                item.setData(qt.Qt.UserRole, model["id"])
                item.setData(qt.Qt.ToolTipRole, "<html>" + model.get("details") + "</html>")

            modelId = self._parameterNode.GetParameter("Model")
            currentModelSelectable = self._setCurrentModelId(modelId)
            if not currentModelSelectable:
                modelId = ""
            sampleDataAvailable = self.logic.model(modelId).get("inputs") if modelId else False
            self.ui.downloadSampleDataToolButton.visible = sampleDataAvailable

            self.ui.fullTextSearchCheckBox.checked = fullTextSearch
            #self.ui.cpuCheckBox.checked = self._parameterNode.GetParameter("CPU") == "true"
            self.ui.showAllModelsCheckBox.checked = showAllModels
            self.ui.useStandardSegmentNamesCheckBox.checked = self._parameterNode.GetParameter("UseStandardSegmentNames") == "true"
            self.ui.outputSegmentationSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputSegmentation"))

            state = self._processingState
            if state == EvoSegWidget.PROCESSING_IDLE:
                self.ui.applyButton.text = "Apply" if self.ui_language=="en-US" else "应用"
                inputErrorMessages = []  # it will contain text if the inputs are not valid
                if modelId:
                    modelInputs = self.logic.model(modelId)["inputs"]
                else:
                    modelInputs = []
                    inputErrorMessages.append("Select a model.")
                inputNodes = []  # list of output nodes so far, for checking for duplicates
                for inputIndex in range(len(self.inputNodeSelectors)):
                    inputNodeSelector = self.inputNodeSelectors[inputIndex]
                    inputNodeLabel = self.inputNodeLabels[inputIndex]
                    if inputIndex < len(modelInputs):
                        inputNodeLabel.visible = True
                        inputTitle = modelInputs[inputIndex]["title"]
                        inputNodeLabel.text = f"{inputTitle}:"
                        inputNodeSelector.visible = True
                        inputNode = self._parameterNode.GetNodeReference("InputNode" + str(inputIndex))
                        inputNodeSelector.setCurrentNode(inputNode)
                        if inputIndex == 0 and inputNode:
                            self.ui.outputSegmentationSelector.baseName = inputNode.GetName() + " segmentation"
                        if not inputNode:
                            inputErrorMessages.append(f"Select {inputTitle}.")
                        else:
                            if inputNode in inputNodes:
                                inputErrorMessages.append(f"'{inputTitle}' does not have a unique input ('{inputNode.GetName()}' is already used as another input).")
                            inputNodes.append(inputNode)
                    else:
                        inputNodeLabel.visible = False
                        inputNodeSelector.visible = False

                if inputErrorMessages:
                    self.ui.applyButton.toolTip = "\n".join(inputErrorMessages)
                    self.ui.applyButton.enabled = False
                else:
                    self.ui.applyButton.toolTip = "Start segmentation" if self.ui_language=="en-US" else "开始分割"
                    self.ui.applyButton.enabled = True

            elif state == EvoSegWidget.PROCESSING_STARTING:
                self.ui.applyButton.text = "Starting..." if self.ui_language=="en-US" else "启动中..."
                self.ui.applyButton.toolTip = "Please wait while the segmentation is being initialized" if self.ui_language=="en-US" else "请稍等，分割正在初始化"
                self.ui.applyButton.enabled = False
            elif state == EvoSegWidget.PROCESSING_IN_PROGRESS:
                self.ui.applyButton.text = "Cancel" if self.ui_language=="en-US" else "取消"
                self.ui.applyButton.toolTip = "Cancel in-progress segmentation" if self.ui_language=="en-US" else "停止分割进程"
                self.ui.applyButton.enabled = True
            elif state == EvoSegWidget.PROCESSING_IMPORT_RESULTS:
                self.ui.applyButton.text = "Importing results..." if self.ui_language=="en-US" else "载入结果..."
                self.ui.applyButton.toolTip = "Please wait while the segmentation result is being imported" if self.ui_language=="en-US" else "请稍等，分割结果正在载入"
                self.ui.applyButton.enabled = False
            elif state == EvoSegWidget.PROCESSING_CANCEL_REQUESTED:
                self.ui.applyButton.text = "Cancelling..." if self.ui_language=="en-US" else "正在取消..."
                self.ui.applyButton.toolTip = "Please wait for the segmentation to be cancelled" if self.ui_language=="en-US" else "请等待分割进程退出"
                self.ui.applyButton.enabled = False

        finally:
            # All the GUI updates are done
            self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        try:

            for inputIndex in range(len(self.inputNodeSelectors)):
                inputNodeSelector = self.inputNodeSelectors[inputIndex]
                self._parameterNode.SetNodeReferenceID("InputNode" + str(inputIndex), inputNodeSelector.currentNodeID)

            self._parameterNode.SetParameter("ModelSearchText", self.ui.modelSearchBox.text)
            modelId = self._currentModelId()
            if modelId:
                # Only save model ID if valid, otherwise it is temporarily filtered out in the selector
                self._parameterNode.SetParameter("Model", modelId)
            self._parameterNode.SetParameter("FullTextSearch", "true" if self.ui.fullTextSearchCheckBox.checked else "false")
            #self._parameterNode.SetParameter("CPU", "true" if self.ui.cpuCheckBox.checked else "false")
            self._parameterNode.SetParameter("ShowAllModels", "true" if self.ui.showAllModelsCheckBox.checked else "false")
            self._parameterNode.SetParameter("UseStandardSegmentNames", "true" if self.ui.useStandardSegmentNamesCheckBox.checked else "false")
            self._parameterNode.SetNodeReferenceID("OutputSegmentation", self.ui.outputSegmentationSelector.currentNodeID)

        finally:
            self._parameterNode.EndModify(wasModified)

    def addLog(self, text):
        """Append text to log window
        """
        self.ui.statusLabel.appendPlainText(text)
        slicer.app.processEvents()  # force update

    def setProcessingState(self, state):
        self._processingState = state
        self.updateGUIFromParameterNode()
        slicer.app.processEvents()


    # def _checkCanApply(self, caller=None, event=None) -> None:
    #     if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
    #         self.ui.applyButton.toolTip = _("Compute output volume")
    #         self.ui.applyButton.enabled = True
    #     else:
    #         self.ui.applyButton.toolTip = _("Select input and output volume nodes")
    #         self.ui.applyButton.enabled = False

    # def onApplyButton(self) -> None:
    #     """Run processing when user clicks "Apply" button."""
    #     with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
    #         # Compute output
    #         self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
    #                            self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

    #         # Compute inverted output (if needed)
    #         if self.ui.invertedOutputSelector.currentNode():
    #             # If additional output volume is selected then result with inverted threshold is written there
    #             self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
    #                                self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """

        if self._processingState == EvoSegWidget.PROCESSING_IDLE:
            self.onApply()
        else:
            self.onCancel()
        
        # NOTE: 临时重置视图到中心
        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        # 重置视图焦点到场景中心
        threeDView.resetFocalPoint()
        # 重新渲染
        threeDView.forceRender()


    def onApply(self):
        self.ui.statusLabel.plainText = ""

        self.setProcessingState(EvoSegWidget.PROCESSING_STARTING)

        if not self.logic.dependenciesInstalled:
            with slicer.util.tryWithErrorDisplay("Failed to install required dependencies.", waitCursor=True):
                self.logic.setupPythonRequirements()

        try:
            with slicer.util.tryWithErrorDisplay("Failed to start processing.", waitCursor=True):

                # Create new segmentation node, if not selected yet
                if not self.ui.outputSegmentationSelector.currentNode():
                    self.ui.outputSegmentationSelector.addNode()

                self.logic.useStandardSegmentNames = self.ui.useStandardSegmentNamesCheckBox.checked

                # Compute output
                inputNodes = []
                for inputNodeSelector in self.inputNodeSelectors:
                    if inputNodeSelector.visible:
                        inputNodes.append(inputNodeSelector.currentNode())
                # self._segmentationProcessInfo = self.logic.process(inputNodes, self.ui.outputSegmentationSelector.currentNode(),
                #     self._currentModelId(), self.ui.noDownloadSearchCheckBox.checked, self.ui.cpuCheckBox.checked, waitForCompletion=False)
                self._segmentationProcessInfo = self.logic.process(inputNodes, self.ui.outputSegmentationSelector.currentNode(),
                    self._currentModelId(), False, False, waitForCompletion=False)
                self.setProcessingState(EvoSegWidget.PROCESSING_IN_PROGRESS)

        except Exception as e:
            self.setProcessingState(EvoSegWidget.PROCESSING_IDLE)

    def onCancel(self):
        with slicer.util.tryWithErrorDisplay("Failed to cancel processing.", waitCursor=True):
            self.logic.cancelProcessing(self._segmentationProcessInfo)
            self.setProcessingState(EvoSegWidget.PROCESSING_CANCEL_REQUESTED)

    def onProcessImportStarted(self, customData):
        self.setProcessingState(EvoSegWidget.PROCESSING_IMPORT_RESULTS)
        import qt
        qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
        slicer.app.processEvents()

    def onProcessImportEnded(self, customData):
        import qt
        qt.QApplication.restoreOverrideCursor()
        slicer.app.processEvents()

    def onProcessingCompleted(self, returnCode, customData):
        self.ui.statusLabel.appendPlainText("\nProcessing finished.")
        self.setProcessingState(EvoSegWidget.PROCESSING_IDLE)
        self._segmentationProcessInfo = None

    def _currentModelId(self):
        import qt
        itemIndex = self.ui.modelComboBox.currentRow
        item = self.ui.modelComboBox.item(itemIndex)
        if not item:
            return ""
        return item.data(qt.Qt.UserRole)

    def _setCurrentModelId(self, modelId):
        import qt
        for itemIndex in range(self.ui.modelComboBox.count):
            item = self.ui.modelComboBox.item(itemIndex)
            if item.data(qt.Qt.UserRole) == modelId:
                self.ui.modelComboBox.setCurrentRow(itemIndex)
                return True
        return False

    def onDownloadSampleData(self):
        model = self.logic.model(self._currentModelId())
        sampleDataName = model.get("sampleData")
        if not sampleDataName:
            slicer.util.messageBox("No sample data is available for this model.")
            return

        if type(sampleDataName) == list:
            # For now, always just use the first data set if multiple data sets are provided
            sampleDataName = sampleDataName[0]

        with slicer.util.tryWithErrorDisplay("Failed to download sample data", waitCursor=True):
            import SampleData
            loadedSampleNodes = SampleData.SampleDataLogic().downloadSamples(sampleDataName)
            inputs = model.get("inputs")

        if not loadedSampleNodes:
            slicer.util.messageBox(f"Failed to load sample data set '{sampleDataName}'.")
            return

        inputNodes = EvoSegLogic.assignInputNodesByName(inputs, loadedSampleNodes)
        #print(inputNodes)
        for inputIndex, inputNode in enumerate(inputNodes):
            #print(inputIndex, inputNode)
            if inputNode:
                self.inputNodeSelectors[inputIndex].setCurrentNode(inputNode)

    def onPackageInfoUpdate(self):
        self.ui.packageInfoTextBrowser.plainText = ""
        with slicer.util.tryWithErrorDisplay("Failed to get EVO package version information", waitCursor=True):
            self.ui.packageInfoTextBrowser.plainText = self.logic.installedEVOPythonPackageInfo().rstrip()

    def onPackageUpgrade(self):
        with slicer.util.tryWithErrorDisplay("Failed to upgrade EVO", waitCursor=True):
            self.logic.setupPythonRequirements(upgrade=True)
        self.onPackageInfoUpdate()
        if not slicer.util.confirmOkCancelDisplay(f"This EVO update requires a 3D Slicer restart.","Press OK to restart."):
            raise ValueError("Restart was cancelled.")
        else:
            slicer.util.restart()

    def onBrowseModelsFolder(self):
        import qt
        self.logic.createModelsDir()
        qt.QDesktopServices().openUrl(qt.QUrl.fromLocalFile(self.logic.modelsPath()))

    def onClearModelsFolder(self):
        if not os.path.exists(self.logic.modelsPath()):
            slicer.util.messageBox("There are no downloaded models.")
            return
        if not slicer.util.confirmOkCancelDisplay("All downloaded model files will be deleted. The files will be automatically downloaded again as needed."):
            return
        self.logic.deleteAllModels()
        slicer.util.messageBox("Downloaded models are deleted.")

#
# EvoSegLogic
#


class EvoSegLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """
    
    EXIT_CODE_USER_CANCELLED = 1001
    EXIT_CODE_DID_NOT_RUN = 1002
    
    def __init__(self,the_ui_language) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)
        from collections import OrderedDict
        import pathlib
        self.fileCachePath = pathlib.Path.home().joinpath(".EvoSeg")

        self.dependenciesInstalled = False  # we don't know yet if dependencies have been installed

        self.moduleDir = os.path.dirname(slicer.util.getModule('EvoSeg').path)

        self.logCallback = None
        self.processingCompletedCallback = None
        self.startResultImportCallback = None
        self.endResultImportCallback = None
        self.useStandardSegmentNames = True
        self.ui_language = the_ui_language

        # List of property type codes that are specified by in the EvoSeg terminology.
        #
        # Codes are stored as a list of strings containing coding scheme designator and code value of the property type,
        # separated by "^" character. For example "SCT^123456".
        #
        # If property the code is found in this list then the EvoSeg terminology will be used,
        # otherwise the DICOM terminology will be used. This is necessary because the DICOM terminology
        # does not contain all the necessary items and some items are incomplete (e.g., don't have color or 3D Slicer label).
        #
        
        #self.EvoSegTerminologyPropertyTypes = self._EvoSegTerminologyPropertyTypes()

        # List of anatomic regions that are specified by EvoSeg.
        self.EvoSegAnatomicRegions = self._EvoSegAnatomicRegions()

        # Segmentation models specified by in models.json file
        self.models = self.loadModelsDescription()
        self.defaultModel = self.models[0]["id"]

        # Timer for checking the output of the segmentation process that is running in the background
        self.processOutputCheckTimerIntervalMsec = 1000

        # Disabling this flag preserves input and output data after execution is completed,
        # which can be useful for troubleshooting.
        self.clearOutputFolder = True

        # For testing the logic without actually running inference, set self.debugSkipInferenceTempDir to the location
        # where inference result is stored and set self.debugSkipInference to True.
        self.debugSkipInference = False
        self.debugSkipInferenceTempDir = r"c:\Users\andra\AppData\Local\Temp\Slicer\__SlicerTemp__2024-01-16_15+26+25.624"

    def model(self, modelId):
        for model in self.models:
            if model["id"] == modelId:
                return model
        raise RuntimeError(f"Model {modelId} not found")


    def modelsDescriptionJsonFilePath(self):
        return os.path.join(self.moduleDir, "Resources", "Models.json")

    def loadModelsDescription(self):
        modelsJsonFilePath = self.modelsDescriptionJsonFilePath()
        try:
            models = []
            import json
            import re
            with open(modelsJsonFilePath) as f:
                modelsTree = json.load(f)["models"]
            for model in modelsTree:
                deprecated = False
                for version in model["versions"]:
                    url = version["url"]
                    # URL format: <path>/<filename>-v<version>.zip
                    # Example URL: https://github.com/lassoan/SlicerEvoSeg/releases/download/Models/17-segments-TotalSegmentator-v1.0.3.zip
                    match = re.search(r"(?P<filename>[^/]+)-v(?P<version>\d+\.\d+\.\d+)", url)
                    if match:
                        filename = match.group("filename")
                        version = match.group("version")
                    else:
                        if model['license'] == "EvoSeg": # TODO: 上下文约束了url格式，这里临时修改，此外在models.json中暂时用license区分自己添加进去的模型
                            filename = model["title"]
                            version = "1"
                        else:
                            logging.error(f"Failed to extract model id and version from url: {url} ")
                    if "inputs" in model:
                        # Contains a list of dict. One dict for each input.
                        # Currently, only "title" (user-displayable name) and "namePattern" of the input are specified.
                        # In the future, inputs could have additional properties, such as name, type, optional, ...
                        #print(self.ui_language,"<<<<<")
                        inputs = model["inputs"]
                    else:
                        # Inputs are not defined, use default (single input volume)
                        #print(self.ui_language,"<<<<<")
                        # 暂不好翻译
                        inputs = [{"title": "Input volume"}] if self.ui_language=="en-US" else [{"title": "输入体积"}]
                    segmentNames = model.get('segmentNames')
                    if not segmentNames:
                        segmentNames = "N/A"
                    models.append({
                        "id": f"{filename}",#-v{version}",
                        "title": model['title'],
                        "version": version,
                        "inputs": inputs,
                        "imagingModality": model["imagingModality"],
                        "description": model["description"],
                        "sampleData": model.get("sampleData"),
                        "segmentNames": model.get("segmentNames"),
                        "details":
                            f"<p><b>Model:</b> {model['title']} (v{version})"
                            f"<p><b>Description:</b> {model['description']}\n"
                            f"<p><b>Imaging modality:</b> {model['imagingModality']}\n"
                            f"<p><b>Subject:</b> {model['subject']}\n"
                            f"<p><b>Segments:</b> {', '.join(segmentNames)}",
                        "url": url,
                        "deprecated": deprecated
                        })
                    # First version is not deprecated, all subsequent versions are deprecated
                    deprecated = True
            return models
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Failed to load models description from {modelsJsonFilePath}")

    @staticmethod
    def humanReadableTimeFromSec(seconds):
        import math
        if not seconds:
            return "N/A"
        if seconds < 55:
            # if less than a minute, round up to the nearest 5 seconds
            return f"{math.ceil(seconds/5) * 5} sec"
        elif seconds < 60 * 60:
            # if less then 1 hour, round up to the nearest minute
            return f"{math.ceil(seconds/60)} min"
        # Otherwise round up to the nearest 0.1 hour
        return f"{seconds/3600:.1f} h"

    def modelsPath(self):
        import pathlib
        return self.fileCachePath.joinpath("models")

    def createModelsDir(self):
        modelsDir = self.modelsPath()
        if not os.path.exists(modelsDir):
            os.makedirs(modelsDir)

    def modelPath(self, modelName):
        import pathlib
        modelRoot = self.modelsPath().joinpath(modelName)
        # find labels.csv file within the modelRoot folder and subfolders
        # for path in pathlib.Path(modelRoot).rglob("labels.csv"): # TODO: 原项目强制要求labels.csv存在
        #     return path.parent
        # modelRoot = self.modelsPath().joinpath(modelName)
        for path in pathlib.Path(modelRoot).rglob("dataset.json"):
            return path.parent
        raise RuntimeError(f"Model {modelName} path not found, You can try:\n 1. click 'open model cache folder' button -> Create a folder name of model name -> Extract your model json and fold_x to this folder.\n 2. click 'Copy to folder' button -> Select your model_name.7z")


    def deleteAllModels(self):
        if self.modelsPath().exists():
            import shutil
            shutil.rmtree(self.modelsPath())

    def extract_7z(self, archive, destination):
        try:
            subprocess.run(['7z', 'x', archive, f'-o{destination}'], check=True)
            print(f"Successfully extracted {archive} to {destination}")
        except subprocess.CalledProcessError as e:
            print(f"Error during extraction: {e}")

    def downloadModel(self, modelName, withDownload):

        url = self.model(modelName)["url"]

        import zipfile
        import requests
        import pathlib

        tempDir = pathlib.Path(slicer.util.tempDirectory())
        modelDir = self.modelsPath().joinpath(modelName)
        print("Evo model download dir: ",modelDir)
        if not os.path.exists(modelDir):
            os.makedirs(modelDir)

        modelZipFile = tempDir.joinpath("autoseg3d_model.zip")
        self.log(f"Downloading model '{modelName}' from {url}...")
        logging.debug(f"Downloading from {url} to {modelZipFile}...")
        
        if not withDownload:
            return
        try:
            with open(modelZipFile, 'wb') as f:
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    reporting_increment_percent = 1.0
                    last_reported_download_percent = -reporting_increment_percent
                    downloaded_size = 0
                    for chunk in r.iter_content(chunk_size=8192 * 16):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        downloaded_percent = 100.0 * downloaded_size / total_size
                        if downloaded_percent - last_reported_download_percent > reporting_increment_percent:
                            self.log(f"Downloading model: {downloaded_size/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB ({downloaded_percent:.1f}%)")
                            last_reported_download_percent = downloaded_percent

            self.log(f"Download finished. Extracting to {modelDir}... \n EvgSeg can not should down it")
            with zipfile.ZipFile(modelZipFile, 'r') as zip_f:
                zip_f.extractall(modelDir)
        except Exception as e:
            raise e
        finally:
            if self.clearOutputFolder:
                self.log("Cleaning up temporary model download folder...")
                if os.path.isdir(tempDir):
                    import shutil
                    shutil.rmtree(tempDir)
            else:
                self.log(f"Not cleaning up temporary model download folder: {tempDir}")

    def _EvoSegTerminologyPropertyTypes(self):
        """Get label terminology property types defined in from EVO Auto3DSeg terminology.
        Terminology entries are either in DICOM or EVO Auto3DSeg "Segmentation category and type".
        """

        terminologiesLogic = slicer.util.getModuleLogic("Terminologies")
        EvoSegTerminologyName = slicer.modules.EvoSegInstance.terminologyName

        # Get anatomicalStructureCategory from the EVO Auto3DSeg terminology
        anatomicalStructureCategory = slicer.vtkSlicerTerminologyCategory()
        numberOfCategories = terminologiesLogic.GetNumberOfCategoriesInTerminology(EvoSegTerminologyName)
        for i in range(numberOfCategories):
            terminologiesLogic.GetNthCategoryInTerminology(EvoSegTerminologyName, i, anatomicalStructureCategory)
            if anatomicalStructureCategory.GetCodingSchemeDesignator() == "SCT" and anatomicalStructureCategory.GetCodeValue() == "123037004":
                # Found the (123037004, SCT, "Anatomical Structure") category within DICOM master list
                break

        # Retrieve all anatomicalStructureCategory property type codes
        terminologyPropertyTypes = []
        terminologyType = slicer.vtkSlicerTerminologyType()
        numberOfTypes = terminologiesLogic.GetNumberOfTypesInTerminologyCategory(EvoSegTerminologyName, anatomicalStructureCategory)
        for i in range(numberOfTypes):
            if terminologiesLogic.GetNthTypeInTerminologyCategory(EvoSegTerminologyName, anatomicalStructureCategory, i, terminologyType):
                terminologyPropertyTypes.append(terminologyType.GetCodingSchemeDesignator() + "^" + terminologyType.GetCodeValue())

        return terminologyPropertyTypes

    def _EvoSegAnatomicRegions(self):
        """Get anatomic regions defined in from EVO Auto3DSeg terminology.
        Terminology entries are either in DICOM or EVO Auto3DSeg "Anatomic codes".
        """
        anatomicRegions = []

        terminologiesLogic = slicer.util.getModuleLogic("Terminologies")
        if not hasattr(terminologiesLogic, "GetNumberOfRegionsInAnatomicContext"):
            # This Slicer version does not have GetNumberOfRegionsInAnatomicContext method,
            # do not add the region modifier (the only impact is that the modifier will not be selectable
            # when editing the terminology on the GUI)
            return anatomicRegions

        EvoSegAnatomicContextName = slicer.modules.EvoSegInstance.anatomicContextName

        # Retrieve all anatomical region codes

        regionObject = slicer.vtkSlicerTerminologyType()
        numberOfRegions = terminologiesLogic.GetNumberOfRegionsInAnatomicContext(EvoSegAnatomicContextName)
        for i in range(numberOfRegions):
            if terminologiesLogic.GetNthRegionInAnatomicContext(EvoSegAnatomicContextName, i, regionObject):
                anatomicRegions.append(regionObject.GetCodingSchemeDesignator() + "^" + regionObject.GetCodeValue())

        return anatomicRegions

    def labelDescriptions(self, modelName):
        """Return mapping from label value to label description.
        Label description is a dict containing "name" and "terminology".
        Terminology string uses Slicer terminology entry format - see specification at
        https://slicer.readthedocs.io/en/latest/developer_guide/modules/segmentations.html#terminologyentry-tag
        """

        # Helper function to get code string from CSV file row
        def getCodeString(field, columnNames, row):
            columnValues = []
            for fieldName in ["CodingSchemeDesignator", "CodeValue", "CodeMeaning"]:
                columnIndex = columnNames.index(f"{field}.{fieldName}")
                try:
                    columnValue = row[columnIndex]
                except IndexError:
                    # Probably the line in the CSV file was not terminated by multiple commas (,)
                    columnValue = ""
                columnValues.append(columnValue)
            return columnValues

        labelDescriptions = {}
        labelsFilePath = self.modelPath(modelName).joinpath("labels.csv")
        print("in this version No should labels.csv",labelsFilePath) # NOTE: label is should define in futrue??
        # import csv
        # with open(labelsFilePath, "r") as f:
        #     reader = csv.reader(f)
        #     columnNames = next(reader)
        #     data = {}
        #     # Loop through the rows of the csv file
        #     for row in reader:

        #         # Determine segmentation category (DICOM or EvoSeg)
        #         terminologyPropertyTypeStr = (  # Example: SCT^23451007
        #             row[columnNames.index("SegmentedPropertyTypeCodeSequence.CodingSchemeDesignator")]
        #             + "^" + row[columnNames.index("SegmentedPropertyTypeCodeSequence.CodeValue")])
        #         if terminologyPropertyTypeStr in self.EvoSegTerminologyPropertyTypes:
        #             terminologyName = slicer.modules.EvoSegInstance.terminologyName
        #         else:
        #             terminologyName = "Segmentation category and type - DICOM master list"

        #         # Determine the anatomic context name (DICOM or EvoSeg)
        #         anatomicRegionStr = (  # Example: SCT^279245009
        #             row[columnNames.index("AnatomicRegionSequence.CodingSchemeDesignator")]
        #             + "^" + row[columnNames.index("AnatomicRegionSequence.CodeValue")])
        #         if anatomicRegionStr in self.EvoSegAnatomicRegions:
        #             anatomicContextName = slicer.modules.EvoSegInstance.anatomicContextName
        #         else:
        #             anatomicContextName = "Anatomic codes - DICOM master list"

        #         terminologyEntryStr = (
        #             terminologyName
        #             +"~"
        #             # Property category: "SCT^123037004^Anatomical Structure" or "SCT^49755003^Morphologically Altered Structure"
        #             + "^".join(getCodeString("SegmentedPropertyCategoryCodeSequence", columnNames, row))
        #             + "~"
        #             # Property type: "SCT^23451007^Adrenal gland", "SCT^367643001^Cyst", ...
        #             + "^".join(getCodeString("SegmentedPropertyTypeCodeSequence", columnNames, row))
        #             + "~"
        #             # Property type modifier: "SCT^7771000^Left", ...
        #             + "^".join(getCodeString("SegmentedPropertyTypeModifierCodeSequence", columnNames, row))
        #             + "~"
        #             + anatomicContextName
        #             + "~"
        #             # Anatomic region (set if category is not anatomical structure): "SCT^64033007^Kidney", ...
        #             + "^".join(getCodeString("AnatomicRegionSequence", columnNames, row))
        #             + "~"
        #             # Anatomic region modifier: "SCT^7771000^Left", ...
        #             + "^".join(getCodeString("AnatomicRegionModifierSequence", columnNames, row))
        #             )

        #         # Store the terminology string for this structure
        #         labelValue = int(row[columnNames.index("LabelValue")])
        #         name = row[columnNames.index("Name")]
        #         labelDescriptions[labelValue] = { "name": name, "terminology": terminologyEntryStr }
        # labelDescriptions[0] = { "name": "none", "terminology": "terminologyEntryStr" }
        # labelDescriptions[1] = { "name": "none", "terminology": "terminologyEntryStr" }
        # labelDescriptions[2] = { "name": "none", "terminology": "terminologyEntryStr" }
        print("labelDescriptions",labelDescriptions)
        return labelDescriptions

    def getSegmentLabelColor(self, terminologyEntryStr):
        """Get segment label and color from terminology"""

        def labelColorFromTypeObject(typeObject):
            """typeObject is a terminology type or type modifier"""
            label = typeObject.GetSlicerLabel() if typeObject.GetSlicerLabel() else typeObject.GetCodeMeaning()
            rgb = typeObject.GetRecommendedDisplayRGBValue()
            return label, (rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)

        tlogic = slicer.modules.terminologies.logic()

        terminologyEntry = slicer.vtkSlicerTerminologyEntry()
        if not tlogic.DeserializeTerminologyEntry(terminologyEntryStr, terminologyEntry):
            raise RuntimeError(f"Failed to deserialize terminology string: {terminologyEntryStr}")

        numberOfTypes = tlogic.GetNumberOfTypesInTerminologyCategory(terminologyEntry.GetTerminologyContextName(), terminologyEntry.GetCategoryObject())
        foundTerminologyEntry = slicer.vtkSlicerTerminologyEntry()
        for typeIndex in range(numberOfTypes):
            tlogic.GetNthTypeInTerminologyCategory(terminologyEntry.GetTerminologyContextName(), terminologyEntry.GetCategoryObject(), typeIndex, foundTerminologyEntry.GetTypeObject())
            if terminologyEntry.GetTypeObject().GetCodingSchemeDesignator() != foundTerminologyEntry.GetTypeObject().GetCodingSchemeDesignator():
                continue
            if terminologyEntry.GetTypeObject().GetCodeValue() != foundTerminologyEntry.GetTypeObject().GetCodeValue():
                continue
            if terminologyEntry.GetTypeModifierObject() and terminologyEntry.GetTypeModifierObject().GetCodeValue():
                # Type has a modifier, get the color from there
                numberOfModifiers = tlogic.GetNumberOfTypeModifiersInTerminologyType(terminologyEntry.GetTerminologyContextName(), terminologyEntry.GetCategoryObject(), terminologyEntry.GetTypeObject())
                foundMatchingModifier = False
                for modifierIndex in range(numberOfModifiers):
                    tlogic.GetNthTypeModifierInTerminologyType(terminologyEntry.GetTerminologyContextName(), terminologyEntry.GetCategoryObject(), terminologyEntry.GetTypeObject(),
                        modifierIndex, foundTerminologyEntry.GetTypeModifierObject())
                    if terminologyEntry.GetTypeModifierObject().GetCodingSchemeDesignator() != foundTerminologyEntry.GetTypeModifierObject().GetCodingSchemeDesignator():
                        continue
                    if terminologyEntry.GetTypeModifierObject().GetCodeValue() != foundTerminologyEntry.GetTypeModifierObject().GetCodeValue():
                        continue
                    return labelColorFromTypeObject(foundTerminologyEntry.GetTypeModifierObject())
                continue
            return labelColorFromTypeObject(foundTerminologyEntry.GetTypeObject())

        raise RuntimeError(f"Color was not found for terminology {terminologyEntryStr}")

    @staticmethod
    def _findFirstNodeBynamePattern(namePattern, nodes):
        import fnmatch
        for node in nodes:
            if fnmatch.fnmatchcase(node.GetName(), namePattern):
                return node
        return None

    @staticmethod
    def assignInputNodesByName(inputs, loadedSampleNodes):
        inputNodes = []
        for inputIndex, input in enumerate(inputs):
            namePattern = input.get("namePattern")
            if namePattern:
                matchingNode = EvoSegLogic._findFirstNodeBynamePattern(namePattern, loadedSampleNodes)
            else:
                matchingNode = loadedSampleNodes[inputIndex] if inputIndex < len(loadedSampleNodes) else loadedSampleNodes[0]
            inputNodes.append(matchingNode)
        return inputNodes

    def log(self, text):
        logging.info(text)
        if self.logCallback:
            self.logCallback(text)

    def installedEVOPythonPackageInfo(self):
        import shutil
        import subprocess
        versionInfo = subprocess.check_output([shutil.which("PythonSlicer"), "-m", "pip", "show", "nnunetv2"]).decode()
        return versionInfo

    def setupPythonRequirements(self, upgrade=False):
        import importlib.metadata
        import importlib.util
        import packaging

        # Install PyTorch
        try:
          import PyTorchUtils
        except ModuleNotFoundError as e:
          raise RuntimeError("This module requires PyTorch extension. Install it from the Extensions Manager.")

        self.log("Initializing PyTorch...")
        minimumTorchVersion = "1.12"
        torchLogic = PyTorchUtils.PyTorchUtilsLogic()
        if not torchLogic.torchInstalled():
            self.log("PyTorch Python package is required. Installing... (it may take several minutes)")
            torch = torchLogic.installTorch(askConfirmation=True, torchVersionRequirement = f">={minimumTorchVersion}")
            if torch is None:
                raise ValueError("PyTorch extension needs to be installed to use this module.")
        else:
            # torch is installed, check version
            from packaging import version
            if version.parse(torchLogic.torch.__version__) < version.parse(minimumTorchVersion):
                raise ValueError(f"PyTorch version {torchLogic.torch.__version__} is not compatible with this module."
                                 + f" Minimum required version is {minimumTorchVersion}. You can use 'PyTorch Util' module to install PyTorch"
                                 + f" with version requirement set to: >={minimumTorchVersion}")

        # Install EVO with required components
        self.log("Initializing EVO...")
        # Specify minimum version 1.3, as this is a known working version (it is possible that an earlier version works, too).
        # Without this, for some users EVO-0.9.0 got installed, which failed with this error:
        # "ImportError: cannot import name ‘MetaKeys’ from 'EVO.utils'"
        EVOInstallString = "nnunetv2[fire,flask,pyyaml,nibabel,pynrrd,psutil,tensorboard,skimage,itk,tqdm,batchgenerators]>=1.3"
        if upgrade:
            EVOInstallString += " --upgrade"
        if self.ui_language=="zh-CN":
            EVOInstallString += " -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
        
        slicer.util.pip_install(EVOInstallString)

        self.dependenciesInstalled = True
        self.log("Dependencies are set up successfully.")


    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("Model"):
            parameterNode.SetParameter("Model", self.defaultModel)
        if not parameterNode.GetParameter("UseStandardSegmentNames"):
            parameterNode.SetParameter("UseStandardSegmentNames", "true")

    def logProcessOutputUntilCompleted(self, segmentationProcessInfo):
        # Wait for the process to end and forward output to the log
        from subprocess import CalledProcessError
        proc = segmentationProcessInfo["proc"]
        while True:
            try:
                line = proc.stdout.readline()
                if not line:
                    break
                self.log(line.rstrip())
            except UnicodeDecodeError as e:
                # Code page conversion happens because `universal_newlines=True` sets process output to text mode,
                # and it fails because probably system locale is not UTF8. We just ignore the error and discard the string,
                # as we only guarantee correct behavior if an UTF8 locale is used.
                pass
        proc.wait()
        retcode = proc.returncode
        segmentationProcessInfo["procReturnCode"] = retcode
        if retcode != 0:
            raise CalledProcessError(retcode, proc.args, output=proc.stdout, stderr=proc.stderr)

    # def getParameterNode(self):
    #     return EvoSegParameterNode(super().getParameterNode())

    def process(self, 
                inputNodes, 
                outputSegmentation, 
                model=None, 
                withDownload=True,
                cpu=False, 
                waitForCompletion=True, 
                customData=None):

        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputNodes: input nodes in a list
        :param outputVolume: thresholding result
        :param model: one of self.models
        :param cpu: use CPU instead of GPU
        :param waitForCompletion: if True then the method waits for the processing to finish
        :param customData: any custom data to identify or describe this processing request, it will be returned in the process completed callback when waitForCompletion is False
        """

        if not inputNodes:
            raise ValueError("Input nodes are invalid")

        if not outputSegmentation:
            raise ValueError("Output segmentation is invalid")

        if model == None:
            model = self.defaultModel

        try:
            modelPath = self.modelPath(model)
        except:
            self.downloadModel(model,withDownload)
            modelPath = self.modelPath(model)
        print("modelPath",modelPath)
        segmentationProcessInfo = {}

        import time
        startTime = time.time()
        self.log("Processing started")

        if self.debugSkipInference:
            # For debugging, use a fixed temporary folder
            tempDir = self.debugSkipInferenceTempDir
        else:
            # Create new empty folder
            tempDir = slicer.util.tempDirectory()

        import pathlib
        tempDirPath = pathlib.Path(tempDir)

        # Get Python executable path
        import shutil
        pythonSlicerExecutablePath = shutil.which("PythonSlicer")
        print(pythonSlicerExecutablePath)
        if not pythonSlicerExecutablePath:
            raise RuntimeError("Python was not found")

        # Write input volume to file
        inputFiles = []
        for inputIndex, inputNode in enumerate(inputNodes):
            if inputNode.IsA('vtkMRMLScalarVolumeNode'):
                inputImageFile = tempDir + f"/input-volume{inputIndex}.nrrd"
                self.log(f"Writing input file to {inputImageFile}")
                volumeStorageNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLVolumeArchetypeStorageNode")
                volumeStorageNode.SetFileName(inputImageFile)
                volumeStorageNode.UseCompressionOff()
                volumeStorageNode.WriteData(inputNode)
                slicer.mrmlScene.RemoveNode(volumeStorageNode)
                inputFiles.append(inputImageFile)
            else:
                raise ValueError(f"Input node type {inputNode.GetClassName()} is not supported")

        outputSegmentationFile = tempDir + "/output-segmentation.nrrd"
        modelPtFile = modelPath #.joinpath("model.pth") # TODO: 符合nnunetv2_inference.py的输入
        inferenceScriptPyFile = os.path.join(self.moduleDir, "Scripts", "nnunetv2_inference.py")
        auto3DSegCommand = [ pythonSlicerExecutablePath, str(inferenceScriptPyFile),
            "--model_folder", str(modelPtFile),
            "--image_file", inputFiles[0],
            "--result_file", str(outputSegmentationFile) ]
        for inputIndex in range(1, len(inputFiles)):
            auto3DSegCommand.append(f"--image-file-{inputIndex+1}")
            auto3DSegCommand.append(inputFiles[inputIndex])

        self.log("Creating segmentations with EvoSeg AI...")
        self.log(f"Auto3DSeg command: {auto3DSegCommand}")

        additionalEnvironmentVariables = None
        if cpu:
            additionalEnvironmentVariables = {"CUDA_VISIBLE_DEVICES": "-1"}
            self.log(f"Additional environment variables: {additionalEnvironmentVariables}")

        if self.debugSkipInference:
            proc = None
        else:
            proc = slicer.util.launchConsoleProcess(auto3DSegCommand, updateEnvironment=additionalEnvironmentVariables)

        segmentationProcessInfo["proc"] = proc
        segmentationProcessInfo["procReturnCode"] = EvoSegLogic.EXIT_CODE_DID_NOT_RUN
        segmentationProcessInfo["cancelRequested"] = False
        segmentationProcessInfo["startTime"] = startTime
        segmentationProcessInfo["tempDir"] = tempDir
        segmentationProcessInfo["segmentationProcess"] = proc
        segmentationProcessInfo["inputNodes"] = inputNodes
        segmentationProcessInfo["outputSegmentation"] = outputSegmentation
        segmentationProcessInfo["outputSegmentationFile"] = outputSegmentationFile
        segmentationProcessInfo["model"] = model
        segmentationProcessInfo["customData"] = customData

        if proc:
            if waitForCompletion:
                # Wait for the process to end before returning
                self.logProcessOutputUntilCompleted(segmentationProcessInfo)
                self.onSegmentationProcessCompleted(segmentationProcessInfo)
            else:
                # Run the process in the background
                self.startSegmentationProcessMonitoring(segmentationProcessInfo)
        else:
            # Debugging
            self.onSegmentationProcessCompleted(segmentationProcessInfo)

        return segmentationProcessInfo

    def cancelProcessing(self, segmentationProcessInfo):
        self.log("Cancel is requested.")
        segmentationProcessInfo["cancelRequested"] = True
        proc = segmentationProcessInfo.get("proc")
        if proc:
            # Simple proc.kill() would not work, that would only stop the launcher
            import psutil
            psProcess = psutil.Process(proc.pid)
            for psChildProcess in psProcess.children(recursive=True):
                psChildProcess.kill()
            if psProcess.is_running():
                psProcess.kill()
        else:
            self.onSegmentationProcessCompleted(segmentationProcessInfo)

    @staticmethod
    def _handleProcessOutputThreadProcess(segmentationProcessInfo):
        # Wait for the process to end and forward output to the log
        proc = segmentationProcessInfo["proc"]
        from subprocess import CalledProcessError
        while True:
            try:
                line = proc.stdout.readline()
                if not line:
                    break
                segmentationProcessInfo["procOutputQueue"].put(line.rstrip())
            except UnicodeDecodeError as e:
                # Code page conversion happens because `universal_newlines=True` sets process output to text mode,
                # and it fails because probably system locale is not UTF8. We just ignore the error and discard the string,
                # as we only guarantee correct behavior if an UTF8 locale is used.
                pass
        proc.wait()
        retcode = proc.returncode  # non-zero return code means error
        segmentationProcessInfo["procReturnCode"] = retcode


    def startSegmentationProcessMonitoring(self, segmentationProcessInfo):
        import queue
        import sys
        import threading

        segmentationProcessInfo["procOutputQueue"] = queue.Queue()
        segmentationProcessInfo["procThread"] = threading.Thread(target=EvoSegLogic._handleProcessOutputThreadProcess, args=[segmentationProcessInfo])
        segmentationProcessInfo["procThread"].start()

        self.checkSegmentationProcessOutput(segmentationProcessInfo)


    def checkSegmentationProcessOutput(self, segmentationProcessInfo):

        import queue
        outputQueue = segmentationProcessInfo["procOutputQueue"]
        while outputQueue:
            if segmentationProcessInfo.get("procReturnCode") != EvoSegLogic.EXIT_CODE_DID_NOT_RUN:
                self.onSegmentationProcessCompleted(segmentationProcessInfo)
                return
            try:
                line = outputQueue.get_nowait()
                self.log(line)
            except queue.Empty:
                break

        # No more outputs to process now, check again later
        import qt
        qt.QTimer.singleShot(self.processOutputCheckTimerIntervalMsec, lambda segmentationProcessInfo=segmentationProcessInfo: self.checkSegmentationProcessOutput(segmentationProcessInfo))


    def onSegmentationProcessCompleted(self, segmentationProcessInfo):

        startTime = segmentationProcessInfo["startTime"]
        tempDir = segmentationProcessInfo["tempDir"]
        inputNodes = segmentationProcessInfo["inputNodes"]
        outputSegmentation = segmentationProcessInfo["outputSegmentation"]
        outputSegmentationFile = segmentationProcessInfo["outputSegmentationFile"]
        model = segmentationProcessInfo["model"]
        customData = segmentationProcessInfo["customData"]
        procReturnCode = segmentationProcessInfo["procReturnCode"]
        cancelRequested = segmentationProcessInfo["cancelRequested"]

        if cancelRequested:
            procReturnCode = EvoSegLogic.EXIT_CODE_USER_CANCELLED
            self.log(f"Processing was cancelled.")
        else:
            if procReturnCode == 0:

                if self.startResultImportCallback:
                    self.startResultImportCallback(customData)

                try:

                    # Load result
                    self.log("Importing segmentation results...")
                    self.readSegmentation(outputSegmentation, outputSegmentationFile, model)

                    # Set source volume - required for DICOM Segmentation export
                    inputVolume = inputNodes[0]
                    if not inputVolume.IsA('vtkMRMLScalarVolumeNode'):
                        raise ValueError("First input node must be a scalar volume")
                    outputSegmentation.SetNodeReferenceID(outputSegmentation.GetReferenceImageGeometryReferenceRole(), inputVolume.GetID())
                    outputSegmentation.SetReferenceImageGeometryParameterFromVolumeNode(inputVolume)

                    # Place segmentation node in the same place as the input volume
                    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
                    inputVolumeShItem = shNode.GetItemByDataNode(inputVolume)
                    studyShItem = shNode.GetItemParent(inputVolumeShItem)
                    segmentationShItem = shNode.GetItemByDataNode(outputSegmentation)
                    shNode.SetItemParent(segmentationShItem, studyShItem)

                finally:

                    if self.endResultImportCallback:
                        self.endResultImportCallback(customData)

            else:
                self.log(f"Processing failed with return code {procReturnCode}")

        if self.clearOutputFolder:
            self.log("Cleaning up temporary folder.")
            if os.path.isdir(tempDir):
                import shutil
                shutil.rmtree(tempDir)
        else:
            self.log(f"Not cleaning up temporary folder: {tempDir}")

        # Report total elapsed time
        import time
        stopTime = time.time()
        segmentationProcessInfo["stopTime"] = stopTime
        elapsedTime = stopTime - startTime
        if cancelRequested:
            self.log(f"Processing was cancelled after {elapsedTime:.2f} seconds.")
        else:
            if procReturnCode == 0:
                self.log(f"Processing was completed in {elapsedTime:.2f} seconds.")
            else:
                self.log(f"Processing failed after {elapsedTime:.2f} seconds.")

        if self.processingCompletedCallback:
            self.processingCompletedCallback(procReturnCode, customData)


    def readSegmentation(self, outputSegmentation, outputSegmentationFile, model):

        labelValueToDescription = self.labelDescriptions(model)

        # Get label descriptions
        # maxLabelValue = max(labelValueToDescription.keys())
        # if min(labelValueToDescription.keys()) < 0:
        #     raise RuntimeError("Label values in class_map must be positive")
        maxLabelValue = 1 # NOTE: one model one label
        # Get color node with random colors
        randomColorsNode = slicer.mrmlScene.GetNodeByID("vtkMRMLColorTableNodeRandom")
        rgba = [0, 0, 0, 0]

        # Create color table for this segmentation model
        colorTableNode = slicer.vtkMRMLColorTableNode()
        colorTableNode.SetTypeToUser()
        colorTableNode.SetNumberOfColors(maxLabelValue+1)
        colorTableNode.SetName(model)
        for labelValue in labelValueToDescription:
            randomColorsNode.GetColor(labelValue,rgba)
            colorTableNode.SetColor(labelValue, rgba[0], rgba[1], rgba[2], rgba[3])
            colorTableNode.SetColorName(labelValue, labelValueToDescription[labelValue]["name"])
        slicer.mrmlScene.AddNode(colorTableNode)

        # Load the segmentation
        outputSegmentation.SetLabelmapConversionColorTableNodeID(colorTableNode.GetID())
        outputSegmentation.AddDefaultStorageNode()
        storageNode = outputSegmentation.GetStorageNode()
        storageNode.SetFileName(outputSegmentationFile)
        storageNode.ReadData(outputSegmentation)

        slicer.mrmlScene.RemoveNode(colorTableNode)

        # Set terminology and color
        for labelValue in labelValueToDescription:
            segmentName = labelValueToDescription[labelValue]["name"]
            terminologyEntryStr = labelValueToDescription[labelValue]["terminology"]
            segmentId = segmentName
            self.setTerminology(outputSegmentation, segmentName, segmentId, terminologyEntryStr)

    def setTerminology(self, segmentation, segmentName, segmentId, terminologyEntryStr):
        segment = segmentation.GetSegmentation().GetSegment(segmentId)
        if not segment:
            # Segment is not present in this segmentation
            return
        if terminologyEntryStr:
            segment.SetTag(segment.GetTerminologyEntryTagName(), terminologyEntryStr)
            try:
                label, color = self.getSegmentLabelColor(terminologyEntryStr)
                if self.useStandardSegmentNames:
                    segment.SetName(label)
                segment.SetColor(color)
            except RuntimeError as e:
                self.log(str(e))

    def updateModelsDescriptionJsonFilePathFromTestResults(self, modelsTestResultsJsonFilePath):
        import json

        modelsDescriptionJsonFilePath = self.modelsDescriptionJsonFilePath()

        with open(modelsTestResultsJsonFilePath) as f:
            modelsTestResults = json.load(f)

        with open(modelsDescriptionJsonFilePath) as f:
            modelsDescription = json.load(f)

        for model in modelsDescription["models"]:
            title = model["title"]
            for modelTestResult in modelsTestResults:
                if modelTestResult["title"] == title:
                    for fieldName in ["segmentNames"]:
                        fieldValue = modelTestResult.get(fieldName)
                        if fieldValue:
                            model[fieldName] = fieldValue
                    break

        with open(modelsDescriptionJsonFilePath, 'w', newline="\n") as f:
            json.dump(modelsDescription, f, indent=2)


#
# EvoSegTest
#


class EvoSegTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_EvoSeg()

    def test_EvoSeg(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Test is space and Done!")

    #     # Logic testing is disabled by default to not overload automatic build machines (pytorch is a huge package and computation
    #     # on CPU takes 5-10 minutes). Set testLogic to True to enable testing.
    #     testLogic = True

    #     if not testLogic:
    #         self.delayDisplay("Logic testing is disabled. Set testLogic to True to enable it.")
    #         return

    #     logic = EvoSegLogic()
    #     logic.logCallback = self._mylog

    #     self.delayDisplay("Set up required Python packages")
    #     logic.setupPythonRequirements()

    #     testResultsPath = logic.fileCachePath.joinpath("ModelsTestResults")
    #     if not os.path.exists(testResultsPath):
    #         os.makedirs(testResultsPath)

    #     import json
    #     modelsTestResultsJsonFilePath = os.path.join(testResultsPath.joinpath("ModelsTestResults.json"))
    #     if os.path.exists(modelsTestResultsJsonFilePath):
    #         # resume testing
    #         with open(modelsTestResultsJsonFilePath) as f:
    #           models = json.load(f)
    #     else:
    #         # start testing from scratch
    #         models = logic.models

    #     import PyTorchUtils
    #     pytorchLogic = PyTorchUtils.PyTorchUtilsLogic()
    #     if pytorchLogic.cuda:
    #         # CUDA is available, test on both CPU and GPU
    #         configurations = [{"forceUseCPU": False}, {"forceUseCPU": True}]
    #     else:
    #         # CUDA is not available, only test on CPU
    #         configurations = [{"forceUseCPU": True}]

    #     for configurationIndex, configuration in enumerate(configurations):
    #         forceUseCpu = configuration["forceUseCPU"]
    #         configurationName = "CPU" if forceUseCpu else "GPU"

    #         for modelIndex, model in enumerate(models):
    #             if model.get("deprecated"):
    #                 # Do not teset deprecated models
    #                 continue

    #             segmentationTimePropertyName = "segmentationTimeSec"+configurationName
    #             if segmentationTimePropertyName in models[modelIndex]:
    #                 # Skip already tested models
    #                 continue

    #             self.delayDisplay(f"Testing {model['title']} (v{model['version']})")
    #             slicer.mrmlScene.Clear()

    #             # Download sample data for model input

    #             sampleDataName = model.get("sampleData")
    #             if not sampleDataName:
    #                 self.delayDisplay(f"Sample data not available for {model['title']}")
    #                 continue

    #             if type(sampleDataName) == list:
    #                 # For now, always just use the first data set if multiple data sets are provided
    #                 sampleDataName = sampleDataName[0]

    #             import SampleData
    #             loadedSampleNodes = SampleData.SampleDataLogic().downloadSamples(sampleDataName)
    #             if not loadedSampleNodes:
    #                 raise RuntimeError(f"Failed to load sample data set '{sampleDataName}'.")

    #             # Set model inputs

    #             inputNodes = []
    #             inputs = model.get("inputs")
    #             inputNodes = EvoSegLogic.assignInputNodesByName(inputs, loadedSampleNodes)

    #             outputSegmentation = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")

    #             # Run the segmentation

    #             self.delayDisplay(f"Running segmentation for {model['title']}...")
    #             import time
    #             startTime = time.time()
    #             logic.process(inputNodes, outputSegmentation, model["id"], forceUseCpu)
    #             segmentationTimeSec = time.time() - startTime

    #             # Save segmentation time (rounded to 0.1 sec) into model description
    #             models[modelIndex][segmentationTimePropertyName] = round(segmentationTimeSec * 10) / 10

    #             # Save all segment names into model description
    #             labelDescriptions = logic.labelDescriptions(model["id"])
    #             segmentNames = []
    #             for terminology in labelDescriptions.values():
    #                 contextName, category, typeStr, typeModifier, anatomicContext, region, regionModifier = terminology["terminology"].split("~")
    #                 typeName = typeStr.split("^")[2]
    #                 typeModifierName = typeModifier.split("^")[2]
    #                 if typeModifierName:
    #                     typeName = f"{typeModifierName} {typeName}"
    #                 regionName = region.split("^")[2]
    #                 regionModifierName = regionModifier.split("^")[2]
    #                 if regionModifierName:
    #                     regionName = f"{regionModifierName} {regionName}"
    #                 name = f"{typeName} in {regionName}" if regionName else typeName
    #                 segmentNames.append(name)
    #             models[modelIndex]["segmentNames"] = segmentNames

    #             sliceScreenshotFilename, rotate3dScreenshotFilename = self._writeScreenshots(outputSegmentation, testResultsPath, model["id"]+"-"+configurationName)
    #             if configurationIndex == 0:
    #                 # Use screenshot computed during the first configuration
    #                 models[modelIndex]["segmentationResultsScreenshot2D"] = sliceScreenshotFilename.name
    #                 models[modelIndex]["segmentationResultsScreenshot3D"] = rotate3dScreenshotFilename.name

    #             # Write results to file (to allow accessing the results before all tests complete)
    #             with open(modelsTestResultsJsonFilePath, 'w') as f:
    #                 json.dump(models, f, indent=2)

    #     logic.updateModelsDescriptionJsonFilePathFromTestResults(modelsTestResultsJsonFilePath)
    #     self._writeTestResultsToMarkdown(modelsTestResultsJsonFilePath)

    #     self.delayDisplay("Test passed")

    # def _mylog(self,text):
    #     print(text)

    # def _writeScreenshots(self, segmentationNode, outputPath, baseName, numberOfImages=25, lightboxColumns=5, numberOfVideoFrames=50):
    #     import ScreenCapture
    #     cap = ScreenCapture.ScreenCaptureLogic()

    #     sliceScreenshotFilename = outputPath.joinpath(f"{baseName}-slices.png")
    #     rotate3dScreenshotFilename = outputPath.joinpath(f"{baseName}-rotate3d.gif")  # gif, mp4, png
    #     videoLengthSec = 5

    #     # Capture slice sweep
    #     sliceScreenshotsFilenamePattern = outputPath.joinpath("slices_%04d.png")
    #     cap.showViewControllers(False)
    #     slicer.app.layoutManager().resetSliceViews()
    #     sliceNode = slicer.util.getNode("vtkMRMLSliceNodeRed")
    #     sliceOffsetMin, sliceOffsetMax = cap.getSliceOffsetRange(sliceNode)
    #     sliceOffsetStart = sliceOffsetMin + (sliceOffsetMax - sliceOffsetMin) * 0.05
    #     sliceOffsetEnd = sliceOffsetMax - (sliceOffsetMax - sliceOffsetMin) * 0.05
    #     cap.captureSliceSweep(
    #         sliceNode, sliceOffsetStart, sliceOffsetEnd, numberOfImages,
    #         sliceScreenshotsFilenamePattern.parent, sliceScreenshotsFilenamePattern.name,
    #         captureAllViews=None, transparentBackground=False)
    #     cap.showViewControllers(True)

    #     # Create lightbox image
    #     cap.createLightboxImage(lightboxColumns,
    #         sliceScreenshotsFilenamePattern.parent,
    #         sliceScreenshotsFilenamePattern.name,
    #         numberOfImages,
    #         sliceScreenshotFilename)
    #     cap.deleteTemporaryFiles(sliceScreenshotsFilenamePattern.parent, sliceScreenshotsFilenamePattern.name, numberOfImages)

    #     # Capture 3D rotation
    #     rotate3dScreenshotsFilenamePattern = outputPath.joinpath("rotate3d_%04d.png")
    #     segmentationNode.CreateClosedSurfaceRepresentation()
    #     segmentationNode.GetDisplayNode().SetOpacity3D(0.6)

    #     if rotate3dScreenshotFilename.suffix.lower() == ".png":
    #         video = False
    #         numberOfImages3d = numberOfImages
    #     else:
    #         video = True
    #         numberOfImages3d = numberOfVideoFrames
    #         if rotate3dScreenshotFilename.suffix.lower() == ".gif":
    #             # animated GIF
    #             extraOptions = "-filter_complex palettegen,[v]paletteuse"
    #         elif rotate3dScreenshotFilename.suffix.lower() == ".mp4":
    #             # H264 high-quality
    #             extraOptions = "-codec libx264 -preset slower -crf 18 -pix_fmt yuv420p"
    #         else:
    #             raise ValueError(f"Unsupported format: {rotate3dScreenshotFilename.suffix}")

    #     viewLabel = "1"
    #     viewNode = slicer.vtkMRMLViewLogic().GetViewNode(slicer.mrmlScene, viewLabel)
    #     viewNode.SetBackgroundColor(0,0,0)
    #     viewNode.SetBackgroundColor2(0,0,0)
    #     viewNode.SetAxisLabelsVisible(False)
    #     viewNode.SetBoxVisible(False)
    #     cap.showViewControllers(False)
    #     slicer.app.layoutManager().resetThreeDViews()
    #     cap.capture3dViewRotation(viewNode, -180, 180, numberOfImages3d, ScreenCapture.AXIS_YAW, rotate3dScreenshotsFilenamePattern.parent, rotate3dScreenshotsFilenamePattern.name)
    #     cap.showViewControllers(True)

    #     if video:
    #         cap.createVideo(numberOfImages3d/videoLengthSec, extraOptions, rotate3dScreenshotsFilenamePattern.parent, rotate3dScreenshotsFilenamePattern.name, rotate3dScreenshotFilename)
    #     else:
    #         cap.createLightboxImage(lightboxColumns,
    #             rotate3dScreenshotsFilenamePattern.parent,
    #             rotate3dScreenshotsFilenamePattern.name,
    #             numberOfImages3d,
    #             rotate3dScreenshotFilename)

    #     cap.deleteTemporaryFiles(rotate3dScreenshotsFilenamePattern.parent, rotate3dScreenshotsFilenamePattern.name, numberOfImages3d)

    #     return sliceScreenshotFilename, rotate3dScreenshotFilename

    # def _writeTestResultsToMarkdown(self, modelsTestResultsJsonFilePath, modelsTestResultsMarkdownFilePath=None, screenshotUrlBase=None):

    #     if modelsTestResultsMarkdownFilePath is None:
    #         modelsTestResultsMarkdownFilePath = modelsTestResultsJsonFilePath.replace(".json", ".md")
    #     if screenshotUrlBase is None:
    #         screenshotUrlBase = "https://github.com/lassoan/SlicerEvoSeg/releases/download/ModelsTestResults/"

    #     import json
    #     from EvoSeg import EvoSegLogic
    #     with open(modelsTestResultsJsonFilePath) as f:
    #         modelsTestResults = json.load(f)

    #     with open(modelsTestResultsMarkdownFilePath, 'w', newline="\n") as f:
    #         f.write("# 3D Slicer EVO Auto3DSeg models\n\n")
    #         # Write hardware information (only on Windows for now)
    #         if os.name == "nt":
    #             import subprocess
    #             cpu = subprocess.check_output('wmic cpu get name', stderr=open(os.devnull, 'w')).decode('utf-8').partition('Name')[2].strip(' \r\n')
    #             systemInfoStr = subprocess.check_output('systeminfo', stderr=open(os.devnull, 'w')).decode('utf-8')
    #             # System information has a line like this: "Total Physical Memory:     32,590 MB"
    #             import re
    #             ram = re.search(r"Total Physical Memory:(.+)", systemInfoStr).group(1).strip()
    #             f.write(f"Testing hardware: {cpu}, {ram}")
    #             import torch
    #             for i in range(torch.cuda.device_count()):
    #                 gpuProperties = torch.cuda.get_device_properties(i)
    #                 f.write(f", {gpuProperties.name} {round(torch.cuda.get_device_properties(0).total_memory/(2**30))}GB")
    #             f.write("\n\n")
    #         # Write test results
    #         for model in modelsTestResults:
    #             if model["deprecated"]:
    #                 continue
    #             title = f"{model['title']} (v{model['version']})"
    #             f.write(f"## {title}\n")
    #             f.write(f"{model['description']}\n\n")
    #             f.write(f"Processing time: {EvoSegLogic.humanReadableTimeFromSec(model['segmentationTimeSecGPU'])} on GPU, {EvoSegLogic.humanReadableTimeFromSec(model['segmentationTimeSecCPU'])} on CPU\n\n")
    #             f.write(f"Segment names: {', '.join(model['segmentNames'])}\n\n")
    #             f.write(f"![2D view]({screenshotUrlBase}{model['segmentationResultsScreenshot2D']})\n")
    #             f.write(f"![3D view]({screenshotUrlBase}{model['segmentationResultsScreenshot3D']})\n")