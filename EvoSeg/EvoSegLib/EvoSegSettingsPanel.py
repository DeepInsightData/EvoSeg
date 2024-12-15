import os
import qt
import ctk
import slicer
from slicer.i18n import tr as _

class EvoSegModel:
    def __init__(self, modelName, color):
        self.name = modelName
        self.defaultColor = color

    def color(self):
        return slicer.util.settingsValue(f'EvoSeg/{self.name}Color', self.defaultColor)
    
    def outputVolumeNodeName(self):
        return slicer.util.settingsValue(f'EvoSeg/{self.name}OutputVolumeNodeName', f'{self.name}_Output_Mask')

class EvoSegModels:
    MODELS = [
        EvoSegModel("Airway", qt.QColor("#c8c8eb")),
        EvoSegModel("Artery", qt.QColor("#d8654f")),
        EvoSegModel("Vein", qt.QColor("#0097ce")),
    ]

    _model_dict = {model.name: model for model in MODELS}

    @classmethod
    def get(cls, modelName):
        return cls._model_dict.get(modelName)
    
    @classmethod
    def all(cls):
        return cls.MODELS
    
    @classmethod
    def names(cls):
        return list(cls._model_dict.keys())
    
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