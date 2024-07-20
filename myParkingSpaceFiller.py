#!/usr/bin/env python

# Copyright (c) 2021 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Authors: <Alireza Sohrabi> and <Martin Liam Plank>
# Context: Project <Testing of Autonomous Parking> @ IAIK 2024

"""
    Version 1.0: Script for filling parking spaces by custom CSV. 
    REQUIRED: Already correctly set-up world (see myConfig.py)

    Description:
        - Script reads and parses CSV file, spawns vehicles according to the specified CSV within the parking lot.
        - As soon as the script is killed (CTRL + C), all spawned vehicles despawn.
        - The script does not change ANY world settings and affects the simulation by spawning / destorying actors.

    Important Notes:
        - A Parking Space Configuration file is ONLY related to the related SPECIFIC World Map!
        - Currently ONLY Town04_Opt is suported (!)

    Configurations Variables:
        - DEFAULT_YAWS: Collection of all possible default values if yaw is not specified in CSV file.
        - DEFAULT_CARS_BP: Collection of all possibel default values if vehicle_bp is not specified in CSV file.

    CSV Columns:
        - id (int): Internal unique identifier for CSV file (not used for CARLA)
        - row (int): Row of the parking spot (see Town04), only used for debugging
        - col (int): Column of the parking spot (see Town04), only used for debugging
        - x (flaot): x - coordinate, where vehicle sould spawn
        - y (float): y - coordinate, were vehicle should spawn
        - yaw (float|None): Value (between 0 and 180) that represends the car's xy- rotation
            -> None: A random value from DEFAULT_YAWS will be used 
            -> 0: Car faces in direction, where gas station is 
            -> 180: Car faces opposite direction of gas station
        - vehicle_bp (string|None): Blueprint for vehicle that should be spawned at given location
            -> None: A random blueprint of DEFAULT_CARS_BP will be used

    Hints for Usage
        - For letting a parking space "empty", simply delete the corresponding row in the CSV file. 
          No Other values needs to be adepted.
        - For intuitively identifying a specific parking slot, see TownXXParkingSpacePosition.png
"""

import glob
import os
import sys
import time

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import argparse
import typing # bc python < 3.8 :(
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------------------------------------------------
# global configuration 

DEFAULT_YAWS = [
    -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5,
    175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185
]

DEFAULT_CARS_BP = [
    "vehicle.audi.a2",
    "vehicle.audi.etron",
    "vehicle.audi.tt",
    "vehicle.bmw.grandtourer",
    "vehicle.citroen.c3",
    "vehicle.dodge.charger_2020",
    "vehicle.dodge.charger_police",
    "vehicle.dodge.charger_police_2020",
    "vehicle.ford.crown",
    "vehicle.ford.mustang",

    "vehicle.jeep.wrangler_rubicon",
    "vehicle.lincoln.mkz_2017",
    "vehicle.lincoln.mkz_2020",
    "vehicle.mercedes.coupe",
    "vehicle.mercedes.coupe_2020",

    "vehicle.micro.microlino",
    "vehicle.mini.cooper_s",
    "vehicle.mini.cooper_s_2021",
    "vehicle.nissan.micra",
    "vehicle.nissan.patrol",
    "vehicle.nissan.patrol_2021",
    "vehicle.seat.leon",
    "vehicle.tesla.model3",
    "vehicle.toyota.prius",
    "vehicle.volkswagen.t2",
    "vehicle.volkswagen.t2_2021",

    # bikes 
    #"vehicle.vespa.zx125",
    #"vehicle.bh.crossbike",
    #"vehicle.yamaha.yzf",
    #"vehicle.kawasaki.ninja"
    #"vehicle.harley-davidson.low_rider",
    #"vehicle.gazelle.omafiets",
    #"vehicle.diamondback.century",

    # quite BUNKY vehicles
    # "vehicle.chevrolet.impala",
    # "vehicle.carlamotors.carlacola",
    # "vehicle.ford.ambulance
    # "vehicle.carlamotors.firetruck
    # "vehicle.tesla.cybertruck"
    # "vehicle.mercedes.sprinter"
]

# ---------------------------------------------------------------------------------------------------------------------

def readParkingConfiguration(file_path: str) -> pd.DataFrame:
    """
    Reads CSV, makes a basic sanity check makes data accessable as pandas dataframe. 

    Args:
        file_path (str): Path to csv file (including file name and .csv ending)

    Returns:
        pd.DataFarme: CSV content ('None' entries are parsed as np.nan).
    """

    df = pd.read_csv(file_path)
    df.replace('None', np.nan, inplace=True)

    # Data verification

    if (['id', 'row', 'col', 'x', 'y', 'yaw', 'vehicle_bp'] != df.columns.tolist()):
        raise ValueError("CSV file expects: <id,row,col,x,y,yaw,vehicle_bp> columns!")

    return df

# ---------------------------------------------------------------------------------------------------------------------

def buildVehicleSpawnBatch(bp_lib: carla.BlueprintLibrary, df: pd.DataFrame,) -> typing.List[carla.command.SpawnActor]:
    """
    Prepares the batch for all spawning vehicles according to the parsed CSV configuration file.

    Args:
        bp_lib (carla.BluePrintLibrary): Reference to the client's blueprint library.
        df (pd.Dataframe): (Already validated) CSV file for parking space configuration.

    Returns:
        list[carla.command.SpawnActor]: The prepared batch for spawning all vehicles according to df. 
    """
    batch = []

    for index, row in df.iterrows():
        # set default values
        vehicle_bp = np.random.choice(bp_lib.filter(np.random.choice(DEFAULT_CARS_BP)))
        color = np.random.choice(vehicle_bp.get_attribute('color').recommended_values)
        yaw = float(np.random.choice(DEFAULT_YAWS))

        # override if CSV specifies concrete values 
        if not pd.isna(row['vehicle_bp']):
            vehicle_bp = np.random.choice(bp_lib.filter("vehicle.tesla.model3"))
        if not pd.isna(row['yaw']):
            yaw = float(row['yaw'])

        vehicle_bp.set_attribute('color', color)

        # finally, build batch (data validity was already verified in readParkingConfiguration)
        batch.append(
            carla.command.SpawnActor(
                vehicle_bp, 
                carla.Transform(
                    carla.Location(x=float(row['x']), y=float(row['y']), z=1), 
                    carla.Rotation(yaw=yaw)
                )
            )
        )

    return batch 

# ---------------------------------------------------------------------------------------------------------------------

def main():

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '-c', '--config',
        default="../../../Town04ParkingSpacePositions.csv",
        type=str,
        required=True,
        help='Input which parking space configuration CSV file should used for filling.'
    )
    args = argparser.parse_args()

    # 1. read csv 

    df = readParkingConfiguration(args.config)
    print(df)

    try:
        # 2. setup connection 

        client = carla.Client('localhost', 2000)
        client.set_timeout(10.0)
        
        world: carla.World             = client.get_world()
        bp_lib: carla.BlueprintLibrary = world.get_blueprint_library()

        ## Sanity Check - This script only make currently only sense for 'Town04_opt' 

        if (not "Town04_Opt" in world.get_map().name):
            raise ValueError("You're not using Town04_Opt! Use <py -3.7 myDynamicWorldEditor --setup-town4opt> first!")

        # 3. build batch for spawning vehicles according to csv

        batch: typing.List[carla.command.SpawnActor] = buildVehicleSpawnBatch(bp_lib, df)

        # 4. send request to server to spawn vehicles 

        responses: typing.List[libcarla.command.Response] = client.apply_batch_sync(batch, True) # Important: sync (we want to fetch the return values!)
        
        vehicle_ids = [response.actor_id for response in responses if not response.has_error()]
        conflicts_count = len(responses) - len(vehicle_ids)

        # 5. Run until aborted (CTRL + C)

        print(f"Spawned {len(vehicle_ids)} vehicles with {conflicts_count} conflicts. Press <CTRL + C> to despawn!")

        while True:
            world.wait_for_tick()
            time.sleep(5) # relieve cpu load

    finally:    
        print("About to clean up ...")
        batch = [carla.command.DestroyActor(vehicle_id) for vehicle_id in vehicle_ids]
        client.apply_batch_sync(batch, False)

# ---------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()

# ---------------------------------------------------------------------------------------------------------------------