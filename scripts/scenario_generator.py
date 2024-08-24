import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import numpy as np # sampling

import random
import argparse
import typing # bc py < 3.8
import re
from entity_spawner import VehicleSpawner

class OSCXBuilder(object):
    LOG_MODE = True

    # ----------------------------------------------------------------------------------------------------------------

    @staticmethod
    def LOG(msg: str):
        """
        Function for logging (debugging purposes only).
        """
        if OSCXBuilder.LOG_MODE:
            print(msg)

    # ----------------------------------------------------------------------------------------------------------------

    def __init__(self, template_file_path: str, output_file_path: str, config: typing.Dict[str, float]):
        """
        Arguments:
            template_file_path (str): The path (incl. name and file type) of the already scenario template with the placeholders. 
            output_file_path (str): The path (incl. name and file type) of the file that will be created as output.
            config (dict[str, foat]): The dictionary, where each placeholder is the key with an assigned value. 

        Raises:
            ValueError: If not all template placeholders were resolved or any configuration does not match the template's palceholder.
            FileNotFoundError: If the specified template file does not exist.
            IsADirectoryError: If the specified template file / output file is a directory, but not a file.
            PermissionError: If there are insufficient permissions to open the template file / create the output file.
            OSError: For other issues related to file operations regarding template_file_path / output_file_path.
        """

        with open(template_file_path, 'r', encoding='utf-8') as file:
            xosc_template = file.read()
            OSCXBuilder.LOG(f"Read template file <{template_file_path}> successfully.") ##

        print(f"Hello: {xosc_template}")

        # Replace placeholder sections

        for key, value in config.items():

            if key in xosc_template:
                xosc_template = xosc_template.replace(key, str(value))
                OSCXBuilder.LOG(f"Replaced <{key}> successfully by <{value}>")  ##
            else:
                raise ValueError(f"The placeholder {key} was not found in the XML content.")

        # Sanity check: No {...} contained anymore ('?' makes it non-greedy)

        matches = re.findall(r"\{.*?\}", xosc_template) 
        
        if len(matches) != 0: 
            raise ValueError(f"Still unresolved placeholders found: {matches}")

        # Generate output oscx file

        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(xosc_template)
            OSCXBuilder.LOG(f"Successfully created <{output_file_path}> successfully.") ##

# =====================================================================================================================

class ParamConfigGeneratorTown04ParkIn(object):
    """
    Generator for a valid configuration param for the secenario "Town04ParkIn".
    => carlaparking/scenarios/Town04ParkIn
    
    Allows sampling of: 
        - proportion: How much the left vehicle contributes (the right vehicle contirbutes 100 - propA)
        - distance: How much both vehicle's bounding boxe inner verteces are vertical distanced. 
    and determining y coordinates for adjacent vehicle based on samples. 
    """

    def __init__(self):
        pass
    
    # ----------------------------------------------------------------------------------------------------------------

    def sample(self) -> typing.Dict[str, float]: 
        """"
        Samples distance and proportion and derives from that the y-coordinates for the adjacent vehicles.

        Returns:
            dict[str, float]:
                - The first element (key Y_VEHICLE_LEFT) contains the y-coordinate of the left vehicle.
                - the second element (key Y_VEHICLE_RIGHT) contains the y-coordinate of the right vehicle.
        """
        MIN_VAL_V_LEFT = -227.65918902158737185
        MAX_VAL_V_LEFT = -225.34593121767042815

        MIN_VAL_V_RIGHT = -233.84848965644836175
        MAX_VAL_V_RIGHT = -231.36835665702819825

        # Sample distance and proportion (indepedent from each other!)

        distance = self._sampleDistance()
        propLeft, propRight = self._sampleProportion()

        assert distance - 1.84552001953125 > 0
        assert 6.63861083984375 - distance > 0

        ## DEBUG 
        distance = 1.84552001953125
        propLeft = 50
        propRight = 50
        ##

        # Calculae coordinates [see BoK: Slide 131]

        y_max_L = MAX_VAL_V_LEFT
        y_max_R = MIN_VAL_V_RIGHT

        d_max = 6.63861083984375

        # Calculation Derivation (see BoK for Visualization)
        #
        # SAMPLED DATA: distance dS, proportion (propL, propR)
        # UNKNOWN:  dL, dR, y_cord_left, y_cord_right 
        # KNOWN: dMAX, YMaxL, YMaxR
        # 
        # Let dx := dA + dB
        #  => dMAX = ds + dx
        # <=> dMAX - ds = dx
        #
        # propL * dx = dL
        # propR * dx = dR
        #
        # y_max_L - dL = yL
        # y_max_R + dR = yR

        dx = d_max - distance
        print(dx)

        y_cord_left = y_max_L - (propLeft/100 * dx)
        y_cord_right = y_max_R + (propRight/100 * dx)

        print(y_cord_left)
        print(y_cord_right)

        # Sanity Check 

        assert y_cord_left  <= MAX_VAL_V_LEFT
        assert MIN_VAL_V_RIGHT <= y_cord_right

        # Return result

        result = {
            'Y_VEHICLE_LEFT' : y_cord_left,
            'Y_VEHICLE_RIGHT': y_cord_right
        }

        return result
    
    # ----------------------------------------------------------------------------------------------------------------

    def _sampleDistance(self) -> float:
        """
        Samples the distance from a normal gaussian distirbution (see distirbution.ipynb).

        Returns:
            float: Samples (clipped) distance that is in [3.957.., 6.63861..].
        """
        # Set limits for clipping

        MAX_VALUE_INCL = 6.63861083984375 - 0.00001
        MIN_VALUE_INCL = 3.9570465087890625 + 0.00001 

        clip_to_range_f = lambda value: max(MIN_VALUE_INCL, min(value, MAX_VALUE_INCL))

        # Distribution settings from distribution.ipynb

        mu = 4.541217239506213
        sigma = 0.6219224902786538

        # Sample according to distirbution.ipynb (and ensure that the RANGE is between MIN_VALUE, MAX_VALUE)

        distance = clip_to_range_f(np.random.normal(mu, sigma))

        # Sanity Check (AssertionError) to ensure correct configuration (avoid spawn conflict)

        assert MIN_VALUE_INCL <= distance <= MAX_VALUE_INCL 

        return distance 

    # ----------------------------------------------------------------------------------------------------------------

    def _sampleProportion(self) -> typing.Tuple[float, float]:
        """
        Samples a proportion of a normal gaussian distribution (see distribution.ipynb). 
        
        Returns:
            (float, float): Calculated (clipped) result based on the sampled propertion (according to distirbution.pynb). 
                - The first element is the proportion of the distance contribution of the left car (between 0 and 100).
                - the second element is the proportion of the distance contribution of the right car (between 0 and 100). 
        """
        # Set limits for clipping

        MAX_VALUE_INCL = 100
        MIN_VALUE_INCL = 0

        clip_to_range_f = lambda value: max(MIN_VALUE_INCL, min(value, MAX_VALUE_INCL))

        # Distribution settings from distribution.ipynb
        
        mu = 50
        sigma = 15

        # Sample according to distirbution.ipynb (and ensure that the RANGE is between MIN_VALUE, MAX_VALUE) 
        
        propLeft = clip_to_range_f(np.random.normal(mu, sigma))
        propRight = 100 - propLeft

        # Sanity Check (AssertionError) to ensure correct configuration (avoid spawn conflict)

        assert propLeft >= MIN_VALUE_INCL and propRight >= MIN_VALUE_INCL
        assert propLeft <= MAX_VALUE_INCL and propRight <= MAX_VALUE_INCL
        assert abs(propLeft + propRight - 100) < 0.1, "Must add up to 1"

        return (propLeft, propRight)

# =====================================================================================================================

class ParamConfigGeneratorTown04OppositeTraffic(object):
    
    def __init__(self):
        pass

    def sample(self) -> typing.Dict[str, float]:

        param_gap = np.random.normal(5.5, 3)
        param_bias = np.random.normal(0, 0.5)
        param_distance = np.random.uniform(0, 10)
        param_velocity = np.random.uniform(0.5, 10)

        dep_right_bias = -229 + param_bias + param_gap/2
        dep_left_bias = -229 + param_bias - param_gap/2
        dep_bike = -225 + param_distance

        return {
            '{Y_BIKE_START}': dep_bike,
            '{Y_LEFT_PARKED_CAR}': dep_left_bias,
            '{Y_RIGHT_PARKED_CAR}': dep_right_bias,
            '{MOVING_CAR_VELOCITY}': param_velocity
        }


# =====================================================================================================================

def main():

    ## ParkInTown04

    parked_cars_generator = VehicleSpawner()
    parked_vehicles: typing.Dict[str, str] = parked_cars_generator.generateXOSC(
        df=parked_cars_generator.readCSV(
            "../scenarios/ParkInTown04/ParkinSpaceConfiguration.csv"
        )
    )

    params: dict[str, float] = ParamConfigGeneratorTown04ParkIn().sample()

    OSCXBuilder(
        template_file_path="../scenarios/ParkInTown04/blueprint.xml", 
        output_file_path="../scenarios/ParkInTown04/output.xosc",
        config={
            "{DECL_PARKED_CARS}" : parked_vehicles["DECL_ENTITY"],
            "{INIT_PARKED_CARS}" : parked_vehicles["INIT_ENTITY"],
            "{Y_POSITION_CAR_LEFT}" : params["Y_VEHICLE_LEFT"],
            "{Y_POSITION_CAR_RIGHT}" : params["Y_VEHICLE_RIGHT"]
        }
    )

    ## OppositeTrafficParkInTown04

    params: dict[str, float] = ParamConfigGeneratorTown04OppositeTraffic().sample()

    OSCXBuilder(
        template_file_path="../scenarios/OpposingTrafficParkInTown04/blueprint.xml", 
        output_file_path="../scenarios/OpposingTrafficParkInTown04/output.xosc",
        config=params
    )

# =====================================================================================================================

if __name__ == '__main__':
    main()
