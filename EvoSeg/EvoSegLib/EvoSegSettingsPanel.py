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

class EvoSegSettingsPanel(ctk.ctkSettingsPanel):
    def __init__(self, *args, **kwargs):
        ctk.ctkSettingsPanel.__init__(self, *args, **kwargs)
        self.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Preferred)
        self.setMinimumSize(0, 0)
        self.ui = _ui_EvoSegSettingsPanel(self)