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
        vBoxLayout.addWidget(airwayColorGroupBox)
        parent.registerProperty('EvoSeg/AirwayColor', self.airwayColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Airway Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
        ateryColorGroupBox = qt.QGroupBox(_('Artery'))
        arteryColorGroupBoxFormLayout = qt.QFormLayout(ateryColorGroupBox)
        self.arteryColorPickerButton = ctk.ctkColorPickerButton()
        self.arteryColorPickerButton.objectName = 'ArteryColorPickerButton'
        self.arteryColorPickerButton.color=EvoSegModels.get('Artery').color()
        self.arteryColorPickerButton.dialogOptions = qt.QColorDialog.DontUseNativeDialog
        self.arteryColorPickerButton.setMinimumSize(0, 0)
        self.arteryColorPickerButton.setMaximumSize(16777215, 16777215)
        arteryColorGroupBoxFormLayout.addRow(_("Color"), self.arteryColorPickerButton)
        vBoxLayout.addWidget(ateryColorGroupBox)
        parent.registerProperty('EvoSeg/ArteryColor', self.arteryColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Artery Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
        veinColorGroupBox = qt.QGroupBox(_('Vein'))
        veinColorGroupBoxFormLayout = qt.QFormLayout(veinColorGroupBox)
        self.veinColorPickerButton = ctk.ctkColorPickerButton()
        self.veinColorPickerButton.objectName = 'VeinColorPickerButton'
        self.veinColorPickerButton.color=EvoSegModels.get('Vein').color()
        self.veinColorPickerButton.dialogOptions=qt.QColorDialog.DontUseNativeDialog
        self.veinColorPickerButton.setMinimumSize(0, 0)
        self.veinColorPickerButton.setMaximumSize(16777215, 16777215)
        veinColorGroupBoxFormLayout.addRow(_("Color"), self.veinColorPickerButton)
        vBoxLayout.addWidget(veinColorGroupBox)
        parent.registerProperty('EvoSeg/VeinColor', self.veinColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Vein Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
        lobeColorGroupBox = qt.QGroupBox(_('Lobe'))
        lobeColorGroupBoxFormLayout = qt.QFormLayout(lobeColorGroupBox)
        self.leftUpperLobeColorPickerButton = ctk.ctkColorPickerButton()
        self.leftUpperLobeColorPickerButton.objectName = 'leftUpperLobeColorPickerButton'
        self.leftUpperLobeColorPickerButton.color=EvoSegModels.get('Lobe').leftUpperLobeColor()
        self.leftUpperLobeColorPickerButton.dialogOptions=qt.QColorDialog.DontUseNativeDialog
        self.leftUpperLobeColorPickerButton.setMinimumSize(0, 0)
        self.leftUpperLobeColorPickerButton.setMaximumSize(16777215, 16777215)
        lobeColorGroupBoxFormLayout.addRow(_("Superior lobe of left lung"), self.leftUpperLobeColorPickerButton)
        self.leftLowerLobeColorPickerButton = ctk.ctkColorPickerButton()
        self.leftLowerLobeColorPickerButton.objectName = 'leftLowerLobeColorPickerButton'
        self.leftLowerLobeColorPickerButton.color=EvoSegModels.get('Lobe').leftLowerLobeColor()
        self.leftLowerLobeColorPickerButton.dialogOptions=qt.QColorDialog.DontUseNativeDialog
        self.leftLowerLobeColorPickerButton.setMinimumSize(0, 0)
        self.leftLowerLobeColorPickerButton.setMaximumSize(16777215, 16777215)
        lobeColorGroupBoxFormLayout.addRow(_("Inferior lobe of left lung"), self.leftLowerLobeColorPickerButton)
        self.rightUpperLobeColorPickerButton = ctk.ctkColorPickerButton()
        self.rightUpperLobeColorPickerButton.objectName = 'rightUpperLobeColorPickerButton'
        self.rightUpperLobeColorPickerButton.color=EvoSegModels.get('Lobe').rightUpperLobeColor()
        self.rightUpperLobeColorPickerButton.dialogOptions=qt.QColorDialog.DontUseNativeDialog
        self.rightUpperLobeColorPickerButton.setMinimumSize(0, 0)
        self.rightUpperLobeColorPickerButton.setMaximumSize(16777215, 16777215)
        lobeColorGroupBoxFormLayout.addRow(_("Superior lobe of right lung"), self.rightUpperLobeColorPickerButton)
        self.rightMiddleLobeColorPickerButton = ctk.ctkColorPickerButton()
        self.rightMiddleLobeColorPickerButton.objectName = 'rightMiddleLobeColorPickerButton'
        self.rightMiddleLobeColorPickerButton.color=EvoSegModels.get('Lobe').rightMiddleLobeColor()
        self.rightMiddleLobeColorPickerButton.dialogOptions=qt.QColorDialog.DontUseNativeDialog
        self.rightMiddleLobeColorPickerButton.setMinimumSize(0, 0)
        self.rightMiddleLobeColorPickerButton.setMaximumSize(16777215, 16777215)
        lobeColorGroupBoxFormLayout.addRow(_("Middle lobe of left lung"), self.rightMiddleLobeColorPickerButton)
        self.rightLowerLobeColorPickerButton = ctk.ctkColorPickerButton()
        self.rightLowerLobeColorPickerButton.objectName = 'rightLowerLobeColorPickerButton'
        self.rightLowerLobeColorPickerButton.color=EvoSegModels.get('Lobe').rightLowerLobeColor()
        self.rightLowerLobeColorPickerButton.dialogOptions=qt.QColorDialog.DontUseNativeDialog
        self.rightLowerLobeColorPickerButton.setMinimumSize(0, 0)
        self.rightLowerLobeColorPickerButton.setMaximumSize(16777215, 16777215)
        lobeColorGroupBoxFormLayout.addRow(_("Inferior lobe of left lung"), self.rightLowerLobeColorPickerButton)
        vBoxLayout.addWidget(lobeColorGroupBox)
        parent.registerProperty('EvoSeg/LeftUpperLobeColor', self.leftUpperLobeColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Left Upper Lobe Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/LeftLowerLobeColor', self.leftLowerLobeColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Left Lower Lobe Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/RightUpperLobeColor', self.rightUpperLobeColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Right Upper Lobe Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/RightMiddleLobeColor', self.rightMiddleLobeColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Right Middle Lobe Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        parent.registerProperty('EvoSeg/RightLowerLobeColor', self.rightLowerLobeColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Right Lower Lobe Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
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

class EvoSegSettingsPanel(ctk.ctkSettingsPanel):
    def __init__(self, *args, **kwargs):
        ctk.ctkSettingsPanel.__init__(self, *args, **kwargs)
        self.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Preferred)
        self.setMinimumSize(0, 0)
        self.ui = _ui_EvoSegSettingsPanel(self)