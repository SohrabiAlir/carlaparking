# Scenarios for Testing Autonomous Parking

**⚠️ Work in Progress ⚠️** (Last Update: 12.08.24)

> **NOTE**: The parent folder `TestingAutonomousParking` is supposed to be directly located inside `scenario_runner-0.9.15` folder (root directory). Otherwise all links are broken!

## Scenario Execution

<details>
 <summary> Windows </summary>
<br>

**Requirement**:

- Completed Setup for [CARLA](https://carla.readthedocs.io/en/latest/start_quickstart/) and [ScenarioRunner](../../Docs/index.md)
- Setup of all files in `integrate` (see comment in each .py file) in order to support `criteria_CustomFinallyInTargetArea` in OpenSCENARIO files.
- Running CARLA Instance (CarlaUE4.exe)

**1. Start ScenarioRunner** from root Scenario Runner folder:
> ```
> py -3.7 scenario_runner.py --openscenario TestingAutonomousParking/scenarios/FILENAME.xosc --json
> ```

Example: `py -3.7 scenario_runner.py --openscenario TestingAutonomousParking/scenarios/PlayfulChild/.PlayfulChildParkInReverseTown04.xosc --json`

**2. Connect with Ego Vehicle**: Execute `manual_drive.py` (from root Scenario Runner directory!)
> ```
> py -3.7 manual_drive.py
> ```

**3. Perform Scenario**: Perform vehicle maneuvers within `manual_drive.py` until scenario termination.

**4. Analyze Result**: Open `[NAME].json` (root directory of Scenario Runner) to analyze the final test results (exit criteria).

</details>

## Scenario Modelling

<details>
<summary> OpenSCENARIO 1</summary>
<br>

The current Scenario-Runner 0.9.15 only supports a subset of **[OpenSCENARIO 1.0](https://releases.asam.net/OpenSCENARIO/1.0.0/ASAM_OpenSCENARIO_BS-1-2_User-Guide_V1-0-0.html)**.
See [Scenario Runner Docs: OpenSCENARIO Support](../../Docs/openscenario_support.md) for more information.

Following custom extensions (see `integrate` directory) were added:
- `criteria_CustomFinallyInTargetArea`: Allows specifying a testing criteria that passes if the specified actor is within a defined rectangle given by min_x, max_x, min_y, max_y. 
- `criteria_CustomFinallyNotInTargetArea`: Analogous to criteria_CustomFinallyInTargetArea, but negated condition for passing. 

</details>

## Scenario Groups

**PlayfulChild** — During a park-in/park-out maneuver, a child suddenly runs into the vehicle's path, necessitating an emergency brake.

**OpposingTraffic** — Waiting for oncoming traffic to clear before starting the park-in/park-out maneuver.

**SurroundingPedestrians** — During the park-in/park-out maneuver, numerous pedestrians are moving near the car, with some crossing into the vehicle's path.

**TrafficConeMarkings** — Requires disregarding the existing line markings and using the traffic cones as reference points to identify the parking space slots.

**Miscellaneous** — Scenarios that don't belong into a specific category.

## Scenario Application

<details>
<summary> Parkin Maneuver </summary>

| Scenario |
| -------- |
| TODO     |

</details>


<details>
<summary> Parkout Maneuver </summary>

| Scenario |
| -------- |
| TODO     |

</details>

<details>
<summary> Park Search </summary>


| Scenario |
| -------- |
| TODO     |


</details>

<details>
<summary> Other </summary>

| Scenario |
| -------- |
| TODO     |

</details>