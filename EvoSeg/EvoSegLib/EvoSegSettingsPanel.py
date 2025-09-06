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
        
        lobeColorGroupBox = qt.QGroupBox(_('Lung Segments'))
        lobeColorGroupBoxGridLayout = qt.QGridLayout(lobeColorGroupBox)
        self.apicalS1ColorPickerButton = ctk.ctkColorPickerButton()
        self.apicalS1ColorPickerButton.objectName = 'apicalS1ColorPickerButton'
        self.apicalS1ColorPickerButton.color = EvoSegModels.get('Lobe').apicalS1Color()
        self.apicalS1ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.apicalS1ColorPickerButton.setMinimumSize(0, 0)
        self.apicalS1ColorPickerButton.setMaximumSize(16777215, 16777215)
        apicalS1Label = qt.QLabel(_("Apical S1 (Right)"))
        lobeColorGroupBoxGridLayout.addWidget(apicalS1Label, 0, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.apicalS1ColorPickerButton, 0, 1)
        
        self.posteriorS2ColorPickerButton = ctk.ctkColorPickerButton()
        self.posteriorS2ColorPickerButton.objectName = 'posteriorS2ColorPickerButton'
        self.posteriorS2ColorPickerButton.color = EvoSegModels.get('Lobe').posteriorS2Color()
        self.posteriorS2ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.posteriorS2ColorPickerButton.setMinimumSize(0, 0)
        self.posteriorS2ColorPickerButton.setMaximumSize(16777215, 16777215)
        posteriorS2Label = qt.QLabel(_("Posterior S2 (Right)"))
        lobeColorGroupBoxGridLayout.addWidget(posteriorS2Label, 0, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.posteriorS2ColorPickerButton, 0, 3)
        self.anteriorS3ColorPickerButton = ctk.ctkColorPickerButton()
        self.anteriorS3ColorPickerButton.objectName = 'anteriorS3ColorPickerButton'
        self.anteriorS3ColorPickerButton.color = EvoSegModels.get('Lobe').anteriorS3Color()
        self.anteriorS3ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.anteriorS3ColorPickerButton.setMinimumSize(0, 0)
        self.anteriorS3ColorPickerButton.setMaximumSize(16777215, 16777215)
        anteriorS3Label = qt.QLabel(_("Anterior S3 (Right)"))
        lobeColorGroupBoxGridLayout.addWidget(anteriorS3Label, 1, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.anteriorS3ColorPickerButton, 1, 1)
        
        self.lateralS4ColorPickerButton = ctk.ctkColorPickerButton()
        self.lateralS4ColorPickerButton.objectName = 'lateralS4ColorPickerButton'
        self.lateralS4ColorPickerButton.color = EvoSegModels.get('Lobe').lateralS4Color()
        self.lateralS4ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.lateralS4ColorPickerButton.setMinimumSize(0, 0)
        self.lateralS4ColorPickerButton.setMaximumSize(16777215, 16777215)
        lateralS4Label = qt.QLabel(_("Lateral S4 (Right)"))
        lobeColorGroupBoxGridLayout.addWidget(lateralS4Label, 1, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.lateralS4ColorPickerButton, 1, 3)
        self.medialS5ColorPickerButton = ctk.ctkColorPickerButton()
        self.medialS5ColorPickerButton.objectName = 'medialS5ColorPickerButton'
        self.medialS5ColorPickerButton.color = EvoSegModels.get('Lobe').medialS5Color()
        self.medialS5ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.medialS5ColorPickerButton.setMinimumSize(0, 0)
        self.medialS5ColorPickerButton.setMaximumSize(16777215, 16777215)
        medialS5Label = qt.QLabel(_("Medial S5 (Right)"))
        lobeColorGroupBoxGridLayout.addWidget(medialS5Label, 2, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.medialS5ColorPickerButton, 2, 1)
        
        self.superiorS6ColorPickerButton = ctk.ctkColorPickerButton()
        self.superiorS6ColorPickerButton.objectName = 'superiorS6ColorPickerButton'
        self.superiorS6ColorPickerButton.color = EvoSegModels.get('Lobe').superiorS6Color()
        self.superiorS6ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.superiorS6ColorPickerButton.setMinimumSize(0, 0)
        self.superiorS6ColorPickerButton.setMaximumSize(16777215, 16777215)
        superiorS6Label = qt.QLabel(_("Superior S6 (Right)"))
        lobeColorGroupBoxGridLayout.addWidget(superiorS6Label, 2, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.superiorS6ColorPickerButton, 2, 3)
        
        self.medialBasalS7ColorPickerButton = ctk.ctkColorPickerButton()
        self.medialBasalS7ColorPickerButton.objectName = 'medialBasalS7ColorPickerButton'
        self.medialBasalS7ColorPickerButton.color = EvoSegModels.get('Lobe').medialBasalS7Color()
        self.medialBasalS7ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.medialBasalS7ColorPickerButton.setMinimumSize(0, 0)
        self.medialBasalS7ColorPickerButton.setMaximumSize(16777215, 16777215)
        medialBasalS7Label = qt.QLabel(_("Medial basal S7 (Right)"))
        lobeColorGroupBoxGridLayout.addWidget(medialBasalS7Label, 3, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.medialBasalS7ColorPickerButton, 3, 1)
        
        self.anteriorBasalS8ColorPickerButton = ctk.ctkColorPickerButton()
        self.anteriorBasalS8ColorPickerButton.objectName = 'anteriorBasalS8ColorPickerButton'
        self.anteriorBasalS8ColorPickerButton.color = EvoSegModels.get('Lobe').anteriorBasalS8Color()
        self.anteriorBasalS8ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.anteriorBasalS8ColorPickerButton.setMinimumSize(0, 0)
        self.anteriorBasalS8ColorPickerButton.setMaximumSize(16777215, 16777215)
        anteriorBasalS8Label = qt.QLabel(_("Anterior basal S8 (Right)"))
        lobeColorGroupBoxGridLayout.addWidget(anteriorBasalS8Label, 3, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.anteriorBasalS8ColorPickerButton, 3, 3)
        self.lateralBasalS9ColorPickerButton = ctk.ctkColorPickerButton()
        self.lateralBasalS9ColorPickerButton.objectName = 'lateralBasalS9ColorPickerButton'
        self.lateralBasalS9ColorPickerButton.color = EvoSegModels.get('Lobe').lateralBasalS9Color()
        self.lateralBasalS9ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.lateralBasalS9ColorPickerButton.setMinimumSize(0, 0)
        self.lateralBasalS9ColorPickerButton.setMaximumSize(16777215, 16777215)
        lateralBasalS9Label = qt.QLabel(_("Lateral basal S9 (Right)"))
        lobeColorGroupBoxGridLayout.addWidget(lateralBasalS9Label, 4, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.lateralBasalS9ColorPickerButton, 4, 1)
        
        self.posteriorBasalS10ColorPickerButton = ctk.ctkColorPickerButton()
        self.posteriorBasalS10ColorPickerButton.objectName = 'posteriorBasalS10ColorPickerButton'
        self.posteriorBasalS10ColorPickerButton.color = EvoSegModels.get('Lobe').posteriorBasalS10Color()
        self.posteriorBasalS10ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.posteriorBasalS10ColorPickerButton.setMinimumSize(0, 0)
        self.posteriorBasalS10ColorPickerButton.setMaximumSize(16777215, 16777215)
        posteriorBasalS10Label = qt.QLabel(_("Posterior basal S10 (Right)"))
        lobeColorGroupBoxGridLayout.addWidget(posteriorBasalS10Label, 4, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.posteriorBasalS10ColorPickerButton, 4, 3)
        self.apicoposteriorS1_2ColorPickerButton = ctk.ctkColorPickerButton()
        self.apicoposteriorS1_2ColorPickerButton.objectName = 'apicoposteriorS1_2ColorPickerButton'
        self.apicoposteriorS1_2ColorPickerButton.color = EvoSegModels.get('Lobe').apicoposteriorS1_2Color()
        self.apicoposteriorS1_2ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.apicoposteriorS1_2ColorPickerButton.setMinimumSize(0, 0)
        self.apicoposteriorS1_2ColorPickerButton.setMaximumSize(16777215, 16777215)
        apicoposteriorS1_2Label = qt.QLabel(_("Apicoposterior S1+2 (Left)"))
        lobeColorGroupBoxGridLayout.addWidget(apicoposteriorS1_2Label, 5, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.apicoposteriorS1_2ColorPickerButton, 5, 1)
        
        self.anteriorS3LeftColorPickerButton = ctk.ctkColorPickerButton()
        self.anteriorS3LeftColorPickerButton.objectName = 'anteriorS3LeftColorPickerButton'
        self.anteriorS3LeftColorPickerButton.color = EvoSegModels.get('Lobe').anteriorS3LeftColor()
        self.anteriorS3LeftColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.anteriorS3LeftColorPickerButton.setMinimumSize(0, 0)
        self.anteriorS3LeftColorPickerButton.setMaximumSize(16777215, 16777215)
        anteriorS3LeftLabel = qt.QLabel(_("Anterior S3 (Left)"))
        lobeColorGroupBoxGridLayout.addWidget(anteriorS3LeftLabel, 5, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.anteriorS3LeftColorPickerButton, 5, 3)
        self.superiorLingularS4ColorPickerButton = ctk.ctkColorPickerButton()
        self.superiorLingularS4ColorPickerButton.objectName = 'superiorLingularS4ColorPickerButton'
        self.superiorLingularS4ColorPickerButton.color = EvoSegModels.get('Lobe').superiorLingularS4Color()
        self.superiorLingularS4ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.superiorLingularS4ColorPickerButton.setMinimumSize(0, 0)
        self.superiorLingularS4ColorPickerButton.setMaximumSize(16777215, 16777215)
        superiorLingularS4Label = qt.QLabel(_("Superior lingular S4 (Left)"))
        lobeColorGroupBoxGridLayout.addWidget(superiorLingularS4Label, 6, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.superiorLingularS4ColorPickerButton, 6, 1)
        
        self.inferiorLingularS5ColorPickerButton = ctk.ctkColorPickerButton()
        self.inferiorLingularS5ColorPickerButton.objectName = 'inferiorLingularS5ColorPickerButton'
        self.inferiorLingularS5ColorPickerButton.color = EvoSegModels.get('Lobe').inferiorLingularS5Color()
        self.inferiorLingularS5ColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.inferiorLingularS5ColorPickerButton.setMinimumSize(0, 0)
        self.inferiorLingularS5ColorPickerButton.setMaximumSize(16777215, 16777215)
        inferiorLingularS5Label = qt.QLabel(_("Inferior lingular S5 (Left)"))
        lobeColorGroupBoxGridLayout.addWidget(inferiorLingularS5Label, 6, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.inferiorLingularS5ColorPickerButton, 6, 3)
        self.superiorS6LeftColorPickerButton = ctk.ctkColorPickerButton()
        self.superiorS6LeftColorPickerButton.objectName = 'superiorS6LeftColorPickerButton'
        self.superiorS6LeftColorPickerButton.color = EvoSegModels.get('Lobe').superiorS6LeftColor()
        self.superiorS6LeftColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.superiorS6LeftColorPickerButton.setMinimumSize(0, 0)
        self.superiorS6LeftColorPickerButton.setMaximumSize(16777215, 16777215)
        superiorS6LeftLabel = qt.QLabel(_("Superior S6 (Left)"))
        lobeColorGroupBoxGridLayout.addWidget(superiorS6LeftLabel, 7, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.superiorS6LeftColorPickerButton, 7, 1)
        
        self.anteriorBasalS8LeftColorPickerButton = ctk.ctkColorPickerButton()
        self.anteriorBasalS8LeftColorPickerButton.objectName = 'anteriorBasalS8LeftColorPickerButton'
        self.anteriorBasalS8LeftColorPickerButton.color = EvoSegModels.get('Lobe').anteriorBasalS8LeftColor()
        self.anteriorBasalS8LeftColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.anteriorBasalS8LeftColorPickerButton.setMinimumSize(0, 0)
        self.anteriorBasalS8LeftColorPickerButton.setMaximumSize(16777215, 16777215)
        anteriorBasalS8LeftLabel = qt.QLabel(_("Anterior basal S8 (Left)"))
        lobeColorGroupBoxGridLayout.addWidget(anteriorBasalS8LeftLabel, 7, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.anteriorBasalS8LeftColorPickerButton, 7, 3)
        self.lateralBasalS9LeftColorPickerButton = ctk.ctkColorPickerButton()
        self.lateralBasalS9LeftColorPickerButton.objectName = 'lateralBasalS9LeftColorPickerButton'
        self.lateralBasalS9LeftColorPickerButton.color = EvoSegModels.get('Lobe').lateralBasalS9LeftColor()
        self.lateralBasalS9LeftColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.lateralBasalS9LeftColorPickerButton.setMinimumSize(0, 0)
        self.lateralBasalS9LeftColorPickerButton.setMaximumSize(16777215, 16777215)
        lateralBasalS9LeftLabel = qt.QLabel(_("Lateral basal S9 (Left)"))
        lobeColorGroupBoxGridLayout.addWidget(lateralBasalS9LeftLabel, 8, 0)
        lobeColorGroupBoxGridLayout.addWidget(self.lateralBasalS9LeftColorPickerButton, 8, 1)
        
        self.posteriorBasalS10LeftColorPickerButton = ctk.ctkColorPickerButton()
        self.posteriorBasalS10LeftColorPickerButton.objectName = 'posteriorBasalS10LeftColorPickerButton'
        self.posteriorBasalS10LeftColorPickerButton.color = EvoSegModels.get('Lobe').posteriorBasalS10LeftColor()
        self.posteriorBasalS10LeftColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.posteriorBasalS10LeftColorPickerButton.setMinimumSize(0, 0)
        self.posteriorBasalS10LeftColorPickerButton.setMaximumSize(16777215, 16777215)
        posteriorBasalS10LeftLabel = qt.QLabel(_("Posterior basal S10 (Left)"))
        lobeColorGroupBoxGridLayout.addWidget(posteriorBasalS10LeftLabel, 8, 2)
        lobeColorGroupBoxGridLayout.addWidget(self.posteriorBasalS10LeftColorPickerButton, 8, 3)
        
        vBoxLayout.addWidget(lobeColorGroupBox)
        parent.registerProperty('EvoSeg/ApicalS1Color', self.apicalS1ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Apical S1 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/PosteriorS2Color', self.posteriorS2ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Posterior S2 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/AnteriorS3Color', self.anteriorS3ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Anterior S3 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/LateralS4Color', self.lateralS4ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Lateral S4 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/MedialS5Color', self.medialS5ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Medial S5 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/SuperiorS6Color', self.superiorS6ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Superior S6 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/MedialBasalS7Color', self.medialBasalS7ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Medial Basal S7 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/AnteriorBasalS8Color', self.anteriorBasalS8ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Anterior Basal S8 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/LateralBasalS9Color', self.lateralBasalS9ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Lateral Basal S9 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/PosteriorBasalS10Color', self.posteriorBasalS10ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Posterior Basal S10 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/ApicoposteriorS1_2Color', self.apicoposteriorS1_2ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Apicoposterior S1+2 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/AnteriorS3LeftColor', self.anteriorS3LeftColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Anterior S3 Left Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/SuperiorLingularS4Color', self.superiorLingularS4ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Superior Lingular S4 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/InferiorLingularS5Color', self.inferiorLingularS5ColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Inferior Lingular S5 Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/SuperiorS6LeftColor', self.superiorS6LeftColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Superior S6 Left Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/AnteriorBasalS8LeftColor', self.anteriorBasalS8LeftColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Anterior Basal S8 Left Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/LateralBasalS9LeftColor', self.lateralBasalS9LeftColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Lateral Basal S9 Left Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/PosteriorBasalS10LeftColor', self.posteriorBasalS10LeftColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Posterior Basal S10 Left Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
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