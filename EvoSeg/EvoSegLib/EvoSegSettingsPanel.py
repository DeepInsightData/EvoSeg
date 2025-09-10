import qt
import ctk
import slicer
from slicer.i18n import tr as _
from .EvoSegModels import EvoSegModels
    
class _ui_EvoSegSettingsPanel:
    def __init__(self, parent):
        vBoxLayout = qt.QVBoxLayout(parent)
        
        airwayColorGroupBox = qt.QGroupBox(_('Airway'))
        airwayColorGroupBoxFormLayout = qt.QFormLayout(airwayColorGroupBox)
        self.airwayColorPickerButton = ctk.ctkColorPickerButton()
        self.airwayColorPickerButton.objectName = 'AirwayColorPickerButton'
        self.airwayColorPickerButton.color = EvoSegModels.get('Airway').color()
        self.airwayColorPickerButton.dialogOptions=qt.QColorDialog.DontUseNativeDialog
        self.airwayColorPickerButton.setMinimumSize(0, 0)
        self.airwayColorPickerButton.setMaximumSize(16777215, 16777215)
        airwayColorGroupBoxFormLayout.addRow(_("Color"),self.airwayColorPickerButton)
        self.airwaySplitByMidPlaneCheckBox = qt.QCheckBox()
        self.airwaySplitByMidPlaneCheckBox.setChecked(EvoSegModels.get('Airway').isSplitByMidPlane())
        airwayColorGroupBoxFormLayout.addRow(_("Split By Middle Plane"), self.airwaySplitByMidPlaneCheckBox)
        vBoxLayout.addWidget(airwayColorGroupBox)
        parent.registerProperty('EvoSeg/AirwayColor', self.airwayColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Airway Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/AirwaySplitByMidPlane', self.airwaySplitByMidPlaneCheckBox,
            "checked", str(qt.SIGNAL("toggled(bool)")),
            _("Split By Middle Plane"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
        ateryColorGroupBox = qt.QGroupBox(_('Artery'))
        arteryColorGroupBoxFormLayout = qt.QFormLayout(ateryColorGroupBox)
        self.arteryColorPickerButton = ctk.ctkColorPickerButton()
        self.arteryColorPickerButton.objectName = 'ArteryColorPickerButton'
        self.arteryColorPickerButton.color=EvoSegModels.get('Artery').color()
        self.arteryColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.arteryColorPickerButton.setMinimumSize(0, 0)
        self.arteryColorPickerButton.setMaximumSize(16777215, 16777215)
        arteryColorGroupBoxFormLayout.addRow(_("Color"), self.arteryColorPickerButton)
        self.arterySplitByMidPlaneCheckBox = qt.QCheckBox()
        self.arterySplitByMidPlaneCheckBox.setChecked(EvoSegModels.get('Artery').isSplitByMidPlane())
        arteryColorGroupBoxFormLayout.addRow(_("Split By Middle Plane"), self.arterySplitByMidPlaneCheckBox)
        vBoxLayout.addWidget(ateryColorGroupBox)
        parent.registerProperty('EvoSeg/ArteryColor', self.arteryColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Artery Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/ArterySplitByMidPlane', self.arterySplitByMidPlaneCheckBox,
            "checked", str(qt.SIGNAL("toggled(bool)")),
            _("Split By Middle Plane"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
        veinColorGroupBox = qt.QGroupBox(_('Vein'))
        veinColorGroupBoxFormLayout = qt.QFormLayout(veinColorGroupBox)
        self.veinColorPickerButton = ctk.ctkColorPickerButton()
        self.veinColorPickerButton.objectName = 'VeinColorPickerButton'
        self.veinColorPickerButton.color=EvoSegModels.get('Vein').color()
        self.veinColorPickerButton.dialogOptions=qt.QColorDialog.DontUseNativeDialog
        self.veinColorPickerButton.setMinimumSize(0, 0)
        self.veinColorPickerButton.setMaximumSize(16777215, 16777215)
        veinColorGroupBoxFormLayout.addRow(_("Color"), self.veinColorPickerButton)
        self.veinSplitByMidPlaneCheckBox = qt.QCheckBox()
        self.veinSplitByMidPlaneCheckBox.setChecked(EvoSegModels.get('Vein').isSplitByMidPlane())
        veinColorGroupBoxFormLayout.addRow(_("Split By Middle Plane"), self.veinSplitByMidPlaneCheckBox)
        vBoxLayout.addWidget(veinColorGroupBox)
        parent.registerProperty('EvoSeg/VeinColor', self.veinColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Vein Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/VeinSplitByMidPlane', self.veinSplitByMidPlaneCheckBox,
            "checked", str(qt.SIGNAL("toggled(bool)")),
            _("Split By Middle Plane"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
        lungLobeModel = EvoSegModels.get('LungLobe')
        lobeColorGroupBox = qt.QGroupBox(_('Lung Segments'))
        lobeColorGroupBoxGridLayout = qt.QGridLayout(lobeColorGroupBox)
        self.apicalRB1ColorPickerButton = ctk.ctkColorPickerButton()
        self.apicalRB1ColorPickerButton.objectName = 'apicalRB1ColorPickerButton'
        self.apicalRB1ColorPickerButton.color = lungLobeModel.apicalRB1Color()
        self.apicalRB1ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.apicalRB1ColorPickerButton.setMinimumSize(0, 0)
        self.apicalRB1ColorPickerButton.setMaximumSize(16777215, 16777215)
        apicalRB1Label = qt.QLabel(_("Apical RB1"))
        lobeColorGroupBoxGridLayout.addWidget(apicalRB1Label, 0, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.apicalRB1ColorPickerButton, 0, 1)
        
        self.posteriorRB2ColorPickerButton = ctk.ctkColorPickerButton()
        self.posteriorRB2ColorPickerButton.objectName = 'posteriorRB2ColorPickerButton'
        self.posteriorRB2ColorPickerButton.color = lungLobeModel.posteriorRB2Color()
        self.posteriorRB2ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.posteriorRB2ColorPickerButton.setMinimumSize(0, 0)
        self.posteriorRB2ColorPickerButton.setMaximumSize(16777215, 16777215)
        posteriorRB2Label = qt.QLabel(_("Posterior RB2"))
        lobeColorGroupBoxGridLayout.addWidget(posteriorRB2Label, 0, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.posteriorRB2ColorPickerButton, 0, 3)
        self.anteriorRB3ColorPickerButton = ctk.ctkColorPickerButton()
        self.anteriorRB3ColorPickerButton.objectName = 'anteriorRB3ColorPickerButton'
        self.anteriorRB3ColorPickerButton.color = lungLobeModel.anteriorRB3Color()
        self.anteriorRB3ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.anteriorRB3ColorPickerButton.setMinimumSize(0, 0)
        self.anteriorRB3ColorPickerButton.setMaximumSize(16777215, 16777215)
        anteriorRB3Label = qt.QLabel(_("Anterior RB3"))
        lobeColorGroupBoxGridLayout.addWidget(anteriorRB3Label, 1, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.anteriorRB3ColorPickerButton, 1, 1)
        
        self.lateralRB4ColorPickerButton = ctk.ctkColorPickerButton()
        self.lateralRB4ColorPickerButton.objectName = 'lateralRB4ColorPickerButton'
        self.lateralRB4ColorPickerButton.color = lungLobeModel.lateralRB4Color()
        self.lateralRB4ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.lateralRB4ColorPickerButton.setMinimumSize(0, 0)
        self.lateralRB4ColorPickerButton.setMaximumSize(16777215, 16777215)
        lateralRB4Label = qt.QLabel(_("Lateral RB4"))
        lobeColorGroupBoxGridLayout.addWidget(lateralRB4Label, 1, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.lateralRB4ColorPickerButton, 1, 3)
        self.medialRB5ColorPickerButton = ctk.ctkColorPickerButton()
        self.medialRB5ColorPickerButton.objectName = 'medialRB5ColorPickerButton'
        self.medialRB5ColorPickerButton.color = lungLobeModel.medialRB5Color()
        self.medialRB5ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.medialRB5ColorPickerButton.setMinimumSize(0, 0)
        self.medialRB5ColorPickerButton.setMaximumSize(16777215, 16777215)
        medialRB5Label = qt.QLabel(_("Medial RB5"))
        lobeColorGroupBoxGridLayout.addWidget(medialRB5Label, 2, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.medialRB5ColorPickerButton, 2, 1)
        
        self.superiorRB6ColorPickerButton = ctk.ctkColorPickerButton()
        self.superiorRB6ColorPickerButton.objectName = 'superiorRB6ColorPickerButton'
        self.superiorRB6ColorPickerButton.color = lungLobeModel.superiorRB6Color()
        self.superiorRB6ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.superiorRB6ColorPickerButton.setMinimumSize(0, 0)
        self.superiorRB6ColorPickerButton.setMaximumSize(16777215, 16777215)
        superiorRB6Label = qt.QLabel(_("Superior RB6"))
        lobeColorGroupBoxGridLayout.addWidget(superiorRB6Label, 2, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.superiorRB6ColorPickerButton, 2, 3)
        
        self.medialBasalRB7ColorPickerButton = ctk.ctkColorPickerButton()
        self.medialBasalRB7ColorPickerButton.objectName = 'medialBasalRB7ColorPickerButton'
        self.medialBasalRB7ColorPickerButton.color = lungLobeModel.medialBasalRB7Color()
        self.medialBasalRB7ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.medialBasalRB7ColorPickerButton.setMinimumSize(0, 0)
        self.medialBasalRB7ColorPickerButton.setMaximumSize(16777215, 16777215)
        medialBasalRB7Label = qt.QLabel(_("Medial Basal RB7"))
        lobeColorGroupBoxGridLayout.addWidget(medialBasalRB7Label, 3, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.medialBasalRB7ColorPickerButton, 3, 1)
        
        self.anteriorBasalRB8ColorPickerButton = ctk.ctkColorPickerButton()
        self.anteriorBasalRB8ColorPickerButton.objectName = 'anteriorBasalRB8ColorPickerButton'
        self.anteriorBasalRB8ColorPickerButton.color = lungLobeModel.anteriorBasalRB8Color()
        self.anteriorBasalRB8ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.anteriorBasalRB8ColorPickerButton.setMinimumSize(0, 0)
        self.anteriorBasalRB8ColorPickerButton.setMaximumSize(16777215, 16777215)
        anteriorBasalRB8Label = qt.QLabel(_("Anterior Basal RB8"))
        lobeColorGroupBoxGridLayout.addWidget(anteriorBasalRB8Label, 3, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.anteriorBasalRB8ColorPickerButton, 3, 3)
        self.lateralBasalRB9ColorPickerButton = ctk.ctkColorPickerButton()
        self.lateralBasalRB9ColorPickerButton.objectName = 'lateralBasalRB9ColorPickerButton'
        self.lateralBasalRB9ColorPickerButton.color = lungLobeModel.lateralBasalRB9Color()
        self.lateralBasalRB9ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.lateralBasalRB9ColorPickerButton.setMinimumSize(0, 0)
        self.lateralBasalRB9ColorPickerButton.setMaximumSize(16777215, 16777215)
        lateralBasalRB9Label = qt.QLabel(_("Lateral Basal RB9"))
        lobeColorGroupBoxGridLayout.addWidget(lateralBasalRB9Label, 4, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.lateralBasalRB9ColorPickerButton, 4, 1)
        
        self.posteriorBasalRB10ColorPickerButton = ctk.ctkColorPickerButton()
        self.posteriorBasalRB10ColorPickerButton.objectName = 'posteriorBasalRB10ColorPickerButton'
        self.posteriorBasalRB10ColorPickerButton.color = lungLobeModel.posteriorBasalRB10Color()
        self.posteriorBasalRB10ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.posteriorBasalRB10ColorPickerButton.setMinimumSize(0, 0)
        self.posteriorBasalRB10ColorPickerButton.setMaximumSize(16777215, 16777215)
        posteriorBasalRB10Label = qt.QLabel(_("Posterior Basal RB10"))
        lobeColorGroupBoxGridLayout.addWidget(posteriorBasalRB10Label, 4, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.posteriorBasalRB10ColorPickerButton, 4, 3)
        self.apicoposteriorLB1_2ColorPickerButton = ctk.ctkColorPickerButton()
        self.apicoposteriorLB1_2ColorPickerButton.objectName = 'apicoposteriorLB1_2ColorPickerButton'
        self.apicoposteriorLB1_2ColorPickerButton.color = lungLobeModel.apicoposteriorLB1_2Color()
        self.apicoposteriorLB1_2ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.apicoposteriorLB1_2ColorPickerButton.setMinimumSize(0, 0)
        self.apicoposteriorLB1_2ColorPickerButton.setMaximumSize(16777215, 16777215)
        apicoposteriorLB1_2Label = qt.QLabel(_("Apicoposterior LB1/2"))
        lobeColorGroupBoxGridLayout.addWidget(apicoposteriorLB1_2Label, 5, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.apicoposteriorLB1_2ColorPickerButton, 5, 1)
        
        self.anteriorLB3ColorPickerButton = ctk.ctkColorPickerButton()
        self.anteriorLB3ColorPickerButton.objectName = 'anteriorLB3ColorPickerButton'
        self.anteriorLB3ColorPickerButton.color = lungLobeModel.anteriorLB3Color()
        self.anteriorLB3ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.anteriorLB3ColorPickerButton.setMinimumSize(0, 0)
        self.anteriorLB3ColorPickerButton.setMaximumSize(16777215, 16777215)
        anteriorLB3Label = qt.QLabel(_("Anterior LB3"))
        lobeColorGroupBoxGridLayout.addWidget(anteriorLB3Label, 5, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.anteriorLB3ColorPickerButton, 5, 3)
        self.superiorLingularLB4ColorPickerButton = ctk.ctkColorPickerButton()
        self.superiorLingularLB4ColorPickerButton.objectName = 'superiorLingularLB4ColorPickerButton'
        self.superiorLingularLB4ColorPickerButton.color = lungLobeModel.superiorLingularLB4Color()
        self.superiorLingularLB4ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.superiorLingularLB4ColorPickerButton.setMinimumSize(0, 0)
        self.superiorLingularLB4ColorPickerButton.setMaximumSize(16777215, 16777215)
        superiorLingularLB4Label = qt.QLabel(_("Superior Lingular LB4"))
        lobeColorGroupBoxGridLayout.addWidget(superiorLingularLB4Label, 6, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.superiorLingularLB4ColorPickerButton, 6, 1)
        
        self.inferiorLingularLB5ColorPickerButton = ctk.ctkColorPickerButton()
        self.inferiorLingularLB5ColorPickerButton.objectName = 'inferiorLingularLB5ColorPickerButton'
        self.inferiorLingularLB5ColorPickerButton.color = lungLobeModel.inferiorLingularLB5Color()
        self.inferiorLingularLB5ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.inferiorLingularLB5ColorPickerButton.setMinimumSize(0, 0)
        self.inferiorLingularLB5ColorPickerButton.setMaximumSize(16777215, 16777215)
        inferiorLingularLB5Label = qt.QLabel(_("Inferior Lingular LB5"))
        lobeColorGroupBoxGridLayout.addWidget(inferiorLingularLB5Label, 6, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.inferiorLingularLB5ColorPickerButton, 6, 3)
        self.superiorLB6ColorPickerButton = ctk.ctkColorPickerButton()
        self.superiorLB6ColorPickerButton.objectName = 'superiorLB6ColorPickerButton'
        self.superiorLB6ColorPickerButton.color = lungLobeModel.superiorLB6Color()
        self.superiorLB6ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.superiorLB6ColorPickerButton.setMinimumSize(0, 0)
        self.superiorLB6ColorPickerButton.setMaximumSize(16777215, 16777215)
        superiorLB6Label = qt.QLabel(_("Superior LB6"))
        lobeColorGroupBoxGridLayout.addWidget(superiorLB6Label, 7, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.superiorLB6ColorPickerButton, 7, 1)
        
        self.anteriorBasalLB8ColorPickerButton = ctk.ctkColorPickerButton()
        self.anteriorBasalLB8ColorPickerButton.objectName = 'anteriorBasalLB8ColorPickerButton'
        self.anteriorBasalLB8ColorPickerButton.color = lungLobeModel.anteriorBasalLB8Color()
        self.anteriorBasalLB8ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.anteriorBasalLB8ColorPickerButton.setMinimumSize(0, 0)
        self.anteriorBasalLB8ColorPickerButton.setMaximumSize(16777215, 16777215)
        anteriorBasalLB8Label = qt.QLabel(_("Anterior Basal LB8"))
        lobeColorGroupBoxGridLayout.addWidget(anteriorBasalLB8Label, 7, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.anteriorBasalLB8ColorPickerButton, 7, 3)
        self.lateralBasalLB9ColorPickerButton = ctk.ctkColorPickerButton()
        self.lateralBasalLB9ColorPickerButton.objectName = 'lateralBasalLB9ColorPickerButton'
        self.lateralBasalLB9ColorPickerButton.color = lungLobeModel.lateralBasalLB9Color()
        self.lateralBasalLB9ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.lateralBasalLB9ColorPickerButton.setMinimumSize(0, 0)
        self.lateralBasalLB9ColorPickerButton.setMaximumSize(16777215, 16777215)
        lateralBasalLB9Label = qt.QLabel(_("Lateral Basal LB9"))
        lobeColorGroupBoxGridLayout.addWidget(lateralBasalLB9Label, 8, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.lateralBasalLB9ColorPickerButton, 8, 1)
        
        self.posteriorBasalLB10ColorPickerButton = ctk.ctkColorPickerButton()
        self.posteriorBasalLB10ColorPickerButton.objectName = 'posteriorBasalLB10ColorPickerButton'
        self.posteriorBasalLB10ColorPickerButton.color = lungLobeModel.posteriorBasalLB10Color()
        self.posteriorBasalLB10ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.posteriorBasalLB10ColorPickerButton.setMinimumSize(0, 0)
        self.posteriorBasalLB10ColorPickerButton.setMaximumSize(16777215, 16777215)
        posteriorBasalLB10Label = qt.QLabel(_("Posterior Basal LB10"))
        lobeColorGroupBoxGridLayout.addWidget(posteriorBasalLB10Label, 8, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.posteriorBasalLB10ColorPickerButton, 8, 3)
        
        vBoxLayout.addWidget(lobeColorGroupBox)
        parent.registerProperty('EvoSeg/ApicalRB1Color', self.apicalRB1ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Apical RB1 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/PosteriorRB2Color', self.posteriorRB2ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Posterior RB2 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/AnteriorRB3Color', self.anteriorRB3ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Anterior RB3 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/LateralRB4Color', self.lateralRB4ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Lateral RB4 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/MedialRB5Color', self.medialRB5ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Medial RB5 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/SuperiorRB6Color', self.superiorRB6ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Superior RB6 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/MedialBasalRB7Color', self.medialBasalRB7ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Medial Basal RB7 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/AnteriorBasalRB8Color', self.anteriorBasalRB8ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Anterior Basal RB8 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/LateralBasalRB9Color', self.lateralBasalRB9ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Lateral Basal RB9 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/PosteriorBasalRB10Color', self.posteriorBasalRB10ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Posterior Basal RB10 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/ApicoposteriorLB1_2Color', self.apicoposteriorLB1_2ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Apicoposterior LB1/2 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/AnteriorLB3Color', self.anteriorLB3ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Anterior LB3 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/SuperiorLingularLB4Color', self.superiorLingularLB4ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Superior Lingular LB4 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/InferiorLingularLB5Color', self.inferiorLingularLB5ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Inferior Lingular LB5 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/SuperiorLB6Color', self.superiorLB6ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Superior LB6 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/AnteriorBasalLB8Color', self.anteriorBasalLB8ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Anterior Basal LB8 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/LateralBasalLB9Color', self.lateralBasalLB9ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Lateral Basal LB9 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/PosteriorBasalLB10Color', self.posteriorBasalLB10ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Posterior Basal LB10 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
        ribColorGroupBox = qt.QGroupBox(_('Rib'))
        ribColorGroupBoxFormLayout = qt.QFormLayout(ribColorGroupBox)
        self.ribColorPickerButton = ctk.ctkColorPickerButton()
        self.ribColorPickerButton.objectName = 'ribColorPickerButton'
        self.ribColorPickerButton.color=EvoSegModels.get('Rib').color()
        self.ribColorPickerButton.dialogOptions=qt.QColorDialog.DontUseNativeDialog
        self.ribColorPickerButton.setMinimumSize(0, 0)
        self.ribColorPickerButton.setMaximumSize(16777215, 16777215)
        ribColorGroupBoxFormLayout.addRow(_("Color"), self.ribColorPickerButton)
        vBoxLayout.addWidget(ribColorGroupBox)
        parent.registerProperty('EvoSeg/RibColor', self.ribColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Rib Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
        noduleColorGroupBox = qt.QGroupBox(_('Pulmonary Nodule'))
        noduleColorGroupBoxFormLayout = qt.QFormLayout(noduleColorGroupBox)
        self.noduleColorPickerButton = ctk.ctkColorPickerButton()
        self.noduleColorPickerButton.objectName = 'noduleColorPickerButton'
        self.noduleColorPickerButton.color=EvoSegModels.get('Nodule').color()
        self.noduleColorPickerButton.dialogOptions=qt.QColorDialog.DontUseNativeDialog
        self.noduleColorPickerButton.setMinimumSize(0, 0)
        self.noduleColorPickerButton.setMaximumSize(16777215, 16777215)
        noduleColorGroupBoxFormLayout.addRow(_("Color"), self.noduleColorPickerButton)
        vBoxLayout.addWidget(noduleColorGroupBox)
        parent.registerProperty('EvoSeg/PulmonaryNoduleColor', self.noduleColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Pulmonary Nodule Color"), ctk.ctkSettingsPanel.OptionRequireRestart)

class EvoSegSettingsPanel(ctk.ctkSettingsPanel):
    def __init__(self, *args, **kwargs):
        ctk.ctkSettingsPanel.__init__(self, *args, **kwargs)
        self.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Preferred)
        self.setMinimumSize(0, 0)
        self.ui = _ui_EvoSegSettingsPanel(self)