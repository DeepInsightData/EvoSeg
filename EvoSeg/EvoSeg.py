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
from qt import QEvent, QObject, QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QFileDialog, QImage, QPixmap, QCheckBox, QButtonGroup,QMessageBox
import subprocess
from Scripts.data import DataModule

#
# EvoSeg
#

class EvoSeg(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("EvoSeg")
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Segmentation")]
        self.parent.dependencies = []  
        self.parent.contributors = ["DeepInsightData"] 
        # TODO: set help text
        self.parent.helpText = _(" ")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _(" ")
        self.terminologyName = None

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", self.EvoSegHello)

    def EvoSegHello(self):
        #print("EvoSeg Init.")
        pass


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
        
        import qt

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

        self.ui.advancedCollapsibleButton.connect("contentsCollapsed(bool)", self.check_set_modifiy)

        #self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.ui.segmentationShow3DButton.setSegmentationNode)
        #self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.logic.)
        #self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.ui.segmentationEditor_.setSegmentationNode)

        # Buttons
        self.ui.copyModelsButton.connect("clicked(bool)", self.onCopyModel)
        
        self.ui.browseToModelsFolderButton.connect("clicked(bool)", self.onBrowseModelsFolder)
        self.ui.deleteAllModelsButton.connect("clicked(bool)", self.onClearModelsFolder)

        self.ui.bt_export.connect("clicked(bool)", self.onExportClick)

        self.ui.bt_seg_all_run.connect("clicked(bool)", self.onCancel)

        # check box
        self.ui.radio_airway_tag.setChecked(True)
        self.ui.radioButton12.setChecked(True)

        # new button click
        self.ui.button_undo.connect("clicked(bool)", self.onButtonUndoClick)

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.ui.radio_airway_tag)
        self.button_group.addButton(self.ui.radio_artery_tag)
        self.button_group.addButton(self.ui.radio_vein_tag)
        self.button_group.buttonToggled.connect(self.onButtonGroupClick)

        self.button_group2 = QButtonGroup()
        self.button_group2.addButton(self.ui.radioButton12) 
        self.button_group2.addButton(self.ui.radioButton22)
        self.button_group2.addButton(self.ui.radioButton32)
        self.button_group2.addButton(self.ui.radioButton42)

        self.CrosshairNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLCrosshairNode')
        
        if self.CrosshairNode:
            self.CrosshairNodeObserverTag = self.CrosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.processEvent)
        
        extensionsPath = slicer.app.extensionsInstallPath
        #print("Extensions Install Path:", extensionsPath)
        layoutManager = slicer.app.layoutManager()
        fourByFourWidget = layoutManager.threeDWidget(0).threeDView()

        # 显示小部件
        fourByFourWidget.show()

        # 新增UI简化更新 update v1
        # 隐藏控件将在之后更新中彻底去除
        self.hide_all_widgets_in_layout(self.ui.gridLayout)
        
        self.ui.bt_seg_airway.setIcon(qt.QIcon(self.resourcePath("Icons/aireway_segmentation.png")))
        self.ui.bt_seg_artery.setIcon(qt.QIcon(self.resourcePath("Icons/artery_segmentation.png")))
        self.ui.bt_seg_airway.clicked.connect(lambda: self.onSegButtonClick('airway'))
        self.ui.bt_seg_artery.clicked.connect(lambda: self.onSegButtonClick('artery'))



    def onButtonGroupClick(self,value_for_group):
        if value_for_group.text=="airway":
            model_name_must_is = "Airway_nnUnet"
        elif value_for_group.text=="artery":
            model_name_must_is = "Artery_nnUnet"
        output_segmentation_node=slicer.mrmlScene.GetFirstNodeByName(model_name_must_is+"_Output_Mask")
        self.ui.outputSegmentationSelector.setCurrentNode(output_segmentation_node)
        for i in self.data_module_list:
            if i["model_name"]==model_name_must_is:
                self.data_module=i["seg_data"]
                #print("set DataModule for:"+model_name_must_is)
                return

    def onExportClick(self):
        dataModuleWidget = slicer.modules.data.widgetRepresentation()
        subjectHierarchyTreeView = dataModuleWidget.findChild(slicer.qMRMLSubjectHierarchyTreeView)

        export_node = [slicer.mrmlScene.GetFirstNodeByName("Airway_nnUnet_Output_Mask"),
                       slicer.mrmlScene.GetFirstNodeByName("Artery_nnUnet_Output_Mask")]
        for node in export_node:
            if node and node.GetSegmentation().GetNumberOfSegments()!=0:
                NodeShItem = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene).GetItemByDataNode(node)
                subjectHierarchyTreeView.setCurrentItem(NodeShItem)
                plugin=slicer.qSlicerSubjectHierarchyPluginHandler.instance().pluginByName('Export')
                openExportDICOMDialogAction=plugin.children()[0]
                openExportDICOMDialogAction.trigger()

    def onSegButtonClick(self,button_name):
        # update v2 目前剩3d按钮和一个输出部分保留原来的
        run_model_name=""
        if "airway"==button_name:
            run_model_name="Airway_nnUnet"
            self.ui.bt_seg_airway.setEnabled(False)
            #self.ui.bt_seg_artery.setEnabled(False)# 并行时删除
            self.ui.bt_seg_all_run.setEnabled(True)
        elif "artery"==button_name:
            run_model_name="Artery_nnUnet"
            self.ui.bt_seg_artery.setEnabled(False)
            #self.ui.bt_seg_airway.setEnabled(False)
            self.ui.bt_seg_all_run.setEnabled(True)
        else:
            slicer.util.messageBox("the model name '"+button_name+"' is Not Update!")
            return
        
        if self._processingState == EvoSegWidget.PROCESSING_IDLE:
            self.onApply(run_model_name)
        else:
            self.onCancel()

    def check_set_modifiy(self,check_it):

        if len(self.data_module_list)==0 and check_it==False:
            self.ui.advancedCollapsibleButton.checked=False
            slicer.util.messageBox("No result output")
            return

        originMarkupsDisplayNodes = slicer.util.getNodesByClass("vtkMRMLMarkupsDisplayNode")

        if not check_it:
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
            self.markup_node.AddControlPoint(0,0,0)
            DisplayNode=self.markup_node.GetDisplayNode()
            print("1",type(DisplayNode),DisplayNode.GetNodeTagName())
            DisplayNode.SetSelectedColor(1,1,1)

            try:
                for observedNode, observation in self.observations:
                    observedNode.RemoveObserver(observation)
            except:
                pass
            
            self.observations=[[DisplayNode, DisplayNode.AddObserver(DisplayNode.CustomActionEvent1, self.someCustomAction)]]
            
            self.markup_node.SetNthControlPointLabel(0, "")
            for view in views:
                markupsDisplayableManager = view.displayableManagerByClassName('vtkMRMLMarkupsDisplayableManager')
                widget = markupsDisplayableManager.GetWidget(DisplayNode)
                widget.SetEventTranslation(widget.WidgetStateOnWidget, slicer.vtkMRMLInteractionEventData.RightButtonClickEvent, vtk.vtkEvent.NoModifier, vtk.vtkWidgetEvent.NoEvent)
                widget.SetEventTranslation(widget.WidgetStateOnWidget, slicer.vtkMRMLInteractionEventData.RightButtonClickEvent, vtk.vtkEvent.NoModifier, widget.WidgetEventCustomAction1)
                
        else:
            self.markup_node.RemoveAllControlPoints()
            if self.markup_node:
                slicer.mrmlScene.RemoveNode(self.markup_node)
            
            for node in originMarkupsDisplayNodes:
                node.SetVisibility(True)
            

    def onButtonUndoClick(self):
        self.data_module.undo()
        self.ui.label_6.setText("Target Modifiy Queue Len:"+str(self.data_module.get_history_len()))
        self.FasterUpdateSegForonPress(self.data_module.get_masks())

    def FasterUpdateSegForonPress(self, segmentation_masks):
        # 新增 模型与其生成的数据 的配对
        import numpy as np
        if self.ui.radio_airway_tag.isChecked():
            segmentationNode=slicer.mrmlScene.GetFirstNodeByName("Airway_nnUnet_Output_Mask")
            combined_mask = np.zeros(segmentation_masks["airway"].shape, dtype=np.uint8)  
        elif self.ui.radio_artery_tag.isChecked():
            segmentationNode=slicer.mrmlScene.GetFirstNodeByName("Artery_nnUnet_Output_Mask")
            combined_mask = np.zeros(segmentation_masks["artery"].shape, dtype=np.uint8) 
        BackgroundVolumeID_Red = slicer.app.layoutManager().sliceWidget("Red").sliceLogic().GetSliceCompositeNode().GetBackgroundVolumeID()
        volumeNode = slicer.mrmlScene.GetNodeByID(BackgroundVolumeID_Red)

        combined_mask[segmentation_masks["airway"]] = 1  
        combined_mask[segmentation_masks["artery"]] = 2  
        combined_mask[segmentation_masks["vein"]] = 3    
        
        if self.ui.radio_airway_tag.isChecked():
            segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName('Airway structure')
        elif self.ui.radio_artery_tag.isChecked():
            segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName('Artery')
        
        # Get segment as numpy array
        segmentArray = slicer.util.arrayFromSegmentBinaryLabelmap(segmentationNode, segmentId, volumeNode)

        slicer.util.updateSegmentBinaryLabelmapFromArray(np.transpose(combined_mask, (2, 1, 0)), segmentationNode, segmentId, volumeNode)

        segmentationNode.CreateClosedSurfaceRepresentation()


    def someCustomAction(self,caller, eventId):
        import numpy as np
        markupsDisplayNode = caller
        #print(type(markupsDisplayNode))
        print(f"Custom action activated in {markupsDisplayNode.GetNodeTagName()}")
        
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

        #try:
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
            param = ast.literal_eval("{'radius':"+str(int(self.ui.radius_slider.value))+",}")
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
            self.ui.label_6.setText("Target Modifiy Queue Len:"+str(self.data_module.get_history_len()))
            self.ui.label_img.setText(self.ui.label_img.text+" ")

            
        # except:
        #     print("No segmentation")
        #     pass

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
        #print("ok?")
        
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
                try:
                    BackgroundVolumeID_Red = slicer.app.layoutManager().sliceWidget("Red").sliceLogic().GetSliceCompositeNode().GetBackgroundVolumeID()
                    ThisVolumeNode = slicer.mrmlScene.GetNodeByID(BackgroundVolumeID_Red)
                except:
                    slicer.util.messageBox("Pelease import and show date in 3Dslicer")
                    self.ui.bt_seg_airway.setEnabled(True)
                    self.ui.bt_seg_artery.setEnabled(True)
                    return
                inputNodes.append(ThisVolumeNode)

                # 配置输出
                output_segmentation_name=model_name+"_Output_Mask"
                self.ui.outputSegmentationSelector.baseName = output_segmentation_name

                print(self.ui.outputSegmentationSelector.nodeTypes)
                #print("---->",dir(self.ui.outputSegmentationSelector))

                output_segmentation_node = slicer.mrmlScene.GetFirstNodeByName(output_segmentation_name)
                if output_segmentation_node:
                    self.ui.outputSegmentationSelector.setCurrentNode(output_segmentation_node)
                else:
                    self.ui.outputSegmentationSelector.addNode()
                
                # 调用self.logic.process

                for i in self._segmentationProcessInfoList:
                    if i["name"]==model_name:
                        slicer.util.messageBox("This model is running.")
                        return
                
                self._segmentationProcessInfo = self.logic.process(inputNodes, 
                                                                self.ui.outputSegmentationSelector.currentNode(),
                                                                model_name, 
                                                                False, 
                                                                False, 
                                                                waitForCompletion=False
                                                                )
                
                self._segmentationProcessInfoList.append({
                                                          "name":model_name,
                                                          "process":self._segmentationProcessInfo
                                                         })

                #print("---->",len(self._segmentationProcessInfoList))
                #print("---->",self._segmentationProcessInfoList)
                print(EvoSegWidget.PROCESSING_IN_PROGRESS,"PROCESSING_IN_PROGRESS")

        except Exception as e:
            print(EvoSegWidget.PROCESSING_IDLE,"PROCESSING_IDLE")
            self.ui.bt_seg_airway.setEnabled(True)
            self.ui.bt_seg_artery.setEnabled(True)
            self.ui.bt_seg_all_run.setEnabled(False)

    def onCancel(self):
        with slicer.util.tryWithErrorDisplay("Failed to cancel processing.", waitCursor=True):
            if len(self._segmentationProcessInfoList)==0:
                slicer.util.messageBox("No Process Run")
                return
            #print(len(self._segmentationProcessInfoList),"----<<")
            for i in self._segmentationProcessInfoList:
                self.logic.cancelProcessing(i["process"])
                self._segmentationProcessInfoList.remove(i)
                if i["name"]=="Airway_nnUnet":
                    self.ui.bt_seg_airway.setEnabled(True)
                if i["name"]=="Artery_nnUnet":
                    self.ui.bt_seg_artery.setEnabled(True)
           
            print(EvoSegWidget.PROCESSING_CANCEL_REQUESTED,"PROCESSING_CANCEL_REQUESTED")

    def onProcessImportStarted(self, customData):
        print(EvoSegWidget.PROCESSING_IMPORT_RESULTS,"PROCESSING_IMPORT_RESULTS")
        import qt
        qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
        slicer.app.processEvents()

    def onProcessImportEnded(self, customData):
        import qt
        qt.QApplication.restoreOverrideCursor()
        slicer.app.processEvents()

    def onProcessingCompleted(self, returnCode, customData):
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

        # 每次执行后随机为所有SegmentationNode中的所有标签重置颜色
        # https://slicer.readthedocs.io/en/latest/developer_guide/script_repository.html#modify-segmentation-display-options
        for name in end_model_name_list:
            
            # 同时把按钮setenbled true
            if name=="Airway_nnUnet":
                self.ui.bt_seg_airway.setEnabled(True)
                self.ui.radio_airway_tag.setChecked(True)
            if name=="Artery_nnUnet":
                self.ui.bt_seg_artery.setEnabled(True)
                self.ui.radio_artery_tag.setChecked(True)
            node = slicer.mrmlScene.GetFirstNodeByName(name+"_Output_Mask")
            node.CreateClosedSurfaceRepresentation()
            segmentation = node.GetSegmentation()
            display_node = node.GetDisplayNode()
            if display_node==None:
                continue
            display_node.SetOpacity3D(0.8)
            for i in range(segmentation.GetNumberOfSegments()):
                segment = segmentation.GetNthSegment(i)
                
                import random
                segment.SetColor(random.random(), random.random(), random.random())
            
            self.ui.statusLabel.appendPlainText("\n"+name+": Processing finished.")
            #segment_id = segment.GetName()
            # display_node.SetSegmentOpacity3D(segment_id, 0.2)
            # display_node.SetSegmentOverrideColor(segment_id, 0, 0, 1)
        
        
        #self.ui.bt_seg_all_run.setEnabled(False)
        #----------------------------------------------------------------------
        self._segmentationProcessInfo = None
        
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

    def onResultSeg(self,myDataModule, model_name):
        # 刷新DataModule 回调
        #print("-------->",model_name,self.data_module_list)
        self.data_module=myDataModule
        for i in self.data_module_list:
            if i["model_name"]==model_name:
                i["seg_data"]=self.data_module
                #print("reinit DataModule ok")
                return
        self.data_module_list.append({"model_name":model_name,"seg_data":self.data_module})
        #print("init DataModule ok")
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
        self.useStandardSegmentNames = True
        self.setResultToLabelCallback = None

        self.mdf_outputSegmentation=None
        self.mdf_outputSegmentationFile=None
        self.mdf_model=None
        
        self.models = ["Airway_nnUnet","Artery_nnUnet"]

        # Timer for checking the output of the segmentation process that is running in the background
        self.processOutputCheckTimerIntervalMsec = 1000

        # Disabling this flag preserves input and output data after execution is completed,
        # which can be useful for troubleshooting.
        self.clearOutputFolder = True #NOTE: Debug的时候用

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
        for path in pathlib.Path(modelRoot).rglob("dataset.json"):
            return path.parent
        raise RuntimeError(f"Model {modelName} path not found, You can try:\n click 'open model cache folder' button -> Create a folder name of model name -> Extract your model json and fold_x to this folder.\nYour model folder should be:\n{modelName} \n  |-fold_1\n  |-dataset.json\n  |-...\n  ...\n")

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
        if not withDownload:
            return

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

        if not inputNodes:
            raise ValueError("Input nodes are invalid")

        if not outputSegmentation:
            raise ValueError("Output segmentation is invalid")

        try:
            modelPath = self.modelPath(model)
        except:
            self.downloadModel(model,withDownload)
            modelPath = self.modelPath(model)
        #print("modelPath",modelPath)
        segmentationProcessInfo = {}

        import time
        startTime = time.time()
        self.log(model+": Processing started")

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
        #print(pythonSlicerExecutablePath)
        if not pythonSlicerExecutablePath:
            raise RuntimeError("Python was not found")

        # Write input volume to file
        inputFiles = []
        for inputIndex, inputNode in enumerate(inputNodes):
            if inputNode.IsA('vtkMRMLScalarVolumeNode'):
                inputImageFile = tempDir + f"/input-volume{inputIndex}.nrrd"
                self.log(model+f": Writing input file to {inputImageFile}")
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

        self.log(model+": Creating segmentations with EvoSeg AI...")
        self.log(model+f": command: {auto3DSegCommand}")

        additionalEnvironmentVariables = None
        if cpu:
            additionalEnvironmentVariables = {"CUDA_VISIBLE_DEVICES": "-1"}
            self.log(model+f": Additional environment variables: {additionalEnvironmentVariables}")

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

    def beforeReadResult(self, result_data,result_data_path,model_name):
        # 刷新DataModule
        from vtk.util import numpy_support
        import nrrd
        import numpy as np
        image_data = result_data.GetImageData()
        if image_data:
            vtk_array = numpy_support.vtk_to_numpy(image_data.GetPointData().GetScalars())
            dimensions = image_data.GetDimensions()
            numpy_array = vtk_array.reshape( dimensions[0], dimensions[1],dimensions[2])  # (Z, Y, X)
            #print("NumPy shape:", numpy_array.shape, dimensions)
            ct_data = numpy_array
            ct_data = ct_data - ct_data.min() * 1.0
            ct_data = ct_data / ct_data.max()

            data, options = nrrd.read(result_data_path+"/output-segmentation.nrrd")
            if data.ndim>3:
                print("4 dim array!!")
                segmentation_masks = {
                    "airway" : data[0, :, :, :] == 1, 
                    "artery": data[2, :, :, :] == 1, 
                    "vein": data[2, :, :, :] == 2
                }
            else:
                segmentation_masks = {
                    "airway" : data[:, :, :] == 1, 
                    "artery": data[:, :, :] == 2, 
                    "vein": data[:, :, :] == 3
                }

            probability_maps = {
                "airway": segmentation_masks["airway"].astype(np.float32),
                "artery": segmentation_masks["artery"].astype(np.float32),
                "vein": segmentation_masks["vein"].astype(np.float32),
            }


            self.data_module = DataModule(ct_data, segmentation_masks, probability_maps)
            
        else:
            print("no image data!")

        self.setResultToLabelCallback(self.data_module,model_name)
        
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
            self.log(model+f": Processing was cancelled.")
        else:
            if procReturnCode == 0:
                if self.startResultImportCallback:
                    self.startResultImportCallback(customData)
                try:
                    #print("------------------->Befor read")
                    self.beforeReadResult(inputNodes[0], tempDir,model) # NOTE:临时
                    # Load result
                    self.log(model+": Importing segmentation results...")
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
            self.processingCompletedCallback(procReturnCode, customData)


    def readSegmentation(self, outputSegmentation, outputSegmentationFile, model):

        labelValueToDescription = self.labelDescriptions(model)
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

        # Set terminology and color
        for labelValue in labelValueToDescription:
            segmentName = labelValueToDescription[labelValue]["name"]
            terminologyEntryStr = labelValueToDescription[labelValue]["terminology"]
            segmentId = segmentName
            self.setTerminology(outputSegmentation, segmentName, segmentId, terminologyEntryStr)

    def setTerminology(self, segmentation, segmentName, segmentId, terminologyEntryStr):
        segment = segmentation.GetSegmentation().GetSegment(segmentId)
        #print("------->",segmentId)
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