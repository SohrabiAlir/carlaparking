#!/usr/bin/env python

# Copyright (c) 2021 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Authors: <Alireza Sohrabi> and <Martin Liam Plank>
# Context: Project <Testing of Autonomous Parking> @ IAIK 2024

"""
    This Script provdes a class that can be used to either
        1. generate OpenSCENARIO 1.0 code for entity definition and initialization with.. 
        2. (live) populate the current CARLA world with..    
    vehicles or static assets, according to provided csv file.

    Configurations Variables for VEHICLE:
        - DEFAULT_YAWS: Collection of all possible default values if yaw is not specified in CSV file.
        - DEFAULT_CARS_BP: Collection of all possibel default values if vehicle_bp is not specified in CSV file.

    CSV Columns for VEHICLE:
        - id (int): Internal unique identifier within CSV file (not used for CARLA)
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

    CSV Columns for STATIC ASSET: 
        - id (int): Internal unique identifier within CSV file (not used for CARLA)
        - x (flaot): x - coordinate of static asset
        - y (float): y - coordinate of static asset
        - z (flaot): z - coordinate of static asset
        - yaw: (float): yaw of static asset
        - asset_bp: The actor.type_id of the static asset that should be used.

    This script can also be used for standalone (live populates the world) with following flags:
        - --vehicle <PATH_TO_CSV>
        - --asset <PATH_TO_CSV>
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
import math
import typing # bc python < 3.8
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------------------------------------------------
# global configuration 

DEFAULT_YAWS = [
    -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0,
    175.0, 176.0, 177.0, 178.0, 179.0, 180.0, 181.0, 182.0, 183.0, 184.0, 185.0
]

DEFAULT_CARS_BP = [
    "vehicle.audi.a2",
    "vehicle.audi.etron",
    "vehicle.audi.tt",
    "vehicle.bmw.grandtourer",
    "vehicle.citroen.c3",
    # "vehicle.dodge.charger_2020",
    # "vehicle.dodge.charger_police",
    # "vehicle.dodge.charger_police_2020",
    "vehicle.ford.crown",
    "vehicle.ford.mustang",

    "vehicle.jeep.wrangler_rubicon",
    # "vehicle.lincoln.mkz_2017",
    # "vehicle.lincoln.mkz_2020",
    "vehicle.mercedes.coupe",
    "vehicle.mercedes.coupe_2020",

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

    # too small
    #"vehicle.micro.microlino",
    
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

class ISpawner(object):

    def readCSV(self, file_path: str) -> pd.DataFrame:
        """
        Reads CSV, makes a basic sanity check makes data accessable as pandas dataframe. 

        Args:
            file_path (str): Path to csv file (including file name and .csv ending)

        Returns:
            pd.DataFarme: CSV content ('None' entries are parsed as np.nan).
        """
        raise NotImplementedError("Must be implemented in derived class!")

    def buildSpawnBatch(self, bp_lib: carla.BlueprintLibrary, df: pd.DataFrame) -> typing.List[carla.command.SpawnActor]:
        """
        Prepares the batch for all spawning entities according to the parsed CSV configuration file.

        Args:
            bp_lib (carla.BluePrintLibrary): Reference to the client's blueprint library.
            df (pd.Dataframe): (Already validated) CSV file for parking space configuration.

        Returns:
            list[carla.command.SpawnActor]: The prepared batch for spawning all vehicles according to df. 
        """
        raise NotImplementedError("Must be implemented in derived class!")

    def generateXOSC(self, df: pd.DataFrame) -> typing.Dict[str, str]:
        """
        Generates the corresponding OpenSCENARIO 1.0 code for the entity definitions. 

        Args:
            df (pd.DataFrame): (Already validated) CSV file for parking space configuration.

        Returns:
            typing.Dict[str, str]: Dictionary with the keys {'Entities', 'Init'} that contain the generated openscenario-tags. 
        """
        raise NotImplementedError("Must be implemented in derived class!")

    def _degToRad(self, degrees: float) -> float:
        """
        Converts degrees to radians.

        Args:
            degrees (float): The angle in degrees.

        Returns: 
            float: The convertes degree in radians.
        """
        return degrees * (math.pi / 180)

# =====================================================================================================================

class VehicleSpawner(ISpawner):
    # buildSpawnBatch.__doc__ = ISpawner.buildSpawnBatch.__doc__
    # readCSV.__doc__ = ISpawner.readCSV.__doc__
    # generateXOSC.__doc__ = ISpawner.generateXOSC.__doc__

    # -----------------------------------------------------------------------------------------------------------------

    def readCSV(self, file_path: str) -> pd.DataFrame:
        df = pd.read_csv(file_path)
        df.replace('None', np.nan, inplace=True)

        # Data verification: Necessary columns

        if (['id', 'row', 'col', 'x', 'y', 'yaw', 'vehicle_bp'] != df.columns.tolist()):
            raise ValueError("CSV file expects: <id,row,col,x,y,yaw,vehicle_bp> columns!")

        # Data verification: ID must be unique

        if (df['id'].duplicated().any()):
            raise ValueError(f"CSV file has non-unique ID: <{df[df.duplicated(subset='id', keep=False)]}>!")
                
        return df

    # -----------------------------------------------------------------------------------------------------------------

    def buildSpawnBatch(self, bp_lib: carla.BlueprintLibrary, df: pd.DataFrame) -> typing.List[carla.command.SpawnActor]:
        batch = []

        for index, row in df.iterrows():
            # set default values
            
            vehicle_bp = np.random.choice(bp_lib.filter(np.random.choice(DEFAULT_CARS_BP)))
            color = np.random.choice(vehicle_bp.get_attribute('color').recommended_values)
            yaw = np.random.choice(DEFAULT_YAWS)

            # override if CSV specifies concrete values 
            
            if not pd.isna(row['vehicle_bp']):
                vehicle_bp = np.random.choice(bp_lib.filter(row['vehicle_bp']))
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

    # -----------------------------------------------------------------------------------------------------------------

    def generateXOSC(self, df: pd.DataFrame) -> typing.Dict[str, str]:
        result = {
            'DECL_ENTITY': '',
            'INIT_ENTITY': ''
        }

        # TODO: Parameterize "z" as well :) [bc other world might have very different z !!!]

        for index, row in df.iterrows():
            x, y = row['x'], row['y']
            vehicle_bp = row['vehicle_bp'] if not pd.isna(row['vehicle_bp']) else np.random.choice(DEFAULT_CARS_BP)
            yaw =  float(row['yaw']) if not pd.isna(row['vehicle_bp']) else np.random.choice(DEFAULT_YAWS)

            result['DECL_ENTITY'] += (
                "<ScenarioObject name='static_vehicle_{id}'>\n"
                "  <Vehicle name='{vehicle_bp}' vehicleCategory='car'>\n"
                "    <ParameterDeclarations/>\n"
                "    <Performance maxSpeed='69.444' maxAcceleration='200' maxDeceleration='10.0'/>\n"
                "    <BoundingBox>\n"
                "      <Center x='1.5' y='0.0' z='0.9'/>\n"
                "      <Dimensions width='2.1' length='4.5' height='1.8'/>\n"
                "    </BoundingBox>\n"
                "    <Axles>\n"
                "      <FrontAxle maxSteering='0.5' wheelDiameter='0.6' trackWidth='1.8' positionX='3.1' positionZ='0.3'/>\n"
                "      <RearAxle maxSteering='0.0' wheelDiameter='0.6' trackWidth='1.8' positionX='0.0' positionZ='0.3'/>\n"
                "    </Axles>\n"
                "    <Properties>\n"
                "      <Property name='type' value='simulation'/>\n"
                "    </Properties>\n"
                "  </Vehicle>\n"
                "</ScenarioObject>\n"
            ).format(id=index, vehicle_bp=vehicle_bp)

            result['INIT_ENTITY'] += (
                "<Private entityRef='static_vehicle_{id}'>\n"
                "  <PrivateAction>\n"
                "    <TeleportAction>\n"
                "      <Position>\n"
                "        <WorldPosition x='{x}' y='{y}' z='0.3' h='{h}'/>\n" 
                "      </Position>\n"
                "    </TeleportAction>\n"
                "  </PrivateAction>\n"
                "</Private>\n"
            ).format(id=index, x=x, y=y, h=self._degToRad(yaw))

        return result

# =====================================================================================================================

class StaticAssetSpawner(ISpawner):
    # buildSpawnBatch.__doc__ = ISpawner.buildSpawnBatch.__doc__
    # readCSV.__doc__ = ISpawner.readCSV.__doc__
    # generateXOSC.__doc__ = ISpawner.generateXOSC.__doc__

    # -----------------------------------------------------------------------------------------------------------------

    def readCSV(self, file_path: str) -> pd.DataFrame:
        df = pd.read_csv(file_path)
        df.replace('None', np.nan, inplace=True)

        # Data verification: Necessary columns

        if (['id', 'x', 'y', 'z', 'yaw', 'asset_bp'] != df.columns.tolist()):
            raise ValueError("CSV file expects: <id,x,y,z,yaw,asset_bp> columns!")

        # Data verification: ID must be unique

        if (df['id'].duplicated().any()):
            raise ValueError("CSV file has non-unique ID: <{row}>!".format(row=df[df.duplicated(subset='id', keep=False)]))

        # Data verification: No 'None' entries

        if df.isna().any().any():
            raise ValueError("CSV file must not contain <None> entries!")
        
        return df

    # -----------------------------------------------------------------------------------------------------------------

    def buildSpawnBatch(self, bp_lib: carla.BlueprintLibrary, df: pd.DataFrame) -> typing.List[carla.command.SpawnActor]:
        return [
            carla.command.SpawnActor(
                bp_lib.find(row['asset_bp']), 
                carla.Transform(
                    carla.Location(x=float(row['x']), y=float(row['y']), z=float(row['z'])), 
                    carla.Rotation(pitch=0, yaw=row['yaw'], roll=0)
                )
            ) for index, row in df.iterrows() ]

    # -----------------------------------------------------------------------------------------------------------------

    def generateXOSC(self, df: pd.DataFrame) -> typing.Dict[str, str]:
        result = {
            'DECL_ENTITY': '',
            'INIT_ENTITY': ''
        }

        for index, row in df.iterrows():
            x, y, z = row['x'], row['y'], row['z']
            asset_bp = row['asset_bp']
            yaw =  float(row['yaw']) if not pd.isna(row['vehicle_bp']) else np.random.choice(DEFAULT_YAWS)

            result['DECL_ENTITY'] += (
                "<ScenarioObject name='static_asset_{id}'>\n"
                "  <MiscObject mass='500.0' name='{asset_bp}' miscObjectCategory='obstacle'>\n"
                "    <ParameterDeclarations/>\n"
                "    <BoundingBox>\n"
                "      <Center x='0' y='0.0' z='0'/>\n"
                "      <Dimensions width='1.0' length='2.0' height='1.7'/>\n"
                "    </BoundingBox>\n"
                "    <Properties>\n"
                "      <Property name='type' value='simulation'/>\n"
                "    </Properties>\n"
                "  </MiscObject>\n"
                "</ScenarioObject>\n"
            ).format(id=index, asset_bp=row['asset_bp'])

            result['INIT_ENTITY'] += (
                "<Private entityRef='static_asset_{id}'>\n"
                "  <PrivateAction>\n"
                "    <TeleportAction>\n"
                "      <Position>\n"
                "        <WorldPosition x='{x}' y='{y}' z='{z}' h='{h}'/>\n"
                "      </Position>\n"
                "    </TeleportAction>\n"
                "  </PrivateAction>\n"
                "</Private>\n"
            ).format(id=index, x=x, y=y, z=z, h=self._degToRad(yaw))

        return result

# =====================================================================================================================

def spawnerFactory(args) -> typing.Tuple[ISpawner, str]:
    """
    Creates ISpawner object.
    """
    if args.vehicle is not None:
        return (VehicleSpawner(), args.vehicle)
    elif args.asset is not None:
        return (StaticAssetSpawner(), args.asset)
    else:
        raise ValueError("Either --vehicle or --asset must be configurated!")

# =====================================================================================================================

def populateWorld(df: pd.DataFrame, spawner: ISpawner) -> None:
    """
    Populates the world by building a spawn batch and finally spawning all actors.

    Raises:
        ValueError: If Town04_Opt is not selected (is currently required!).

    Args:
        df (pd.DataFrame): (Already validated) CSV file for parking space configuration.
        spawner (ISpawner): Spawner object that provides interfaces for building spawn batch.
    """
    try:
        # 1. setup connection 

        client = carla.Client('localhost', 2000)
        client.set_timeout(10.0)
        
        world: carla.World             = client.get_world()
        bp_lib: carla.BlueprintLibrary = world.get_blueprint_library()

        ## Sanity Check - This script only make currently only sense for 'Town04_opt' 

        if (not "Town04_Opt" in world.get_map().name):
            raise ValueError("You're not using Town04_Opt! Use <py -3.7 myDynamicWorldEditor --setup-town4opt> first!")

        # 2. build batch for spawning vehicles according to csv

        batch: typing.List[carla.command.SpawnActor] = spawner.buildSpawnBatch(bp_lib, df)

        # 3. send request to server to spawn vehicles 

        responses: typing.List[libcarla.command.Response] = client.apply_batch_sync(batch, True) # Important: sync (we want to fetch the return values!)
        
        actor_ids = [response.actor_id for response in responses if not response.has_error()]
        conflicts_count = len(responses) - len(actor_ids)

        # 4. Run until aborted (CTRL + C)

        print(f"Spawned {len(actor_ids)} actors with {conflicts_count} conflicts. Press <CTRL + C> to despawn!")

        while True:
            world.wait_for_tick()
            time.sleep(5) # relieve cpu load

    finally:    
        print("About to clean up ...")
        batch = [carla.command.DestroyActor(actor_id) for actor_id in actor_ids]
        client.apply_batch_sync(batch, False)

# ---------------------------------------------------------------------------------------------------------------------

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '-v', '--vehicle',
        default=None,
        type=str,
        help='Input which parking space configuration CSV file should used for filling.'
    )
    argparser.add_argument(
        '-a', '--asset',
        default=None,
        type=str,
        help='Input which parking space configuration CSV file should used for filling.'
    )
    argparser.add_argument(
        '-xosc', '--openscenario-output',
        action='store_true',
        help='Information whether word should be populated directly.'
    )
    args = argparser.parse_args()
    
    if not args.vehicle is None and args.asset is None:
        print("Nothing to do!")

    if args.vehicle is not None and args.asset is not None:
        print("Combination of flag --vehicle (-v) and --asset (-a) not supported!") 

    spawner, file_path = spawnerFactory(args) 
    
    df = spawner.readCSV(file_path)
    print(df)

    if args.openscenario_output:
        xosc_generated = spawner.generateXOSC(df)
        print("\n{entities}\n{init}\n".format(entities=xosc_generated['DECL_ENTITY'], init=xosc_generated['INIT_ENTITY']))
    else:
        populateWorld(df, spawner)

# ---------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
