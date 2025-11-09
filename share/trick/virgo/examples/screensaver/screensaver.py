#!/usr/bin/env python3.11
import numpy as np
import datetime

import sys, os, argparse, yaml, inspect
# Add location of VIRGO code to sys.path so we can import classes
thisFileDir = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0)))
sys.path.append(os.path.abspath(os.path.join(thisFileDir, '../../')))
# Import the only VIRGO class we need
from Virgo import VirgoScene, VirgoControlCenter
from VirgoLabel import VirgoLabel

parser = argparse.ArgumentParser(description=
        'Start up a VIRGO-based screensaver',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
parser.add_argument("--scene-config", help="YAML config file to load",
                    default=os.path.join(thisFileDir,'scene.yml'))
args = parser.parse_args()


class VirgoScreenSaverControlCenter(VirgoControlCenter):
    def __init__(self, renderers, render_window, interactor, scene,
                 world_time=0.0, images_dir=None):
        super().__init__(renderers=renderers, render_window=render_window,
                         interactor=interactor, scene=scene)
        self.rotation_speed = 0.05
        self.text_actors = {}
        self.text_actors['thetime'] = self.create_overlay_text_actor()
        self.text_actors['thetime'].GetTextProperty().SetFontFamilyToArial()
        self.text_actors['thetime'].GetTextProperty().SetBold(1)
        self.text_actors['thetime'].GetTextProperty().SetFontSize(50)
        self.text_actors['thetime'].GetTextProperty().SetColor(0.6, 0.0, 0.0)
        self.text_actors['weather'] = self.create_overlay_text_actor()
        self.text_actors['weather'].GetTextProperty().SetFontFamilyToArial()
        self.text_actors['weather'].GetTextProperty().SetFontSize(50)
        self.text_actors['weather'].GetTextProperty().SetColor(0.5, 0.5, 0.5)
        self.text_actors['weather'].GetTextProperty().SetBold(1)
        

    def on_key_press(self, caller, event):
        """
        Overrides base class to provide limited key press functionality
        """
        key = self.interactor.GetKeySym()
        print(f'DEBUG: Key pressed: {key}')
        if key == 'a':
            # Turn actor axes on/off
            self.toggle_axes()
        if key == "V":
            # Verbosely print state of all non-text actors
            for n in self.nodes:
                # Call report() on root nodes only since they recurse
                if self.nodes[n].parent == None:
                    self.nodes[n].report()
        if key == "c":
            self.camera_report()
        if key == 'l':
            # Turn actor axes on/off
            self.toggle_lighting_modes()
        if key == 'equal':
            self.fontsize('up')
        if key == 'minus':
            pass
            self.fontsize('down')
        if key == "space":
            self.handle_pause_button()

    def handle_pause_button(self):
        """
        If paused, go to playing. If playing, go to paused.
        """
        if self.mode == 'PAUSED':
            self.mode = 'PLAYING'
        else:
            self.mode = 'PAUSED'

    def initialize(self):
        """
        Overrides base class to add additional customizations at init
        """
        super().initialize()
        for n in self.nodes:
            self.nodes[n].show_labels()
            # Force all labels to be bright regardless of lighting mode
            for l in self.nodes[n].labels:
                self.nodes[n].labels[l].label_follower.GetProperty().SetAmbient(1.0)
        self.weather = self.get_weather()

    def get_weather(self):
        import requests
        import json
        
        # Your API key from OpenWeatherMap
        API_KEY = '5b3da7d3c5d7003bec78b3a2f20bf711'
        
        # --- Get Weather by Zip Code ---
        zip_code = '77573' # Example: Beverly Hills, CA
        country_code = 'US'
        units = 'imperial' # 'imperial' for F, 'metric' for C
        
        # Construct the API URL
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        url = f"{base_url}?zip={zip_code},{country_code}&appid={API_KEY}&units={units}"
        
        try:
            # Make the API request
            response = requests.get(url)
            response.raise_for_status() # Raises an error for bad responses (4xx or 5xx)
        
            # Parse the JSON response
            data = response.json()
        
            # Extract the relevant weather data
            main_weather = data['weather'][0]['main']
            description = data['weather'][0]['description']
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            city_name = data['name']
        
            ret_str = (f"""{description} in {city_name.lower()}
{temp}°F @ {humidity} % humidity
      wind @ {wind_speed} mph""")
            return (ret_str)
        
        except requests.exceptions.HTTPError as err:
            if response.status_code == 404:
                print(f"Error: Could not find weather for zip code {zip_code}")
            else:
                print(f"HTTP error occurred: {err}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def display_weather(self):
        self.text_actors['weather'].SetInput(self.weather)
        hud_padding = 20 # pixels
        window_width, window_height  = self.render_window.GetSize()
        bounds = [0] * 4 # Get the text bounding box in display coordinates  [xmin, xmax, ymin, ymax]
        self.text_actors['weather'].GetBoundingBox(self.renderers['foreground'], bounds)
        text_width = bounds[1] - bounds[0] + 1  # Width in pixels
        text_height = bounds[3] - bounds[2] + 1  # Height in pixels
        # Calculate position for bottom-right corner with padding
        x_pos = (window_width/2.0 - text_width/2.0)  # Right edge minus width
        #y_pos = window_height - text_height - hud_padding  # Bottom edge (20 pixels from bottom)
        #y_pos = text_height + hud_padding  # Bottom edge (20 pixels from bottom)
        y_pos = hud_padding  # Bottom edge (20 pixels from bottom)
        #print(f"x:{x_pos}, y:{y_pos}")
        self.text_actors['weather'].SetPosition(x_pos, y_pos)

    def display_time(self):
        now = datetime.datetime.now()
        # Choose any format you like
        time_str = now.strftime("%I:%M %p")     # 12-h with AM/PM
        date_str = datetime.date.today()
        self.text_actors['thetime'].SetInput(f"{date_str}   {time_str}")
        # Position thetime in the HUD
        hud_padding = 20 # pixels
        window_width, window_height  = self.render_window.GetSize()
        bounds = [0] * 4 # Get the text bounding box in display coordinates  [xmin, xmax, ymin, ymax]
        self.text_actors['thetime'].GetBoundingBox(self.renderers['foreground'], bounds)
        text_width = bounds[1] - bounds[0] + 1  # Width in pixels
        text_height = bounds[3] - bounds[2] + 1  # Height in pixels
        # Calculate position for bottom-right corner with padding
        x_pos = (window_width/2.0 - text_width/2.0)  # Right edge minus width
        y_pos = window_height - text_height - hud_padding  # Bottom edge (20 pixels from bottom)
        self.text_actors['thetime'].SetPosition(x_pos, y_pos)

    def move_camera(self):
        # Rotate the camera each frame for coolness
        self.cameras['foreground'].Azimuth(self.rotation_speed)
        self.cameras['foreground'].SetFocalPoint(0, 0, 0)

    def update_scene(self):
        self.display_time()
        self.display_weather()
        if self.mode == 'PLAYING':
            self.update_nodes()
            self.move_camera()
        # Auto-adjust clipping range
        self.renderers['foreground'].ResetCameraClippingRange()


class VirgoScreenSaver(VirgoScene):
    """
    TBD
    """
    def __init__(self, scene, verbosity=2):
        super().__init__(scene=scene, verbosity=verbosity)
        self.controller = VirgoScreenSaverControlCenter(
            renderers=self.renderers, render_window=self.render_window,
            interactor=self.interactor, scene=self.scene)

    def initialize(self):
        super().initialize()
class MyScreenSaver:
    def __init__(self):
        with open(args.scene_config) as file:
            scene = yaml.safe_load(file) 
        # VirgoDataPlayback is the VirgoScene we want because it's built
        # to consume TrickPy-compatible data, which log_Satellite.csv meets
        self.v = VirgoScreenSaver(scene=scene)
        self.v.initialize()

    def execute(self):
        # Start the Virgo 3D scene
        return(self.v.run())

if __name__ == '__main__':
    sys.exit(MyScreenSaver().execute())