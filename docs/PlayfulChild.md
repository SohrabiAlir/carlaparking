[← All Scenarios](README.md)

# Scenario: Playful Child

File: `PlayfulChild.xosc`

## Scenario Description

While the ego vehicle executes a reverse parking maneuver, a child abruptly runs into the vehicle's rear path.

| Key Figure        | Value                       |
| ----------------- | --------------------------- |
| Time Limit        | 30s                         |
| Map               | `Town04_Opt`                |
| Weather           | cloudy, wet                 |
| Ego Vehicle       | `vehicle.mercedes.sprinter` |
| Invovled Entities | `walker.pedestrian.0010`    |

## Scenario Test Aspects

The scenario test is considered successful, if the ego vehicle breaks to avoid a collission with the child and finally reaches the dedicated parking slot area.

- `criteria_CollisionTest`: Avoid any kind of collission (especially with the child).
- `criteria_CustomFinallyInTargetArea`: Ego vehicle is inside the dedicated parking slot at scenario end.

## Scenario Overview

TODO.

## Scenario Model

TODO.
