"""
Cylone
(c) 2017 Bastian Mäuser
based on SolidColor (c) 2016 Simon Leiner
licensed under the GNU Public License, version 2
"""

import itertools

from helpers.color import blend_whole_strip_to_color,linear_dim
from lightshows.templates.colorcycle import *
from helpers.preprocessors import list_to_tuple
from lightshows.templates.base import *
import math

logger = logging.getLogger('102shows.server.mqttcontrol.cylone')

class Cylone(ColorCycle):
    """
    The whole strip is in Big Knightrider or Cylone Ship Style.

    Parameters:
       =====================================================================
       ||                     ||    python     ||   JSON representation   ||
       ||       color:        ||   3x1 tuple   ||       3x1 array         ||
       ||       highlight:    ||   3x1 tuple   ||       3x1 array         ||
       ||       radius:       ||   1 integer   ||       1 integer         ||
       =====================================================================
    """

    def init_parameters(self):
        super().init_parameters()
        self.set_parameter('num_steps_per_cycle', self.strip.num_leds)
        self.register('color', None, verify.rgb_color_tuple, preprocessor=list_to_tuple)
        self.register('highlight', None, verify.rgb_color_tuple, preprocessor=list_to_tuple)
        self.register('radius', 1, verify.not_negative_numeric)

        #local stuff
        self.dir = 0
        self.cpixel = 0
        self.centerdistance = 0
        self.waitmodifier = 0
        self.velocity = 5 # TODO

    def check_runnable(self):
        if self.p['color'] is None:
            raise InvalidParameters.missing('color')
        if self.p['highlight'] is None:
            raise InvalidParameters.missing('highlight')
        if self.p['radius'] is None:
            raise InvalidParameters.missing('radius')


    def before_start(self):
        pass

    def expospeed(self,x):
        #Expo festlegen (funktion: y=a(b^x)+c)
        a=0.3
        b=1.03
        c=-0.2
        y = (a*(b**x)+c)
        return y

    def update(self, current_step: int, current_cycle: int) -> bool:
        if current_cycle==0 and current_step==0:
            blend_whole_strip_to_color(self.strip, self.p['color'])
        self.dir = (current_cycle%2)
        pixel_color = self.p['color']
        highlight_color = self.p['highlight']
        if self.dir == 0:
            self.cpixel = current_step
        else:
            self.cpixel = (self.strip.num_leds-current_step)
        self.centerdistance = abs((self.strip.num_leds/2) - self.cpixel)
        self.waitmodifier = self.expospeed(self.centerdistance)

        #Paint Wurst
        for led in range(self.cpixel-(self.p['radius']//2), self.cpixel+(self.p['radius']//2)+1):
            distance = abs(led - self.cpixel)
            dim_factor = (1 - (distance / self.p['radius'])) ** 2
            color = linear_dim(highlight_color, dim_factor)
            self.strip.set_pixel(led, *color)

        #Clean Up b4 and after Wurst
        if current_step > 0 and current_step < self.strip.num_leds: #Cleanup
            if self.dir == 0:
                self.strip.set_pixel(self.cpixel-(self.p['radius']//2)-1,*pixel_color)
            else:
                self.strip.set_pixel(self.cpixel+(self.p['radius']//2)+2,*pixel_color)
        #Velocity applied TBD dynamically through MQTT
        self.sleep(0.1*self.waitmodifier)
        return True
