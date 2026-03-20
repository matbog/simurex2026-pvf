# Get started

Comment créer un environnement Python propre pour faire tourner les exercices de
la session. 

## 1. Créer un environnement Python propre

Il est recommandé d'utiliser un environnement Python "vierge". 
Selon vos préférence, utilisez `conda`, `miniconda`, `venv`, ...

* Conda : 
```bash
conda create -n simurex-pvf python=3.11
conda activate simurex-pvf
```

* `venv`


## 2. Installer les packages nécessaires 

```bash
pip install requirements
```

## 3. Récupérer les fichiers sources 

_selon ou on heberge les fichiers

* Notebooks / Scripts
```bash
git clone https://github.com/matbog/simurex2026-pvf.git
cd simurex2026-pvf/session
```

* Geométries 
```bash
cd simurex2026-pvf/session/datasets
```

## 4. Vérifier que tout s'importe 

```python
import numpy as np
import pyvista as pv
import pyviewfactor as pvf

print("Environment OK")
```