# À propos de pyViewFactor


[![GitLab](https://img.shields.io/badge/GitLab-source-FC6D26?logo=gitlab&logoColor=white)](https://gitlab.com/arep-dev/pyViewFactor)
[![Docs](https://img.shields.io/badge/docs-available-brightgreen?logo=gitbook&logoColor=white)](https://arep-dev.gitlab.io/pyViewFactor/)
[![Article](https://img.shields.io/badge/Article-IBPSA%202022-purple?logo=googlescholar&logoColor=white)](https://www.researchgate.net/publication/360835982_Calcul_des_facteurs_de_forme_entre_polygones_-Application_a_la_thermique_urbaine_et_aux_etudes_de_confort)
[![JOSS](https://img.shields.io/badge/JOSS-submitted-blue)](https://joss.theoj.org/papers/cc7d3aebf5e8ed25b343c6dd822f70b4)

## 1. Pourquoi parler de `pyViewFactor` dans cette formation ?

**`pyViewFactor`** est une bibliothèque Python dédiée au calcul des
**facteurs de forme** (*view factors*) entre surfaces planes.

Elle a été développée pour des cas où les échanges radiatifs dépendent fortement de la
géométrie :

- thermique du bâtiment,
- microclimat urbain,
- confort thermique,
- analyse de scènes 3D maillées.

!!! info "Idée centrale"
    Un facteur de forme décrit quelle fraction du rayonnement émis par une surface
    atteint une autre surface. Il dépend uniquement de la géométrie : position,
    orientation, distance, visibilité et obstructions.

Dans cette formation, `pyViewFactor` sert de support pratique pour passer :

1. d'une formulation scientifique des échanges radiatifs,
2. à un calcul numérique sur des géométries réelles,
3. puis à une intégration dans un workflow Python reproductible.


## 2. Pourquoi utiliser une bibliothèque dédiée ?

Les facteurs de forme peuvent être calculés de plusieurs manières, mais les outils
généralistes ne sont pas toujours adaptés à un usage pédagogique ou scientifique ouvert 
et interopérable. 

### 2.1 Limites fréquentes des approches existantes

Liste non exhaustive : 
- **EnergyPlus**  
  Très utile pour la simulation énergétique, mais les facteurs de forme sont intégrés
  dans un modèle plus global. Le contrôle fin des surfaces, des maillages et des tests
  géométriques est moins direct.

- **Radiance**  
  Très puissant pour le ray tracing et l'éclairage, mais il demande une expertise
  spécifique et repose sur une logique de lancer de rayons plutôt que sur une
  formulation explicite des facteurs de forme.

- **OpenFOAM**  
  Très complet pour la simulation numérique, mais plus lourd à mettre en place lorsqu'on
  veut seulement explorer ou enseigner le calcul de facteurs de forme.
  
- **Code_Aster**
  Très puissant pour la simulation multiphysique, mais moins orienté vers
  l'exploration interactive des facteurs de forme.

- D'autres outils existent également, mais ils ne sont pas toujours adaptés à une
exploration légère et / ou scriptable.

### 2.2 Besoin ciblé

Dans beaucoup d'applications de recherche :

- les surfaces sont issues de maillages polygonaux,
- les interactions surface-surface sont nombreuses,
- les obstructions peuvent modifier fortement les échanges,
- on souhaite garder la main sur chaque étape du calcul.

!!! success "Objectif de `pyViewFactor`"
    Fournir un outil Python lisible, scriptable et suffisamment robuste pour calculer
    des facteurs de forme sur des géométries planes issues de maillages.


## 3. Fonctionnalités principales

La bibliothèque permet notamment de :

- tester si deux faces sont orientées de manière compatible pour échanger du rayonnement,
- tester si une obstruction bloque la ligne de vue entre deux faces,
- calculer un facteur de forme entre deux surfaces planes,
- calculer une matrice complète de facteurs de forme sur un maillage,
- exploiter la réciprocité des facteurs de forme,
- visualiser la distribution des facteurs de forme depuis une cellule donnée,
- **intégrer ces calculs dans des workflows Python** basés sur `PyVista`, `NumPy`, `SciPy` et `Numba`.

## 4. Principe de la méthode

La méthode utilisée dans `pyViewFactor` s'appuie sur une formulation classique du
facteur de forme entre surfaces planes, puis sur une réduction de l'intégrale surfacique
en **intégrale de contour**.

Cette approche correspond à des travaux présentés à IBPSA France 2022 :  
[Calcul des facteurs de forme entre polygones — application à la thermique urbaine et aux études de confort](https://www.researchgate.net/publication/360835982_Calcul_des_facteurs_de_forme_entre_polygones_-Application_a_la_thermique_urbaine_et_aux_etudes_de_confort).

### 4.1 Idée théorique

La formulation générale d'un facteur de forme repose sur une double intégrale de
surface. Pour des polygones plans, cette intégrale peut être transformée en intégrale
sur les contours des deux surfaces, via le théorème de Stokes.

Conséquence pratique : au lieu d'intégrer sur toutes les surfaces, on somme des
contributions associées aux paires d'arêtes des deux polygones.

### 4.2 Stratégie numérique

`pyViewFactor` (v1.1.0) utilise le noyau **SA-30** : l'intégrale intérieure est évaluée en **forme fermée** (semi-analytique), ce qui élimine le biais numérique sur les faces adjacentes ou coplanaires sans recourir à un décalage epsilon.
Les paires sont ensuite traitées en parallèle grâce à Numba (`prange`), pour un gain de ×33 sur un cas urbain de référence.

!!! info "Historique"
    Les versions antérieures à v1.1.0 utilisaient une stratégie hybride Gauss–Legendre / `dblquad`. Le noyau SA-30 remplace cette approche en gérant tous les cas de manière unifiée et plus précise.


## 5. Architecture du code

Le calcul est organisé en quatre grandes étapes. Cette section est utile pour comprendre
ce qui se passe lorsqu'on appelle une fonction haut niveau
comme `compute_viewfactor_matrix()`.

### 5.1 Prétraitement géométrique

Objectif : convertir les cellules du maillage en données numériques directement
exploitables.

Fonctions et classes associées :

| Élément | Rôle |
|---|---|
| `fc_unstruc2poly()` | Convertit une cellule extraite sous forme `UnstructuredGrid` en `PolyData`. |
| `face_to_array()` | Extrait les coordonnées des sommets d'une face sous forme de tableau `NumPy`. |
| `face_normal_numpy()` | Calcule la normale unitaire d'un polygone plan. |
| `polygon_area()` | Calcule l'aire d'un polygone plan. |
| `polygon_centroid()` | Calcule le centroïde d'un polygone plan. |
| `ProcessedGeometry` | Met en cache les sommets, normales, centroïdes, aires et tailles caractéristiques de toutes les faces d'un maillage. |
| `FaceMeshPreprocessor` | Prépare un maillage d'obstacles triangulé pour accélérer les tests d'intersection. |
| `tri_overlaps_aabb()` | Teste rapidement si un triangle intersecte une boîte englobante alignée sur les axes. |

!!! note "Pourquoi un cache géométrique ?"
    Dans une matrice complète, les mêmes normales, centroïdes et aires sont réutilisés
    des milliers de fois. Les pré-calculer évite de refaire les mêmes opérations pour
    chaque paire de faces.

### 5.2 Test de visibilité

Objectif : vérifier si deux faces sont orientées de manière compatible pour échanger du rayonnement.

Fonctions associées :

| Élément | Rôle |
|---|---|
| `get_visibility()` | Teste la visibilité géométrique entre deux faces `PyVista`, à partir des normales et des centroïdes. |
| `get_visibility_from_cache()` | Variante optimisée qui utilise un objet `ProcessedGeometry`. |

Deux modes existent :

- `strict=False` : test principalement basé sur les centroïdes, plus permissif,
- `strict=True` : test plus pénalisant, qui vérifie les positions relatives des sommets pour éviter de valider des cas partiellement visibles.

!!! warning "Interprétation du mode strict"
    Le mode strict est volontairement conservatif. Il peut rejeter des configurations partiellement visibles. Pour des maillages complexes, la solution recommandée est souvent d'améliorer ou raffiner le maillage plutôt que d'assouplir ce critère.

### 5.3 Test d'obstruction

Objectif : déterminer si un obstacle bloque le chemin entre deux faces.

Fonctions associées :

| Élément | Rôle |
|---|---|
| `ray_intersects_triangle()` | Teste l'intersection entre un segment et un triangle avec l'algorithme de Möller–Trumbore. |
| `is_ray_blocked()` | Vérifie si un segment est bloqué par au moins un triangle d'un ensemble de triangles. |
| `get_obstruction()` | Teste l'obstruction entre deux faces et un maillage obstacle. |
| `get_obstruction_from_cache()` | Variante optimisée utilisant `ProcessedGeometry` et `FaceMeshPreprocessor`. |
| `FaceMeshPreprocessor.aabb_filter()` | Réduit le nombre de triangles candidats grâce à une boîte englobante. |
| `FaceMeshPreprocessor.exclude_exact_match()` | Évite de considérer les faces testées elles-mêmes comme des obstacles. |

Modes d'obstruction :

- `strict=False` : un rayon centroïde-centroïde est testé,
- `strict=True` : plusieurs rayons sommet-sommet sont testés, ce qui rend le critère plus conservatif.

#### Accélération BVH (v1.1.0)

Pour chaque paire de faces, tester séquentiellement tous les triangles de l'obstacle coûte **O(N)** par rayon. Depuis la v1.1.0, `FaceMeshPreprocessor` construit une **BVH** (*Bounding Volume Hierarchy*) : un arbre binaire de boîtes englobantes alignées sur les axes (AABB).

La traversée de l'arbre élimine à chaque niveau environ la moitié des triangles candidats, ramenant le coût à **O(log N)** par rayon. L'arbre est stocké sous forme de tableaux NumPy plats pour une traversée compatible Numba.

!!! info "Pour aller plus loin"
    Le fonctionnement détaillé de la BVH (construction, traversée, stockage) est présenté dans [l'article de blog dédié à la v1.1.0](https://lhypercube.arep.fr/blog/pyviewfactor_v110/).

### 5.4 Intégration numérique du facteur de forme

Objectif : évaluer l'intégrale de contour entre les deux polygones.

Depuis la v1.1.0, un noyau unique **SA-30** gère tous les cas :

| Élément | Rôle |
|---|---|
| `compute_viewfactor()` | Calcule le facteur de forme entre deux faces via le noyau SA-30. |
| `compute_viewfactor_matrix()` | Calcule la matrice complète avec tests de visibilité, obstruction (BVH) et parallélisation Numba. |

Le noyau SA-30 évalue l'intégrale intérieure en forme fermée (formule arc-tangente ou décomposition en racines réelles selon le signe du discriminant), ce qui élimine le biais des faces adjacentes sans recourir à un décalage `epsilon`.

!!! info "Pour aller plus loin"
    Le détail mathématique du noyau SA-30 et des mesures de performance sont présentés dans [l'article de blog dédié à la v1.1.0](https://lhypercube.arep.fr/blog/pyviewfactor_v110/).

### 5.5 Fonctions haut niveau

Ces fonctions orchestrent les étapes précédentes.

| Élément | Rôle |
|---|---|
| `compute_viewfactor()` | Calcule le facteur de forme entre deux faces. |
| `batch_compute_viewfactors()` | Calcule plusieurs facteurs de forme en lot, principalement pour les paires disjointes. |
| `compute_viewfactor_matrix()` | Calcule la matrice complète des facteurs de forme d'un maillage, avec options de visibilité, obstruction et modes stricts. |
| `plot_viewfactor()` | Visualise sur le maillage la distribution des facteurs de forme associés à une cellule source. |

!!! example "Lecture du pipeline"
    `compute_viewfactor_matrix()` commence par prétraiter le maillage, applique les tests de visibilité et d'obstruction (accélérés par BVH depuis la v1.1.0), puis calcule tous les facteurs de forme via le noyau SA-30 en parallèle (Numba `prange`).


## 6. Exemple minimal

```python
import pyvista as pv
import pyviewfactor as pvf

# Deux triangles parallèles et opposés
face_1 = pv.Triangle([
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
])

face_2 = pv.Triangle([
    [0.0, 0.0, 1.0],
    [0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0],
])

visible, message = pvf.get_visibility(face_1, face_2)

if visible:
    F_21 = pvf.compute_viewfactor(face_1, face_2)
    print(F_21)
```

## 7. Performance et compromis

Le design de `pyViewFactor` repose sur :

- `NumPy` pour les tableaux et opérations vectorisées,
- `Numba` pour accélérer les noyaux numériques,
- `SciPy` pour un fallback robuste,
- `PyVista` pour manipuler les géométries 3D.

Les principaux compromis sont :

- **précision vs coût** : le noyau SA-30 est à la fois plus précis et plus rapide que l'ancienne stratégie hybride, grâce à la forme fermée et à la parallélisation Numba,
- **mode strict vs mode permissif** : le mode strict évite certains faux positifs, mais peut rejeter des cas partiels,
- **maillage grossier vs maillage raffiné** : un maillage plus fin représente mieux les visibilités partielles, mais augmente le nombre de paires à calculer.

## 8. Cas d'usage

`pyViewFactor` peut être utilisé pour :

- construire une matrice d'échanges radiatifs longue longueur d'onde,
- analyser l'effet d'une géométrie urbaine sur les échanges radiatifs,
- alimenter un calcul de température radiante moyenne,
- produire des abaques pour des cas de validation,
- comparer des méthodes numériques de calcul de facteurs de forme,
- servir de support pédagogique pour relier théorie, géométrie et simulation.

