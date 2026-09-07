# Satellite Quantum Communication Simulator

A Python-based simulation and visualization tool for studying **satellite quantum communication networks** and their time-varying topology.

The project was developed as a university research project focusing on satellite-based Quantum Key Distribution (QKD).

## Features

* Satellite orbit propagation using **TLE data** and Skyfield
* Satellite–ground station visibility and link calculation
* Inter-satellite line-of-sight (ISL) connections
* Time-varying network graphs using **NetworkX**
* Simplified optical link and **QKD / Effective Secure Key Rate (ESKR)** model
* End-to-end network capacity analysis using **max-flow / min-cut**
* 2D satellite constellation and network visualization
* Configurable satellite constellation, ground stations and simulation parameters

## Technologies

Python · Skyfield · NumPy · Pandas · NetworkX · Matplotlib · Cartopy

## Running the simulation

Install the required Python packages:

```bash
pip install numpy pandas networkx matplotlib skyfield cartopy
```

Then run:

```bash
python main.py
```

Simulation parameters such as the constellation, number of satellites, ground stations and QKD model parameters can be modified in:

```text
simulation_config.py
```

## Project Status

This is an experimental / educational simulator developed for studying the behavior and limitations of **time-varying satellite quantum communication networks**.
