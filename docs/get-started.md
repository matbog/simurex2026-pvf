# Get started

Ce document explique comment préparer un environnement Python propre pour faire tourner
les exercices de la session.

L'objectif est d'éviter les conflits avec les packages déjà installés sur votre machine,
et de garantir que tout le monde utilise une configuration proche.


## 1. Récupérer les fichiers sources

Commencez par récupérer les notebooks, scripts et données nécessaires à la session.

```bash
git clone https://github.com/matbog/simurex2026-pvf.git
cd simurex2026-pvf/session
```

Les géométries et jeux de données utilisés pendant la session se trouvent dans :

```bash
cd src_data
```



## 2. Créer un environnement Python propre

Il est recommandé d'utiliser un environnement Python dédié à la session.

Vous pouvez utiliser l'une des solutions suivantes :

- `conda`, si Anaconda ou Miniconda est déjà installé ;
- `miniconda`, si vous voulez une installation légère de conda ;
- `venv`, si vous préférez utiliser uniquement les outils Python standards.

Python `3.11` est recommandé.


### Option A — Avec conda

Si `conda` est déjà installé sur votre machine :

```bash
conda create -n simurex-pvf python=3.11
conda activate simurex-pvf
```

Pour vérifier que le bon environnement est actif :

```bash
python --version
which python
```

Sous Windows, utilisez plutôt :

```powershell
python --version
where python
```

---

### Option B — Avec Miniconda

Miniconda est une version légère d'Anaconda. Elle installe uniquement `conda`, Python
et les outils de base.

Après installation de Miniconda, ouvrez un nouveau terminal puis vérifiez que `conda`
est disponible :

```bash
conda --version
```

Créez ensuite l'environnement de travail :

```bash
conda create -n simurex-pvf python=3.11
conda activate simurex-pvf
```

Si la commande `conda` n'est pas reconnue, fermez puis rouvrez le terminal. Sur Windows,
vous pouvez aussi utiliser le terminal **Anaconda Prompt** ou **Miniconda Prompt**.

---

### Option C — Avec venv

`venv` est inclus avec Python. Cette option est utile si vous ne souhaitez pas utiliser
conda.

Depuis le dossier de la session :

```bash
python -m venv .venv
```

Activez ensuite l'environnement.

Sur Linux ou macOS :

```bash
source .venv/bin/activate
```

Sur Windows avec PowerShell :

```powershell
.venv\Scripts\Activate.ps1
```

Sur Windows avec `cmd.exe` :

```cmd
.venv\Scripts\activate.bat
```

Vérifiez ensuite que l'environnement est actif :

```bash
python --version
pip --version
```

Si l'activation a fonctionné, le nom de l'environnement apparaît généralement au début
de la ligne de commande, par exemple :

```bash
(.venv) user@machine:~/simurex2026-pvf/session$
```

## 3. Installer les packages nécessaires

Une fois l'environnement activé, mettez d'abord `pip` à jour :

```bash
python -m pip install --upgrade pip
```

Installez ensuite les dépendances de la session. A priori les bonnes versions des
dépendances sont : 
```
numpy==1.26.4
pyvista==0.45
scipy==1.11.4
numba==0.61.2
tqdm==4.65.0
```
MLais vous pouvez utiliser directement :
```bash
python -m pip install -r requirements.txt
```



## 4. Utilisation de Jupyter (optionnel)

Les exercices sont fournis sous forme de scripts Python.
Cependant, si vous préférez travailler avec Jupyter Notebook ou JupyterLab, vous pouvez
utiliser votre environnement comme noyau.

### Installer Jupyter dans l’environnement

Assurez-vous que votre environnement est activé, puis installez :

```bash
python -m pip install notebook ipykernel
```

### Ajouter l’environnement comme noyau

```bash
python -m ipykernel install --user --name simurex-pvf --display-name "Python (simurex-pvf)"
```

### Lancer Jupyter
```bash
jupyter notebook
```
ou :
```bash
jupyter lab
```

### Sélectionner le bon noyau

Dans l’interface Jupyter :

- Ouvrez un notebook
- Sélectionnez le noyau :
```bash
Python (simurex-pvf)
```

!!! warning " "
    Même si Jupyter est installé, les packages ne seront disponibles que si le bon noyau est sélectionné.



## 5. Vérifier l'installation

Dans un terminal où l'environnement est activé, lancez Python :

```bash
python
```

Puis testez les imports principaux :

```python
import numpy as np
import pyvista as pv
import pyviewfactor as pvf

print("Environment OK")
```

Vous pouvez aussi vérifier les versions installées :

```python
import numpy as np
import pyvista as pv
import pyviewfactor as pvf

print("numpy:", np.__version__)
print("pyvista:", pv.__version__)
print("pyviewfactor:", pvf.__version__ if hasattr(pvf, "__version__") else "version non déclarée")
```

---

## 6. Problèmes fréquents

* `pip install -r requirements.txt` ne trouve pas le fichier
    * Vérifiez que vous êtes dans le bon dossier :
    ```bash
    pwd
    ls
    ```
    * Sous Windows :
    ```cmd
    cd
    dir
    ```

    Le fichier `requirements.txt` doit apparaître dans la liste.



*  `conda activate simurex-pvf` ne fonctionne pas

    * Essayez d'initialiser conda :

    ```bash
    conda init
    ```

    * Fermez puis rouvrez le terminal.

    Sur Windows, utilisez **Anaconda Prompt** ou **Miniconda Prompt**.

*  Jupyter n'utilise pas le bon environnement

    * Vérifiez que le noyau Jupyter a bien été installé :

    ```bash
    jupyter kernelspec list
    ```

    * Si nécessaire, réinstallez le noyau depuis l'environnement actif :

    ```bash
    python -m ipykernel install --user --name simurex-pvf --display-name "Python (simurex-pvf)"
    ```

*  `pyvista` ne s'affiche pas correctement

    * Sur certaines machines ou connexions distantes, l'affichage 3D peut nécessiter une configuration supplémentaire.
    * Pour tester rapidement PyVista :

    ```python
    import pyvista as pv

    sphere = pv.Sphere()
    sphere.plot()
    ```

    Si une fenêtre 3D ne s'ouvre pas, le problème vient probablement de l'affichage graphique, pas forcément de l'installation Python.


## 7. Désactiver ou supprimer l'environnement

Pour désactiver l'environnement courant :

```bash
conda deactivate
```

ou, si vous utilisez `venv` :

```bash
deactivate
```

Pour supprimer l'environnement conda :

```bash
conda remove -n simurex-pvf --all
```

Pour supprimer un environnement `venv`, supprimez simplement le dossier `.venv` :

```bash
rm -rf .venv
```

Sous Windows PowerShell :

```powershell
Remove-Item -Recurse -Force .venv
```

---

## Résumé rapide

Avec conda ou Miniconda :

```bash
git clone https://github.com/matbog/simurex2026-pvf.git
cd simurex2026-pvf/session

conda create -n simurex-pvf python=3.11
conda activate simurex-pvf

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m pip install notebook ipykernel
python -m ipykernel install --user --name simurex-pvf --display-name "Python (simurex-pvf)"
```

Avec `venv` :

```bash
git clone https://github.com/matbog/simurex2026-pvf.git
cd simurex2026-pvf/session

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m pip install notebook ipykernel
python -m ipykernel install --user --name simurex-pvf --display-name "Python (simurex-pvf)"
```

Sur Windows, remplacez l'activation de `venv` par :

```powershell
.venv\Scripts\Activate.ps1
```