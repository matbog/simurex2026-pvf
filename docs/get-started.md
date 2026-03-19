# Get started

This page explains how to prepare a clean Python environment and run the examples used during the session.

## 1. Create a clean Python environment

We recommend using a dedicated conda environment.

```bash
conda create -n simurex-pvf python=3.11
conda activate simurex-pvf
```
## 2. Install the required packages

```bash
pip install numpy scipy matplotlib pyvista jupyter
pip install pyviewfactor
```

3. Retrieve the session material

```
git clone https://github.com/matbog/simurex2026-pvf.git
cd simurex2026-pvf
```

## 4. Check that the environment works

```python
import numpy as np
import pyvista as pv
import pyviewfactor

print("Environment OK")
```