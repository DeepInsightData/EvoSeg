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
    LeftUpperLobeSegments = ["Apicoposterior LB1/2", "Anterior LB3", "Superior lingular LB4", "Inferior lingular LB5"]
    LeftLowerLobeSegments = ["Superior LB6", "Anterior basal LB8", "Lateral basal LB9", "Posterior basal LB10"]
    RightUpperLobeSegments = ["Apical RB1", "Posterior RB2", "Anterior RB3"]
    RightMiddleLobeSegments = ["Lateral RB4", "Medial RB5"]
    RightLowerLobeSegments = ["Superior RB6", "Medial basal RB7", "Anterior basal RB8", "Lateral basal RB9", "Posterior basal RB10"]

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

    def apicalRB1Color(self):
        return slicer.util.settingsValue(f'EvoSeg/ApicalRB1Color', qt.QColor("#f1948a"))  # 浅红

    def posteriorRB2Color(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorRB2Color', qt.QColor("#cd6155"))  # 深红

    def anteriorRB3Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorRB3Color', qt.QColor("#e59866"))  # 橙棕

    def lateralRB4Color(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralRB4Color', qt.QColor("#f7dc6f"))  # 浅黄

    def medialRB5Color(self):
        return slicer.util.settingsValue(f'EvoSeg/MedialRB5Color', qt.QColor("#d4ac0d"))  # 深黄

    def superiorRB6Color(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorRB6Color', qt.QColor("#a93226"))  # 深红棕

    def medialBasalRB7Color(self):
        return slicer.util.settingsValue(f'EvoSeg/MedialBasalRB7Color', qt.QColor("#922b21"))  # 深酒红

    def anteriorBasalRB8Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorBasalRB8Color', qt.QColor("#b03a2e"))  # 暖红

    def lateralBasalRB9Color(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralBasalRB9Color', qt.QColor("#dc7633"))  # 橙红

    def posteriorBasalRB10Color(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorBasalRB10Color', qt.QColor("#873600"))  # 棕色

    def apicoposteriorLB1_2Color(self):
        return slicer.util.settingsValue(f'EvoSeg/ApicoposteriorLB1_2Color', qt.QColor("#5dade2"))  # 蓝青

    def anteriorLB3Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorLB3Color', qt.QColor("#3498db"))  # 天蓝

    def superiorLingularLB4Color(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorLingularLB4Color', qt.QColor("#1abc9c"))  # 青绿

    def inferiorLingularLB5Color(self):
        return slicer.util.settingsValue(f'EvoSeg/InferiorLingularLB5Color', qt.QColor("#16a085"))  # 深青绿

    def superiorLB6Color(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorLB6Color', qt.QColor("#2e86c1"))  # 深蓝

    def anteriorBasalLB8Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorBasalLB8Color', qt.QColor("#1f618d"))  # 靛蓝

    def lateralBasalLB9Color(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralBasalLB9Color', qt.QColor("#117864"))  # 青绿深色

    def posteriorBasalLB10Color(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorBasalLB10Color', qt.QColor("#0e6251"))  # 墨绿色

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