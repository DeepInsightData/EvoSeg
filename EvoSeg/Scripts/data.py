import numpy as np
from typing import Dict
from skimage.morphology import ball

class DataModule:

    def __init__(
            self, 
            img : np.ndarray, 
            segmentation_masks : Dict[str, np.ndarray], 
            probability_maps : Dict[str, np.ndarray], 
        ):
        '''
            Initialize the image data and segmentation masks, 
            which can be accessed by the DisplayModule and 
            updated by the Labeler.
        '''

        self.img = img
        self.probability_maps = probability_maps
        self.segmentation_masks = segmentation_masks

        self.history = []

    def sphere_addition(
            self, 
            x : int, 
            y : int, 
            z : int, 
            target : str, 
            radius: float = 1,
        ):

        nx, ny, nz = self.img.shape
        radius = min(radius, x + 1, nx - x, y + 1, ny - y, z + 1, nz - z)
        if (radius <= 0):
            return

        ball_array = ball(radius - 1).astype(bool)

        change = ball_array ^ (ball_array & self.segmentation_masks[target][x-radius+1:x+radius, y-radius+1:y+radius, z-radius+1:z+radius])
        change = np.stack(change.nonzero(), axis = 1)
        change += np.array([[x-radius+1, y-radius+1, z-radius+1]])
        self.history.append((target, change, []))

        self.segmentation_masks[target][x-radius+1:x+radius, y-radius+1:y+radius, z-radius+1:z+radius] |= ball_array
    

    def sphere_erasure(
            self, 
            x : int, 
            y : int, 
            z : int, 
            target : str, 
            radius: float = 1,
        ):

        nx, ny, nz = self.img.shape
        radius = min(radius, x + 1, nx - x, y + 1, ny - y, z + 1, nz - z)
        if (radius <= 0):
            return

        ball_array = ball(radius - 1).astype(bool)

        change = (ball_array & self.segmentation_masks[target][x-radius+1:x+radius, y-radius+1:y+radius, z-radius+1:z+radius])
        self.segmentation_masks[target][x-radius+1:x+radius, y-radius+1:y+radius, z-radius+1:z+radius] ^= change

        change = np.stack(change.nonzero(), axis = 1)
        change += np.array([[x-radius+1, y-radius+1, z-radius+1]])
        self.history.append((target, [], change))

    def undo(self, ):

        if len(self.history) == 0:
            return
        
        target, change_on, change_off = self.history[-1]
        if len(change_on) > 0:
            self.segmentation_masks[target][change_on[:, 0], change_on[:, 1], change_on[:, 2]] = False
        if len(change_off) > 0:
            self.segmentation_masks[target][change_off[:, 0], change_off[:, 1], change_off[:, 2]] = True
        self.history.pop()
    
    def get_masks(self, ):
        return self.segmentation_masks
    def get_history_len(self, ):
        return len(self.history)
        

        
    



        

    