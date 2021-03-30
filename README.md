# OR Datasets

A client to fetch datasets across. The package is inspired by the datasets module of Scikit-learn https://scikit-learn.org/stable/datasets/

## Installation

For Python do

```
pip install or-datasets
```

## Usage

For Python the example pattern is

```
from or_datasets import fetch_vrp_rep
bunch = vrp_rep.fetch_vrp_rep(name="solomon-1987-r1", instance="R101_025")
name, n, E, c, d, Q, t, a, b, x, y = bunch["instance"]
```

This imports the `vrp_rep` module and fetches the instance named `R101_025` from the dataset denoted `solomon-1987-r1`. The `bunch` is a dictionary-like object that can contains a single dataset instances or a list of instances. For this particular case it is an instance of the vehicle routing problem with time windows and is unpacked to the instance name, number of nodes, an array of edge tuples, an arry of edge costs, an arry of node demands, a vehicle capacity, an array of travel times per edge, arrays of start and end time for customers time windows, and the x and y coordinates of the nodes.

## Data Sources

- Knapsack instances http://hjemmesider.diku.dk/~pisinger/codes.html (small coefficients, large coefficients, hard instances)
- VRP-REP http://vrp-rep.org (supports only VRPTW instances for now)
- LinerLib http://www.linerlib.org
