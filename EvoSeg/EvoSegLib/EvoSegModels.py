import qt
import slicer

class EvoSegModel:
    def __init__(self, modelName: str, color: qt.QColor, splitByMidPlane : bool = False):
        self.name = modelName
        self.defaultColor = color
        self.splitByMidPlane = splitByMidPlane

    def isSplitByMidPlane(self):
        return slicer.util.settingsValue(f'EvoSeg/{self.name}SplitByMidPlane', self.splitByMidPlane)

    def color(self):
        return slicer.util.settingsValue(f'EvoSeg/{self.name}Color', self.defaultColor)
    
    def outputVolumeNodeName(self):
        return slicer.util.settingsValue(f'EvoSeg/{self.name}OutputVolumeNodeName', f'{self.name}_Output_Mask')
    
class LungLobeModel(EvoSegModel):
    LeftUpperLobeSegments = ["Apicoposterior S1+2", "Anterior S3", "Superior lingular S4", "Inferior lingular S5"]
    LeftLowerLobeSegments = ["Superior S6", "Anterior basal S8", "Lateral basal S9", "Posterior basal S10"]
    RightUpperLobeSegments = ["Apical S1", "Posterior S2", "Anterior S3"]
    RightMiddleLobeSegments = ["Lateral S4", "Medial S5"]
    RightLowerLobeSegments = ["Superior S6", "Medial basal S7", "Anterior basal S8", "Lateral basal S9", "Posterior basal S10"]
    
    def __init__(self, modelName: str, color: qt.QColor, splitByMidPlane : bool):
        super().__init__(modelName, color, splitByMidPlane)
    
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
    
    def apicalS1Color(self):
        return slicer.util.settingsValue(f'EvoSeg/ApicalS1Color', qt.QColor("#ff6b6b"))
    
    def posteriorS2Color(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorS2Color', qt.QColor("#4ecdc4"))
    
    def anteriorS3Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorS3Color', qt.QColor("#45b7d1"))
    
    def lateralS4Color(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralS4Color', qt.QColor("#96ceb4"))
    
    def medialS5Color(self):
        return slicer.util.settingsValue(f'EvoSeg/MedialS5Color', qt.QColor("#feca57"))
    
    def superiorS6Color(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorS6Color', qt.QColor("#ff9ff3"))
    
    def medialBasalS7Color(self):
        return slicer.util.settingsValue(f'EvoSeg/MedialBasalS7Color', qt.QColor("#54a0ff"))
    
    def anteriorBasalS8Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorBasalS8Color', qt.QColor("#5f27cd"))
    
    def lateralBasalS9Color(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralBasalS9Color', qt.QColor("#00d2d3"))
    
    def posteriorBasalS10Color(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorBasalS10Color', qt.QColor("#ff9f43"))
    
    def apicoposteriorS1_2Color(self):
        return slicer.util.settingsValue(f'EvoSeg/ApicoposteriorS1_2Color', qt.QColor("#a55eea"))
    
    def anteriorS3LeftColor(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorS3LeftColor', qt.QColor("#26de81"))
    
    def superiorLingularS4Color(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorLingularS4Color', qt.QColor("#fd79a8"))
    
    def inferiorLingularS5Color(self):
        return slicer.util.settingsValue(f'EvoSeg/InferiorLingularS5Color', qt.QColor("#fdcb6e"))
    
    def superiorS6LeftColor(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorS6LeftColor', qt.QColor("#6c5ce7"))
    
    def anteriorBasalS8LeftColor(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorBasalS8LeftColor', qt.QColor("#a29bfe"))
    
    def lateralBasalS9LeftColor(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralBasalS9LeftColor', qt.QColor("#fd79a8"))
    
    def posteriorBasalS10LeftColor(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorBasalS10LeftColor', qt.QColor("#fdcb6e"))

class EvoSegModels:
    MODELS = [
        EvoSegModel("Airway", qt.QColor("#c8c8eb"), True),
        EvoSegModel("Artery", qt.QColor("#d8654f"), True),
        EvoSegModel("Vein", qt.QColor("#0097ce"), True),
        LungLobeModel("Lobe", qt.QColor("#fde89e"), False),
        EvoSegModel("Rib", qt.QColor("#fde89e"), False),
        EvoSegModel("Nodule", qt.QColor("#804f00"), False),
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