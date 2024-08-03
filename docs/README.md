# Scenarios for Testing Autonomous Parking

**⚠️ Work in Progress ⚠️** (Last Update: 03.08.24)

> **NOTE**: The parent folder `TestingAutonomousParking` is supposed to be directly located inside `scenario_runner-0.9.15` folder (root directory). Otherwise all links are broken!

## Scenario Execution

<details>
 <summary> Windows </summary>
<br>

**Requirement**:

- Completed Setup for [CARLA](https://carla.readthedocs.io/en/latest/start_quickstart/) and [ScenarioRunner](../../Docs/index.md)
- Running CARLA Instance (CarlaUE4.exe)

**1. Start ScenarioRunner** from root Scenario Runner folder:
> ```
> py -3.7 scenario_runner.py --openscenario myExamples/FILENAME.xosc --json
> ```

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

</details>

## Scenario Overview

**[PlayfulChild](PlayfulChild.md)** — During reversing parking maneuver, child suddenly runs into the vehicle's rear path.