import qt
import slicer

class EvoSegModel:
    def __init__(self, modelName: str, color: qt.QColor):
        self.name = modelName
        self.defaultColor = color

    def color(self):
        return slicer.util.settingsValue(f'EvoSeg/{self.name}Color', self.defaultColor)
    
    def outputVolumeNodeName(self):
        return slicer.util.settingsValue(f'EvoSeg/{self.name}OutputVolumeNodeName', f'{self.name}_Output_Mask')
    
class LungLobeModel(EvoSegModel):
    def __init__(self, modelName: str, color: qt.QColor):
        super().__init__(modelName, color)
    
    def leftUpperLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/LeftUpperLobeColor', qt.QColor("#80ae80"))
    
    def leftLowerLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/LeftLowerLobeColor', qt.QColor("#f1d691"))
    
    def rightUpperLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/RightUpperLobeColor', qt.QColor("#b17a65"))
    
    def rightMiddleLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/RightMiddleLobeColor', qt.QColor("#6fb8d2"))
    
    def rightLowerLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/RightLowerLobeColor', qt.QColor("#d8654f"))

class EvoSegModels:
    MODELS = [
        EvoSegModel("Airway", qt.QColor("#c8c8eb")),
        EvoSegModel("Artery", qt.QColor("#d8654f")),
        EvoSegModel("Vein", qt.QColor("#0097ce")),
        LungLobeModel("Lobe", qt.QColor("#fde89e")),
        EvoSegModel("Rib", qt.QColor("#fde89e")),
    ]

    _model_dict = {model.name: model for model in MODELS}

    @classmethod
    def get(cls, modelName : str):
        return cls._model_dict.get(modelName)
    
    @classmethod
    def all(cls):
        return cls.MODELS
    
    @classmethod
    def names(cls):
        return list(cls._model_dict.keys())