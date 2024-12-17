import numpy as np
from typing import Dict
from skimage.morphology import ball
from skimage.transform import resize

class DataModule:

    def __init__(
            self, 
            img : np.ndarray, 
            segmentation_masks : Dict[str, np.ndarray], 
            probability_maps : Dict[str, np.ndarray], 
            spacing: tuple = (1.0, 1.0, 1.0)
        ):
        '''
            Initialize the image data and segmentation masks, 
            which can be accessed by the DisplayModule and 
            updated by the Labeler.
        '''

        self.img = img
        self.probability_maps = probability_maps
        self.segmentation_masks = segmentation_masks
        self.spacing = spacing
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

        ball_array = ball(radius).astype(bool)

        scale_shape =[int(radius/self.spacing[0]+0.5),int(radius/self.spacing[1]+0.5),int(radius/self.spacing[2]+0.5)]
        new_shape = [dim if dim % 2 == 0 else dim - 1 for dim in scale_shape]
        scale_ball=resize(ball_array, new_shape, mode="edge", order=0)

        radius_x=scale_ball.shape[0]//2
        radius_y=scale_ball.shape[1]//2
        radius_z=scale_ball.shape[2]//2
    
        change = scale_ball ^ (scale_ball & self.segmentation_masks[target][x-radius_x:x+radius_x, y-radius_y:y+radius_y, z-radius_z:z+radius_z])
        change = np.stack(change.nonzero(), axis = 1)
        change += np.array([[x-radius_x, y-radius_y, z-radius_z]])
        self.history.append((target, change, []))

        self.segmentation_masks[target][x-radius_x:x+radius_x, y-radius_y:y+radius_y, z-radius_z:z+radius_z] |= scale_ball
    

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

        scale_shape =[int(radius/self.spacing[0]+0.5),int(radius/self.spacing[1]+0.5),int(radius/self.spacing[2]+0.5)]
        new_shape = [dim if dim % 2 == 0 else dim - 1 for dim in scale_shape]
        scale_ball=resize(ball_array, new_shape, mode="edge", order=0)

        radius_x=scale_ball.shape[0]//2
        radius_y=scale_ball.shape[1]//2
        radius_z=scale_ball.shape[2]//2

        change = (scale_ball & self.segmentation_masks[target][x-radius_x:x+radius_x, y-radius_y:y+radius_y, z-radius_z:z+radius_z])
        self.segmentation_masks[target][x-radius_x:x+radius_x, y-radius_y:y+radius_y, z-radius_z:z+radius_z] ^= change

        change = np.stack(change.nonzero(), axis = 1)
        change += np.array([[x-radius_x, y-radius_y, z-radius_z]])
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
        

        
    



        

    