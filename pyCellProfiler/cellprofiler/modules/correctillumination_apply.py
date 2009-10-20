'''<b>CorrectIllumination_Apply:</b> Applies an illumination function, created by
CorrectIllumination_Calculate, to an image in order to correct for uneven
illumination (uneven shading).
<hr>

This module applies a previously created illumination correction function,
either loaded by <b>LoadSingleImage</b> or created by <b>CorrectIllumination_Calculate</b>.
This module corrects each image in the pipeline using the function you specify. 

See also <b>CorrectIllumination_Calculate, RescaleIntensity</b>.'''

#CellProfiler is distributed under the GNU General Public License.
#See the accompanying file LICENSE for details.
#
#Developed by the Broad Institute
#Copyright 2003-2009
#
#Please see the AUTHORS file for credits.
#
#Website: http://www.cellprofiler.org

__version__="$Revision$"

import numpy as np

import cellprofiler.cpmodule as cpm
import cellprofiler.settings as cps
import cellprofiler.cpimage  as cpi

######################################
#
# Choices for "Divide or subtract"?
#
######################################
DOS_DIVIDE = "Divide"
DOS_SUBTRACT = "Subtract"

######################################
#
# Rescaling choices
#
######################################
RE_NONE = "No rescaling"
RE_STRETCH = "Stretch 0 to 1"
RE_MATCH = "Match maximums"

######################################
#
# # of settings per image when writing pipeline
#
######################################

SETTINGS_PER_IMAGE = 5

class CorrectIllumination_Apply(cpm.CPModule):
    category = "Image Processing"
    variable_revision_number = 2
    module_name = "CorrectIllumination_Apply"
    
    def create_settings(self):
        """Make settings here (and set the module name)"""
        self.images = []
        self.add_image(can_delete = False)
        self.add_image_button = cps.DoSomething("Add another image","Add",
                                                self.add_image)
    
    def add_image(self, can_delete = True):
        '''Add an image and its settings to the list of images'''
        image_name = cps.ImageNameSubscriber("Select the input image","None", doc = '''What did you call the image to be corrected?''')
        corrected_image_name = cps.ImageNameProvider("Name the output image","CorrBlue", doc = '''What do you want to call the corrected image?''')
        illum_correct_function_image_name = cps.ImageNameSubscriber("Select the illumination function","None", doc = '''What did you call the 
                                        illumination correction function image to be used to carry out the correction (produced by another module 
                                        or loaded as a .mat format image using Load Single Image)?''')
        divide_or_subtract = cps.Choice("How do you want to apply the illumination correction function?",
                                        [DOS_DIVIDE, DOS_SUBTRACT], doc = '''This choice depends on how the illumination function was calculated
                                        and on your physical model of how illumination variation affects the background of images relative to 
                                        the objects in images. <ul><li>Subtract: Use <i>Subtract</i> if the background signal is significant relative to the real signal
                                        coming from the cells (a somewhat empirical decision).  If you created the illumination correction function using <i>Background</i>,
                                        then you will want to choose <i>Subtract</i> here.</li><li>Divide: Use <i>Divide</i> if the the signal to background ratio 
                                        is quite high (the cells are stained very strongly).  If you created the illumination correction function using <i>Regular</i>,
                                        then you will want to choose <i>Divide</i> here.</ul>''')
        rescale_option = cps.Choice("Choose rescaling method",
                                    [RE_NONE, RE_STRETCH, RE_MATCH], doc = '''<ul><li>Subtract: Any pixels that end up negative are set to zero, so no rescaling is necessary.
                                    <li>Divide: The resulting image may be in a very different range of intensity values relative to the original image.
                                    If the illumination correction function is in the range 1 to infinity, <i>Divide</i> will usually yield an image in a reasonable
                                    range (0 to 1).  However, if the image is not in this range, or the intensity gradient within the image is still very great,
                                    you may want to rescale the image.  There are two:<ul><li>Stretch the image from 0 to 1.<li>Match the maximum of the corrected image
                                    to the maximum of the original image.</ul></ul>''')
        image_settings = cps.SettingsGroup()
        image_settings.append("image_name", image_name)
        image_settings.append("corrected_image_name", corrected_image_name)
        image_settings.append("illum_correct_function_image_name", 
                              illum_correct_function_image_name)
        image_settings.append("divide_or_subtract", divide_or_subtract)
        image_settings.append("rescale_option", rescale_option)
        if can_delete:
            image_settings.append("remover",
                                  cps.RemoveSettingButton("Remove this image",
                                                          "Remove",
                                                          self.images,
                                                          image_settings))
        image_settings.append("divider",cps.Divider())
        self.images.append(image_settings)

    def settings(self):
        """Return the settings to be loaded or saved to/from the pipeline
        
        These are the settings (from cellprofiler.settings) that are
        either read from the strings in the pipeline or written out
        to the pipeline. The settings should appear in a consistent
        order so they can be matched to the strings in the pipeline.
        """
        result = []
        for image in self.images:
            result += [image.image_name, image.corrected_image_name,
                       image.illum_correct_function_image_name, 
                       image.divide_or_subtract, image.rescale_option]
        return result

    def visible_settings(self):
        """Return the list of displayed settings
        
        Only display the rescale option when dividing
        """
        result = []
        for image in self.images:
            result += [image.image_name, image.corrected_image_name,
                       image.illum_correct_function_image_name, 
                       image.divide_or_subtract]
            if image.divide_or_subtract == DOS_DIVIDE:
                result.append(image.rescale_option)
            #
            # Get the "remover" button if there is one
            #
            remover = getattr(image, "remover", None)
            if remover is not None:
                result.append(remover)
            result.append(image.divider)
        result.append(self.add_image_button)
        return result

    def prepare_to_set_values(self, setting_values):
        """Do any sort of adjustment to the settings required for the given values
        
        setting_values - the values for the settings just prior to mapping
                         as done by set_setting_values
        This method allows a module to specialize itself according to
        the number of settings and their value. For instance, a module that
        takes a variable number of images or objects can increase or decrease
        the number of relevant settings so they map correctly to the values.
        """
        #
        # Figure out how many images there are based on the number of setting_values
        #
        assert len(setting_values) % SETTINGS_PER_IMAGE == 0
        image_count = len(setting_values) / SETTINGS_PER_IMAGE
        del self.images[image_count:]
        while len(self.images) < image_count:
            self.add_image()
        
    def run(self, workspace):
        """Run the module
        
        workspace    - The workspace contains
            pipeline     - instance of cpp for this run
            image_set    - the images in the image set being processed
            object_set   - the objects (labeled masks) in this image set
            measurements - the measurements for this run
            frame        - the parent frame to whatever frame is created. None means don't draw.
        """
        for image in self.images:
            self.run_image(image, workspace)
        
        if workspace.frame:
            self.display(workspace)
            
    def run_image(self, image, workspace):
        '''Perform illumination according to the parameters of one image setting group
        
        '''
        #
        # Get the image names from the settings
        #
        image_name = image.image_name.value
        illum_correct_name = image.illum_correct_function_image_name.value
        corrected_image_name = image.corrected_image_name.value
        #
        # Get grayscale images from the image set
        #
        orig_image = workspace.image_set.get_image(image_name,
                                                   must_be_grayscale=True)
        illum_function = workspace.image_set.get_image(illum_correct_name,
                                                       must_be_grayscale=True)
        #
        # Either divide or subtract the illumination image from the original
        #
        if image.divide_or_subtract == DOS_DIVIDE:
            output_pixels = orig_image.pixel_data / illum_function.pixel_data
            output_pixels = self.rescale(image, output_pixels,
                                         orig_image.pixel_data)
        elif image.divide_or_subtract == DOS_SUBTRACT:
            output_pixels = orig_image.pixel_data - illum_function.pixel_data
            output_pixels[output_pixels < 0] = 0
        else:
            raise ValueError("Unhandled option for divide or subtract: %s"%
                             image.divide_or_subtract.value)
        #
        # Save the output image in the image set and have it inherit
        # mask & cropping from the original image.
        #
        output_image = cpi.Image(output_pixels, parent_image = orig_image) 
        workspace.image_set.add(corrected_image_name, output_image)
    
    def rescale(self, image, pixel_data, orig_pixel_data):
        """Rescale according to the rescale option setting"""
        if image.rescale_option == RE_NONE:
            return pixel_data
        elif image.rescale_option == RE_STRETCH:
            #
            # Scale the image intensity linearly so that the minimum
            # is zero and the maximum is one.
            #
            pmin = pixel_data.min()
            pmax = pixel_data.max()
            if pmin==pmax:
                return np.ones(pixel_data.shape)
            return (pixel_data-pmin)/(pmax-pmin)
        elif image.rescale_option == RE_MATCH:
            #
            # Make the maximum value in the output match the maximum
            # value in the input, scaling all other pixels linearly
            #
            pmax = pixel_data.max()
            omax = orig_pixel_data.max()
            if pmax == 0:
                return np.ones(orig_pixel_data.shape) * omax
            else:
                return pixel_data * omax /pmax
        else:
            raise ValueError("Unhandled option for rescaling: %s"%(self.rescale_option))

    def display(self, workspace):
        ''' Display one row of orig / illum / output per image setting group'''
        figure = workspace.create_or_find_figure(subplots=(3,len(self.images)))
        for j, image in enumerate(self.images):
            image_name = image.image_name.value
            illum_correct_function_image_name = image.illum_correct_function_image_name.value
            corrected_image_name = image.corrected_image_name.value
            orig_image = workspace.image_set.get_image(image_name,
                                                       must_be_grayscale=True)
            illum_image = workspace.image_set.get_image(illum_correct_function_image_name,
                                                        must_be_grayscale=True)
            corrected_image = workspace.image_set.get_image(corrected_image_name)

            figure.subplot_imshow_grayscale(0, j, orig_image.pixel_data,
                                            "Original image: %s" % image_name)
            title = ("Illumination function: %s\nmin=%f, max=%f" %
                     (illum_correct_function_image_name,
                      round(illum_image.pixel_data.min(),4),
                      round(illum_image.pixel_data.max(),4)))

            figure.subplot_imshow_grayscale(1, j, illum_image.pixel_data, title)
            figure.subplot_imshow_grayscale(2, j, corrected_image.pixel_data,
                                            "Final image: %s" %
                                            corrected_image_name)

    def upgrade_settings(self, setting_values, variable_revision_number, 
                         module_name, from_matlab):
        """Adjust settings based on revision # of save file
        
        setting_values - sequence of string values as they appear in the
                         saved pipeline
        variable_revision_number - the variable revision number of the module
                                   at the time of saving
        module_name - the name of the module that did the saving
        from_matlab - True if saved in CP Matlab, False if saved in pyCP
        
        returns the updated setting_values, revision # and matlab flag
        """
        # No SVN records of revisions 1 & 2
        if from_matlab and variable_revision_number == 3:
            # Same order as pyCP
            from_matlab = False
            variable_revision_number = 1
        if not from_matlab and variable_revision_number == 1:
            # Added multiple settings, but, if you only had 1,
            # the order didn't change
            variable_revision_number = 2
        return setting_values, variable_revision_number, from_matlab

            
