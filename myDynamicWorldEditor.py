#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Authors: <Alireza Sohrabi> and <Martin Liam Plank>
# Context: Project <Testing of Autonomous Parking> @ IAIK 2024

"""
    Version 1.1: Configuration script for multiple purposes, such as ...
        - printing the spectator current view position and rotation
        - setting up defined world environments
        - removing existing actors / pedestrians from the world
        - loading a map

    Important Notes:
        - The "_Opt" map enable map layering, which is used for removing already parked vehicles.
        - No setup for Town15 as it is not layered

    Args:
        --setup-town04opt
            -> Loads "Town04_Opt"
            -> Removes already parked vehicle (by removing the corresp. map layer)
            -> Set specatator view above parking space
         
        --load XXX (where XXX is the map name in CARLA, i.e. "Town01", "Town01_Opt", ...)
            -> Loads the corresponding map
            -> Does NOT perform anything else (spectator, layer removement, ...)
            -> Consider using the --setup-XXX method for performing a sequence of setup steps

        --remove-all-vehicles
            -> Simply removes all existing actor vehicles from the map
            -> Note: Does not do anything with traffic manager, behavioured car might lead to bug!

        --remove-all-pedestrians
            -> Removes all actors (of type WalkingControllers + Walker) from the map

        --remove-all-cones
            -> Removes all static assets that are (in context of this script!!!) considered 'cones'.

        --remove-last-actor
            -> Removes the last actor that was added. If no actor was added, undefined behaviour might occur.

        --spawn-cone-XXX x,y,z,yaw (where XXX is in {1, 2, 3, 4, 5})
            -> Spawns a static assert at the given position with the given rotation
            -> Though the name is 'cone', it might be not an actual cone (but semantically similar!)
"""
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

# ---------------------------------------------------------------------------------------------------------------------

def removeAllVehicles(client: carla.Client, world: carla.World):
    print("Removing all vehicles ...")
    all_actors = world.get_actors()
    batch = [carla.command.DestroyActor(actor.id) for actor in all_actors if 'vehicle.' in actor.type_id]
    client.apply_batch_sync(batch, False)

# ---------------------------------------------------------------------------------------------------------------------

def removeAllPedestrians(client: carla.Client, world: carla.World):
    print("Removing all (walking and non walking) pedestrians ...")

    all_actors = world.get_actors()

    # Stop all walker controllers
    walker_controllers = [actor for actor in all_actors if 'controller.ai.walker' in actor.type_id]
    for walk_controller in walker_controllers:
        walker_controllers.stop()

    # Remove first walker controller, then corresp. walker actor
    batch = [ walker_controller.id for walker_controller in walker_controllers ]
    batch.extend([carla.command.DestroyActor(actor.id) for actor in all_actors if 'walker.' in actor.type_id])
    client.apply_batch_sync(batch, False)

# ---------------------------------------------------------------------------------------------------------------------

def removeAllCones(client: carla.Client, world: carla.World):
    print("Removing all static assert cones ...")

    all_actors = world.get_actors()

    cone_types = [
        "static.prop.trafficcone01", 
        "static.prop.trafficcone02", 
        "static.prop.constructioncone", 
        "static.prop.trafficwarning", 
        "static.prop.warningconstruction"
    ]

    batch = [ carla.command.DestroyActor(actor.id) for actor in all_actors if actor.type_id in cone_types ]
    client.apply_batch_sync(batch, False)

# ---------------------------------------------------------------------------------------------------------------------

def removeLastActor(client: carla.Client, world: carla.World):
    print("About to remove last added actor ...")

    all_actors = world.get_actors()
    all_actors_sorted_asc = sorted(all_actors, key=lambda actor: actor.id)

    batch = [ carla.command.DestroyActor(all_actors_sorted_asc[-1]) ]
    client.apply_batch_sync(batch, False)

# ---------------------------------------------------------------------------------------------------------------------

def spawnCone(client: carla.Client, bp_lib: carla.BlueprintLibrary, cone_type: int, args):
    print(f"About to spawn static asset ...")

    arg_split = args.split(',')

    if (len(arg_split) != 4):
        raise ValueError("Invalid Usage of --spawn-cone: Use X,Y,Z,YAW as param value!")

    x, y, z, yaw = float(arg_split[0]), float(arg_split[1]), float(arg_split[2]), float(arg_split[3])

    if cone_type == 1:
        type_id = 'static.prop.trafficcone01'
    elif cone_type == 2:
        type_id = 'static.prop.trafficcone02'
    elif cone_type == 3:
        type_id = 'static.prop.constructioncone'
    elif cone_type == 4:
        type_id = 'static.prop.trafficwarning'
    elif cone_type == 5:
        type_id = 'static.prop.warningconstruction'
    else:
        raise ValueError("Invalid Use for traffic cone!")

    traffic_cone_bp = bp_lib.find(type_id)

    spawn_point = carla.Transform(
        carla.Location(x=x, y=y, z=z),
        carla.Rotation(pitch=0, yaw=yaw, roll=0)
    )

    batch = [ carla.command.SpawnActor(traffic_cone_bp, spawn_point) ]
    client.apply_batch_sync(batch,False)

# ---------------------------------------------------------------------------------------------------------------------

def town04Setup(client: carla.Client, 
                world: carla.World, 
                settings: carla.WorldSettings, 
                bp_lib: carla.BlueprintLibrary, 
                spectator: carla.Actor):
    print("About to setup Town04_Opt (without parked vehicles, with default spectator above parking space) ...")

    # Load world and remove existing parked vehicles
    world = client.load_world("Town04_Opt") 
    world.unload_map_layer(carla.MapLayer().ParkedVehicles)

    # Reassignments (IMPORTANT: load_world() recreates .world object =>  prior .world() members will be outdated)
    settings = world.get_settings()
    bp_lib = world.get_blueprint_library()
    spectator = world.get_spectator()

    # Set spectator view to parking space 
    transform = carla.Transform()
    transform.location = carla.Location(x=283.127258, y=-167.923187, z=17.841476)
    transform.rotation = carla.Rotation(pitch=-26.895767, yaw=-86.895027, roll=0.000022)
    spectator.set_transform(transform)

# ---------------------------------------------------------------------------------------------------------------------

def loadWorld(client: carla.Client, 
              world: carla.World, 
              settings: carla.WorldSettings, 
              bp_lib: carla.BlueprintLibrary, 
              spectator: carla.Actor, 
              request_world_name: str):
    print(f"About to load requested world {request_world_name}...")

    # Load map name and throw away path (i.e. '/Game/Carla/Maps/Town06' => 'Town06')
    maps_available = [ entry.split("/")[-1] for entry in client.get_available_maps() ] 

    # Check if request map exists
    if (request_world_name not in maps_available):
        raise ValueError(f"Map <{requested_world_name}> does not exist. Please choose one of {maps_available}!")
    
    # Actually load requested world
    world = client.load_world(request_world_name)

    # Reassignments (IMPORTANT: load_world() recreates .world object =>  prior .world() members will be outdated)
    settings = world.get_settings()
    bp_lib = world.get_blueprint_library()
    spectator = world.get_spectator()

# ---------------------------------------------------------------------------------------------------------------------

def main():
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        '-st04', '--setup-town04opt',
        action='store_true',
        help='Loads the predefined settings for the Town04_Opt setup.'
    )
    argparser.add_argument(
        '-t', '--load',
        type=str,
        help='Loads a CARLA map, i.e. `--load Town04_Opt` loads the corresponding map.'
    )
    argparser.add_argument(
        '-rv', '--remove-all-vehicles',
        action='store_true',
        help='Removes all vehicle actors from the world (will not affected static assets!).'
    )
    argparser.add_argument(
        '-rp', '--remove-all-pedestrians',
        action='store_true',
        help='Removes all Walker + WalkerController actors from the world (will not affect static assets!).'
    )
    argparser.add_argument(
        '-rl', '--remove-last-actor',
        action='store_true',
        help='Removes the last actor. If you added one, it\'s the previously added. Otherwise Undefined Behaviour!'
    )
    argparser.add_argument(
        '-rc', '--remove-all-cones',
        action='store_true',
        help='Removes all static assets that are considered "cones".'
    )
    argparser.add_argument(
        '-sc1', '--spawn-cone-1',
        type=str,
        default=None,
        help='Spawns a cone (static asset). Usage: --spawn-cone-1 X,Y,Z,YAW'
    )
    argparser.add_argument(
        '-sc2', '--spawn-cone-2',
        type=str,
        default=None,
        help='Spawns a cone (static asset). Usage: --spawn-cone-2 X,Y,Z,YAW'
    )
    argparser.add_argument(
        '-sc3', '--spawn-cone-3',
        type=str,
        default=None,
        help='Spawns a cone (static asset). Usage: --spawn-cone-3 X,Y,Z,YAW'
    )
    argparser.add_argument(
        '-sc4', '--spawn-cone-4',
        type=str,
        default=None,
        help='Spawns a cone (static asset). Usage: --spawn-cone-4 X,Y,Z,YAW'
    )
    argparser.add_argument(
        '-sc5', '--spawn-cone-5',
        type=str,
        default=None,
        help='Spawns a cone (static asset). Usage: --spawn-cone-5 X,Y,Z,YAW'
    )

    args = argparser.parse_args()

    actor_list = []

    try:
        # 1. setup

        client = carla.Client('localhost', 2000)
        client.set_timeout(200.0)
        
        # 2. object variables 

        world: carla.World             = client.get_world()
        settings: carla.WorldSettings  = world.get_settings()
        bp_lib: carla.BlueprintLibrary = world.get_blueprint_library()
        spectator: carla.Actor         = world.get_spectator()

        # 3. peform tasks 

        print(f"Current View: {spectator.get_transform()}")

        if (args.setup_town04opt):
            town04Setup(client=client, world=world, settings=settings, bp_lib=bp_lib, spectator=spectator)
        
        if (args.load):
            loadWorld(client=client, 
                      world=world, 
                      settings=settings, 
                      bp_lib=bp_lib, 
                      spectator=spectator, 
                      request_world_name=args.load)

        if (args.remove_all_vehicles):
            removeAllVehicles(client=client, world=world)

        if (args.remove_all_pedestrians):
            removeAllPedestrians(client=client, world=world)

        if (args.remove_all_cones):
            removeAllCones(client=client, world=world)

        if (args.remove_last_actor):
            removeLastActor(client=client, world=world)

        if (args.spawn_cone_1 is not None):
            spawnCone(client=client, bp_lib=bp_lib, cone_type=1, args=args.spawn_cone_1)
        
        if (args.spawn_cone_2 is not None):
            spawnCone(client=client, bp_lib=bp_lib, cone_type=2, args=args.spawn_cone_2)
        
        if (args.spawn_cone_3 is not None):
            spawnCone(client=client, bp_lib=bp_lib, cone_type=3, args=args.spawn_cone_3)
        
        if (args.spawn_cone_4 is not None):
            spawnCone(client=client, bp_lib=bp_lib, cone_type=4, args=args.spawn_cone_4)

        if (args.spawn_cone_5 is not None):
            spawnCone(client=client, bp_lib=bp_lib, cone_type=5, args=args.spawn_cone_5)
    
        # TODO: Weather setup ?

        # 4. wait a tick just in case (not stricly necessary)

        world.wait_for_tick()

    except BaseException as e:
        print(f"{e}")

    finally:
        print('All done, bye~')
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        sys.exit(0)

# ---------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()

# ---------------------------------------------------------------------------------------------------------------------
