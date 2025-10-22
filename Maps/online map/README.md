This document presents the Python tools, the input data and the installation requirements to use the provided Python tools. 

Two Python tools are provided to test and to visualize the routes. The first one allows the user to visualise the routes or the points on a fixed map without calling an external server, called offline map. The second tool allows the user to visualise and to simulate the routes on a animated map whose needs to call a server to create the map, called online map.  

### Data

The input data of the Python tools are provided in the folder `data`. 

- `points.csv`: CSV file containing information (address, GPS coordinates, ...) on the 328 collection points and the depot. The address is not always known. The last line of the file corresponds to the depot. 
- `Serpenson.json`: JSON (JavaScript Object Notation) file containing information (GPS coordinates, speed, length, ...) about the roads of the studied area around the lake of Serpenson. 
- `distances.json`: JSON file containing  a 329x329 matrix of the travel distances in meters. The indexes of the matrix follows the order of the file `points.csv`.
- `durations.json`: similarly to the travel distance file, this file contains the travel durations in seconds. 
- `example_routes.json`: example of a JSON file representing the routes to visualize. It contains an array of routes where each route is an array of route points. The route points are represented using the index in `points.csv`.
- `example_points_service_time.csv`: example of a CSV file containing the service time in seconds of each point in \textit{points.csv}. It follows the same order as in `points.csv`.

### Python tools

This section describes how to use the provided Python tools to display the routes on the map. 

In order to visualize the routing map with the tools, after computing a routing, the user needs to create these two files:

- a JSON file with the same format as `example_routes.json` containing the set of routes to display
- a CSV file with the same format as `example_points_service_time.csv` containing the service time in seconds of each point (including the depot) used to optimize the routing


#### Online map - Jupyter notebook

- `display_routes.ipynb`: Jupyter notebook to display routes.

- `_display_routes.py`: private Python module containing the implementation of the notebook.

The user can launch the Jupyter notebook and runs the first cell, and he should see something like in the figure `maps/exemple_screenshot.png`.

To display set of routes, the user can change the paths in `display_routes.ipynb` accordingly and after executing the Jupyter notebook the user should see its routes. Each route has its own color. See the comments in `display_routes.ipynb` for details.

### Requirements

In order to use the Python tools that are provided, the user needs to ensure that all the requirements are satisfied. 

The code was tested using Python 3.9 with `pip` installed. The user can download the latest version of Python at the following link: https://www.python.org/downloads/. 
If the user does not have `pip`, depending on his system, he can follow the instructions given on this website to install it: https://pip.pypa.io/en/stable/installation/. If `pip` is already installed, the user needs to verify that he has the version 21.1.2 or a latest version. To upgrade `pip`, use the following command on a terminal: `python -m pip install --upgrade pip`.

In order to use the tools, the Python dependencies need to be installed. They are given in the files `requirements_offline.txt` and `requirements_online.txt` for the offline map tool and the online map tool respectively. The user can install them using the command: `python -m pip install -r requirements_filename` (he needs to replace `requirements\_filename` by either `requirements_offline.txt` or `requirements_online.txt`).

The online version of the map is using Jupyter notebook (https://jupyter.org) to create the animated map. The user can launch the Jupyter notebook with the command `jupyter-notebook tools/display_routes.ipynb`. If he has any issues with Jupyter, it is recommended to use a virtual environment: 

- create it with `python -m venv env`
- activate it with `source env/bin/activate`
- install the dependencies with `pip install -r requirements_filename` (inside the virtual environment he can safely use `pip` instead of `python -m pip`). Then he can launch the notebook with the same command as before. 
- exit the virtual environment with the command `deactivate`

Once that the virtual environment is created, he can use starting from the activation step. 
