# tcc-GNL-amazon
Modeling of LNG distribution network for the Isolated System in the Brazilian Amazon.

## Overview
The objective of this work is to propose a liquefied natural gas (LNG) distribution
network for the Sistema Isolado (SI) of the State of Amazonas in Brazil.

Taking into account the possibility of substituting diesel fuel by natural gas in the thermoelectric plants that supply isolated localities, which are not in the National Interconnected System (SIN),
the periodic routing for complying with the energy demand of this alternative is studied.

Based on energy consumption data and the geographic locations of selected municipalities, the real problem is mathematically modeled and implemented using the optimization software *Gurobi*. Finally, results such as routes elaborated and fleet sizing are explored and analyzed for rivers Amazonas, Madeira and Solimões.

**Keywords**: Periodic routing. Distribution network. Liquefied natural gas. Sistema
Isolado (SI).

The project was part of a final thesis project for Naval Engineering's diploma at Escola Politécnica
da Universidade de São Paulo, Brazil.

## Setup

Firstly, a license for [Gurobi Optimizer](https://www.gurobi.com/) is required in order to perform
the Simplex interations of the proposed models. You can apply for a [Free Academic License](https://www.gurobi.com/academia/academic-program-and-licenses/) at their website.

[Poetry](https://python-poetry.org/) was used for dependency management.
To install poetry simply use the command in terminal:

`pip install poetry` or `conda install poetry`

After, install all necessary dependecies with command in terminal:

`poetry install`

You are ready!

## Usage

All commands are specified in the root of the project.

### Route generator

To preprocess a set of routes, use the command in terminal:

`poetry run python .\scripts\route_generator\route_generator.py`

It will generate a *parquet* file in `data/` folder containing the respective conditions
which are set by the user in `config.yaml`.

### Optimization

Two models were implemented in two different scripts:

1. Single: One river is selected (options: Amazonas, Madeira, Solimões).
    - Setup: `.\model\single\config.yaml`.
    - Run: `poetry run python .\model\single\app.py`.

2. Multiple: More than one river will be optimized (two-by-two or all).
    - Setup: `.\model\multiple\config.yaml`.
    - Run: `poetry run python .\model\multiple\app.py`.

Results containing the full mathematical model and optimization information
is written in `results/`.


## Structure

The project's tree was organized in 5 main branches (or folders).



```
├──archive: Vehicle Routing Problem (VRP) implementation - as a baseline.
├──data
|  │───demand_raw: Consolidated demand given by EPE (Empresa de Pesquisa Energética).
|  │───distances: Distance matrix.
|  └───preprocessing
│      ├───demands: Demands by localities based on one or more rivers.
│      ├───departure_patterns: Sparse departure pattern matrix.
│      └───routes: All pre-generated routes.
├──results
├──model: Optimization model scripts.
│  |───multiple
│  |   │───app.py
│  |   └───config.yaml
│  └───single
|      │───app.py
|      └───config.yaml
├──notebooks
|  └───demand_SI_AM.ipynb: Analytics and summarized decisions done prior to optimization.
└──scripts
   |───activation
   |    └───_vetor_A.py: test implementation of activation function.
   └───route_generator: Route generation script.
       │───config.yaml
       └───route_generator.py:

```

## Credits

Guilherme Urbano (@guidurbano)
Vitor Cesar (@V-Cesar)

## License

MIT License

Copyright (c) 2022 Guilherme Urbano

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
