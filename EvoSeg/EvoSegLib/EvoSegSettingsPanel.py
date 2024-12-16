import qt
import ctk
from slicer.i18n import tr as _
from .EvoSegModels import EvoSegModels
    
class _ui_EvoSegSettingsPanel:
    def __init__(self, parent):
        vBoxLayout = qt.QVBoxLayout(parent)
        
        airwayColorGroupBox = qt.QGroupBox(_('Airway'))
        airwayColorGroupBoxFormLayout = qt.QFormLayout(airwayColorGroupBox)
        airwayColorPickerButton = ctk.ctkColorPickerButton()
        airwayColorPickerButton.color = EvoSegModels.get('Airway').color()
        airwayColorGroupBoxFormLayout.addRow(_("Color"), airwayColorPickerButton)
        vBoxLayout.addWidget(airwayColorGroupBox)
        parent.registerProperty('EvoSeg/AirwayColor', airwayColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Airway Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
        ateryColorGroupBox = qt.QGroupBox(_('Artery'))
        arteryColorGroupBoxFormLayout = qt.QFormLayout(ateryColorGroupBox)
        arteryColorPickerButton = ctk.ctkColorPickerButton()
        arteryColorPickerButton.color=EvoSegModels.get('Artery').color()
        arteryColorGroupBoxFormLayout.addRow(_("Color"), arteryColorPickerButton)
        vBoxLayout.addWidget(ateryColorGroupBox)
        parent.registerProperty('EvoSeg/ArteryColor', arteryColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Artery Color"), ctk.ctkSettingsPanel.OptionRequireRestart)
        
        veinColorGroupBox = qt.QGroupBox(_('Vein'))
        veinColorGroupBoxFormLayout = qt.QFormLayout(veinColorGroupBox)
        veinColorPickerButton = ctk.ctkColorPickerButton()
        veinColorPickerButton.color=EvoSegModels.get('Vein').color()
        veinColorGroupBoxFormLayout.addRow(_("Color"), veinColorPickerButton)
        vBoxLayout.addWidget(veinColorGroupBox)
        parent.registerProperty('EvoSeg/VeinColor', veinColorPickerButton,
            "color", str(qt.SIGNAL("colorChanged(QColor)")),
            _("Vein Color"), ctk.ctkSettingsPanel.OptionRequireRestart)

class EvoSegSettingsPanel(ctk.ctkSettingsPanel):
    def __init__(self, *args, **kwargs):
        ctk.ctkSettingsPanel.__init__(self, *args, **kwargs)
        self.ui = _ui_EvoSegSettingsPanel(self)