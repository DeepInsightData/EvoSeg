import pathlib
import re
import shutil
import tempfile
import qt
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
from qt import QEvent, QObject, QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QFileDialog, QImage, QPixmap, QCheckBox, QButtonGroup
import subprocess
import SegmentStatistics
import numpy as np
from EvoSegLib import *
from EvoSegLib.utils import splitSegment
#
# EvoSeg
#

class EvoSeg(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("EvoSeg")
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "")]
        self.parent.dependencies = []  
        self.parent.contributors = ["DeepInsightData"] 
        # TODO: set help text
        self.parent.helpText = _(" ")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _(" ")
        self.terminologyName = None
        self.settingsPanel = EvoSegSettingsPanel()
        slicer.app.settingsDialog().addPanel("EvoSeg", self.settingsPanel)

class EvoSegProcess:
    class Segment:
        def __init__(self, name, visibilityButton, opacitySlider):
            self.name=name
            self.visibilityButton=visibilityButton
            self.opacitySlider=opacitySlider
    class SegmentGroup:
        def __init__(self, name, visibilityButton, opacitySlider, segmentNames):
            self.name = name
            self.visibilityButton = visibilityButton
            self.opacitySlider = opacitySlider
            self.segmentNames = segmentNames

    def __init__(self, name, segmentationButton, segmentationNode, radioButton, groupBox, visibilityButton, opacitySlider, model, segments=[], segmentGroups=[]):
        self.name = name
        self.segmentationButton = segmentationButton
        self.segmentationNode = segmentationNode
        self.radioButton = radioButton
        self.groupBox = groupBox
        self.visibilityButton = visibilityButton
        self.opacitySlider = opacitySlider
        self.model = model
        self.segments = segments
        self.segmentGroups = segmentGroups
        
        if self.segmentGroups:
            for segmentGroup in self.segmentGroups:
                if not segmentGroup.visibilityButton:
                    continue
                # Connect visibility button signals
                for segmentName in segmentGroup.segmentNames:
                    for segment in self.segments:
                        if segment.name == segmentName and segment.visibilityButton:
                            segmentGroup.visibilityButton.toggled.connect(segment.visibilityButton.setChecked)
                
                # Connect opacity slider signals
                if segmentGroup.opacitySlider:
                    for segmentName in segmentGroup.segmentNames:
                        for segment in self.segments:
                            if segment.name == segmentName and segment.opacitySlider:
                                segmentGroup.opacitySlider.connect("valueChanged(double)", segment.opacitySlider.setValue)


    def init_segmentation_node(self):
        self.segmentationNode = slicer.mrmlScene.GetFirstNodeByName(f'{self.name}_Output_Mask')
        self.groupBox.setVisible(self.segmentationNode is not None)
        if self.segmentationNode:
            displayNode = self.segmentationNode.GetDisplayNode()
            self.opacitySlider.setValue(displayNode.GetOpacity3D())
            self.visibilityButton.setChecked(displayNode.GetVisibility())
            
            # Initialize all segment slider values
            for segment in self.segments:
                segmentID = self.segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segment.name)
                if segmentID:
                    segment.opacitySlider.setValue(displayNode.GetSegmentOpacity3D(segmentID))
                    segment.visibilityButton.setChecked(displayNode.GetSegmentVisibility(segmentID))
            
            # Initialize all segmentGroup slider values
            for segmentGroup in self.segmentGroups:
                if segmentGroup.segmentNames:
                    # Use the first segment's opacity as the default opacity for the group
                    segmentID = self.segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segmentGroup.segmentNames[0])
                    if segmentID:
                        segmentGroup.opacitySlider.setValue(displayNode.GetSegmentOpacity3D(segmentID))
                        segmentGroup.visibilityButton.setChecked(displayNode.GetSegmentVisibility(segmentID))

    @staticmethod
    def filterOne(processes, attr, value):
        for process in processes:
            if getattr(process, attr) == value:
                return process
        return None

#
# EvoSegWidget
#

class EvoSegWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
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
        self._updatingGUIFromParameterNode = False
        self._processingState = EvoSegWidget.PROCESSING_IDLE
        self._segmentationProcessInfo = None
        self._segmentationProcessInfoList = []
    
        self.observations = None
        self.markup_node=None
        self.data_module=None
        self.data_module_name=''
        self.data_module_list=[]
        self.logic = EvoSegLogic()

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/EvoSeg.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # 为self.logic设置回调
        self.logic.logCallback = self.addLog
        self.logic.processingCompletedCallback = self.onProcessingCompleted
        self.logic.startResultImportCallback = self.onProcessImportStarted
        self.logic.endResultImportCallback = self.onProcessImportEnded
        self.logic.setResultToLabelCallback = self.onResultSeg

        self.ui.VolumeNodeComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.onVolumeNodeSelected)
        self.onVolumeNodeSelected(self.ui.VolumeNodeComboBox.currentNode())
        self.ui.bt_place.connect("clicked(bool)", self.check_set_modifiy)
        self.bt_place_down = False

        # Buttons
        # self.ui.copyModelsButton.connect("clicked(bool)", self.onCopyModel)
        
        self.ui.browseToModelsFolderButton.connect("clicked(bool)", self.onBrowseModelsFolder)

        self.ui.bt_export.connect("clicked(bool)", self.onExportClick)

        self.ui.bt_batch.connect("clicked(bool)", self.onBatchSegmentation)
        self.ui.bt_cancel_run.connect("clicked(bool)", self.onCancel)
        

        # check box
        self.ui.radio_airway_tag.setChecked(True)
        self.ui.radioButtonSphereAddition.setChecked(True)

        # new button click
        self.ui.button_undo.connect("clicked(bool)", self.onButtonUndoClick)

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.ui.radio_airway_tag)
        self.button_group.addButton(self.ui.radio_artery_tag)
        self.button_group.addButton(self.ui.radio_vein_tag)
        self.button_group.addButton(self.ui.radio_lobe_tag)
        self.button_group.addButton(self.ui.radio_rib_tag)
        self.button_group.buttonToggled.connect(self.onButtonGroupClick)

        self.button_group2 = QButtonGroup()
        self.button_group2.addButton(self.ui.radioButtonSphereAddition) 
        self.button_group2.addButton(self.ui.radioButtonSphereErasure)
        self.button_group2.addButton(self.ui.radioButtonTubeAddition)
        self.button_group2.addButton(self.ui.radioButtonMagicAddition)
        self.button_group2.addButton(self.ui.radioButtonMagicErasure)

        self.ui.bt_seg_airway.setIcon(qt.QIcon(self.resourcePath("Icons/airway_segmentation.png")))
        self.ui.bt_seg_artery.setIcon(qt.QIcon(self.resourcePath("Icons/artery_segmentation.png")))
        self.ui.btn_seg_lobe.setIcon(qt.QIcon(self.resourcePath("Icons/lunglobe_segmentation.png")))
        self.ui.btn_seg_rib.setIcon(qt.QIcon(self.resourcePath("Icons/rib_segmentation.png")))
        self.ui.btn_seg_vein.setIcon(qt.QIcon(self.resourcePath("Icons/vein_segmentation.png")))
        self.ui.btn_seg_nodule.setIcon(qt.QIcon(self.resourcePath("Icons/nodule_segmentation.png")))
        self.ui.bt_batch.setIcon(qt.QIcon(self.resourcePath("Icons/EvoSeg_Batch.png")))
        self.ui.bt_cancel_run.setIcon(qt.QIcon(self.resourcePath("Icons/EvoSeg_Cancel.png")))
        self.ui.bt_place.setIcon(qt.QIcon(self.resourcePath("Icons/EvoSeg_Place.png")))
        self.ui.bt_place.toggled.connect(lambda checked: self.ui.bt_place.setIcon(
            qt.QIcon(":/Icons/MarkupsFiducialMouseModePlace.png" if checked else self.resourcePath("Icons/EvoSeg_Place.png"))
        ))
        self.ui.bt_export.setIcon(qt.QIcon(self.resourcePath("Icons/EvoSeg_Export.png")))
        self.ui.browseToModelsFolderButton.setIcon(qt.QIcon(self.resourcePath("Icons/EvoSeg_Model.png")))
        self.ui.bt_seg_airway.clicked.connect(lambda: self.onSegButtonClick(self.ui.bt_seg_airway))
        self.ui.bt_seg_artery.clicked.connect(lambda: self.onSegButtonClick(self.ui.bt_seg_artery))
        self.ui.btn_seg_vein.clicked.connect(lambda: self.onSegButtonClick(self.ui.btn_seg_vein))
        self.ui.btn_seg_lobe.clicked.connect(lambda: self.onSegButtonClick(self.ui.btn_seg_lobe))
        self.ui.btn_seg_rib.clicked.connect(lambda: self.onSegButtonClick(self.ui.btn_seg_rib))
        self.ui.btn_seg_nodule.clicked.connect(lambda: self.onSegButtonClick(self.ui.btn_seg_nodule))
        
        self.ui.groupBox_Modify.hide()
        self.interactionNodeObserver=None

        self.ui.airwayVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.airwayVisibilityButton))
        self.ui.leftAirwayVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.leftAirwayVisibilityButton))
        self.ui.rightAirwayVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.rightAirwayVisibilityButton))
        self.ui.arteryVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.arteryVisibilityButton))
        self.ui.leftArteryVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.leftArteryVisibilityButton))
        self.ui.rightArteryVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.rightArteryVisibilityButton))
        self.ui.veinVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.veinVisibilityButton))
        self.ui.leftVeinVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.leftVeinVisibilityButton))
        self.ui.rightVeinVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.rightVeinVisibilityButton))    
        self.ui.lobeVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.lobeVisibilityButton))
        
        self.ui.ribsVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.ribsVisibilityButton))
        self.ui.noduleVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.noduleVisibilityButton))
        
        # 新增肺段控件的可见性信号连接 (31-48)
        # 右肺段 (31-40)
        self.ui.apicalRB1VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.apicalRB1VisibilityButton))
        self.ui.posteriorRB2VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.posteriorRB2VisibilityButton))
        self.ui.anteriorRB3VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.anteriorRB3VisibilityButton))
        self.ui.lateralRB4VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.lateralRB4VisibilityButton))
        self.ui.medialRB5VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.medialRB5VisibilityButton))
        self.ui.superiorRB6VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.superiorRB6VisibilityButton))
        self.ui.medialBasalRB7VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.medialBasalRB7VisibilityButton))
        self.ui.anteriorBasalRB8VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.anteriorBasalRB8VisibilityButton))
        self.ui.lateralBasalRB9VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.lateralBasalRB9VisibilityButton))
        self.ui.posteriorBasalRB10VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.posteriorBasalRB10VisibilityButton))
        
        # 左肺段 (41-48)
        self.ui.apicoposteriorLB1_2VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.apicoposteriorLB1_2VisibilityButton))
        self.ui.anteriorLB3VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.anteriorLB3VisibilityButton))
        self.ui.superiorLingularLB4VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.superiorLingularLB4VisibilityButton))
        self.ui.inferiorLingularLB5VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.inferiorLingularLB5VisibilityButton))
        self.ui.superiorLB6VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.superiorLB6VisibilityButton))
        self.ui.anteriorBasalLB8VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.anteriorBasalLB8VisibilityButton))
        self.ui.lateralBasalLB9VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.lateralBasalLB9VisibilityButton))
        self.ui.posteriorBasalLB10VisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.posteriorBasalLB10VisibilityButton))

        self.ui.sliderOpacityAirway.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityAirway))
        self.ui.sliderOpacityLeftAirway.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityLeftAirway))
        self.ui.sliderOpacityRightAirway.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityRightAirway))
        
        self.ui.sliderOpacityArtery.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityArtery))
        self.ui.sliderOpacityLeftArtery.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityLeftArtery))
        self.ui.sliderOpacityRightArtery.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityRightArtery))

        self.ui.sliderOpacityVein.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityVein))
        self.ui.sliderOpacityLeftVein.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityLeftVein))
        self.ui.sliderOpacityRightVein.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityRightVein))

        self.ui.sliderOpacityLobe.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityLobe))
        self.ui.sliderOpacityLeftUpperLobe.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityLeftUpperLobe))
        self.ui.sliderOpacityLeftLowerLobe.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityLeftLowerLobe))
        self.ui.sliderOpacityRightUpperLobe.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityRightUpperLobe))
        self.ui.sliderOpacityRightMiddleLobe.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityRightMiddleLobe))
        self.ui.sliderOpacityRightLowerLobe.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityRightLowerLobe))
        self.ui.sliderOpacityRibs.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityRibs))
        self.ui.sliderOpacityNodule.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityNodule))
        
        self.ui.sliderOpacityApicalRB1.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityApicalRB1))
        self.ui.sliderOpacityPosteriorRB2.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityPosteriorRB2))
        self.ui.sliderOpacityAnteriorRB3.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityAnteriorRB3))
        self.ui.sliderOpacityLateralRB4.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityLateralRB4))
        self.ui.sliderOpacityMedialRB5.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityMedialRB5))
        self.ui.sliderOpacitySuperiorRB6.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacitySuperiorRB6))
        self.ui.sliderOpacityMedialBasalRB7.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityMedialBasalRB7))
        self.ui.sliderOpacityAnteriorBasalRB8.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityAnteriorBasalRB8))
        self.ui.sliderOpacityLateralBasalRB9.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityLateralBasalRB9))
        self.ui.sliderOpacityPosteriorBasalRB10.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityPosteriorBasalRB10))
        
        self.ui.sliderOpacityApicoposteriorLB1_2.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityApicoposteriorLB1_2))
        self.ui.sliderOpacityAnteriorLB3.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityAnteriorLB3))
        self.ui.sliderOpacitySuperiorLingularLB4.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacitySuperiorLingularLB4))
        self.ui.sliderOpacityInferiorLingularLB5.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityInferiorLingularLB5))
        self.ui.sliderOpacitySuperiorLB6.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacitySuperiorLB6))
        self.ui.sliderOpacityAnteriorBasalLB8.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityAnteriorBasalLB8))
        self.ui.sliderOpacityLateralBasalLB9.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityLateralBasalLB9))
        self.ui.sliderOpacityPosteriorBasalLB10.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityPosteriorBasalLB10))
        
        self._process = {
            "Airway_nnUnet" : EvoSegProcess(
                name = "Airway_nnUnet", 
                segmentationButton=self.ui.bt_seg_airway,
                segmentationNode=None,
                radioButton=self.ui.radio_airway_tag,
                groupBox = self.ui.groupBoxAirway,
                visibilityButton=self.ui.airwayVisibilityButton,
                opacitySlider=self.ui.sliderOpacityAirway,
                model = lambda: EvoSegModels.get('Airway'),
                segments=[
                    EvoSegProcess.Segment("Airway_Left", self.ui.leftAirwayVisibilityButton, self.ui.sliderOpacityLeftAirway),
                    EvoSegProcess.Segment("Airway_Right", self.ui.rightAirwayVisibilityButton, self.ui.sliderOpacityRightAirway),
                ]
            ),
            "Artery_nnUnet" : EvoSegProcess(
                name = "Artery_nnUnet", 
                segmentationButton=self.ui.bt_seg_artery,
                segmentationNode=None,
                radioButton=self.ui.radio_artery_tag,
                groupBox=self.ui.groupBoxArtery,
                visibilityButton=self.ui.arteryVisibilityButton,
                opacitySlider=self.ui.sliderOpacityArtery,
                model = lambda: EvoSegModels.get('Artery'),
                segments=[
                    EvoSegProcess.Segment("Artery_Left", self.ui.leftArteryVisibilityButton, self.ui.sliderOpacityLeftArtery),
                    EvoSegProcess.Segment("Artery_Right", self.ui.rightArteryVisibilityButton, self.ui.sliderOpacityRightArtery),
                ]
            ),
            "Vein_nnUnet": EvoSegProcess(
                name = "Vein_nnUnet", 
                segmentationButton=self.ui.btn_seg_vein,
                segmentationNode=None,
                radioButton=self.ui.radio_vein_tag,
                groupBox=self.ui.groupBoxVein,
                visibilityButton=self.ui.veinVisibilityButton,
                opacitySlider=self.ui.sliderOpacityVein,
                model = lambda: EvoSegModels.get('Vein'),
                segments=[
                    EvoSegProcess.Segment("Vein_Left", self.ui.leftVeinVisibilityButton, self.ui.sliderOpacityLeftVein),
                    EvoSegProcess.Segment("Vein_Right", self.ui.rightVeinVisibilityButton, self.ui.sliderOpacityRightVein),
                ]
            ),
            "LungLobe_nnUnet": EvoSegProcess(
                name = "LungLobe_nnUnet",
                segmentationButton=self.ui.btn_seg_lobe,
                segmentationNode=None,
                radioButton=self.ui.radio_lobe_tag,
                groupBox=self.ui.groupBoxLobe,
                visibilityButton=self.ui.lobeVisibilityButton,
                opacitySlider=self.ui.sliderOpacityLobe,
                model = lambda: EvoSegModels.get('LungLobe'),
                segments=[
                    # right lung segments 
                    EvoSegProcess.Segment("Apical RB1", self.ui.apicalRB1VisibilityButton, self.ui.sliderOpacityApicalRB1),  # Right apical segment
                    EvoSegProcess.Segment("Posterior RB2", self.ui.posteriorRB2VisibilityButton, self.ui.sliderOpacityPosteriorRB2),  # Right posterior segment
                    EvoSegProcess.Segment("Anterior RB3", self.ui.anteriorRB3VisibilityButton, self.ui.sliderOpacityAnteriorRB3),  # Right anterior segment
                    EvoSegProcess.Segment("Lateral RB4", self.ui.lateralRB4VisibilityButton, self.ui.sliderOpacityLateralRB4),  # Right lateral segment
                    EvoSegProcess.Segment("Medial RB5", self.ui.medialRB5VisibilityButton, self.ui.sliderOpacityMedialRB5),  # Right medial segment
                    EvoSegProcess.Segment("Superior RB6", self.ui.superiorRB6VisibilityButton, self.ui.sliderOpacitySuperiorRB6),  # Right superior segment
                    EvoSegProcess.Segment("Medial basal RB7", self.ui.medialBasalRB7VisibilityButton, self.ui.sliderOpacityMedialBasalRB7),  # Right medial basal segment
                    EvoSegProcess.Segment("Anterior basal RB8", self.ui.anteriorBasalRB8VisibilityButton, self.ui.sliderOpacityAnteriorBasalRB8),  # Right anterior basal segment
                    EvoSegProcess.Segment("Lateral basal RB9", self.ui.lateralBasalRB9VisibilityButton, self.ui.sliderOpacityLateralBasalRB9),  # Right lateral basal segment
                    EvoSegProcess.Segment("Posterior basal RB10", self.ui.posteriorBasalRB10VisibilityButton, self.ui.sliderOpacityPosteriorBasalRB10),  # Right posterior basal segment
                    # Left lung segments
                    EvoSegProcess.Segment("Apicoposterior LB1/2", self.ui.apicoposteriorLB1_2VisibilityButton, self.ui.sliderOpacityApicoposteriorLB1_2),  # Left apicoposterior segment
                    EvoSegProcess.Segment("Anterior LB3", self.ui.anteriorLB3VisibilityButton, self.ui.sliderOpacityAnteriorLB3),  # Left anterior segment
                    EvoSegProcess.Segment("Superior lingular LB4", self.ui.superiorLingularLB4VisibilityButton, self.ui.sliderOpacitySuperiorLingularLB4),  # Left superior lingular segment
                    EvoSegProcess.Segment("Inferior lingular LB5", self.ui.inferiorLingularLB5VisibilityButton, self.ui.sliderOpacityInferiorLingularLB5),  # Left inferior lingular segment
                    EvoSegProcess.Segment("Superior LB6", self.ui.superiorLB6VisibilityButton, self.ui.sliderOpacitySuperiorLB6),  # Left superior segment
                    EvoSegProcess.Segment("Anterior basal LB8", self.ui.anteriorBasalLB8VisibilityButton, self.ui.sliderOpacityAnteriorBasalLB8),  # Left anterior basal segment
                    EvoSegProcess.Segment("Lateral basal LB9", self.ui.lateralBasalLB9VisibilityButton, self.ui.sliderOpacityLateralBasalLB9),  # Left lateral basal segment
                    EvoSegProcess.Segment("Posterior basal LB10", self.ui.posteriorBasalLB10VisibilityButton, self.ui.sliderOpacityPosteriorBasalLB10),  # Left posterior basal segment
                ],
                segmentGroups=[
                    EvoSegProcess.SegmentGroup(
                        "LeftUpperLobe", 
                        self.ui.leftUpperLobeVisibilityButton, 
                        self.ui.sliderOpacityLeftUpperLobe, 
                        LungLobeModel.LeftUpperLobeSegments
                    ),
                    EvoSegProcess.SegmentGroup(
                        "LeftLowerLobe", 
                        self.ui.leftLowerLobeVisibilityButton, 
                        self.ui.sliderOpacityLeftLowerLobe, 
                        LungLobeModel.LeftLowerLobeSegments
                    ),
                    EvoSegProcess.SegmentGroup(
                        "RightUpperLobe", 
                        self.ui.rightUpperLobeVisibilityButton, 
                        self.ui.sliderOpacityRightUpperLobe, 
                        LungLobeModel.RightUpperLobeSegments
                    ),
                    EvoSegProcess.SegmentGroup(
                        "RightMiddleLobe", 
                        self.ui.rightMiddleLobeVisibilityButton, 
                        self.ui.sliderOpacityRightMiddleLobe, 
                        LungLobeModel.RightMiddleLobeSegments
                    ),
                    EvoSegProcess.SegmentGroup(
                        "RightLowerLobe", 
                        self.ui.rightLowerLobeVisibilityButton, 
                        self.ui.sliderOpacityRightLowerLobe, 
                        LungLobeModel.RightLowerLobeSegments
                    )
                ]
            ),
            "Rib_nnUnet": EvoSegProcess(
                name = "Rib_nnUnet", 
                segmentationButton=self.ui.btn_seg_rib,
                segmentationNode=None,
                radioButton=self.ui.radio_rib_tag,
                groupBox=self.ui.groupBoxRibs,
                visibilityButton=self.ui.ribsVisibilityButton,
                opacitySlider=self.ui.sliderOpacityRibs,
                model = lambda: EvoSegModels.get('Rib')
            ),
            "Nodule_nnUnet": EvoSegProcess(
                name = "Nodule_nnUnet", 
                segmentationButton=self.ui.btn_seg_nodule,
                segmentationNode=None,
                radioButton=None,
                groupBox=self.ui.groupBoxNodule,
                visibilityButton=self.ui.noduleVisibilityButton,
                opacitySlider=self.ui.sliderOpacityNodule,
                model = lambda: EvoSegModels.get('Nodule')
            )
        }

        for process in self._process.values():
            process.groupBox.setVisible(False)

        self.sceneEndCloseObserverTag = self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        self.sceneEndImportObserverTag = self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndImportEvent, self.onSceneEndImport)

    def enter(self):
        """Called when the user enters the module."""
        for process in self._process.values():
            process.init_segmentation_node()
        
    def exit(self):
        # 切出模块时，及时关掉修改
        if self.bt_place_down:
            self.ui.bt_place.click()

    def onSceneEndClose(self, caller, event):
        for process in self._process.values():
            process.segmentationNode=None
            process.groupBox.setVisible(False)

    def onSceneEndImport(self, caller, event):
        """Called when a scene is imported."""
        for process in self._process.values():
            process.init_segmentation_node()

    def onButtonGroupClick(self, button, checked):
        process = EvoSegProcess.filterOne(self._process.values(), "radioButton", button)
        if not process:
            print(f"No process found for button {button}")
            return
        self.data_module=None
        self.data_module_name=''
        for i in self.data_module_list:
            if i["model_name"]==process.name:
                self.data_module=i["seg_data"]
                self.data_module_name=process.name
                break

    def onExportClick(self):
        dataModuleWidget = slicer.modules.data.widgetRepresentation()
        subjectHierarchyTreeView = dataModuleWidget.findChild(slicer.qMRMLSubjectHierarchyTreeView)

        export_labelmap_node = [slicer.mrmlScene.GetFirstNodeByName("Airway_nnUnet_Output_Mask"),
                                slicer.mrmlScene.GetFirstNodeByName("Artery_nnUnet_Output_Mask"),
                                slicer.mrmlScene.GetFirstNodeByName("LungLobe_nnUnet_Output_Mask"),
                                slicer.mrmlScene.GetFirstNodeByName("Rig_nnUnet_Output_Mask"),
                                slicer.mrmlScene.GetFirstNodeByName("Vein_nnUnet_Output_Mask"),
                                slicer.mrmlScene.GetFirstNodeByName("Nodule_nnUnet_Output_Mask")]
        for node in export_labelmap_node:
            if node and node.GetSegmentation().GetNumberOfSegments()!=0:
                NodeShItem = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene).GetItemByDataNode(node)
                subjectHierarchyTreeView.setCurrentItem(NodeShItem)
                plugin=slicer.qSlicerSubjectHierarchyPluginHandler.instance().pluginByName('Segmentations')
                openExportDICOMDialogAction=plugin.children()[0]
                openExportDICOMDialogAction.trigger()

                export_node = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLLabelMapVolumeNode')

                NodeShItem = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene).GetItemByDataNode(export_node)
                subjectHierarchyTreeView.setCurrentItem(NodeShItem)
                plugin=slicer.qSlicerSubjectHierarchyPluginHandler.instance().pluginByName('Export')
                openExportDICOMDialogAction=plugin.children()[0]
                openExportDICOMDialogAction.trigger()
                slicer.mrmlScene.RemoveNode(export_node)

    def onSegButtonClick(self, button):
        process = EvoSegProcess.filterOne(self._process.values(), "segmentationButton", button)
        if not process:
            print(f"No process found for segmentationButton {button}")
            return
        
        process.segmentationButton.setEnabled(False)
        self.ui.bt_cancel_run.setEnabled(True)
        
        if self._processingState == EvoSegWidget.PROCESSING_IDLE:
            self.onApply(process.name)
        else:
            self.onCancel()

    def check_set_modifiy(self):
        if len(self.data_module_list)==0 and self.bt_place_down==False:
            self.ui.bt_place.setChecked(False)
            slicer.util.messageBox("No result output")
            return

        originMarkupsDisplayNodes = slicer.util.getNodesByClass("vtkMRMLMarkupsDisplayNode")

        if not self.bt_place_down:

            self.bt_place_down = True
            self.ui.groupBox_Modify.show()

            self.layoutManager = slicer.app.layoutManager()
        
            views = [
                slicer.app.layoutManager().threeDWidget(0).threeDView(),
                slicer.app.layoutManager().sliceWidget("Red").sliceView(),
                slicer.app.layoutManager().sliceWidget("Yellow").sliceView(),
                slicer.app.layoutManager().sliceWidget("Green").sliceView()
            ]
            

            for node in originMarkupsDisplayNodes:
                node.SetVisibility(False)
            self.markup_node=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
            self.markup_node.SetMarkupLabelFormat("")
            DisplayNode=self.markup_node.GetDisplayNode()
            DisplayNode.SetSelectedColor(1,1,1)
            DisplayNode.SetGlyphSize(self.ui.radius_slider.value)
            DisplayNode.SetUseGlyphScale(False)
            self.ui.radius_slider.valueChanged.connect(lambda value: DisplayNode.SetGlyphSize(value))
            selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
            if selectionNode:
                selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
            interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
            if interactionNode:
                interactionNode.SwitchToSinglePlaceMode()

                if self.interactionNodeObserver:
                    interactionNode.RemoveObserver(self.interactionNodeObserver)
                self.interactionNodeObserver = interactionNode.AddObserver(slicer.vtkMRMLInteractionNode.InteractionModeChangedEvent, self.onInteractionModeChanged)

            try:
                for observedNode, observation in self.observations:
                    observedNode.RemoveObserver(observation)
            except:
                pass
            
            self.observations=[[DisplayNode, DisplayNode.AddObserver(DisplayNode.CustomActionEvent1, self.someCustomAction)]]
            
            for view in views:
                markupsDisplayableManager = view.displayableManagerByClassName('vtkMRMLMarkupsDisplayableManager')
                widget = markupsDisplayableManager.GetWidget(DisplayNode)
                widget.SetEventTranslation(widget.WidgetStateOnWidget, slicer.vtkMRMLInteractionEventData.RightButtonClickEvent, vtk.vtkEvent.NoModifier, vtk.vtkWidgetEvent.NoEvent)
                widget.SetEventTranslation(widget.WidgetStateOnWidget, slicer.vtkMRMLInteractionEventData.RightButtonClickEvent, vtk.vtkEvent.NoModifier, widget.WidgetEventCustomAction1)
                
        else:

            self.bt_place_down = False
            self.ui.groupBox_Modify.hide()

            interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
            if interactionNode:
                interactionNode.SwitchToViewTransformMode()
            if self.markup_node:
                self.markup_node.RemoveAllControlPoints()
                slicer.mrmlScene.RemoveNode(self.markup_node)
            
            for node in originMarkupsDisplayNodes:
                node.SetVisibility(True)
            
    def onInteractionModeChanged(self, event, _):
        # print(event.GetCurrentInteractionMode())
        if event.GetCurrentInteractionMode()==2:
            # print(self.markup_node.GetNumberOfControlPoints())
            if self.markup_node.GetNumberOfControlPoints()==0:
                self.ui.bt_place.click()
                event.RemoveObserver(self.interactionNodeObserver)



    def onButtonUndoClick(self):
        self.data_module.undo()
        self.ui.label_6.setText("Target Modifiy Queue Len:"+str(self.data_module.get_history_len()))
        self.FasterUpdateSegForonPress(self.data_module.get_masks())

    def FasterUpdateSegForonPress(self, segmentation_masks,select_radio_tag_text):
        import numpy as np

        is_splited_segment=False # 临时

        if select_radio_tag_text=="airway":
            segment_name=["airway"]
            seg_number_for_this_node=1
            is_splited_segment=True
        elif select_radio_tag_text=="artery":
            segment_name=["artery"]
            seg_number_for_this_node=2
            is_splited_segment=True
        elif select_radio_tag_text=="vein":
            segment_name=["vein"]
            seg_number_for_this_node=3
            is_splited_segment=True
        elif select_radio_tag_text=="rib":
            segment_name=["rib"]
            seg_number_for_this_node=20
        else: #select_radio_tag_text=="lobe":
            
            segment_name=[select_radio_tag_text]#临时["left upper lobe","left lower lobe","right upper lobe","right middle lobe","right lower lobe"]
            
            k=10
            for i in ["left upper lobe","left lower lobe","right upper lobe","right middle lobe","right lower lobe"]:
                if select_radio_tag_text==i:
                    break
                else:
                    k+=1
            seg_number_for_this_node=k
            #print("(lung lobe unique)-->",seg_number_for_this_node)

        segmentationNode=slicer.mrmlScene.GetFirstNodeByName(self.data_module_name+"_Output_Mask")


        combined_mask = np.zeros(segmentation_masks["airway"].shape, dtype=np.uint8) #TODO: 临时,shape都一样直接使用segmentation_masks["airway"].shape 虽然可读性不强

        BackgroundVolumeID_Red = slicer.app.layoutManager().sliceWidget("Red").sliceLogic().GetSliceCompositeNode().GetBackgroundVolumeID()
        volumeNode = slicer.mrmlScene.GetNodeByID(BackgroundVolumeID_Red)
        
        combined_mask[segmentation_masks[segment_name[0]]] = seg_number_for_this_node
        

        is_splited_segment_and_check_splited = EvoSegModels.get(segment_name[0].split('_')[0].capitalize()).isSplitByMidPlane()

        if is_splited_segment and is_splited_segment_and_check_splited:
            mergeSegments(segmentationNode,
            segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segment_name[0]+"_left"),
            segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segment_name[0]+"_right")
            )
        
        if len(segment_name)==1:
            segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segment_name[0])
        # else:
        #     segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName('Artery')
        
        # Get segment as numpy array
        segmentArray = slicer.util.arrayFromSegmentBinaryLabelmap(segmentationNode, segmentId, volumeNode)

        slicer.util.updateSegmentBinaryLabelmapFromArray(np.transpose(combined_mask, (2, 1, 0)), segmentationNode, segmentId, volumeNode)

        segmentationNode.CreateClosedSurfaceRepresentation()

        if is_splited_segment and is_splited_segment_and_check_splited:
            splitSegment(segmentationNode,
            segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segment_name[0])
            )


    def someCustomAction(self, caller, eventId):
        import numpy as np
        #markupsDisplayNode = caller
        #print(type(markupsDisplayNode))
        #print(f"Custom action activated in {markupsDisplayNode.GetNodeTagName()}")
        
        BackgroundVolumeID_Red = slicer.app.layoutManager().sliceWidget("Red").sliceLogic().GetSliceCompositeNode().GetBackgroundVolumeID()
        # inputNodeName = self.ui.inputNodeSelector0.currentNode().GetName()
        volumeNode = slicer.mrmlScene.GetNodeByID(BackgroundVolumeID_Red) #slicer.util.getNode(inputNodeName)
        pointListNode = self.markup_node
        markupsIndex = 0

        # Get point coordinate in RAS
        point_Ras = [0, 0, 0]
        pointListNode.GetNthControlPointPositionWorld(markupsIndex, point_Ras)

        # If volume node is transformed, apply that transform to get volume's RAS coordinates
        transformRasToVolumeRas = vtk.vtkGeneralTransform()
        slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(None, volumeNode.GetParentTransformNode(), transformRasToVolumeRas)
        point_VolumeRas = transformRasToVolumeRas.TransformPoint(point_Ras)

        # Get voxel coordinates from physical coordinates
        volumeRasToIjk = vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(volumeRasToIjk)
        point_Ijk = [0, 0, 0, 1]
        volumeRasToIjk.MultiplyPoint(np.append(point_VolumeRas,1.0), point_Ijk)
        point_Ijk = [ int(round(c)) for c in point_Ijk[0:3] ]

        # Print output
        #print(point_Ijk)
        # 获取所选模型name
        segmentationNode=slicer.mrmlScene.GetFirstNodeByName(self.data_module_name+"_Output_Mask")

        if segmentationNode is None:
            print("No have "+self.data_module_name+"_Output_Mask")
            return

        r,a,s = point_Ras
        print(r,a,s,"------------------")
        radiu=self.ui.radius_slider.value/2 # UI上slider的值确认为为直径

        # 三个视图都检查 理论上必找到mukup附近的label类别，TODO:可能只需要一个窗口并且4个方向即可
        for sliceViewName in ["Red","Green","Yellow"]: 
            segmentationsDisplayableManager = slicer.app.layoutManager().sliceWidget(sliceViewName).sliceView().displayableManagerByClassName("vtkMRMLSegmentationsDisplayableManager2D")
            # 先检查point_Ras，再检查point_Ras周围六个方向为radiu的一个点,尽可能找到mukup粘到的模型
            for ras in [point_Ras,[r+radiu,a,s],[r-radiu,a,s],[r,a+radiu,s],[r,a-radiu,s],[r,a,s+radiu],[r,a,s-radiu]]:
                # print(sliceViewName,ras)
                # pointListNode.GetNthControlPointPositionWorld(0, ras) # TODO: 之前查找失败的原因是这一句重新赋值了所遍历的ras坐标
                # print(sliceViewName,ras)
                segmentIds = vtk.vtkStringArray()
                segmentationsDisplayableManager.GetVisibleSegmentsForPosition(ras, segmentationNode.GetDisplayNode(), segmentIds)

                segment=None
                for idIndex in range(segmentIds.GetNumberOfValues()):
                    segment = segmentationNode.GetSegmentation().GetSegment(segmentIds.GetValue(idIndex))
                    #print("Segment found at position {0}: {1}".format(ras, segment.GetName()))
                    print("^")
                    break
                if segment!=None:
                    break
            if segment!=None:
                break

        

        import ast
        x,y,z=point_Ijk
        
        #print(self.data_module.get_masks())
        optin_select=self.button_group2.checkedButton().text
        seg_net_select=self.button_group.checkedButton().text
        if seg_net_select=="lobe":
            if segment !=None:
                seg_net_select=segment.GetName()# 改成临近label类型
            else:
                # 不处理, 注意现在的lobe选项的时候不可能会离开模型表面太远添加模型, 其它标签则可以凭空添加
                return
        param = ast.literal_eval("{'radius':"+str(int(self.ui.radius_slider.value))+",}")
        #self.ui.label_img.setText(self.ui.label_img.text+ self.button_group.checkedButton().text+" "+self.button_group2.checkedButton().text+" "+str(param['radius']))
        if optin_select=="Sphere Addition":
            self.data_module.sphere_addition(x, y, z, seg_net_select, **param)
        elif optin_select=="Sphere Erasure":
            self.data_module.sphere_erasure(x, y, z, seg_net_select, **param)
        else:
            return
        self.FasterUpdateSegForonPress(self.data_module.get_masks(),seg_net_select)
        #print(self.button_group.checkedButton().text)
        #self.data_module.
        self.ui.label_6.setText("Target Modifiy Queue Len:"+str(self.data_module.get_history_len()))
        
    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()
        EvoSegmentator.get_instance().reset()

    def removeObservers(self):
        try:
            for observedNode, observation in self.observations:
                observedNode.RemoveObserver(observation)
            
            if self.sceneEndCloseObserverTag:
                self.removeObserver(self.sceneEndCloseObserverTag)
            if self.sceneEndImportObserverTag:
                self.removeObserver(self.sceneEndImportObserverTag)
        except:
            print("No have observation")

    def addLog(self, text):
        """Append text to log window
        """
        self.ui.statusLabel.appendPlainText(text)
        slicer.app.processEvents()  # force update

    def onApply(self,model_name):
        #self.ui.statusLabel.plainText = ""

        try:
            with slicer.util.tryWithErrorDisplay("Failed to start processing.", waitCursor=True):

                # 配置输入
                inputNodes = []
                ThisVolumeNode = self.ui.VolumeNodeComboBox.currentNode()
                inputNodes.append(ThisVolumeNode)
                slicer.util.setSliceViewerLayers(background=ThisVolumeNode)

                # 配置输出
                output_segmentation_name=model_name+"_Output_Mask"

                output_segmentation_node = slicer.mrmlScene.GetFirstNodeByName(output_segmentation_name)
                if not output_segmentation_node:
                    output_segmentation_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", output_segmentation_name)
                
                # 调用self.logic.process

                for i in self._segmentationProcessInfoList:
                    if i["name"]==model_name:
                        slicer.util.messageBox("This model is running.")
                        return
                
                self._segmentationProcessInfo = self.logic.process(inputNodes, output_segmentation_node, model_name)
                self._segmentationProcessInfoList.append({
                                                          "name":model_name,
                                                          "process":self._segmentationProcessInfo
                                                         })

                print(EvoSegWidget.PROCESSING_IN_PROGRESS,"PROCESSING_IN_PROGRESS")

        except Exception as e:
            print(EvoSegWidget.PROCESSING_IDLE,"PROCESSING_IDLE")
            self.ui.bt_seg_airway.setEnabled(True)
            self.ui.bt_seg_artery.setEnabled(True)
            self.ui.btn_seg_vein.setEnabled(True)
            self.ui.btn_seg_lobe.setEnabled(True)
            self.ui.btn_seg_rib.setEnabled(True)
            self.ui.btn_seg_nodule.setEnabled(True)
            self.ui.bt_cancel_run.setEnabled(False)
            self.ui.bt_batch.setEnabled(True)

    def onBatchSegmentation(self):
        with slicer.util.tryWithErrorDisplay("Batch processing failed.", waitCursor=True):
            self.ui.bt_batch.setEnabled(False)
            self.logic.batchMode = True
            self.onSegButtonClick(self._process["Airway_nnUnet"].segmentationButton)

    def onCancel(self):
        with slicer.util.tryWithErrorDisplay("Failed to cancel processing.", waitCursor=True):
            self.logic.batchMode = False
            self.ui.bt_batch.setEnabled(True)
            if len(self._segmentationProcessInfoList)==0:
                slicer.util.messageBox("No Process Run")
                return
            #print(len(self._segmentationProcessInfoList),"----<<")
            for i in reversed(self._segmentationProcessInfoList):
                self.logic.cancelProcessing(i["process"])
                self._segmentationProcessInfoList.remove(i)
                for process in self._process.values():
                    if i["name"] == process.name:
                        process.segmentationButton.setEnabled(True)
                        break
            print(EvoSegWidget.PROCESSING_CANCEL_REQUESTED,"PROCESSING_CANCEL_REQUESTED")

    def onProcessImportStarted(self):
        print(EvoSegWidget.PROCESSING_IMPORT_RESULTS,"PROCESSING_IMPORT_RESULTS")
        qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
        slicer.app.processEvents()

    def onProcessImportEnded(self):
        qt.QApplication.restoreOverrideCursor()
        slicer.app.processEvents()

    def onProcessingCompleted(self, returnCode):
        # self.ui.statusLabel.appendPlainText("\nProcessing finished.")
        print(EvoSegWidget.PROCESSING_IDLE,"PROCESSING_IDLE")

        # TODO: 以下代码是临时写在此处的！
        # 临时在这个回调里处理 3d视图居中和颜色重调(不使用原标准色彩) 和 self._segmentationProcessInfoList
        #---------------------------------------------------------------------
        # Center the 3D view

        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.rotateToViewAxis(3)  # look from anterior direction
        threeDView.resetFocalPoint()  # reset the 3D view cube size and center it
        threeDView.resetCamera()  # reset camera zoom

        # 运行完成的Process要在列表中删除
        # 并确定当前运行完的模型名字
        end_model_name_list=[]
        for i in self._segmentationProcessInfoList:
            proc = i["process"]["proc"]
            if proc.returncode==0:
                end_model_name_list.append(i["name"])
                self._segmentationProcessInfoList.remove(i)
                continue
            #其它操作待定

        # 现在使用Slicer Setting所设置的颜色
        for name in end_model_name_list:
            # 同时把按钮setenbled true
            for process in self._process.values():
                if name == process.name:
                    process.segmentationButton.setEnabled(True)
                    if process.radioButton:
                        process.radioButton.setChecked(True)
                    break

            node = slicer.mrmlScene.GetFirstNodeByName(name+"_Output_Mask")
            node.CreateClosedSurfaceRepresentation()
            segmentation = node.GetSegmentation()
            display_node = node.GetDisplayNode()
            if display_node==None:
                continue
            display_node.SetOpacity3D(1)
            model_name = name.split('_')[0]

            if model_name in ["Airway","Artery","Vein", "Rib", "Nodule"]:
                model_color = EvoSegModels.get(model_name).color()
                for i in range(segmentation.GetNumberOfSegments()):
                    segment = segmentation.GetNthSegment(i)
                    segment.SetColor(model_color.redF(), model_color.greenF(), model_color.blueF())
            elif model_name == "LungLobe":
                model_settings = EvoSegModels.get(model_name)
                for i in range(segmentation.GetNumberOfSegments()):
                    segment = segmentation.GetNthSegment(i)
                    segment_name = segment.GetName()
                    color = model_settings.getSegmentColor(segment_name)
                    segment.SetColor(color.redF(), color.greenF(), color.blueF())

            self.ui.statusLabel.appendPlainText("\n"+name+": Processing finished.")
            #segment_id = segment.GetName()
            # display_node.SetSegmentOpacity3D(segment_id, 0.2)
            # display_node.SetSegmentOverrideColor(segment_id, 0, 0, 1)
        
        #----------------------------------------------------------------------
        self._segmentationProcessInfo = None
        if self.logic.batchMode:
            if "Airway_nnUnet" in end_model_name_list:
                self.onSegButtonClick(self._process["Artery_nnUnet"].segmentationButton)
            elif "Artery_nnUnet" in end_model_name_list:
                self.onSegButtonClick(self._process["Vein_nnUnet"].segmentationButton)
            elif "Vein_nnUnet" in end_model_name_list:
                self.onSegButtonClick(self._process["LungLobe_nnUnet"].segmentationButton)
            elif "LungLobe_nnUnet" in end_model_name_list:
                self.onSegButtonClick(self._process["Rib_nnUnet"].segmentationButton)
            elif "Rib_nnUnet" in end_model_name_list:
                self.onSegButtonClick(self._process["Nodule_nnUnet"].segmentationButton)
            else:
                self.logic.batchMode = False
                self.ui.bt_batch.setEnabled(True)
        
    def onBrowseModelsFolder(self):
        self.logic.createModelsDir()
        qt.QDesktopServices().openUrl(qt.QUrl.fromLocalFile(self.logic.fileCachePath.joinpath("models")))

    def onResultSeg(self,myDataModule, model_name, minPrecision):
        # 刷新DataModule 回调
        append = True
        for i in self.data_module_list:
            if i["model_name"]==model_name:
                i["seg_data"]=myDataModule
                append = False
                break
        if append:
            self.data_module_list.append({"model_name":model_name,"seg_data":myDataModule})
            process = EvoSegProcess.filterOne(self._process.values(), "name", model_name)
            if process and process.radioButton == self.button_group.checkedButton():
                self.data_module = myDataModule
                self.data_module_name = model_name
                
        # print(dir(self.ui.radius_slider))
        # self.ui.radius_slider.singleStep= minPrecision #
        self.ui.radius_slider.minimum = minPrecision*2 # 最大为2倍最大间距
        self.ui.radius_slider.maximum = minPrecision*20 # 最大为20倍最大间距
        self.ui.radius_slider.setValue(minPrecision*5) # 默认为5倍最大间距 

    def onVisibilityButtonToggled(self, toggled : bool, visibilityButton : qt.QPushButton):
        for process in self._process.values():
            if not process.segmentationNode:
                continue
            displayNode = process.segmentationNode.GetDisplayNode()
            if visibilityButton == process.visibilityButton:
                displayNode.SetVisibility3D(toggled)
                displayNode.SetVisibility2DFill(toggled)
                displayNode.SetVisibility2DOutline(toggled)
                return
            else:
                for segment in process.segments:
                    if segment.visibilityButton == visibilityButton:
                        segmentID = process.segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segment.name)
                        if segmentID:
                            displayNode.SetSegmentVisibility(segmentID, toggled)
                            displayNode.SetSegmentVisibility3D(segmentID, toggled)
                        return

    def onSegmentationOpacityChanged(self, value, slider) -> None:
        process = EvoSegProcess.filterOne(self._process.values(), "opacitySlider", slider)
        if process:
            node = process.segmentationNode
            if node:
                displayNode = node.GetDisplayNode()
                displayNode.SetOpacity3D(value)
                displayNode.SetOpacity2DFill(value)
                
    def onSegmentOpacityChanged(self, value, slider) -> None:
        for process in self._process.values():
            if not process.segmentationNode:
                continue
            displayNode = process.segmentationNode.GetDisplayNode()
            for segment in process.segments:
                if segment.opacitySlider == slider:
                    segmentID = process.segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segment.name)
                    if segmentID:
                        displayNode.SetSegmentOpacity3D(segmentID, value)
                        displayNode.SetSegmentOpacity2DFill(segmentID, value)
                    return
                
    def onVolumeNodeSelected(self, node):
        # Reset EvoSegmentator singleton when volume node changes
        if node:
            nodeName = node.GetName()
            case_dir = 'case_' + re.sub(r'[^a-zA-Z0-9_-]', '_', nodeName)
            EvoSegmentator.get_instance().reset(case_dir)
        else:
            EvoSegmentator.get_instance().reset()
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
    
    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)
        from collections import OrderedDict
        import pathlib
        self.fileCachePath = pathlib.Path.home().joinpath(".EvoSeg")

        self.moduleDir = os.path.dirname(slicer.util.getModule('EvoSeg').path)
        self.logCallback = None
        self.processingCompletedCallback = None
        self.startResultImportCallback = None
        self.endResultImportCallback = None
        self.setResultToLabelCallback = None
        
        # Timer for checking the output of the segmentation process that is running in the background
        self.processOutputCheckTimerIntervalMsec = 1000

        self.clearOutputFolder = True #NOTE: 清除缓存目录

        self.data_module = []
        self.batchMode = False

    def createModelsDir(self):
        modelsDir = self.fileCachePath.joinpath("models")
        if not os.path.exists(modelsDir):
            os.makedirs(modelsDir)

    def modelPath(self, modelName):
        import pathlib
        modelRoot = self.fileCachePath.joinpath("models").joinpath(modelName)
        for path in pathlib.Path(modelRoot).rglob("dataset.json"):
            return path.parent
        raise RuntimeError(f"Model {modelName} path not found, You can try:\n click 'open model cache folder' button -> Create a folder name of model name -> Extract your model json and fold_x to this folder.\nYour model folder should be:\n{modelName} \n  |-fold_1\n  |-dataset.json\n  |-...\n  ...\n")

    def log(self, text):
        logging.info(text)
        if self.logCallback:
            self.logCallback(text)
        
    def process(self, inputNodes, outputSegmentation, model):
        """
        """
        if not inputNodes:
            raise ValueError("Input nodes are invalid")
        if not outputSegmentation:
            raise ValueError("Output segmentation is invalid")

        is_self_deploy_model=False

        if model.split("_")[0]=="Nodule":
            is_self_deploy_model=True

        try:
            modelPath = self.modelPath(model)
        except RuntimeError as e:
            self.log(f"Model {model} not found: {e}")
            return None
        
        segmentationProcessInfo = {}

        import time
        startTime = time.time()
        self.log(model+": Processing started")
        segmentator = EvoSegmentator.get_instance()
        caseDir = segmentator.case_dir

        # Get Python executable path
        pythonSlicerExecutablePath = shutil.which("PythonSlicer")
        #print(pythonSlicerExecutablePath)
        if not pythonSlicerExecutablePath:
            raise RuntimeError("Python was not found")

        # 写入缓存目录
        # Write input volume to file
        inputFiles = []
        
        for inputIndex, inputNode in enumerate(inputNodes):
            if inputNode.IsA('vtkMRMLScalarVolumeNode'):
                inputImageFile = os.path.join(segmentator.input_dir, f"input-volume{inputIndex}.nii.gz")
                self.log(model+f": Writing input file to {inputImageFile}")
                volumeStorageNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLVolumeArchetypeStorageNode")
                volumeStorageNode.SetFileName(inputImageFile)
                volumeStorageNode.UseCompressionOff()
                volumeStorageNode.WriteData(inputNode)
                slicer.mrmlScene.RemoveNode(volumeStorageNode)
                inputFiles.append(inputImageFile)
            else:
                raise ValueError(f"Input node type {inputNode.GetClassName()} is not supported")

        # make Command
        if not is_self_deploy_model:
            # 执行nnunet
            outputSegmentationFile = os.path.join(segmentator.output_dir, "output-segmentation.nii.gz")
            modelPtFile = modelPath
            inferenceScriptPyFile = os.path.join(self.moduleDir, "EvoSegLib", "nnunetv2_inference.py")
            is_total_model=False
            is_multi_input=False

            modelName = model.split("_")[0]
            if modelName=="Rib" :
                is_total_model=True
            elif modelName=="LungLobe":
                is_multi_input=True

            command = [ pythonSlicerExecutablePath, str(inferenceScriptPyFile),
                "--model_folder", str(modelPtFile),
                "--image_file", inputFiles[0],
                "--result_file", str(outputSegmentationFile),
                "--use_total", str(is_total_model),
                "--use_multi_input", str(is_multi_input),
                "--case_dir", str(caseDir)
                ]

            for inputIndex in range(1, len(inputFiles)):
                command.append(f"--image-file-{inputIndex+1}")
                command.append(inputFiles[inputIndex])

            self.log(model+": Creating segmentations with EvoSeg AI...")
            self.log(model+f": command: {command}")
        else:
            if model.split("_")[0]=="Nodule":
                # 这里执行自建模型Nodule
                outputSegmentationFile = os.path.join(segmentator.output_dir, "output-segmentation.nii.gz")
                inferenceScriptPyFile = os.path.join(modelPath, "lung_nodule_ct_detection/scripts" , "generate_mask.py")
                command = [ pythonSlicerExecutablePath, str(inferenceScriptPyFile),
                    "--i", segmentator.input_dir,
                    "--o", segmentator.output_dir,
                    "--t", str(0.86),
                    "--spp", pythonSlicerExecutablePath
                    ]

                self.log(model+": Creating segmentations with New EvoSeg AI...")
                self.log(model+f": command: {command}")
        
        # Ensure case directory exists
        os.makedirs(caseDir, exist_ok=True)
        proc = slicer.util.launchConsoleProcess(command, updateEnvironment=None, cwd=caseDir)

        segmentationProcessInfo["proc"] = proc
        segmentationProcessInfo["procReturnCode"] = EvoSegLogic.EXIT_CODE_DID_NOT_RUN
        segmentationProcessInfo["cancelRequested"] = False
        segmentationProcessInfo["startTime"] = startTime
        segmentationProcessInfo["tempDir"] = caseDir
        segmentationProcessInfo["segmentationProcess"] = proc
        segmentationProcessInfo["inputNodes"] = inputNodes
        segmentationProcessInfo["outputSegmentation"] = outputSegmentation
        segmentationProcessInfo["outputSegmentationFile"] = outputSegmentationFile
        segmentationProcessInfo["model"] = model

        if proc:
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
            try:
                psProcess = psutil.Process(proc.pid)
                for psChildProcess in psProcess.children(recursive=True):
                    if psChildProcess.is_running():
                        psChildProcess.kill()
                if psProcess.is_running():
                    psProcess.kill()
            except psutil.NoSuchProcess:
                pass
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
        qt.QTimer.singleShot(self.processOutputCheckTimerIntervalMsec, lambda segmentationProcessInfo=segmentationProcessInfo: self.checkSegmentationProcessOutput(segmentationProcessInfo))

    def dataModuleReadResult(self, result_data, result_data_path, model_name):
        # 刷新DataModule, 这会清除data.py之前的修改，也就是每次模型输出结果后都会覆盖原结果
        # 现在的逻辑不改变的话，推荐在重新运行模型前务必对修改结果，优化方向：可以检查"modifiy queue lenth"不为1时，再次重运行模型前进行提示保存
        from vtk.util import numpy_support
        import nibabel as nib
        import numpy as np

        image_data = result_data.GetImageData()
        # print(result_data)
        if image_data:
            vtk_array = numpy_support.vtk_to_numpy(image_data.GetPointData().GetScalars())
            # TODO: 这里有一个顺序BUG 不是(Z, Y, X)
            numpy_array = vtk_array.reshape(image_data.GetDimensions())  
            # print("NumPy shape:", numpy_array.shape)

            ct_data = numpy_array
            ct_data = ct_data - ct_data.min() * 1.0
            ct_data = ct_data / ct_data.max()

            nii_image = nib.load(result_data_path+"/output/output-segmentation.nii.gz")
            data = nii_image.get_fdata()

            if data.ndim>3:
                print("4 dim array!!") #未出现该情况
                segmentation_masks = {
                    "airway" : data[0, :, :, :] == 1, 
                    "artery": data[2, :, :, :] == 1, 
                    "vein": data[2, :, :, :] == 2
                }
            else:
                segmentation_masks = {
                    "airway" : data[:, :, :] == 1, 
                    "artery": data[:, :, :] == 2, 
                    "vein": data[:, :, :] == 3,
                    "left upper lobe": data[:, :, :] == 10,
                    "left lower lobe": data[:, :, :] == 11,
                    "right upper lobe": data[:, :, :] == 12,
                    "right middle lobe": data[:, :, :] == 13,
                    "right lower lobe": data[:, :, :] == 14,
                    "rib": data[:, :, :] == 20,
                    "Apical RB1": data[:, :, :] == 31,
                    "Posterior RB2": data[:, :, :] == 32,
                    "Anterior RB3": data[:, :, :] == 33,
                    "Lateral RB4": data[:, :, :] == 34,
                    "Medial RB5": data[:, :, :] == 35,
                    "Superior RB6": data[:, :, :] == 36,
                    "Medial basal RB7": data[:, :, :] == 37,
                    "Anterior basal RB8": data[:, :, :] == 38,
                    "Lateral basal RB9": data[:, :, :] == 39,
                    "Posterior basal RB10": data[:, :, :] == 40,
                    "Apicoposterior LB1/2": data[:, :, :] == 41,
                    "Anterior LB3": data[:, :, :] == 42,
                    "Superior lingular LB4": data[:, :, :] == 43,
                    "Inferior lingular LB5": data[:, :, :] == 44,
                    "Superior LB6": data[:, :, :] == 45,
                    "Anterior basal LB8": data[:, :, :] == 46,
                    "Lateral basal LB9": data[:, :, :] == 47,
                    "Posterior basal LB10": data[:, :, :] == 48,
                    "nodule": data[:, :, :] == 201
                }

            probability_maps = {
                "airway": segmentation_masks["airway"].astype(np.float32),
                "artery": segmentation_masks["artery"].astype(np.float32),
                "vein": segmentation_masks["vein"].astype(np.float32),

                "rib": segmentation_masks["rib"].astype(np.float32),
                "Apical RB1": segmentation_masks["Apical RB1"].astype(np.float32),
                "Posterior RB2": segmentation_masks["Posterior RB2"].astype(np.float32),
                "Anterior RB3": segmentation_masks["Anterior RB3"].astype(np.float32),
                "Lateral RB4": segmentation_masks["Lateral RB4"].astype(np.float32),
                "Medial RB5": segmentation_masks["Medial RB5"].astype(np.float32),
                "Superior RB6": segmentation_masks["Superior RB6"].astype(np.float32),
                "Medial basal RB7": segmentation_masks["Medial basal RB7"].astype(np.float32),
                "Anterior basal RB8": segmentation_masks["Anterior basal RB8"].astype(np.float32),
                "Lateral basal RB9": segmentation_masks["Lateral basal RB9"].astype(np.float32),
                "Posterior basal RB10": segmentation_masks["Posterior basal RB10"].astype(np.float32),
                "Apicoposterior LB1/2": segmentation_masks["Apicoposterior LB1/2"].astype(np.float32),
                "Anterior LB3": segmentation_masks["Anterior LB3"].astype(np.float32),
                "Superior lingular LB4": segmentation_masks["Superior lingular LB4"].astype(np.float32),
                "Inferior lingular LB5": segmentation_masks["Inferior lingular LB5"].astype(np.float32),
                "Superior LB6": segmentation_masks["Superior LB6"].astype(np.float32),
                "Anterior basal LB8": segmentation_masks["Anterior basal LB8"].astype(np.float32),
                "Lateral basal LB9": segmentation_masks["Lateral basal LB9"].astype(np.float32),
                "Posterior basal LB10": segmentation_masks["Posterior basal LB10"].astype(np.float32),
                "nodule": segmentation_masks["nodule"].astype(np.float32),
            }

            self.data_module = DataModule(ct_data, segmentation_masks, probability_maps, result_data.GetSpacing())
            
            # TODO: 临时，需要设置data.py对模型修改的最小精度,
            # 可能正确做法是通过某种vtk方法修改模型，然后需要时再从vtk模型中取mask，通过data.py的做法则是通过直接修改mask然后重新生成模型。
            # 目前的做法半径越小缩放插值带来的误差越大
            minPrecision = max(result_data.GetSpacing()) # 用三个方向的最大Spacing表示最小半径,单位mm 
            
            self.setResultToLabelCallback(self.data_module, model_name, minPrecision)
        else:
            print("no image data!")
        
    def onSegmentationProcessCompleted(self, segmentationProcessInfo):
        startTime = segmentationProcessInfo["startTime"]
        tempDir = segmentationProcessInfo["tempDir"]
        inputNodes = segmentationProcessInfo["inputNodes"]
        outputSegmentation = segmentationProcessInfo["outputSegmentation"]
        outputSegmentationFile = segmentationProcessInfo["outputSegmentationFile"]
        model = segmentationProcessInfo["model"]
        procReturnCode = segmentationProcessInfo["procReturnCode"]
        cancelRequested = segmentationProcessInfo["cancelRequested"]

        if cancelRequested:
            procReturnCode = EvoSegLogic.EXIT_CODE_USER_CANCELLED
            self.log(model+f": Processing was cancelled.")
        else:
            if procReturnCode == 0:
                if self.startResultImportCallback:
                    self.startResultImportCallback()
                try:
                    # data.py module class add result
                    self.dataModuleReadResult(inputNodes[0], tempDir, model)

                    # Load result
                    self.log(model+": Importing segmentation results...")
                    
                    #print(type(outputSegmentation), outputSegmentationFile, type(model))
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

                    # Nodule
                    if model == "Nodule_nnUnet":
                        # 初始化 Segment Editor
                        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
                        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
                        segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
                        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)

                        # 使用 outputSegmentation 作为分割节点
                        segmentEditorWidget.setSegmentationNode(outputSegmentation)

                        # 遍历 outputSegmentation 的所有段
                        segmentIDs = vtk.vtkStringArray()
                        segmentation = outputSegmentation.GetSegmentation()
                        segmentation.GetSegmentIDs(segmentIDs)
                        for i in range(segmentIDs.GetNumberOfValues()):
                            segmentID = segmentIDs.GetValue(i)
                            print(f"Processing segment: {segmentID}")

                            # 设置当前段为选中状态
                            segmentEditorNode.SetSelectedSegmentID(segmentID)

                            # 设置 MaskMode（支持动态检查）
                            if hasattr(slicer.vtkMRMLSegmentEditorNode, 'PaintAllowedEverywhere'):
                                segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentEditorNode.PaintAllowedEverywhere)
                            else:
                                segmentEditorNode.SetMaskMode(0)  # 无掩码限制

                            # 激活 Islands 工具并设置参数
                            segmentEditorWidget.setActiveEffectByName("Islands")
                            effect = segmentEditorWidget.activeEffect()
                            if effect:
                                effect.setParameter("MinimumSize", "5")
                                effect.setParameter("Operation", "SPLIT_ISLANDS_TO_SEGMENTS")
                                effect.self().onApply()
                                print(f"  Applied KEEP_LARGEST_ISLAND to segment: {segmentID}")
                            else:
                                print(f"  Failed to activate Islands effect for segment: {segmentID}")
                        
                        segStatLogic = SegmentStatistics.SegmentStatisticsLogic()
                        segStatLogic.getParameterNode().SetParameter("Segmentation", outputSegmentation.GetID())
                        segStatLogic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.obb_diameter_mm.enabled",str(True))
                        segStatLogic.computeStatistics()
                        stats = segStatLogic.getStatistics()
                        
                        segmentIDs = vtk.vtkStringArray()
                        segmentation.GetSegmentIDs(segmentIDs)
                        for i in range(segmentIDs.GetNumberOfValues()):
                            segmentID = segmentIDs.GetValue(i)
                            diameterMm = np.max(np.array(stats[segmentID,"LabelmapSegmentStatisticsPlugin.obb_diameter_mm"]))
                            segment = segmentation.GetSegment(segmentID)
                            segmentName = segment.GetName()
                            segment.SetName(f"{segmentName}_d{diameterMm:.2f}mm")

                        # 清理资源
                        segmentEditorWidget.setActiveEffect(None)
                        segmentEditorWidget = None
                        slicer.mrmlScene.RemoveNode(segmentEditorNode)

                        print("Finished processing outputSegmentation.")

                    widget = slicer.modules.evoseg.widgetRepresentation().self()
                    process = EvoSegProcess.filterOne(widget._process.values(), 'name', model)
                    if process:
                        process.segmentationNode = outputSegmentation
                        process.groupBox.setVisible(True)
                        process.opacitySlider.setValue(outputSegmentation.GetDisplayNode().GetOpacity3D()) 
                        if process.model().isSplitByMidPlane():
                            segmentIDs = vtk.vtkStringArray()
                            segmentation = outputSegmentation.GetSegmentation()
                            segmentation.GetSegmentIDs(segmentIDs)
                            for i in range(segmentIDs.GetNumberOfValues()):
                                segmentID = segmentIDs.GetValue(i)
                                splitSegment(outputSegmentation, segmentID)

                finally:
                    if self.endResultImportCallback:
                        self.endResultImportCallback()

            else:
                self.log(f"{model}: Processing failed with return code {procReturnCode}")
                widget = slicer.modules.evoseg.widgetRepresentation().self()
                process = EvoSegProcess.filterOne(widget._process.values(), 'name', model)
                if process:
                    process.segmentationButton.setEnabled(True)

        # Report total elapsed time
        import time
        stopTime = time.time()
        segmentationProcessInfo["stopTime"] = stopTime
        elapsedTime = stopTime - startTime
        if cancelRequested:
            self.log(model+f": Processing was cancelled after {elapsedTime:.2f} seconds.")
        elif procReturnCode == 0:
            self.log(f"{model}: Processing was completed in {elapsedTime:.2f} seconds.")
        else:
            self.log(f"{model}: Processing failed after {elapsedTime:.2f} seconds.")

        if self.processingCompletedCallback:
            self.processingCompletedCallback(procReturnCode)

    def readSegmentation(self, outputSegmentation, outputSegmentationFile, model):
        labelValueToDescription ={ 
            1: {"name": "Airway", "terminology": 'Segmentation category and type - DICOM master list~SCT^123037004^Anatomical Structure~SCT^89187006^Airway structure~SCT^^~~^^~^^'},
            2: {"name": "Artery", "terminology": 'Segmentation category and type - DICOM master list~SCT^85756007^Tissue~SCT^51114001^Artery~SCT^^~~^^~^^'},
            3: {"name": "Vein", "terminology": 'Segmentation category and type - DICOM master list~SCT^85756007^Tissue~SCT^29092000^Vein~SCT^^~~^^~^^'},
            10:{"name": "left upper lobe", "terminology":"Segmentation category and type - 3D Slicer General Anatomy list~SCT^123037004^Anatomical Structure~SCT^45653009^Upper lobe of Lung~SCT^7771000^Left~Anatomic codes - DICOM master list~^^~^^"},
            11:{"name": "left lower lobe", "terminology":"Segmentation category and type - 3D Slicer General Anatomy list~SCT^123037004^Anatomical Structure~SCT^90572001^Lower lobe of lung~SCT^7771000^Left~Anatomic codes - DICOM master list~^^~^^"},
            12:{"name": "right upper lobe", "terminology":"Segmentation category and type - 3D Slicer General Anatomy list~SCT^123037004^Anatomical Structure~SCT^45653009^Upper lobe of lung~SCT^24028007^Right~Anatomic codes - DICOM master list~^^~^^"},
            13:{"name": "right middle lobe", "terminology":"Segmentation category and type - 3D Slicer General Anatomy list~SCT^123037004^Anatomical Structure~SCT^72481006^Middle lobe of right lung~^^~Anatomic codes - DICOM master list~^^~^^"},
            14:{"name": "right lower lobe", "terminology":"Segmentation category and type - 3D Slicer General Anatomy list~SCT^123037004^Anatomical Structure~SCT^90572001^Lower lobe of lung~SCT^24028007^Right~Anatomic codes - DICOM master list~^^~^^"},
            20:{"name": "rib", "terminology":"None"},
            31: {"name": "Apical RB1", "terminology":"None"},
            32: {"name": "Posterior RB2", "terminology":"None"},
            33: {"name": "Anterior RB3", "terminology":"None"},
            34: {"name": "Lateral RB4", "terminology":"None"},
            35: {"name": "Medial RB5", "terminology":"None"},
            36: {"name": "Superior RB6", "terminology":"None"},
            37: {"name": "Medial basal RB7", "terminology":"None"},
            38: {"name": "Anterior basal RB8", "terminology":"None"},
            39: {"name": "Lateral basal RB9", "terminology":"None"},
            40: {"name": "Posterior basal RB10", "terminology":"None"},
            41: {"name": "Apicoposterior LB1/2", "terminology":"None"},
            42: {"name": "Anterior LB3", "terminology":"None"},
            43: {"name": "Superior lingular LB4", "terminology":"None"},
            44: {"name": "Inferior lingular LB5", "terminology":"None"},
            45: {"name": "Superior LB6", "terminology":"None"},
            46: {"name": "Anterior basal LB8", "terminology":"None"},
            47: {"name": "Lateral basal LB9", "terminology":"None"},
            48: {"name": "Posterior basal LB10", "terminology":"None"},
            201:{"name": "nodule", "terminology":"None"}
        }

        maxLabelValue = max(labelValueToDescription.keys())
        randomColorsNode = slicer.mrmlScene.GetNodeByID("vtkMRMLColorTableNodeRandom")
        rgba = [0, 0, 0, 0]

        colorTableNode = None
        try:
            # Create color table for this segmentation model
            colorTableNode = slicer.vtkMRMLColorTableNode()
            colorTableNode.SetTypeToUser()
            colorTableNode.SetNumberOfColors(maxLabelValue+1)
            colorTableNode.SetName(model)
            for labelValue in labelValueToDescription:
                #print(labelValue,labelValueToDescription[labelValue]["name"])
                randomColorsNode.GetColor(labelValue,rgba)
                colorTableNode.SetColor(labelValue, rgba[0], rgba[1], rgba[2], rgba[3])
                colorTableNode.SetColorName(labelValue, labelValueToDescription[labelValue]["name"])
            #print(colorTableNode,"----<<")
            slicer.mrmlScene.AddNode(colorTableNode)

            # Load the segmentation
            outputSegmentation.SetLabelmapConversionColorTableNodeID(colorTableNode.GetID())
            outputSegmentation.AddDefaultStorageNode()
            storageNode = outputSegmentation.GetStorageNode()
            storageNode.SetFileName(outputSegmentationFile)
            storageNode.ReadData(outputSegmentation)
            
        finally:
            # 确保清理资源
            if colorTableNode:
                slicer.mrmlScene.RemoveNode(colorTableNode)
