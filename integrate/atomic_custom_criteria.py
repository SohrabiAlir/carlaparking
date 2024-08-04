import math
import numpy as np
import py_trees
import shapely.geometry

import carla
from agents.tools.misc import get_speed

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.timer import GameTime
from srunner.scenariomanager.traffic_events import TrafficEvent, TrafficEventType

from srunner.scenariomanager.scenarioatomics.atomic_criteria import Criterion

# ⚠️ This script belongs in: `scenario_runner-0.9.15 > srunner > scenariomanager > scenarioatomics > atomic_custom_criteria.py`
# Tested for scenario_runner-0.9.15

"""
    Custom extension for Scenario Runner.
    In order to use htis class, the modified `openscenario_parser.py` is required.
"""

class CustomFinallyInTargetArea(Criterion):

    """
    This custom class contains the test for checking whether the actor is finally i
    The test is a success if the actor is inside the specified region upon termination.

    Important parameters:
    - actor: CARLA actor to be used for this test
    - min_x, max_x, min_y, max_y: Bounding box of the checked region (all INCLUSIVE)
    """

    def __init__(self, actor, min_x, max_x, min_y, max_y, name="CustomFinallyInTargetArea"):
        """
        Setup trigger region (rectangle provided by [min_x,min_y] and [max_x,max_y]
        """
        super(CustomFinallyInTargetArea, self).__init__(name, actor)

        if not (min_x <= max_x and min_y <= max_y):
            print(f"Values: {min_x}, {max_x}, {min_y}, {max_y}")
            raise ValueError("Constraint min_x <= max_x and min_y <= max_y not fulfilled!")

        self._min_x = min_x
        self._max_x = max_x
        self._min_y = min_y
        self._max_y = max_y

        self.last_location = None
        self.success_value = 0
        self.actual_value = 1

    def update(self):
        """
        Check if the actor location is within trigger region
        """
        new_status = py_trees.common.Status.RUNNING

        location = CarlaDataProvider.get_location(self.actor)

        if location is not None:
            self.last_location = location
            self.test_status = "FAILURE"

        if self._terminate_on_failure and (self.test_status == "FAILURE"):
            new_status = py_trees.common.Status.FAILURE

        self.logger.debug("%s.update()[%s->%s]" % (self.__class__.__name__, self.status, new_status))
        
        print(f"End update for {self.name}!")

        return new_status

    def terminate(self, new_status):
        """
        Set final status
        """
        if self._in_region():
            self.test_status = "SUCCESS" 
            new_status = py_trees.common.Status.SUCCESS
            self.actual_value = 0
        else:
            self.actual_value = 1
            self.test_status == "FAILURE"
            new_status = py_trees.common.Status.FAILURE
            
        super(CustomFinallyInTargetArea, self).terminate(new_status)

    def _in_region(self) -> bool:
        return self.last_location.x >= self._min_x \
           and self.last_location.x <= self._max_x \
           and self.last_location.y >= self._min_y \
           and self.last_location.y <= self._max_y