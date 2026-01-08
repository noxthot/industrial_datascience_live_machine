# Simulation of a Pick and Place machine for live process optimization

This script runs a machine simulating a pick and place process with four steps:
- Move to pick up a component with random weight placed at a random location.
 Pick up the component using the vacuum system.
- Move to the target placement location on the circuit board with random speed. This is always at the center of the board at (150, 150).
- Place the component and measure the placement accuracy using the camera system.

The machine is instrumented with various sensors to monitor its operation, including:
- Air temperature [K]: ambient temperature around the machine.
- Attached Weight [mg]: weight of the component picked up by the vacuum system.
- Position x [mm]: target position in direction.
- Position y [mm]: target position in direction.
- Process step: current step in the process (0 to 3).
- Process temperature [K]: temperature inside the machine.
- Speed [mm/s]: speed of the current movement.
- Speed next [mm/s]: speed for the next movement.
- Error x [mm]: placement error in direction (only available at the end of the cycle).
- Error y [mm]: placement error in direction (only available at the end of the cycle).

These measurements are available in real-time via OPC UA.

This simulator is used in the course material found at https://noxthot.github.io/ws25_industrial_datascience_manuscript/, a course about Industrial Data Science.

## Author
Gregor Ehrensperger -- ehrensperger.dev -- 2025

## Citing
[![DOI](https://zenodo.org/badge/1117321259.svg)](https://zenodo.org/badge/latestdoi/1117321259)
TODO -> fix

## Usage
- Option A (prerequisite: [uv](https://docs.astral.sh/uv/) installed and trust in the author of the code):
Run
```bash
uv sync
```
to install dependencies and then run the script with
```bash
uv run dist/opc-ua-server.py
```

- Option B (prerequisite: [Docker](https://www.docker.com/)):
Build the Docker image with
```bash
docker build -t live-machine .
```
Then run the container with
```bash
docker run --rm -v $(pwd)/output:/app/data -p 4840:4840 live-machine
```


## Configuration
The machine's behaviour can only be influenced by setting `correction_x` and `correction_y` via OPC UA.

## Goal
The target is to minimize the placement error (error x and error y) by adjusting the correction values.

## Note
This is a very simplified simulation and does not represent real-world manufacturing processes.
The simulator is intended for educational and demonstration purposes only.
It is also subject to stochastic variations, so results may vary between runs.
