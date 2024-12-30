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
    def __init__(self, modelName: str, color: qt.QColor
                 , leftUpperLobeColor: qt.QColor=qt.QColor("#80ae80")
                 , leftLowerLobeColor: qt.QColor=qt.QColor("#f1d691")
                 , rightUpperLobeColor: qt.QColor=qt.QColor("#b17a65")
                 , rightMiddleLobeColor: qt.QColor=qt.QColor("#6fb8d2")
                 , rightLowerLobeColor: qt.QColor=qt.QColor("#d8654f")):
        super().__init__(modelName, color)
        self.leftUpperLobeColor=leftUpperLobeColor
        self.leftLowerLobeColor=leftLowerLobeColor
        self.rightUpperLobeColor=rightUpperLobeColor
        self.rightMiddleLobeColor=rightMiddleLobeColor
        self.rightLowerLobeColor=rightLowerLobeColor

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