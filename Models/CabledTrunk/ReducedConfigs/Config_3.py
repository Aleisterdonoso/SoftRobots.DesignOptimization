# -*- coding: utf-8 -*-
"""Reduced config for the Cabled Trunk
A big problem for investigating if a shape can be matched with cables everywhere.
"""

__authors__ = "tnavez"
__contact__ = "tanguy.navez@inria.fr"
__version__ = "1.0.0"
__copyright__ = "(c) 2020, Inria"
__date__ = "Jun 16 2023"


import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.absolute())+"/../")
sys.path.insert(0, str(pathlib.Path(__file__).parent.absolute()))

from Config import Config

import numpy as np 

class ReducedConfig(Config):

    def __init__(self):
        # TODO
        super().__init__()
        self.n_cables = 4
        self.n_short_cables = 4 * (self.n_modules - 4) 
        print("self.n_short_cables:", self.n_short_cables)
        
        self.end_each_short_cable = []
        for i in range(2, self.n_modules - 2):
            self.end_each_short_cable += [i, i, i, i]
        print("self.end_each_short_cable:", len(self.end_each_short_cable))

        self.init_cables()

    def get_objective_data(self):
        t = 40
        return {#"ShapeMatchingBigS": ["minimize", t]
                #"ShapeMatchingL": ["minimize", t]
                #"ShapeMatchingS": ["minimize", t]
                #"ShapeMatchingCircularObject": ["minimize", t]
                "ShapeMatchingCubicObject": ["minimize", t]
        }

    def get_assessed_together_objectives(self):
        #return [["ShapeMatchingBigS"]]
        #return [["ShapeMatchingL"]]
        #return [["ShapeMatchingS"]]
        #return [["ShapeMatchingCircularObject"]]
        return [["ShapeMatchingCubicObject"]]

    
    
