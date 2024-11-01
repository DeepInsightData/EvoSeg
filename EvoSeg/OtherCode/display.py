import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RangeSlider, CheckButtons, RadioButtons, TextBox
from matplotlib.colors import LinearSegmentedColormap
from OtherCode.data import DataModule
from typing import Dict
import ast

class DisplayModule:

    def __init__(
        self, 
        data_module : DataModule, 
        class_display_colors : Dict
    ):

        self.data_module = data_module
        self.class_display_colors = class_display_colors
        self.class_display_colormap = dict()
        for class_name, color in class_display_colors.items():
            self.class_display_colormap[class_name] = LinearSegmentedColormap.from_list(
                f"cmap_for_{class_name}", 
                [(0, 0, 0), color]
            )

        # Create the figure and the line that we will manipulate
        self.fig, self.axs = plt.subplot_mosaic(
            [
                ['target','target', 'main'],
                ['option','option','main'],
                ['parameter', 'parameter','main'],
                ['undo','save', 'main'],
                ["visability","visability", 'empty']
            ],
            width_ratios=[0.5, 0.5, 4],
            height_ratios=[1, 1, 1, 0.3, 1],
            layout='constrained',
        )
        plt.subplots_adjust(left=0.25, bottom=0.25)
        for spine in self.axs["empty"].spines.values():
            spine.set_visible(False)
        self.axs["empty"].set_xticks([])
        self.axs["empty"].set_yticks([])
        

        # Initial plot
        ct_data = self.data_module.img
        mask_data = self.data_module.segmentation_masks["airway"]
        z_init = ct_data.shape[2] // 2  # Starting at the middle slice
        vmin, vmax = np.quantile(ct_data.ravel(), (ct_data==0).mean()+0.01), np.quantile(ct_data.ravel(), (ct_data<1).mean()-0.01)
        self.im_object = self.axs["main"].imshow(ct_data[:, :, z_init].T, cmap='gray', origin='upper', vmin = vmin, vmax = vmax)
        self.mask_object = dict()
        for class_name, mask_data in self.data_module.segmentation_masks.items():
            display_mask_data = mask_data[:, :, z_init].T
            display_mask_data = np.ma.masked_where(~display_mask_data, display_mask_data)
            self.mask_object[class_name] = self.axs["main"].imshow(
                display_mask_data, 
                alpha=0.8, 
                visible = True,
                cmap=self.class_display_colormap[class_name], 
                origin='upper', vmin = 0, vmax = 1
            )
        
        self.axs["main"].set_title(f'Slice: {z_init}')
        pos = self.axs["main"].get_position()

        # Add a slider below the image
        axcolor = 'lightgoldenrodyellow'
        slider_ax = plt.axes([pos.x0, 0.1, pos.width, 0.03], facecolor=axcolor)
        self.slider = Slider(slider_ax, 'Slice', 0, ct_data.shape[2] - 1, valinit=z_init, valstep=1)
        self.slider.on_changed(self.update)

        # Create the range slider below the original slider
        range_slider_ax = plt.axes([pos.x0, 0.05, pos.width, 0.03], facecolor=axcolor)
        # Assuming ct_data is in the range of 0-255 for CT images
        self.range_slider = RangeSlider(range_slider_ax, 'Intensity Range', 0, 1, valinit=(vmin, vmax))
        self.range_slider.on_changed(self.update_range)

        # Create the checkbox axes to the left of the image
        checkbox_ax = self.axs["visability"]
        checkbox_ax.set_title("visability")
        # Create the checkbox
        self.checkbox = CheckButtons(
            checkbox_ax, 
            actives=[True] * len(class_display_colors),
            labels = list(class_display_colors.keys()),
            label_props={'color': list(class_display_colors.values())},
            check_props={'facecolor': list(class_display_colors.values())},
        )
        self.checkbox.on_clicked(self.toggle_mask)

        # Segmentation target box
        segmentation_target_ax = self.axs["target"]
        self.segmentation_target = RadioButtons(
            segmentation_target_ax, 
            labels = list(class_display_colors.keys()),
        )
        segmentation_target_ax.set_title('segmentation target')

        # Segmentation option
        segmentation_option_ax = self.axs["option"]
        self.segmentation_option = RadioButtons(
            segmentation_option_ax, 
            labels = [
                'Sphere Addition',
                'Sphere Erasure',
                'Magic Addition',
                'Magic Erasure',
            ],
        )
        segmentation_option_ax.set_title("segmentation option")

        # Segmentation parameter
        segmentation_param_ax = self.axs["parameter"]
        self.segmentation_param = TextBox(segmentation_param_ax, "", "{'radius':3, }")
        segmentation_param_ax.set_title('segmentation parameter')

        # Undo/Redo/Save
        self.button_undo = Button(
            self.axs["undo"], 'Undo'
        )
        self.button_undo.on_clicked(self.undo)
        self.button_save = Button(
            self.axs["save"], 'Save'
        )

        # Position the button axes relative to the slider axis
        button_left_ax = plt.axes([pos.x0, 0.15, 0.02, 0.03])  # Adjust the x position to be left of the slider
        button_right_ax = plt.axes([pos.x0 + pos.width, 0.15, 0.02, 0.03])  # Adjust the x position to be right of the slider
        self.button_left = Button(button_left_ax, '<')
        self.button_left.on_clicked(self.decrement)
        self.button_right = Button(button_right_ax, '>')
        self.button_right.on_clicked(self.increment)

        self.fig.canvas.mpl_connect('button_release_event', self.on_button_release)
    
    def refresh(self):
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()

    # Function to update the plot based on the slider value
    def update(self, val = None):
        z_pos = int(self.slider.val)
        
        ct_data = self.data_module.img
        self.im_object.set_data(ct_data[:, :, z_pos].T)
        
        for class_name, mask_data in self.data_module.segmentation_masks.items():
            display_mask_data = mask_data[:, :, z_pos].T
            display_mask_data = np.ma.masked_where(~display_mask_data, display_mask_data)
            self.mask_object[class_name].set_data(display_mask_data)

        self.axs["main"].set_title(f'Slice: {z_pos}')
        self.refresh()

    def update_range(self, val):
        vmin, vmax = self.range_slider.val
        self.im_object.set_clim(vmin, vmax)
        self.refresh()

    # Button to decrease the slice index
    def decrement(self, val):
        current_val = self.slider.val
        self.slider.set_val(max(current_val - 1, self.slider.valmin))  # Ensure the value does not go below the minimum

    # Button to increase the slice index
    def increment(self, val):
        current_val = self.slider.val
        self.slider.set_val(min(current_val + 1, self.slider.valmax))  # Ensure the value does not go above the maximum

    # Callback function for the checkbox
    def toggle_mask(self, label):
        mask_obj = self.mask_object[label]
        print(mask_obj.get_visible())
        mask_obj.set_visible(not mask_obj.get_visible())
        self.refresh()

    def undo(self, value):
        self.data_module.undo()
        self.update()

    def on_button_release(self, event):

        x, y = round(event.xdata), round(event.ydata)
        z = int(self.slider.val)

        if (self.fig.canvas.cursor().shape().name == "ArrowCursor") and (event.inaxes == self.axs["main"]):

            option = self.segmentation_option.value_selected
            target = self.segmentation_target.value_selected
            param = ast.literal_eval(self.segmentation_param.text)
            
            if option == "Sphere Addition":
                self.data_module.sphere_addition(
                    x, y, z, target, **param
                )
                self.update()
            elif option == "Sphere Erasure":
                self.data_module.sphere_erasure(
                    x, y, z, target, **param
                )
                self.update()
            else:
                raise NotImplementedError

            # obj = plt.scatter(
            #     y, x, 
            #     marker = "x" if ty == 0 else "o", 
            #     facecolor = "white" if ty == 0 else "red", 
            #     s = 15, 
            #     zorder = 2,
            # )
            # point_objects.append(obj)
            # plt.draw()

            
