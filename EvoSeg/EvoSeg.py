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

from Scripts.data import DataModule
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

        self.label_np=None

        self.observations = None

        self.markup_node=None
        self.data_module=None
        

        self.logic = EvoSegLogic()

        super().setup()
        

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/EvoSeg.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
        
        import qt

        self.inputNodeSelectors = [self.ui.inputNodeSelector0]

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
        
        self.logic.setResultToLabelCallback = self.onResultSeg

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

         # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).
        for inputNodeSelector in self.inputNodeSelectors:
            inputNodeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.useStandardSegmentNamesCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)

        self.ui.set_modifiy.connect("toggled(bool)", self.check_set_modifiy)

        self.ui.modelComboBox.currentTextChanged.connect(self.updateParameterNodeFromGUI)
        self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.ui.segmentationShow3DButton.setSegmentationNode)
        #self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.logic.)
        #self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.ui.segmentationEditor_.setSegmentationNode)

        # Buttons
        self.ui.copyModelsButton.connect("clicked(bool)", self.onCopyModel)
        
        self.ui.browseToModelsFolderButton.connect("clicked(bool)", self.onBrowseModelsFolder)
        self.ui.deleteAllModelsButton.connect("clicked(bool)", self.onClearModelsFolder)

        # check box
        self.ui.radioButton1.setChecked(True)
        self.ui.radioButton12.setChecked(True)

        # new button click
        self.ui.lineEdit_radius.setText("{'radius':3,}")
        self.ui.button_undo.connect("clicked(bool)", self.onButtonUndoClick)
        self.ui.button_save.connect("clicked(bool)", self.onButtonSaveClick)

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.ui.radioButton1)
        self.button_group.addButton(self.ui.radioButton2)
        self.button_group.addButton(self.ui.radioButton3)
        self.button_group2 = QButtonGroup()
        self.button_group2.addButton(self.ui.radioButton12)
        self.button_group2.addButton(self.ui.radioButton22)
        self.button_group2.addButton(self.ui.radioButton32)
        self.button_group2.addButton(self.ui.radioButton42)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

        self.updateGUIFromParameterNode()

        self.CrosshairNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLCrosshairNode')
        
        if self.CrosshairNode:
            self.CrosshairNodeObserverTag = self.CrosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.processEvent)
        
        extensionsPath = slicer.app.extensionsInstallPath
        print("Extensions Install Path:", extensionsPath)
        layoutManager = slicer.app.layoutManager()
        fourByFourWidget = layoutManager.threeDWidget(0).threeDView()

        # 显示小部件
        fourByFourWidget.show()

        # 新增UI简化更新 update v1
        # 隐藏控件将在之后更新中彻底去除
        self.hide_all_widgets_in_layout(self.ui.formLayout_2)
        self.hide_all_widgets_in_layout(self.ui.gridLayout)

        self.ui.bt_seg_airway.clicked.connect(lambda: self.onSegButtonClick('airway'))
        self.ui.bt_seg_artery.clicked.connect(lambda: self.onSegButtonClick('artery'))

    def onSegButtonClick(self,button_name):
        # update v1 临时借用未删除的隐藏控件
        run_model_name=""
        if "airway"==button_name:
            run_model_name="Airway_nnUnet"
        elif "artery"==button_name:
            run_model_name="Artery_nnUnet"
        else:
            slicer.util.messageBox("the model name '"+button_name+"' is Not Update!")
            return

        model_list_widget = self.ui.modelComboBox
        found = False
        for i in range(model_list_widget.count):
            item = model_list_widget.item(i)
            if item.text() == run_model_name:
                model_list_widget.setCurrentRow(i)
                #slicer.util.messageBox(f"selected model in list : {run_model_name}")
                found = True
                break
        if not found:
            slicer.util.messageBox(f"Model '{run_model_name}' not found in the QListWidget.")
            return
        
        self.onApplyButton()


    def check_set_modifiy(self,check_it):
        #print("?>>>",check_it)
        if check_it:
            self.layoutManager = slicer.app.layoutManager()
        
            views = [
                slicer.app.layoutManager().threeDWidget(0).threeDView(),
                slicer.app.layoutManager().sliceWidget("Red").sliceView(),
                slicer.app.layoutManager().sliceWidget("Yellow").sliceView(),
                slicer.app.layoutManager().sliceWidget("Green").sliceView()
            ]

            
            self.markup_node=slicer.modules.markups.logic().AddControlPoint(0)
            
            markupsDisplayNodes = slicer.util.getNodesByClass("vtkMRMLMarkupsDisplayNode")
            try:
                for observedNode, observation in self.observations:
                    observedNode.RemoveObserver(observation)
            except:
                pass

            self.observations=[]
            for markupsDisplayNode in markupsDisplayNodes:
                self.observations.append([markupsDisplayNode, markupsDisplayNode.AddObserver(markupsDisplayNode.CustomActionEvent1, self.someCustomAction)])

            pointListNode = slicer.util.getNode("vtkMRMLMarkupsFiducialNode1")
            pointListNode.SetNthControlPointLabel(0, "")
            for view in views:
                markupsDisplayableManager = view.displayableManagerByClassName('vtkMRMLMarkupsDisplayableManager')
                widget = markupsDisplayableManager.GetWidget(markupsDisplayNode)
                widget.SetEventTranslation(widget.WidgetStateOnWidget, slicer.vtkMRMLInteractionEventData.RightButtonClickEvent, vtk.vtkEvent.NoModifier, vtk.vtkWidgetEvent.NoEvent)
                widget.SetEventTranslation(widget.WidgetStateOnWidget, slicer.vtkMRMLInteractionEventData.RightButtonClickEvent, vtk.vtkEvent.NoModifier, widget.WidgetEventCustomAction1)
                
        else:
            print("should delete")
            pointListNode = slicer.util.getNode("vtkMRMLMarkupsFiducialNode1")
            pointListNode.RemoveAllMarkups()

    def onButtonUndoClick(self):
        self.data_module.undo()
        self.ui.label_6.setText("Modifiy Queue Len:"+str(self.data_module.get_history_len()))
        self.FasterUpdateSegForonPress(self.data_module.get_masks())
    def onButtonSaveClick(self):
        #segmentation_nodes = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')
        self.logic.set_new_data_module(self.data_module);
        print("Save click")

    def onPress(self,arg1, arg2):
        
        try:
            import ast
            position_=self.ui.label_img.text.split("<b>")
            x,y,z=ast.literal_eval(position_[0])
            #print(x,y,z,position_[1].split("</b>")[0]=="Out of Frame")
            #print("Press")
            if self.data_module==None and position_[1].split("</b>")[0]=="Out of Frame":
                #self.ui.label_img.setText(self.ui.label_img.text+" Erro: data module no init!")
                QMessageBox.warning(None, "错误", f"模型输出数据丢失，请先进行分割")
            else:
                #print(self.data_module.get_masks())
                optin_select=self.button_group2.checkedButton().text
                param = ast.literal_eval(self.ui.lineEdit_radius.text)
                #self.ui.label_img.setText(self.ui.label_img.text+ self.button_group.checkedButton().text+" "+self.button_group2.checkedButton().text+" "+str(param['radius']))
                if optin_select=="Sphere Addition":
                    self.data_module.sphere_addition(x, y, z, self.button_group.checkedButton().text, **param)
                elif optin_select=="Sphere Erasure":
                    self.data_module.sphere_erasure(x, y, z, self.button_group.checkedButton().text, **param)
                else:
                    return
                self.FasterUpdateSegForonPress(self.data_module.get_masks())
                #print(self.button_group.checkedButton().text)
                #self.data_module.
                self.ui.label_6.setText("Modifiy Queue Len:"+str(self.data_module.get_history_len()))
                self.ui.label_img.setText(self.ui.label_img.text+"  ")

            
        except:
            print("No segmentation")
            pass
    def FasterUpdateSegForonPress(self, segmentation_masks):
        import numpy as np
        inputNodeName = self.ui.inputNodeSelector0.currentNode().GetName()
        outputSegmentationNodeName = self.ui.outputSegmentationSelector.currentNode().GetName()
        #print("-----> new debug:", inputNode, outputSegmentationNode)
        #print("-----> new debug:",self.ui.inputNodeSelector0.text,self.ui.outputSegmentationSelector.text)
        volumeNode = slicer.util.getNode(inputNodeName)
        segmentationNode = slicer.util.getNode(outputSegmentationNodeName)

        combined_mask = np.zeros(segmentation_masks["airway"].shape, dtype=np.uint8)  # NOTE: 临时的
        combined_mask[segmentation_masks["airway"]] = 1  
        combined_mask[segmentation_masks["Artery"]] = 2  
        combined_mask[segmentation_masks["Vein"]] = 3    
        
        segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName('Airway structure')

        # Get segment as numpy array
        segmentArray = slicer.util.arrayFromSegmentBinaryLabelmap(segmentationNode, segmentId, volumeNode)

        slicer.util.updateSegmentBinaryLabelmapFromArray(np.transpose(combined_mask, (2, 1, 0)), segmentationNode, segmentId, volumeNode)

        self.ui.segmentationShow3DButton.setChecked(True)

    def someCustomAction(self,caller, eventId):
        import numpy as np
        markupsDisplayNode = caller
        print(type(markupsDisplayNode))
        print(f"Custom action activated in {markupsDisplayNode.GetNodeTagName()}")
        inputNodeName = self.ui.inputNodeSelector0.currentNode().GetName()
        volumeNode = slicer.util.getNode(inputNodeName)
        pointListNode = slicer.util.getNode("F")
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
        print(point_Ijk)

        try:
            import ast
            position_=self.ui.label_img.text.split("<b>")
            x,y,z=point_Ijk#ast.literal_eval(position_[0])
            #print(x,y,z,position_[1].split("</b>")[0]=="Out of Frame")
            #print("Press")
            if self.data_module==None and position_[1].split("</b>")[0]=="Out of Frame":
                self.ui.label_img.setText(self.ui.label_img.text+" Erro: data module no init!")
            else:
                #print(self.data_module.get_masks())
                optin_select=self.button_group2.checkedButton().text
                param = ast.literal_eval(self.ui.lineEdit_radius.text)
                #self.ui.label_img.setText(self.ui.label_img.text+ self.button_group.checkedButton().text+" "+self.button_group2.checkedButton().text+" "+str(param['radius']))
                if optin_select=="Sphere Addition":
                    self.data_module.sphere_addition(x, y, z, self.button_group.checkedButton().text, **param)
                elif optin_select=="Sphere Erasure":
                    self.data_module.sphere_erasure(x, y, z, self.button_group.checkedButton().text, **param)
                else:
                    return
                self.FasterUpdateSegForonPress(self.data_module.get_masks())
                #print(self.button_group.checkedButton().text)
                #self.data_module.
                self.ui.label_6.setText("modifiy queue len:"+str(self.data_module.get_history_len()))
                self.ui.label_img.setText(self.ui.label_img.text+" ")

            
        except:
            print("No segmentation")
            pass

        #slicer.mrmlScene.RemoveNode(markupsDisplayNode)


    def processEvent(self,observee,event):

        insideView = False
        ras = [0.0,0.0,0.0]
        xyz = [0.0,0.0,0.0]
        sliceNode = None
        if self.CrosshairNode:
            insideView = self.CrosshairNode.GetCursorPositionRAS(ras)
            sliceNode = self.CrosshairNode.GetCursorPositionXYZ(xyz)
        sliceLogic = None
        if sliceNode:
            appLogic = slicer.app.applicationLogic()
            if appLogic:
                sliceLogic = appLogic.GetSliceLogic(sliceNode)

        if not insideView or not sliceNode or not sliceLogic:
            return
        displayableManagerCollection = vtk.vtkCollection()
        if sliceNode:
            sliceWidget = slicer.app.layoutManager().sliceWidget(sliceNode.GetName())
            if sliceWidget:
                # sliceWidget is owned by the layout manager
                sliceView = sliceWidget.sliceView()
                sliceView.getDisplayableManagers(displayableManagerCollection)
        aggregatedDisplayableManagerInfo = ''
        myManagerInfo=""
        for index in range(displayableManagerCollection.GetNumberOfItems()):
            displayableManager = displayableManagerCollection.GetItemAsObject(index)
            infoString = displayableManager.GetDataProbeInfoStringForPosition(xyz)
            if infoString != "":
                aggregatedDisplayableManagerInfo += infoString + "<br>"
                myManagerInfo=infoString
        
        try:
            infoWidget = slicer.modules.DataProbeInstance.infoWidget
            #for layer in ("B", "F", "L", "S"):
                #print(infoWidget.layerNames[layer].text, infoWidget.layerIJKs[layer].text, infoWidget.layerValues[layer].text)
            
            self.ui.label_img.setText(infoWidget.layerIJKs["B"].text+" "+infoWidget.layerValues["B"].text)
            if aggregatedDisplayableManagerInfo != '':
                #print(myManagerInfo)
                self.ui.label_img.setText(self.ui.label_img.text+"<br>"+myManagerInfo.split('</font>')[-1])
            else:
                self.ui.label_img.setText(self.ui.label_img.text+"<br> ")
                # position_RAS = xyz
                # crosshairNode = slicer.util.getNode("Crosshair")
                # # Set crosshair position
                # crosshairNode.SetCrosshairRAS(position_RAS)
                # # Center the position in all slice views
                # slicer.vtkMRMLSliceNode.JumpAllSlices(slicer.mrmlScene, *position_RAS, slicer.vtkMRMLSliceNode.CenteredJumpSlice)
                # # Make the crosshair visible
                # crosshairNode.SetCrosshairMode(slicer.vtkMRMLCrosshairNode.ShowBasic)
            
            
            

            # self.ui.label_img.setText(self.generateViewDescription(xyz, ras, sliceNode, sliceLogic))
        except:
            pass
        # collect information from displayable managers
    
    def hide_all_widgets_in_layout(self,layout, HIDE=True):
        for i in range(layout.count()):
            item = layout.itemAt(i) 
            widget = item.widget()
            if widget is not None:
                if HIDE:
                    widget.hide()
                else:
                    widget.show()
            child_layout = item.layout()
            if child_layout is not None:
                self.hide_all_widgets_in_layout(child_layout)
        
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
        
    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def removeObservers(self):
        print("rm obse..")
        try:
            for observedNode, observation in self.observations:
                observedNode.RemoveObserver(observation)
        except:
            print("No have observation")

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

            self.ui.useStandardSegmentNamesCheckBox.checked = self._parameterNode.GetParameter("UseStandardSegmentNames") == "true"
            self.ui.outputSegmentationSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputSegmentation"))
            self.ui.segmentationShow3DButton.setChecked(True)
            # Center and fit displayed content in 3D view
            layoutManager = slicer.app.layoutManager()
            threeDWidget = layoutManager.threeDWidget(0)
            threeDView = threeDWidget.threeDView()
            threeDView.rotateToViewAxis(3)  # look from anterior direction
            threeDView.resetFocalPoint()  # reset the 3D view cube size and center it
            threeDView.resetCamera()  # reset camera zoom
            state = self._processingState
            if state == EvoSegWidget.PROCESSING_IDLE:
                inputErrorMessages = []  # it will contain text if the inputs are not valid
                if modelId:
                    modelInputs = self.logic.model(modelId)["inputs"]
                else:
                    modelInputs = []
                    inputErrorMessages.append("Select a model.")
                inputNodes = []  # list of output nodes so far, for checking for duplicates

                if inputErrorMessages:
                    print(inputErrorMessages)
                else:
                    print("Start segmentation")

            elif state == EvoSegWidget.PROCESSING_STARTING:
                print("Starting...") 
                print("Please wait while the segmentation is being initialized")
            elif state == EvoSegWidget.PROCESSING_IN_PROGRESS:
                print("Cancel") 
                print("Cancel in-progress segmentation")
            elif state == EvoSegWidget.PROCESSING_IMPORT_RESULTS:
                print("Importing results...") 
                print("Please wait while the segmentation result is being imported") 
            elif state == EvoSegWidget.PROCESSING_CANCEL_REQUESTED:
                print("Cancelling...") 
                print("Please wait for the segmentation to be cancelled")
                # self.ui.applyButton.enabled = False
            

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

            modelId = self._currentModelId()
            if modelId:
                # Only save model ID if valid, otherwise it is temporarily filtered out in the selector
                self._parameterNode.SetParameter("Model", modelId)
            #self._parameterNode.SetParameter("CPU", "true" if self.ui.cpuCheckBox.checked else "false")
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

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """

        if self._processingState == EvoSegWidget.PROCESSING_IDLE:
            self.onApply()
        else:
            self.onCancel()
        

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
                #print(self.ui.outputSegmentationSelector.currentNode(),"<<<<<")
                self.logic.useStandardSegmentNames = self.ui.useStandardSegmentNamesCheckBox.checked

                # Compute output
                inputNodes = []
                # for inputNodeSelector in self.inputNodeSelectors:
                #     print(inputNodeSelector,"<-")
                #     if inputNodeSelector.visible:
                #         inputNodes.append(inputNodeSelector.currentNode())

                # 改为以当前 red窗口显示的node为输入node
                BackgroundVolumeID_Red = slicer.app.layoutManager().sliceWidget("Red").sliceLogic().GetSliceCompositeNode().GetBackgroundVolumeID()
                ThisVolumeNode = slicer.mrmlScene.GetNodeByID(BackgroundVolumeID_Red)
                inputNodes.append(ThisVolumeNode)
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
        
        copy2dir= os.path.join(self.logic.modelsPath())
        print(self.logic.modelsPath())
        if not os.path.exists(copy2dir):
            os.makedirs(copy2dir)
            
        select_file = QFileDialog.getOpenFileNames(None, "快速选择文件", "", "File (*.nii.gz)")
        if len(select_file)>=1:
            slicer.util.loadVolume(select_file[0])

        # for inputIndex, inputNode in enumerate(inputNodes):
        #     #print(inputIndex, inputNode)
        #     if inputNode:
        #         self.inputNodeSelectors[inputIndex].setCurrentNode(inputNode)

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


        
    def onResultSeg(self,myDataModule):
        # 刷新DataModule 回调
        self.data_module=myDataModule
        print("init DataModule ok")
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

        self.dependenciesInstalled = True  # 默认所有依赖已经安装，不需要每次检查依赖以绕过代理导致的pip install问题

        self.moduleDir = os.path.dirname(slicer.util.getModule('EvoSeg').path)

        self.logCallback = None
        self.processingCompletedCallback = None
        self.startResultImportCallback = None
        self.endResultImportCallback = None
        self.useStandardSegmentNames = True
        self.setResultToLabelCallback = None

        self.mdf_outputSegmentation=None
        self.mdf_outputSegmentationFile=None
        self.mdf_model=None

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
        
        # Segmentation models specified by in models.json file
        self.models = self.loadModelsDescription()
        self.defaultModel = self.models[0]["id"]

        # Timer for checking the output of the segmentation process that is running in the background
        self.processOutputCheckTimerIntervalMsec = 1000

        # Disabling this flag preserves input and output data after execution is completed,
        # which can be useful for troubleshooting.
        self.clearOutputFolder = False #NOTE: 临时

        # For testing the logic without actually running inference, set self.debugSkipInferenceTempDir to the location
        # where inference result is stored and set self.debugSkipInference to True.
        self.debugSkipInference = False
        self.debugSkipInferenceTempDir = r"c:\Users\andra\AppData\Local\Temp\Slicer\__SlicerTemp__2024-01-16_15+26+25.624"

        self.data_module = []

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
                        inputs = []#[{"title": "Input volume"}] if self.ui_language=="en-US" else [{"title": "输入体积"}]
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

        labelDescriptions = { 
            1: {"name": "Airway", "terminology": 'Segmentation category and type - DICOM master list~SCT^123037004^Anatomical Structure~SCT^89187006^Airway structure~SCT^^~~^^~^^'},
            2: {"name": "Artery", "terminology": 'Segmentation category and type - DICOM master list~SCT^85756007^Tissue~SCT^51114001^Artery~SCT^^~~^^~^^'},
            3: {"name": "Vein", "terminology": 'Segmentation category and type - DICOM master list~SCT^85756007^Tissue~SCT^29092000^Vein~SCT^^~~^^~^^'}
        }
        # labelsFilePath = self.modelPath(modelName).joinpath("labels.csv")
        # print("in this version No should labels.csv",labelsFilePath) # NOTE: label is should define in futrue??
        
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

    def installPyTorchUtils(self):
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
    
    def installNnunetv2(self, upgrade=False):
        import importlib.metadata
        import importlib.util

        # Specify minimum version 1.3, as this is a known working version (it is possible that an earlier version works, too).
        # Without this, for some users EVO-0.9.0 got installed, which failed with this error:
        # "ImportError: cannot import name ‘MetaKeys’ from 'EVO.utils'"
        EVOInstallString = "nnunetv2[fire,scikit-image,flask,pyyaml,nibabel,pynrrd,psutil,tensorboard,skimage,itk,tqdm,batchgenerators]>=1.3"
        if upgrade:
            EVOInstallString += " --upgrade"
            EVOInstallString += " -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
        
        slicer.util.pip_install(EVOInstallString)

    def setupPythonRequirements(self, upgrade=False):
        # Install EVO with required components
        self.log("Setup Dependencies...")
        try:
          import torch
        except ModuleNotFoundError as e:
          self.log("Installing PyTorchUtils...")
          self.installPyTorchUtils()
        
        self.log("Check and install nnunetv2...")
        self.installNnunetv2(upgrade)
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
        self.log(f"command: {auto3DSegCommand}")

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

    def beforeReadResult(self, result_data,result_data_path):
        # 刷新DataModule
        from vtk.util import numpy_support
        import nrrd
        import numpy as np
        image_data = result_data.GetImageData()
        if image_data:
            vtk_array = numpy_support.vtk_to_numpy(image_data.GetPointData().GetScalars())
            dimensions = image_data.GetDimensions()
            numpy_array = vtk_array.reshape( dimensions[0], dimensions[1],dimensions[2])  # (Z, Y, X)
            print("NumPy shape:", numpy_array.shape, dimensions)
            ct_data = numpy_array
            ct_data = ct_data - ct_data.min() * 1.0
            ct_data = ct_data / ct_data.max()

            data, options = nrrd.read(result_data_path+"/output-segmentation.nrrd")
            #data_prob, options = nrrd.read(result_data_path+"/output-segmentation_prob.nrrd")
            #print("------------------------->>>>",options,"<<<<<<<<<<<--------------------")
            #print("------------------>",ct_data.shape,data.shape,data_prob.shape)
            #print("------------------>",ct_data.shape,data.shape,data_prob.shape)
            if data.ndim>3:
                print("4 dim array!!")
                segmentation_masks = {
                    "airway" : data[0, :, :, :] == 1, 
                    "Artery": data[2, :, :, :] == 1, 
                    "Vein": data[2, :, :, :] == 2
                }
            else:
                segmentation_masks = {
                    "airway" : data[:, :, :] == 1, 
                    "Artery": data[:, :, :] == 2, 
                    "Vein": data[:, :, :] == 3
                }
            #print(data_prob,"<<<")
            # probability_maps = {
            #     "airway": data_prob[segmentation_masks["airway"]].astype(np.float32),
            #     "artery": data_prob[segmentation_masks["Artery"]].astype(np.float32),
            #     "vein": data_prob[segmentation_masks["Vein"]].astype(np.float32),
            # }

            probability_maps = {
                "airway": segmentation_masks["airway"].astype(np.float32),
                "artery": segmentation_masks["Artery"].astype(np.float32),
                "vein": segmentation_masks["Vein"].astype(np.float32),
            }


            self.data_module = DataModule(ct_data, segmentation_masks, probability_maps)
            
            

        else:
            print("no image data!")

        




        self.setResultToLabelCallback(self.data_module)

    def set_new_data_module(self, new_data_module):
        import nrrd
        import numpy as np
        self.data_module=new_data_module
        data, options = nrrd.read(self.mdf_outputSegmentationFile)

        combined_mask = np.zeros(data.shape, dtype=np.uint8)  # 创建一个空的掩码
        
        segmentation_masks=new_data_module.get_masks()
        
        combined_mask[segmentation_masks["airway"]] = 1  # 标记 airway
        combined_mask[segmentation_masks["Artery"]] = 2   # 标记 artery
        combined_mask[segmentation_masks["Vein"]] = 3     # 标记 vein

        nrrd.write(self.mdf_outputSegmentationFile, combined_mask, options)

        self.readSegmentation(self.mdf_outputSegmentation, self.mdf_outputSegmentationFile, self.mdf_model)
        print("ok")

    def onSegmentationProcessCompleted(self, segmentationProcessInfo):
        import nrrd
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


                    print("------------------->Befor read")
                    self.beforeReadResult(inputNodes[0], tempDir) # NOTE:临时
                    # Load result
                    self.log("Importing segmentation results...")
                    #print(outputSegmentation,outputSegmentationFile,model)
                    
                    self.mdf_outputSegmentation=outputSegmentation
                    self.mdf_outputSegmentationFile=outputSegmentationFile
                    self.mdf_model=model
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
        maxLabelValue = max(labelValueToDescription.keys())
        # if min(labelValueToDescription.keys()) < 0:
        #     raise RuntimeError("Label values in class_map must be positive")
        # maxLabelValue = 3 #
        # Get color node with random colors
        randomColorsNode = slicer.mrmlScene.GetNodeByID("vtkMRMLColorTableNodeRandom")
        rgba = [0, 0, 0, 0]

        # Create color table for this segmentation model
        colorTableNode = slicer.vtkMRMLColorTableNode()
        colorTableNode.SetTypeToUser()
        colorTableNode.SetNumberOfColors(maxLabelValue+1)
        colorTableNode.SetName(model)
        for labelValue in labelValueToDescription:
            print(labelValue,labelValueToDescription[labelValue]["name"])
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

        # Set terminology and color
        for labelValue in labelValueToDescription:
            segmentName = labelValueToDescription[labelValue]["name"]
            terminologyEntryStr = labelValueToDescription[labelValue]["terminology"]
            segmentId = segmentName
            self.setTerminology(outputSegmentation, segmentName, segmentId, terminologyEntryStr)

    def setTerminology(self, segmentation, segmentName, segmentId, terminologyEntryStr):
        segment = segmentation.GetSegmentation().GetSegment(segmentId)
        print("------->",segmentId)
        if not segment:
            self.log(f"Segment with ID '{segmentId}' is not present in this segmentation.")
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