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
        print("--->",target)
        change = scale_ball ^ (scale_ball & self.segmentation_masks[target][x-radius_x:x+radius_x, y-radius_y:y+radius_y, z-radius_z:z+radius_z])
        change = np.stack(change.nonzero(), axis = 1)
        change += np.array([[x-radius_x, y-radius_y, z-radius_z]])
        self.history.append((target, change, []))

        self.segmentation_masks[target][x-radius_x:x+radius_x, y-radius_y:y+radius_y, z-radius_z:z+radius_z] |= scale_ball
    
    def tube_addition(
        self,
        start_point: np.ndarray,  # [x1, y1, z1] 
        end_point: np.ndarray,    # [x2, y2, z2]
        target: str,
        radius: float = 1
        ):
        nx, ny, nz = self.img.shape
        radius = int(radius)
        
        start = np.round(start_point).astype(int)
        end = np.round(end_point).astype(int)
        
        direction = end - start
        length = np.linalg.norm(direction)
        if length == 0:
            return
        
        direction = direction / length

        num_points = int(length) + 1
        points = np.array([start + direction * i for i in range(num_points)])
        points = points.astype(int)
        
        all_changes = []
        
        for point in points:
            x, y, z = point
            
            if (0 <= x < nx and 0 <= y < ny and 0 <= z < nz):
                x_min = max(0, x - radius)
                x_max = min(nx, x + radius + 1)
                y_min = max(0, y - radius)
                y_max = min(ny, y + radius + 1)
                z_min = max(0, z - radius)
                z_max = min(nz, z + radius + 1)
                
                sphere = ball(radius)
                
                pad_x_min = max(0, radius - x)
                pad_x_max = min(2*radius + 1, radius + (nx - x))
                pad_y_min = max(0, radius - y)
                pad_y_max = min(2*radius + 1, radius + (ny - y))
                pad_z_min = max(0, radius - z)
                pad_z_max = min(2*radius + 1, radius + (nz - z))
                
                sphere = sphere[pad_x_min:pad_x_max, 
                            pad_y_min:pad_y_max, 
                            pad_z_min:pad_z_max]
                
                current_mask = self.segmentation_masks[target][x_min:x_max, y_min:y_max, z_min:z_max]
                change = sphere & ~current_mask
                
                if np.any(change):
                    change_coords = np.stack(np.where(change), axis=1)
                    change_coords += np.array([[x_min, y_min, z_min]])
                    all_changes.extend(change_coords)
                
                self.segmentation_masks[target][x_min:x_max, y_min:y_max, z_min:z_max] |= sphere
        
        if all_changes:
            all_changes = np.stack(all_changes)
            self.history.append((target, all_changes, []))

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
        

        
    



        

    