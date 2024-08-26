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
import pygame
import numpy as np

import random
import time
import argparse
import typing # bc py < 3.8

class ParkEntity(object):
    """
    Wrapper for an actor class (esepcially vehicle) that is able to show the bounding box verteces 
    and calculating the vertical distance between 2 entities.
    """

    def __init__(self, vehicle: carla.Actor):
        assert vehicle is not None and isinstance(vehicle, carla.Actor)
        self._vehicle = vehicle
    
    # -----------------------------------------------------------------------------------------------------------------

    def _getBoundingBoxWorldCoordinates(self) -> typing.List[carla.Location]:
        """
        Returns: 
            list[carla.Location]: The list of the vehicle's bounding box verteces world (= absolute) coordinates. 
        """
        # https://carla.readthedocs.io/en/latest/python_api/#carlaboundingbox
        # https://carla.readthedocs.io/en/stable/measurements/

        # carla.BoundingBox:         Description                                 Unit per entry
        #   .transform (Transform)   Transformation relativ to vehicle           
        #   .extend (Vector3D)       Radii dim of the bounding box (half-box).   m

        # carla.Transform:           Description        Unit per entry
        #   .location (Vector3D):    World location     m
        #   .rotation (Rotation3D):  Pitch,roll,yaw     degrees

        bounding_box: carla.BoundingBox = self._vehicle.bounding_box
        vehicle_transform: carla.Transform = self._vehicle.get_transform()

        world_vertices: typing.List[carla.Location] = bounding_box.get_world_vertices(vehicle_transform)
        
        return world_vertices

    # -----------------------------------------------------------------------------------------------------------------

    @staticmethod
    def shortestVerticalDistanceAlongXAxis(a: 'ParkEntity', b: 'ParkEntity') -> float: # bc py < 3.10: type annotation via forward references
        """
        Measures the vertical (y-) distance (along the x axis) of the bounding box in meters.
        This function assumes, that one parked entity completely y-dominates the other one (otherwise: ValueError). 

        Raises:
            ValueError: If none of the given object instances y-domaintes the other one. 

        Arguments:
            a (ParkEntity): Object instance of the parked entity.
            b (ParkEntity): Object instance of the other parked entity.

        Returns:
            float: The absolute vertical distance between both bounding box entities (z will be ignored) in meters (m).
        """
        bb_wloc_verteces_a: typing.List[carla.Location] = a._getBoundingBoxWorldCoordinates()
        bb_wloc_verteces_b: typing.List[carla.Location] = b._getBoundingBoxWorldCoordinates()

        # Sort y values in ascending order

        bb_wloc_verteces_a.sort(key=lambda loc: loc.y)
        bb_wloc_verteces_b.sort(key=lambda loc: loc.y)

        # Does one y entity y-dominate?

        a_y_dominates_b: bool = len([ loc for loc in bb_wloc_verteces_b if loc.y > bb_wloc_verteces_a[-1].y ]) == 0
        b_y_dominates_a: bool =  len([ loc for loc in bb_wloc_verteces_a if loc.y > bb_wloc_verteces_b[-1].y ]) == 0
        assert not (a_y_dominates_b and b_y_dominates_a)
        
        if not a_y_dominates_b and not b_y_dominates_a:
            raise ValueError("The metric only makes sense if a ParkedEntity y-dominates the other one!")
        
        # If a dominates b => Exchange a and b (s.t. b dominates a in y-dimension now)

        if a_y_dominates_b:
            bb_wloc_verteces_a, bb_wloc_verteces_b = bb_wloc_verteces_b, bb_wloc_verteces_a
            
        # P: Point with max y from A, Q: point with min y from B (see graphic visual in BoK)

        P: carla.Location = bb_wloc_verteces_a[-1]
        Q: carla.Location = bb_wloc_verteces_b[0]

        return Q.y - P.y

    # -----------------------------------------------------------------------------------------------------------------

    def getVehicleLength(self) -> float:
        """
        Returns:
            float The vehicle's bounding box length in meters (m).
        """
        # https://carla.readthedocs.io/en/latest/python_api/#carlaboundingbox

        return 2 * self._vehicle.bounding_box.extent.x

    # -----------------------------------------------------------------------------------------------------------------

    def getVehicleWidth(self) -> float:
        """
        Returns:
            float The vehicle's bounding box width in meters (m).
        """
        # https://carla.readthedocs.io/en/latest/python_api/#carlaboundingbox

        return 2 * self._vehicle.bounding_box.extent.y

    # -----------------------------------------------------------------------------------------------------------------

    def getVehicleHeight(self) -> float:
        """
        Returns: 
            float: The vehicle's bounding box height in meters (m).
        """
        # https://carla.readthedocs.io/en/latest/python_api/#carlaboundingbox

        return 2 * self._vehicle.bounding_box.extent.z

    # -----------------------------------------------------------------------------------------------------------------
    
    def applyParkingBrake(self) -> None:
        control = carla.VehicleControl()
        control.parking_brake = True

        self._vehicle.apply_control(control)

    # -----------------------------------------------------------------------------------------------------------------

    def releaseParkingBrake(self) -> None:
        control = carla.VehicleControl()
        control.parking_brake = False

        self._vehicle.apply_control(control)

# ---------------------------------------------------------------------------------------------------------------------

def selectVehicleActor(world: carla.World) -> carla.Actor:
    # List all selectable actors

    selectable_actors: typing.Dict[str, Actor] = {
        str(actor.id): actor
        for actor in world.get_actors() if actor.type_id.startswith("vehicle")
    }

    for actor_id, actor in selectable_actors.items():
        actor_loc = actor.get_location()
        print(f"[{actor_id}] ({actor.type_id}) @ ({actor_loc.x}, {actor_loc.y}, {actor_loc.z})")

    # Choose relevant actor to track 

    target_actor_id = str(int(input("Enter [ID] that should be tracked: ")))
    target_actor = selectable_actors[target_actor_id] or None

    if target_actor is None:
        raise ValueError("Given actor ID not found!")

    # Return found actor

    return target_actor

# ---------------------------------------------------------------------------------------------------------------------

def selectDiffVehicleActor(world: carla.World) -> carla.Actor:
    # List all selectable actors

    prior_actor_ids: typing.Set[int] = {
        actor.id
        for actor in world.get_actors() if actor.type_id.startswith("vehicle")
    }

    input("Enter [OK] after you spawned the entities that you want to select.")

    selectable_actors: typing.Dict[str, Actor] = {
        str(actor.id): actor
        for actor in world.get_actors() if actor.type_id.startswith("vehicle") and actor.id not in prior_actor_ids
    }

    for actor_id, actor in selectable_actors.items():
        actor_loc = actor.get_location()
        print(f"[{actor_id}] ({actor.type_id}) @ ({actor_loc.x}, {actor_loc.y}, {actor_loc.z})")

    # Choose relevant actor to track 

    target_actor_id = str(int(input("Enter [ID] that should be tracked: ")))
    target_actor = selectable_actors[target_actor_id] or None

    if target_actor is None:
        raise ValueError("Given actor ID not found!")

    # Return found actor

    return target_actor

# ---------------------------------------------------------------------------------------------------------------------

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '-l', '--diff',
        action='store_true',
        help='Information whether a given entity\'s BoundingBox should be drawn.'
    )
    argparser.add_argument(
        '-sb', '--show-boundingbox',
        action='store_true',
        help='Information whether a given entity\'s BoundingBox should be drawn.'
    )
    argparser.add_argument(
        '-sv', '--show-vehicle-size',
        action='store_true',
        help='Information whether a given entity\'s BoundingBox should be drawn.'
    )
    args = argparser.parse_args()

    # 1. Connect with server 

    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    
    world: carla.World = client.get_world()
    bp_lib: carla.BlueprintLibrary = world.get_blueprint_library()

    if (args.diff):
        a = ParkEntity(vehicle=selectDiffVehicleActor(world))
        b = ParkEntity(vehicle=selectVehicleActor(world))

        print(f"Difference: {ParkEntity.shortestVerticalDistanceAlongXAxis(a, b)} m")

    if (args.show_boundingbox):
        bb_vertec_wc: typing.List[carla.Location] = sorted(ParkEntity(vehicle=selectVehicleActor(world))._getBoundingBoxWorldCoordinates(), key=lambda loc: loc.y)

        for loc in bb_vertec_wc:
            print(f"Vertex: ({loc.x}, {loc.y}, {loc.z})")

    if (args.show_vehicle_size):
        selected = ParkEntity(vehicle=selectVehicleActor(world))
        print(f"Width: {selected.getVehicleWidth()} / Length: {selected.getVehicleLength()} / Height: {selected.getVehicleHeight()}")

    return

# ---------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()

