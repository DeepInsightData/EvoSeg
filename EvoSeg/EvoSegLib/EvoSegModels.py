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

    def __init__(self, modelName: str, color: qt.QColor, splitByMidPlane: bool):
        super().__init__(modelName, color, splitByMidPlane)

    def leftUpperLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/LeftUpperLobeColor', qt.QColor("#5dade2"))  # 蓝青

    def leftLowerLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/LeftLowerLobeColor', qt.QColor("#2874a6"))  # 深蓝

    def rightUpperLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/RightUpperLobeColor', qt.QColor("#e67e22"))  # 橙色

    def rightMiddleLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/RightMiddleLobeColor', qt.QColor("#f1c40f"))  # 黄色

    def rightLowerLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/RightLowerLobeColor', qt.QColor("#c0392b"))  # 深红

    def apicalS1Color(self):
        return slicer.util.settingsValue(f'EvoSeg/ApicalS1Color', qt.QColor("#f1948a"))  # 浅红

    def posteriorS2Color(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorS2Color', qt.QColor("#cd6155"))  # 深红

    def anteriorS3Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorS3Color', qt.QColor("#e59866"))  # 橙棕

    def lateralS4Color(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralS4Color', qt.QColor("#f7dc6f"))  # 浅黄

    def medialS5Color(self):
        return slicer.util.settingsValue(f'EvoSeg/MedialS5Color', qt.QColor("#d4ac0d"))  # 深黄

    def superiorS6Color(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorS6Color', qt.QColor("#a93226"))  # 深红棕

    def medialBasalS7Color(self):
        return slicer.util.settingsValue(f'EvoSeg/MedialBasalS7Color', qt.QColor("#922b21"))  # 深酒红

    def anteriorBasalS8Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorBasalS8Color', qt.QColor("#b03a2e"))  # 暖红

    def lateralBasalS9Color(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralBasalS9Color', qt.QColor("#dc7633"))  # 橙红

    def posteriorBasalS10Color(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorBasalS10Color', qt.QColor("#873600"))  # 棕色

    def apicoposteriorS1_2Color(self):
        return slicer.util.settingsValue(f'EvoSeg/ApicoposteriorS1_2Color', qt.QColor("#5dade2"))  # 蓝青

    def anteriorS3LeftColor(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorS3LeftColor', qt.QColor("#3498db"))  # 天蓝

    def superiorLingularS4Color(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorLingularS4Color', qt.QColor("#1abc9c"))  # 青绿

    def inferiorLingularS5Color(self):
        return slicer.util.settingsValue(f'EvoSeg/InferiorLingularS5Color', qt.QColor("#16a085"))  # 深青绿

    def superiorS6LeftColor(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorS6LeftColor', qt.QColor("#2e86c1"))  # 深蓝

    def anteriorBasalS8LeftColor(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorBasalS8LeftColor', qt.QColor("#1f618d"))  # 靛蓝

    def lateralBasalS9LeftColor(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralBasalS9LeftColor', qt.QColor("#117864"))  # 青绿深色

    def posteriorBasalS10LeftColor(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorBasalS10LeftColor', qt.QColor("#0e6251"))  # 墨绿色

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