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
        return slicer.util.settingsValue(f'EvoSeg/LeftUpperLobeColor', qt.QColor("#5dade2"))

    def leftLowerLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/LeftLowerLobeColor', qt.QColor("#2874a6"))

    def rightUpperLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/RightUpperLobeColor', qt.QColor("#e67e22"))

    def rightMiddleLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/RightMiddleLobeColor', qt.QColor("#f1c40f"))

    def rightLowerLobeColor(self):
        return slicer.util.settingsValue(f'EvoSeg/RightLowerLobeColor', qt.QColor("#c0392b"))

    def apicalRB1Color(self):
        return slicer.util.settingsValue(f'EvoSeg/ApicalRB1Color', qt.QColor("#f1f049"))

    def posteriorRB2Color(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorRB2Color', qt.QColor("#d9a166"))

    def anteriorRB3Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorRB3Color', qt.QColor("#da636f"))

    def lateralRB4Color(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralRB4Color', qt.QColor("#41ec48"))

    def medialRB5Color(self):
        return slicer.util.settingsValue(f'EvoSeg/MedialRB5Color', qt.QColor("#4da37c"))  

    def superiorRB6Color(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorRB6Color', qt.QColor("#5ce7ef"))  

    def medialBasalRB7Color(self):
        return slicer.util.settingsValue(f'EvoSeg/MedialBasalRB7Color', qt.QColor("#b57ee6"))  

    def anteriorBasalRB8Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorBasalRB8Color', qt.QColor("#8c67aa"))  

    def lateralBasalRB9Color(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralBasalRB9Color', qt.QColor("#4946ed"))

    def posteriorBasalRB10Color(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorBasalRB10Color', qt.QColor("#5659a0"))  

    def apicoposteriorLB1_2Color(self):
        return slicer.util.settingsValue(f'EvoSeg/ApicoposteriorLB1_2Color', qt.QColor("#cd9b5c"))  

    def anteriorLB3Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorLB3Color', qt.QColor("#da636f"))  

    def superiorLingularLB4Color(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorLingularLB4Color', qt.QColor("#41ec48"))  

    def inferiorLingularLB5Color(self):
        return slicer.util.settingsValue(f'EvoSeg/InferiorLingularLB5Color', qt.QColor("#4da37c"))  

    def superiorLB6Color(self):
        return slicer.util.settingsValue(f'EvoSeg/SuperiorLB6Color', qt.QColor("#5de8ef"))

    def anteriorBasalLB8Color(self):
        return slicer.util.settingsValue(f'EvoSeg/AnteriorBasalLB8Color', qt.QColor("#984EA3"))

    def lateralBasalLB9Color(self):
        return slicer.util.settingsValue(f'EvoSeg/LateralBasalLB9Color', qt.QColor("#FF7F00"))

    def posteriorBasalLB10Color(self):
        return slicer.util.settingsValue(f'EvoSeg/PosteriorBasalLB10Color', qt.QColor("#E41A1C"))  

    def getSegmentColor(self, segmentName: str):
        """Get color for a specific lung segment by name"""
        # Mapping from segment names to their corresponding color methods
        segment_color_map = {
            "Apical RB1": "apicalRB1Color",
            "Posterior RB2": "posteriorRB2Color", 
            "Anterior RB3": "anteriorRB3Color",
            "Lateral RB4": "lateralRB4Color",
            "Medial RB5": "medialRB5Color",
            "Superior RB6": "superiorRB6Color",
            "Medial basal RB7": "medialBasalRB7Color",
            "Anterior basal RB8": "anteriorBasalRB8Color",
            "Lateral basal RB9": "lateralBasalRB9Color",
            "Posterior basal RB10": "posteriorBasalRB10Color",
            "Apicoposterior LB1/2": "apicoposteriorLB1_2Color",
            "Anterior LB3": "anteriorLB3Color",
            "Superior lingular LB4": "superiorLingularLB4Color",
            "Inferior lingular LB5": "inferiorLingularLB5Color",
            "Superior LB6": "superiorLB6Color",
            "Anterior basal LB8": "anteriorBasalLB8Color",
            "Lateral basal LB9": "lateralBasalLB9Color",
            "Posterior basal LB10": "posteriorBasalLB10Color"
        }
        
        # Get the method name for the segment
        method_name = segment_color_map.get(segmentName)
        if method_name:
            # Use getattr to dynamically call the color method
            color_method = getattr(self, method_name)
            return color_method()
        else:
            # Return default color if segment name not found
            return self.defaultColor

class EvoSegModels:
    MODELS = [
        EvoSegModel("Airway", qt.QColor("#c8c8eb"), True),
        EvoSegModel("Artery", qt.QColor("#d8654f"), True),
        EvoSegModel("Vein", qt.QColor("#0097ce"), True),
        LungLobeModel("LungLobe", qt.QColor("#fde89e"), False),
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
