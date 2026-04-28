# Exercices — pyViewFactor

Cette page regroupe les exercices pratiques de la formation.  
Ils sont pensés pour être lancés comme des scripts Python indépendants, depuis un IDE
comme **Spyder**, **VS Code** ou **PyCharm**, ou dans un **notebook**. 

!!! info "Objectif de la séance"
    Passer progressivement d'un cas académique simple à des scènes plus réalistes :
    visibilité, obstruction, validation analytique, discrétisation, matrice complète de
    facteurs de forme et export VTK.

### Fichiers sources et scripts de base

Les fichiers exemples sont disponibles dans le dossier `session/.`, et les données
associées sont dans `session/src_data/.`

### Lancer un exercice dans un IDE

1. Ouvrir le dossier du dépôt `pyViewFactor` dans l'IDE.
2. Vérifier que l'interpréteur Python sélectionné est bien celui où `pyviewfactor` est installé.
3. Ouvrir le fichier d'exemple dans le dossier `session/`.
4. Vérifier les chemins vers les fichiers de données, par exemple `./session/src_data/...`.
5. Lancer le script avec le bouton **Run** de l'IDE.
6. Observer les sorties :
   - valeurs imprimées dans la console,
   - fenêtres PyVista,
   - figures Matplotlib,
   - fichiers `.vtk` exportés si l'exercice en produit.

!!! warning "Affichage 3D"
    Les exemples utilisant `pyvista.Plotter()` ouvrent une fenêtre interactive. Sur certains environnements distants ou notebooks, il peut être nécessaire de configurer l'affichage graphique.

## Exercices

### Exercice 1 — Premier facteur de forme

* Fichier : `example_viewfactor.py`
* Description / point clé :
    * Cas minimal entre deux surfaces
    * Importance de l’orientation des normales
    * Convention : compute_viewfactor(receiver, emitter)

* Observer :
    * le résultat de get_visibility
    * la valeur du facteur de forme

* Code essentiel :
```python
import pyvista as pv
from pyviewfactor import get_visibility, compute_viewfactor

rectangle = pv.Rectangle([[0,0,0],[1,0,0],[0,1,0]])
triangle  = pv.Triangle([[0,0,1],[0,1,1],[1,1,1]])

if get_visibility(rectangle, triangle)[0]:
    F = compute_viewfactor(triangle, rectangle)
    print("VF rectangle → triangle :", F)
```

---

### Exercice 2 — Visibilité et obstruction

* Fichiers :
    * `understanding_visibility_obstruction.py`
    * `example_obstructions.py`
* Description / point clé :
    * Visibilité : orientation des surfaces
    * Obstruction : présence d’un obstacle
    * get_obstruction(...) retourne True si NON obstrué

* Observer :
    * différence strict=False / strict=True
    * rayons centroïde vs sommet

* Code essentiel :
```python
import pyviewfactor as pvf

vis = pvf.get_visibility(face1, face2, strict=False)[0]

unobstructed = pvf.get_obstruction(
    face1, face2, obstacle,
    strict=False
)[0]

if vis and unobstructed:
    F = pvf.compute_viewfactor(face2, face1)
```

---

### Exercice 3 — Validation analytique

* Fichier : `analytical_comparison.py`
* Description / point clé :
    * Comparaison avec solution analytique
    * Cas adjacent → intégration robuste

* Observer :
    * erreur relative
    * comparaison courbe analytique / numérique

* Code essentiel :
```python
f_num = pvf.compute_viewfactor(
    rectangle,
    square
)
```

```python
for h in h_values:
    f_ana = analytical_f12(h)
    f_num = numerical_f12(h)

    err = abs(f_num - f_ana) / f_ana
    print(h, f_ana, f_num, err)
```

---

### Exercice 4 — Influence de la discrétisation

* Fichier : `discretization_influence.py`
* Description / point clé :
    * Surface courbe → approximation par facettes
    * Convergence avec raffinement

* Observer :
    * évolution de F(wall → sphere)
    * nombre de facettes visibles

* Code essentiel :
```python
sphere = pv.Sphere(theta_resolution=res, phi_resolution=res)
sphere.triangulate(inplace=True)

F_total = 0
for i in range(sphere.n_cells):
    facet = pvf.fc_unstruc2poly(sphere.extract_cells(i))

    if pvf.get_visibility(facet, wall)[0]:
        F_total += pvf.compute_viewfactor(facet, wall)
```

---

### Exercice 5 — Géométrie fermée

* Fichier : `example_closed_geometry.py`
* Description / point clé :
    * Vérification de la propriété de somme

* Observer :
    * sum(F_i) ≈ 1

* Code essentiel :
```python
import numpy as np

F = np.zeros(mesh.n_cells)

for i in range(mesh.n_cells):
    if i != ref_id:
        face = pvf.fc_unstruc2poly(mesh.extract_cells(i))

        if pvf.get_visibility(face, ref_face)[0]:
            F[i] = pvf.compute_viewfactor(face, ref_face)

print("Sum:", F.sum())
```

```python
Fmat = pvf.compute_viewfactor_matrix(mesh)
print(Fmat[:, ref_id].sum())
```

---

### Exercice 6 — Scène avec individu (doorman)

* Fichier : `example_doorman.py`
* Description / point clé :
    * Application à une géométrie réaliste
    * Agrégation par type de surface

* Observer :
    * utilisation de geom_id
    * export VTK

* Code essentiel :
```python
import pyvista as pv
import pyviewfactor as pvf

mesh = pv.read(file)

for idx in doorman_cells:
    face = pvf.fc_unstruc2poly(mesh.extract_cells(idx))

    if pvf.get_visibility(wall, face)[0]:
        F[idx] = pvf.compute_viewfactor(wall, face)
```

---

### Exercice 7 — Environnement urbain

* Fichier : `example_wall_viewfactors.py`
* Description / point clé :
    * Agrégation mur → ciel / sol / bâtiments
    * Pipeline complet

* Observer :
    * classification visibilité / obstruction
    * influence des paramètres strict

* Code essentiel :
```python
if pvf.get_visibility(patch, wall)[0]:
    if pvf.get_obstruction(patch, wall, mesh)[0]:
        F += pvf.compute_viewfactor(patch, wall)
```

```python
F_wall_sky = sum(F_patch for patch in sky)
```

---

### Exercice 8 — Matrice complète

* Fichier : `example_LR.py`
* Description / point clé :
    * Comparaison naïf vs optimisé
    * performance

* Observer :
    * temps de calcul
    * écart entre méthodes

* Code essentiel :
```python
F = pvf.compute_viewfactor_matrix(
    mesh,
    obstacles=mesh,
    strict_visibility=True,
    strict_obstruction=True
)
```

---

## Calcul de validation !