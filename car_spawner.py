import carla
import random
import time

def main():
    # Connect to the Carla server
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    # Get the blueprint library
    blueprint_library = world.get_blueprint_library()

    # Filter for the vehicle blueprint (e.g., 'vehicle.*' to get all vehicle blueprints)
    vehicle_bps = blueprint_library.filter('vehicle.*')

    # Define spawn points with specific locations and orientations (angles)
    specific_spawn_points = [
        #carla.Transform(carla.Location(x=230, y=195, z=40), carla.Rotation(pitch=0, yaw=180, roll=0)),
        #carla.Transform(carla.Location(x=235, y=200, z=40), carla.Rotation(pitch=0, yaw=90, roll=0)),
        #carla.Transform(carla.Location(x=240, y=205, z=40), carla.Rotation(pitch=0, yaw=0, roll=0)),
        # Add more specific spawn points here
    ]
    for i in range(100):
        specific_spawn_points.append(carla.Transform(carla.Location(x= 10, y= 10, z=40), carla.Rotation(pitch=90, yaw=90, roll=0)) )

    # Ensure there are enough specific spawn points
    if len(specific_spawn_points) < 100:
        raise Exception('Not enough specific spawn points to respawn 30 vehicles.')

    # Respawn logic
    def respawn_vehicles(vehicle_actors):
        for vehicle_actor in vehicle_actors:
            if vehicle_actor:
                print(f'Destroying vehicle {vehicle_actor.type_id}...')
                vehicle_actor.destroy()
                time.sleep(0.5)  # Wait a bit to ensure the actor is destroyed

        new_vehicles = []
        for i in range(100):
            vehicle_bp = random.choice(vehicle_bps)
            spawn_point = specific_spawn_points[i % len(specific_spawn_points)]  # Cycle through specific spawn points
            new_vehicle = world.spawn_actor(vehicle_bp, spawn_point)
            new_vehicles.append(new_vehicle)
            print(f'New vehicle spawned: {new_vehicle.type_id} at {spawn_point.location} with rotation {spawn_point.rotation}')
            time.sleep(2)

        return new_vehicles

    # Find existing vehicle actors to destroy
    existing_vehicles = [actor for actor in world.get_actors() if 'vehicle' in actor.type_id]

    # Respawn the vehicles
    new_vehicles = respawn_vehicles(existing_vehicles)

    # Keep the simulation running to observe the vehicles
    try:
        while True:
            world.wait_for_tick()
    except KeyboardInterrupt:
        pass

    # Clean up
    print('Cleaning up...')
    for vehicle in new_vehicles:
        if vehicle:
            vehicle.destroy()

if __name__ == '__main__':
    main()
