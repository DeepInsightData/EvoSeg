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

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", self.EvoSegHello)

    def EvoSegHello(self):
        pass

class EvoSegProcess:
    class Segment:
        def __init__(self, name, visibilityButton, opacitySlider):
            self.name=name
            self.visibilityButton=visibilityButton
            self.opacitySlider=opacitySlider

    def __init__(self, name, segmentationButton, segmentationNode, radioButton, groupBox, visibilityButton, opacitySlider, segments=[]):
        self.name = name
        self.segmentationButton = segmentationButton
        self.segmentationNode = segmentationNode
        self.radioButton=radioButton
        self.groupBox = groupBox
        self.visibilityButton = visibilityButton
        self.opacitySlider = opacitySlider
        self.segments = segments

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
        self.data_module_name=None
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

        self.ui.bt_place.connect("clicked(bool)", self.check_set_modifiy)
        self.bt_place_down = False

        # Buttons
        # self.ui.copyModelsButton.connect("clicked(bool)", self.onCopyModel)
        
        self.ui.browseToModelsFolderButton.connect("clicked(bool)", self.onBrowseModelsFolder)

        self.ui.bt_export.connect("clicked(bool)", self.onExportClick)

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
        self.ui.bt_cancel_run.setIcon(qt.QIcon(self.resourcePath("Icons/EvoSeg_Cancel.png")))
        self.ui.bt_place.setIcon(qt.QIcon(self.resourcePath("Icons/EvoSeg_Place.png")))
        self.ui.bt_place.toggled.connect(lambda checked: self.ui.bt_place.setIcon(
            qt.QIcon(":/Icons/MarkupsFiducialMouseModePlace.png" if checked else self.resourcePath("Icons/EvoSeg_Place.png"))
        ))
        self.ui.bt_export.setIcon(qt.QIcon(self.resourcePath("Icons/EvoSeg_Export.png")))
        self.ui.browseToModelsFolderButton.setIcon(qt.QIcon(self.resourcePath("Icons/EvoSeg_Model.png")))
        self.ui.bt_seg_airway.clicked.connect(lambda: self.onSegButtonClick('airway'))
        self.ui.bt_seg_artery.clicked.connect(lambda: self.onSegButtonClick('artery'))
        self.ui.btn_seg_lobe.clicked.connect(lambda: self.onSegButtonClick('lobe'))
        self.ui.btn_seg_rib.clicked.connect(lambda: self.onSegButtonClick('rib'))
        self.ui.btn_seg_vein.clicked.connect(lambda: self.onSegButtonClick('vein'))
        self.ui.btn_seg_nodule.clicked.connect(lambda: self.onSegButtonClick('nodule'))
        
        self.ui.groupBox_Modify.hide()
        self.interactionNodeObserver=None

        self.ui.airwayVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.airwayVisibilityButton))
        self.ui.arteryVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.arteryVisibilityButton))
        self.ui.veinVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.veinVisibilityButton))
        self.ui.lobeVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.lobeVisibilityButton))
        self.ui.leftUpperLobeVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.leftUpperLobeVisibilityButton))
        self.ui.leftLowerLobeVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.leftLowerLobeVisibilityButton))
        self.ui.rightUpperLobeVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.rightUpperLobeVisibilityButton))
        self.ui.rightMidLobeVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.rightMidLobeVisibilityButton))
        self.ui.rightLowerLobeVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.rightLowerLobeVisibilityButton))
        self.ui.ribsVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.ribsVisibilityButton))
        self.ui.noduleVisibilityButton.toggled.connect(lambda toggled: self.onVisibilityButtonToggled(toggled, self.ui.noduleVisibilityButton))

        self.ui.sliderOpacityAirway.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityAirway))
        self.ui.sliderOpacityArtery.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityArtery))
        self.ui.sliderOpacityVein.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityVein))
        self.ui.sliderOpacityLobe.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityLobe))
        self.ui.sliderOpacityLeftUpperLobe.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityLeftUpperLobe))
        self.ui.sliderOpacityLeftLowerLobe.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityLeftLowerLobe))
        self.ui.sliderOpacityRightUpperLobe.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityRightUpperLobe))
        self.ui.sliderOpacityRightMiddleLobe.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityRightMiddleLobe))
        self.ui.sliderOpacityRightLowerLobe.connect("valueChanged(double)", lambda value: self.onSegmentOpacityChanged(value, self.ui.sliderOpacityRightLowerLobe))
        self.ui.sliderOpacityRibs.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityRibs))
        self.ui.sliderOpacityNodule.connect("valueChanged(double)", lambda value: self.onSegmentationOpacityChanged(value, self.ui.sliderOpacityNodule))
        
        self._process = {
            "Airway_nnUnet" : EvoSegProcess(
                name = "Airway_nnUnet", 
                segmentationButton=self.ui.bt_seg_airway,
                segmentationNode=None,
                radioButton=self.ui.radio_airway_tag,
                groupBox = self.ui.groupBoxAirway,
                visibilityButton=self.ui.airwayVisibilityButton,
                opacitySlider=self.ui.sliderOpacityAirway,
            ),
            "Artery_nnUnet" : EvoSegProcess(
                name = "Artery_nnUnet", 
                segmentationButton=self.ui.bt_seg_artery,
                segmentationNode=None,
                radioButton=self.ui.radio_artery_tag,
                groupBox=self.ui.groupBoxArtery,
                visibilityButton=self.ui.arteryVisibilityButton,
                opacitySlider=self.ui.sliderOpacityArtery,
            ),
            "Vein_nnUnet": EvoSegProcess(
                name = "Vein_nnUnet", 
                segmentationButton=self.ui.btn_seg_vein,
                segmentationNode=None,
                radioButton=self.ui.radio_vein_tag,
                groupBox=self.ui.groupBoxVein,
                visibilityButton=self.ui.veinVisibilityButton,
                opacitySlider=self.ui.sliderOpacityVein,
            ),
            "LungLobe_nnUnet": EvoSegProcess(
                name = "LungLobe_nnUnet",
                segmentationButton=self.ui.btn_seg_lobe,
                segmentationNode=None,
                radioButton=self.ui.radio_lobe_tag,
                groupBox=self.ui.groupBoxLobe,
                visibilityButton=self.ui.lobeVisibilityButton,
                opacitySlider=self.ui.sliderOpacityLobe,
                segments=[
                    EvoSegProcess.Segment("left upper lobe", self.ui.leftUpperLobeVisibilityButton, self.ui.sliderOpacityLeftUpperLobe),
                    EvoSegProcess.Segment("left lower lobe", self.ui.leftLowerLobeVisibilityButton, self.ui.sliderOpacityLeftLowerLobe),
                    EvoSegProcess.Segment("right upper lobe", self.ui.rightUpperLobeVisibilityButton, self.ui.sliderOpacityRightUpperLobe),
                    EvoSegProcess.Segment("right middle lobe", self.ui.rightMidLobeVisibilityButton, self.ui.sliderOpacityRightMiddleLobe),
                    EvoSegProcess.Segment("right lower lobe", self.ui.rightLowerLobeVisibilityButton, self.ui.sliderOpacityRightLowerLobe),
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
            ),
            "Nodule_nnUnet": EvoSegProcess(
                name = "Nodule_nnUnet", 
                segmentationButton=self.ui.btn_seg_nodule,
                segmentationNode=None,
                radioButton=None,
                groupBox=self.ui.groupBoxNodule,
                visibilityButton=self.ui.noduleVisibilityButton,
                opacitySlider=self.ui.sliderOpacityNodule,
            )
        }

        for process in self._process.values():
            process.groupBox.setVisible(False)

        self.sceneEndCloseObserverTag = self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        self.sceneEndImportObserverTag = self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndImportEvent, self.onSceneEndImport)

    def enter(self):
        pass
        
    def exit(self):
        # 切出模块时，及时关掉修改
        if self.bt_place_down:
            self.ui.bt_place.click()
        if self.sceneEndCloseObserverTag:
            self.removeObserver(self.sceneEndCloseObserverTag)
        if self.sceneEndImportObserverTag:
            self.removeObserver(self.sceneEndImportObserverTag)

    def onSceneEndClose(self, caller, event):
        for process in self._process.values():
            process.segmentationNode=None
            process.groupBox.setVisible(False)

    def onSceneEndImport(self, caller, event):
        pass

    def onButtonGroupClick(self,value_for_group):
        model_name_must_is=""
        if value_for_group.text=="airway":
            model_name_must_is = "Airway_nnUnet"
        elif value_for_group.text=="artery":
            model_name_must_is = "Artery_nnUnet"
        elif value_for_group.text=="rib":
            model_name_must_is = "Rib_nnUnet"
        elif value_for_group.text=="lobe":
            model_name_must_is = "LungLobe_nnUnet"
        elif value_for_group.text=="vein":
            model_name_must_is = "Vein_nnUnet"
        elif value_for_group.text=="nodule":
            model_name_must_is = "Nodule_nnUnet"
        
        if model_name_must_is=="":
            return
        else:
            output_segmentation_node=slicer.mrmlScene.GetFirstNodeByName(model_name_must_is+"_Output_Mask")
            for i in self.data_module_list:
                if i["model_name"]==model_name_must_is:
                    self.data_module=i["seg_data"]
                    self.data_module_name=model_name_must_is
                    #print("set DataModule for:"+model_name_must_is)
                    return
        

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

    def onSegButtonClick(self,button_name):
        
        run_model_name=""
        if "airway"==button_name:
            run_model_name="Airway_nnUnet"
            self.ui.bt_seg_airway.setEnabled(False)
            self.ui.bt_cancel_run.setEnabled(True)
        elif "artery"==button_name:
            run_model_name="Artery_nnUnet"
            self.ui.bt_seg_artery.setEnabled(False)
            self.ui.bt_cancel_run.setEnabled(True)
        elif "lobe"==button_name:
            run_model_name="LungLobe_nnUnet"
            self.ui.btn_seg_lobe.setEnabled(False)
            self.ui.bt_cancel_run.setEnabled(True)
        elif "rib"==button_name:
            run_model_name="Rib_nnUnet"
            self.ui.btn_seg_rib.setEnabled(False)
            self.ui.bt_cancel_run.setEnabled(True)
        elif "vein"==button_name:
            run_model_name="Vein_nnUnet"
            self.ui.btn_seg_vein.setEnabled(False)
            self.ui.bt_cancel_run.setEnabled(True)
        elif "nodule"==button_name:
            run_model_name="Nodule_nnUnet"
            self.ui.btn_seg_nodule.setEnabled(False)
            self.ui.bt_cancel_run.setEnabled(True)
        else:
            slicer.util.messageBox("the model name '"+button_name+"' is Not Update!")
            return
        
        if self._processingState == EvoSegWidget.PROCESSING_IDLE:
            self.onApply(run_model_name)
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

        if select_radio_tag_text=="airway":
            segment_name=["airway"]
            seg_number_for_this_node=1
        elif select_radio_tag_text=="artery":
            segment_name=["artery"]
            seg_number_for_this_node=2
        elif select_radio_tag_text=="vein":
            segment_name=["vein"]
            seg_number_for_this_node=3
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
        

        if len(segment_name)==1:
            segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segment_name[0])
        # else:
        #     segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName('Artery')
        
        # Get segment as numpy array
        segmentArray = slicer.util.arrayFromSegmentBinaryLabelmap(segmentationNode, segmentId, volumeNode)

        slicer.util.updateSegmentBinaryLabelmapFromArray(np.transpose(combined_mask, (2, 1, 0)), segmentationNode, segmentId, volumeNode)

        segmentationNode.CreateClosedSurfaceRepresentation()


    def someCustomAction(self, caller, eventId):
        import numpy as np
        markupsDisplayNode = caller
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

    def removeObservers(self):
        #print("rm obse..")
        try:
            for observedNode, observation in self.observations:
                observedNode.RemoveObserver(observation)
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
            self.ui.bt_cancel_run.setEnabled(False)

    def onCancel(self):
        with slicer.util.tryWithErrorDisplay("Failed to cancel processing.", waitCursor=True):
            if len(self._segmentationProcessInfoList)==0:
                slicer.util.messageBox("No Process Run")
                return
            #print(len(self._segmentationProcessInfoList),"----<<")
            for i in self._segmentationProcessInfoList:
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
            if i["process"]["proc"].returncode==0:
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
            display_node.SetOpacity3D(0.8)

            for i in range(segmentation.GetNumberOfSegments()):
                segment = segmentation.GetNthSegment(i)
                
                # import random
                # segment.SetColor(random.random(), random.random(), random.random())
                try:
                    color = EvoSegModels.get(name.split('_')[0]).color()
                    segment.SetColor(color.redF(), color.greenF(), color.blueF())
                except:
                    seg_name=segment.GetName()
                    #固定颜色参考：
                    #https://github.com/Slicer/SlicerLungCTAnalyzer/blob/e2f23dafb6994421ad65606050979b10e8a932aa/LungCTSegmenter/LungCTSegmenter.py#L1266
                    if seg_name=="right upper lobe":
                        color = EvoSegModels.get('Lobe').rightUpperLobeColor()
                        segment.SetColor(color.redF(), color.greenF(), color.blueF())
                    if seg_name=="right middle lobe":
                        color = EvoSegModels.get('Lobe').rightMiddleLobeColor()
                        segment.SetColor(color.redF(), color.greenF(), color.blueF())
                    if seg_name=="right lower lobe":
                        color = EvoSegModels.get('Lobe').rightLowerLobeColor()
                        segment.SetColor(color.redF(), color.greenF(), color.blueF())
                    if seg_name=="left upper lobe":
                        color = EvoSegModels.get('Lobe').leftUpperLobeColor()
                        segment.SetColor(color.redF(), color.greenF(), color.blueF())
                    if seg_name=="left lower lobe":
                        color = EvoSegModels.get('Lobe').leftLowerLobeColor()
                        segment.SetColor(color.redF(), color.greenF(), color.blueF())
                    if "nodule" in seg_name:
                        color = EvoSegModels.get('Nodule').color()
                        segment.SetColor(color.redF(), color.greenF(), color.blueF())
                    # if seg_name=="rib": # 应该不需要这个if, TODO 待检查
                    #     color = EvoSegModels.get('Rib').color()
                    #     segment.SetColor(color.redF(), color.greenF(), color.blueF())
            
            self.ui.statusLabel.appendPlainText("\n"+name+": Processing finished.")
            #segment_id = segment.GetName()
            # display_node.SetSegmentOpacity3D(segment_id, 0.2)
            # display_node.SetSegmentOverrideColor(segment_id, 0, 0, 1)
        
        #----------------------------------------------------------------------
        self._segmentationProcessInfo = None
        
    def onBrowseModelsFolder(self):
        self.logic.createModelsDir()
        qt.QDesktopServices().openUrl(qt.QUrl.fromLocalFile(self.logic.fileCachePath.joinpath("models")))

    def onResultSeg(self,myDataModule, model_name, minPrecision):
        # 刷新DataModule 回调
        self.data_module=myDataModule
        for i in self.data_module_list:
            if i["model_name"]==model_name:
                i["seg_data"]=self.data_module
                return
        self.data_module_list.append({"model_name":model_name,"seg_data":self.data_module})

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
                        displayNode.SetSegmentVisibility(segment.name, toggled)
                        displayNode.SetSegmentVisibility3D(segment.name, toggled)
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
                    displayNode.SetSegmentOpacity3D(segment.name, value)
                    displayNode.SetSegmentOpacity2DFill(segment.name, value)
                    return

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

        self.clearOutputFolder = False #NOTE: 清除缓存目录

        self.data_module = []

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

        # TODO: 下载Vein_EvoSeg.zip，并将压缩包中的目录解压到".....\.EvoSeg\models\", 含有total模型和调整好的新模型
        # https://github.com/DeepInsightData/EvoSeg/releases/download/v0.0.1/Vein_EvoSeg.zip
        is_self_deploy_model=False
        if model.split("_")[0]=="Vein": # 改用total 293模型 注释掉该if
            is_self_deploy_model=True

        # TODO: 下载Nodule_EvoSeg.zip，并将压缩包中的目录解压到".....\.EvoSeg\models\", 含有Nodule模型运行文件
        # https://github.com/DeepInsightData/EvoSeg/releases/download/v0.0.1/Nodule_EvoSeg.zip
        if model.split("_")[0]=="Nodule": # 同Vein
            is_self_deploy_model=True

        #if not is_self_deploy_model: 
        try:
            modelPath = self.modelPath(model)
        except:
            # TODO: 需要重构
            return
        
        segmentationProcessInfo = {}

        import time
        startTime = time.time()
        self.log(model+": Processing started")

        tempDir = slicer.util.tempDirectory()

        import pathlib
        tempDirPath = pathlib.Path(tempDir)

        # Get Python executable path
        import shutil
        pythonSlicerExecutablePath = shutil.which("PythonSlicer")
        #print(pythonSlicerExecutablePath)
        if not pythonSlicerExecutablePath:
            raise RuntimeError("Python was not found")

        # 写入缓存目录
        # Write input volume to file
        inputFiles = []
        if model.split("_")[0]=="Nodule": # Nodule的时候Volume要保存成多个dicom文件
            for inputIndex, inputNode in enumerate(inputNodes):
                if inputNode.IsA('vtkMRMLScalarVolumeNode'):
                    inputImageFile = tempDir + f"/input/"
                    os.makedirs(inputImageFile, exist_ok=True)
                    self.log(model+f": Writing input file to {inputImageFile}")

                    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)

                    volumeShItemID = shNode.GetItemByDataNode(inputNode)
                    patientItemID = shNode.GetItemParent(volumeShItemID)

                    if patientItemID != shNode.GetSceneItemID():
                        parentName = shNode.GetItemName(patientItemID)
                        self.log(f"{inputNode.GetName()} is already under subject hierarchy: {parentName}")
                    else:
                        patientItemID = shNode.CreateSubjectItem(shNode.GetSceneItemID(), "Nodule patient")
                        parentName = "Nodule patient"
                        studyItemID = shNode.CreateStudyItem(patientItemID, "Nodule study")
                        shNode.SetItemParent(volumeShItemID, studyItemID)
                        self.log(f"Added {inputNode.GetName()} to new hierarchy under 'Nodule patient' and 'Nodule study'")
                    
                    

                    import DICOMScalarVolumePlugin
                    exporter = DICOMScalarVolumePlugin.DICOMScalarVolumePluginClass()
                    exportables = exporter.examineForExport(volumeShItemID)
                    for exp in exportables:
                        exp.directory = inputImageFile
                        exp.setTag(patientItemID, parentName)
                        exp.setTag('StudyID', "Nodule study")

                    exporter.export(exportables)

                    # slicer.mrmlScene.RemoveNode(shNode)
                    # shNode.RemoveItem(patientItemID)
                    # slicer.mrmlScene.AddNode(copyVolumeNode)

                    inputFiles.append(inputImageFile)
                else:
                    raise ValueError(f"Input node type {inputNode.GetClassName()} is not supported")    

        else: # 其它情况的保存
            for inputIndex, inputNode in enumerate(inputNodes):
                if inputNode.IsA('vtkMRMLScalarVolumeNode'):
                    inputImageFile = tempDir + f"/input/input-volume{inputIndex}.nii.gz"
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
            outputSegmentationFile = tempDir + "/output/output-segmentation.nii.gz"
            modelPtFile = modelPath
            inferenceScriptPyFile = os.path.join(self.moduleDir, "EvoSegLib", "nnunetv2_inference.py")
            is_total_model=False
            if model.split("_")[0]=="Rib" or model.split("_")[0]=="LungLobe" or model.split("_")[0]=="Vein":
                is_total_model=True

            auto3DSegCommand = [ pythonSlicerExecutablePath, str(inferenceScriptPyFile),
                "--model_folder", str(modelPtFile),
                "--image_file", inputFiles[0],
                "--result_file", str(outputSegmentationFile),
                "--use_total", str(is_total_model)
                ]

            for inputIndex in range(1, len(inputFiles)):
                auto3DSegCommand.append(f"--image-file-{inputIndex+1}")
                auto3DSegCommand.append(inputFiles[inputIndex])

            self.log(model+": Creating segmentations with EvoSeg AI...")
            self.log(model+f": command: {auto3DSegCommand}")
        else:
            if model.split("_")[0]=="Nodule":
                # 这里执行自建模型Nodule
                outputSegmentationFile = tempDir + "/output/output-segmentation.nii.gz"
                inferenceScriptPyFile = os.path.join(modelPath, "lung_nodule_ct_detection/scripts" , "generate_mask.py")
                auto3DSegCommand = [ pythonSlicerExecutablePath, str(inferenceScriptPyFile),
                    "--i", tempDir+"/input",
                    "--o", tempDir+"/output",
                    "--t", str(0.86),
                    "--spp", pythonSlicerExecutablePath
                    ]

                self.log(model+": Creating segmentations with New EvoSeg AI...")
                self.log(model+f": command: {auto3DSegCommand}")
            else:
                # 这里执行自建模型Vein，当前版本仅取它对Vein的分割结果
                outputSegmentationFile = tempDir + "/output/output-segmentation.nii.gz"
                inferenceScriptPyFile = os.path.join(modelPath, "artery_vein_code" , "run.py")
                auto3DSegCommand = [ pythonSlicerExecutablePath, str(inferenceScriptPyFile),
                    "--input", tempDir+"/input",
                    "--output", tempDir+"/output",
                    "--slicer_python_path", pythonSlicerExecutablePath
                    ]

                self.log(model+": Creating segmentations with New EvoSeg AI...")
                self.log(model+f": command: {auto3DSegCommand}")

        proc = slicer.util.launchConsoleProcess(auto3DSegCommand, updateEnvironment=None)

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
                    "nodule": data[:, :, :] == 201
                }

            probability_maps = {
                "airway": segmentation_masks["airway"].astype(np.float32),
                "artery": segmentation_masks["artery"].astype(np.float32),
                "vein": segmentation_masks["vein"].astype(np.float32),

                "left upper lobe": segmentation_masks["left upper lobe"].astype(np.float32),
                "left lower lobe": segmentation_masks["left lower lobe"].astype(np.float32),
                "right upper lobe": segmentation_masks["right upper lobe"].astype(np.float32),
                "right middle lobe": segmentation_masks["right middle lobe"].astype(np.float32),
                "right lower lobe": segmentation_masks["right lower lobe"].astype(np.float32),
                "rib": segmentation_masks["rib"].astype(np.float32),
                "nodule": segmentation_masks["rib"].astype(np.float32),
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
                finally:

                    if self.endResultImportCallback:
                        self.endResultImportCallback()

            else:
                self.log(model+f": Processing failed with return code {procReturnCode}")

        if self.clearOutputFolder:
            self.log(model+": Cleaning up temporary folder.")
            if os.path.isdir(tempDir):
                import shutil
                shutil.rmtree(tempDir)
        else:
            self.log(model+f": Not cleaning up temporary folder: {tempDir}")

        # Report total elapsed time
        import time
        stopTime = time.time()
        segmentationProcessInfo["stopTime"] = stopTime
        elapsedTime = stopTime - startTime
        if cancelRequested:
            self.log(model+f": Processing was cancelled after {elapsedTime:.2f} seconds.")
        else:
            if procReturnCode == 0:
                self.log(model+f": Processing was completed in {elapsedTime:.2f} seconds.")
            else:
                self.log(model+f": Processing failed after {elapsedTime:.2f} seconds.")

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
            201:{"name": "nodule", "terminology":"None"}
        }

        maxLabelValue = max(labelValueToDescription.keys())
        randomColorsNode = slicer.mrmlScene.GetNodeByID("vtkMRMLColorTableNodeRandom")
        rgba = [0, 0, 0, 0]

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

        slicer.mrmlScene.RemoveNode(colorTableNode)