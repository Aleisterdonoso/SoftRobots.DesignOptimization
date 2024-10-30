# -*- coding: utf-8 -*-
"""Base config class to reimplement for each model"""

__authors__ = "tnavez"
__contact__ = "tanguy.navez@inria.fr"
__version__ = "1.0.0"
__copyright__ = "(c) 2020, Inria"
__date__ = "Oct 28 2022"

import os
import multiprocessing
import time

class BaseConfig(object):

    def __init__(self, model_name):
        """
        Classical initialization of a python class.
        """

        # Script names
        self.model_name = model_name
        self.scene_name = model_name + ".py"
        self.design_generation_name = "Generation"

        # Design variables
        self.init_model_parameters()
        self.design_variables = self.get_design_variables()

        # Objectives
        self.currently_assessed_objectives = []

        # Multithreading feature
        self.in_optimization_loop = False
        self.base_meshes_path = os.path.dirname(os.path.abspath(__file__)) + '/' + model_name + '/Meshes/'
        self.meshes_path = self.base_meshes_path

    def get_scene_name(self):
        """
        Return the name of the model SOFA simulation scene
        ----------
        Outputs
        ----------
        name : str
            Name of the SOFA scene
        """
        return self.scene_name

    def get_design_generation_script_name(self):
        """
        Return the name of the design generation script
        ----------
        Outputs
        ----------
        name : str
            Name of the design generation script
        """
        return self.design_generation_name

    @staticmethod
    def init_model_parameters(self):
        """
        This function implement initialization of model parameters
        """
        return None
    

    ########################################################
    ###### Functions for managign Design Optimization ######
    ########################################################
    @staticmethod
    def get_design_variables(self):
        """
        Return a dictionnary of triplets {name: [value, minValue, maxValue]} for each design variable.
        ----------
        Outputs
        ----------
        name : str
            Name of the design variable.
        value : float
            Value for the design variable.
        minValue : float
            Minimum value for the design variable.
        maxValue : float
            Maximum value for the design variable.
        """
        return None

    def set_design_variables(self, new_values): 
        """
        Set new values for design variables
        ----------
        Inputs
        ----------
        new_values: list of duets [name, value] for each design variable
            New value for each design variables
        """
        for var in new_values:
            if var[1] >= self.get_design_variables()[var[0]][1] and var[1] <= self.get_design_variables()[var[0]][2]:
                setattr(self, var[0], var[1])    
            else:
                print("Error: assigned new value for design variable are out of bounds.")

    @staticmethod
    def get_objective_data(self):
        """
        Return a dict of duets {objective_name: [direction, n_dt]} for each implemented fitness function
        ----------
        Outputs
        ----------
        objective_name: str
            Name of the fitness function
        direction: str in {"minimize", "maximize"}
            Direction for objective optimization
        n_dt: int
            Number of dt steps for the evaluation of the objective
        """
        return None

    @staticmethod
    def get_assessed_together_objectives(self):
        """
        Return objectives that are assessed together.
        Objectives can be assessed successively on different tasks or at the same time on the same task.
        ----------
        Outputs
        ----------
        assessed_together_objectives: list of list of string
            List of objectives assessed at the same time
        """
        return None

    def get_currently_assessed_objectives(self):
        """
        Return the currently assessed fitness function(s)
        ----------
        Outputs
        ----------
        currently_assessed_objectives: list of string
            List of currently assessed objectives  
        """
        return self.currently_assessed_objectives
    
    def set_currently_assessed_objectives(self, new_objectives):
        """
        Set the next fitness function(s) to assess
        ----------
        Inputs
        ----------
        new_objectives: list of string
            List of next objective(s) to assess
        """
        self.currently_assessed_objectives = new_objectives


#######################################################################
###### Functions for managing Design Optimization Multithreading ######
#######################################################################
# An adaptation of the xshape library from Damien Marchal: https://github.com/SofaDefrost/xshape
import gmsh
import tempfile
import hashlib
import shutil

class GmshDesignOptimization(BaseConfig):
    def __init__(self, model_name):
        super(BaseConfig,self).__init__(model_name)

    #@staticmethod
    def set_cache_mode(self, in_optimization_loop):
        """
        Set the cache mode i.e. the folder in which we save results.
        ----------
        Inputs
        ----------
        in_optimization_loop: boolean
            Specify if we are in a design optimization loop or not.
        """
        if in_optimization_loop:
            self.in_optimization_loop = True
            self.meshes_path = self.base_meshes_path + "/Cache/"
        else:
            self.in_optimization_loop = False
            self.meshes_path = self.base_meshes_path

    #@staticmethod
    def manage_temporary_directories(self):
        """
        Check if the cache directories need to be emptied.
        """
        # Create mesh directory if not already done
        if not os.path.exists(self.base_meshes_path):
            print("Creating the {0} directory".format(self.base_meshes_path))
            os.mkdir(self.base_meshes_path)            

        # Crate cache directory if not already done
        if not os.path.exists(self.base_meshes_path + "/Cache/"):
            print("Creating the {0} directory to cache mesh generation data".format(self.base_meshes_path + "/Cache/"))
            os.mkdir(self.base_meshes_path + "/Cache/")      

        # Check that the Cache directory is not too big
        size = 0
        file = 0
        for ele in os.scandir(self.base_meshes_path + "/Cache/"):
            size+=os.path.getsize(ele)
            file+=1
        size = size/(1024*1024)
        if size > 1000:
            print("Temporary directory is in: "+self.base_meshes_path + "/Cache/")
            print("                     file: "+str(file))
            print("                     size: "+str(int(size))+" Mb")
            print("The cache directory is too big...  please consider cleaning")

    #@staticmethod
    def get_unique_filename(self, generating_function):
        """
        Get the unique name of a geometry using hashmap.
        ----------
        Inputs
        ----------
        generating_function: func
            Link to the gmsh generating function.
        ----------
        Outputs
        ----------
        hashed_name: string
            An unique hashed name for the generated geometry.
        """
        # gmsh.fltk.run()
        temporary_file = tempfile.NamedTemporaryFile(suffix='.geo_unrolled')
        temporary_file.close()
        gmsh.write(temporary_file.name)
        result = hashlib.md5(open(temporary_file.name).read().encode())

        md5digest=result.hexdigest()

        return generating_function.__name__+ "_" + md5digest

    #@staticmethod
    def get_mesh_filename(self, mode, refine, generating_function, **kwargs):
        """
        Get the full hashed name of a mesh.
        ----------
        Inputs
        ----------
        mode: string in {Surface, Volume}
            Mesh file mode.
        refine: int
            Indicate how many time we should refine the mesh
        generating_function: func
            Link to the gmsh generating function.
        
        **kwargs: args
            Arguments for the mesh generation.
        ----------
        Outputs
        ----------
        full_filename: string
            The full path to the generated mesh.
        """
        
        # Main function
        def _get_mesh_filename(mode, refine, generating_function, **kwargs):
            self.manage_temporary_directories()
            gmsh.initialize()
            # Silence gmsh so by default nothing is printed
            gmsh.option.setNumber("General.Terminal", 0)
            id = generating_function(**kwargs)            
            # id = self.run_with_timeout(generating_function, kwargs, 15)
            gmsh.model.occ.synchronize()            
            filename = self.get_unique_filename(generating_function)
            if mode == "Step":
                full_filename = os.path.join(self.meshes_path, filename+".step") 
            elif mode == "Surface":
                full_filename = os.path.join(self.meshes_path, filename+"_surface.stl")   
            elif mode == "Volume":
                
                full_filename = os.path.join(self.meshes_path, filename+"_volume.vtk") 
            if not os.path.exists(full_filename):
                # When we are generating the mesh, it is better to know something is happening so let's reactive the printed messages
                gmsh.option.setNumber("General.Terminal", 1)
                if mode == "Surface":
                    gmsh.model.mesh.generate(2)
                elif mode == "Volume":
                    
                    gmsh.model.mesh.generate(3)
                if refine:
                    gmsh.model.mesh.refine()
                gmsh.write(full_filename)
            gmsh.finalize()
            return full_filename

        # Cancel the process if it takes too much time #VERLOOOOOO
        args = {
            "mode": mode,
            "refine": refine,
            "generating_function": generating_function,
        }
        combined_args = {**args, **kwargs}
        return self.run_with_timeout(_get_mesh_filename, combined_args, 10)

    
    def save(self, source_filename, as_filename):
        """
        Save a gmsh geometry in a file with a known filename.
        ----------
        Inputs
        ----------
        source_filename: string
            Path to the source filename. 
            A good use is here to provide the result of get_mesh_filename as input.
        as_filename: string
            Path to the copied file name.
        """
        return shutil.copy(source_filename, as_filename)
    
    def show(self, generating_function, **kwargs):
        """
        Show a generated gmsh geoemtry. 
        Usefull for debuguing.
        ----------
        Inputs
        ----------
        generating_function: func
            Link to the gmsh generating function.
        as_filename: string
            Path to the copied file name.
        """
        self.manage_temporary_directories()
        gmsh.initialize()
        # Silence gmsh so by default nothing is printed
        gmsh.option.setNumber("General.Terminal", 0)
        id = generating_function(**kwargs)
        gmsh.model.occ.synchronize()
        gmsh.fltk.run()
        gmsh.finalize()

    #@staticmethod
    def run_with_timeout(self, target_func, args, timeout): #VERLOOOOOOO
        """
        Run a specified function and return an error if it takes too much time.
        ----------
        Inputs
        ----------
        target_func: func
            The target function to monitor.
        args: dict
            Arguments for calling function target_func.
        timeout: int
            Maximum delay time.
        """        
        result_queue = multiprocessing.Queue()
        
        def target_with_result(queue):
            result = target_func(**args)
            queue.put(result)
        
        process = multiprocessing.Process(target = target_with_result, args = (result_queue,))
        process.start()
        process.join(timeout)
        
        # Limited time has been overcomed
        if process.is_alive():
            process.terminate()
            process.join()
            print("Shape generation takes too much time. The process is terminated.")
            raise Exception 
        else:
            result = result_queue.get()
            print("Shape generation went well.")
            return result
        