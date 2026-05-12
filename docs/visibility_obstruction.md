# Tests de visibilité et d'obstruction



!!! success "Comprendre par l'exemple"
    Le fichier `1_understanding_visibility_obstruction.py` permet de comprendre les différentes stratégies décrites ci-dessous avec des exemples. 



## 1. Introduction

Le calcul des facteurs de forme ne repose pas uniquement sur une intégration numérique.  
Avant même d'évaluer une intégrale, il est nécessaire de déterminer si deux surfaces :

- peuvent **géométriquement se voir** (visibilité),
- sont **effectivement visibles sans obstacle** (obstruction).

Ces deux étapes sont fondamentales car elles permettent :

- de réduire fortement le nombre de calculs,
- d'éviter des intégrations inutiles,
- de garantir la cohérence physique des résultats.

!!! info "Pipeline"
    Dans `pyViewFactor`, ces tests sont effectués **avant toute intégration**, et conditionnent directement le calcul des facteurs de forme.


## 2. Test de visibilité

### 2.1 Principe

Le test de visibilité consiste à vérifier si deux facettes sont **orientées l'une vers l'autre**.

Autrement dit, même en l'absence d'obstacles, deux surfaces ne peuvent échanger du rayonnement que si :

- leurs normales sont orientées de manière compatible,
- leurs centres sont mutuellement visibles.


### 2.2 Formulation géométrique

Soient deux facettes \(S_i\) et \(S_j\), de centres \(C_i\) et \(C_j\), et de normales \(\vec{n}_i\), \(\vec{n}_j\).

On considère le vecteur :

$$
\vec{v}_{ij} = C_i - C_j
$$

Les conditions de visibilité s'écrivent :

$$
\vec{v}_{ij} \cdot \vec{n}_j > 0
\quad \text{et} \quad
\vec{v}_{ij} \cdot \vec{n}_i < 0
$$

Ces deux conditions garantissent que :

- \(S_j\) est orientée vers \(S_i\),
- \(S_i\) est orientée vers \(S_j\).


### 2.3 Interprétation

Ce test revient à vérifier que :

- chaque surface "regarde" l'autre,
- les normales ne sont pas divergentes.



### 2.4 Modes strict et non strict

Dans la pratique, deux stratégies existent :

#### Mode non strict

- basé sur les centroïdes,
- rapide,
- tolère les cas partiellement visibles.

#### Mode strict

- vérifie tous les points des facettes,
- rejette les cas partiellement visibles,
- plus conservatif.

!!! warning "Cas limites"
    Dans les géométries réelles, une facette peut être partiellement visible. Le choix du mode strict dépend de l'application.



## 3. Test d'obstruction

### 3.1 Principe

Même si deux surfaces sont orientées correctement, elles peuvent être **masquées par une troisième surface**.

Le test d'obstruction consiste à vérifier que le segment reliant les deux surfaces ne coupe aucun obstacle.


### 3.2 Formulation

On considère un rayon entre deux points :

$$
\vec{r}(t) = (1 - t) \, P + t \, Q
\quad \text{avec} \quad t \in (0,1)
$$

Le problème devient :

> Existe-t-il une intersection entre ce segment et une autre facette ?


### 3.3 Algorithme utilisé

Une méthode classique est l'algorithme de [**Möller–Trumbore**](https://en.wikipedia.org/wiki/M%C3%B6ller%E2%80%93Trumbore_intersection_algorithm) :

- test rapide d'intersection rayon-triangle,
- robuste numériquement,
- adapté aux maillages triangulés.



### 3.4 Filtrage spatial

Pour éviter de tester toutes les facettes, un filtrage est appliqué :

- construction d'une **boîte englobante** (AABB - _Axis Aligned Bounding Box_),
- sélection des triangles candidats,
- exclusion des faces testées.

!!! success "Optimisation clé"
    Le filtrage spatial réduit fortement le coût du test d'obstruction.



### 3.5 Modes strict et non strict

#### Mode non strict

- un seul rayon (centroïde → centroïde),
- rapide,
- approximation.

#### Mode strict

- rayons entre tous les sommets,
- plus précis,
- plus coûteux.



## 4. Difficultés pratiques

### 4.1 Bruit géométrique

Les données issues de CAD contiennent souvent :

- des coordonnées quasi nulles,
- des arêtes non parfaitement partagées,
- des décalages minimes.

Ces défauts peuvent conduire à :

- des faux positifs d'obstruction,
- des incohérences de visibilité.



### 4.2 Cas dégénérés

Certains cas sont particulièrement sensibles :

- surfaces partageant une arête,
- surfaces partageant un sommet,
- surfaces quasi coplanaires,
- distances très faibles.



### 4.3 Gestion numérique

Plusieurs solutions sont utilisées :

- arrondi des coordonnées,
- introduction d'un seuil \(\varepsilon\),
- exclusion des intersections aux extrémités,
- filtrage des triangles identiques.



## 5. Lien avec `pyViewFactor`

### 5.1 Test de visibilité

Le test de visibilité repose sur :

- les centroïdes,
- les normales,
- des produits scalaires.

!!! abstract "Implémentation"
    `get_visibility(cell_1, cell_2, ...)`



### 5.2 Test d'obstruction

Le test d'obstruction repose sur :

- ray tracing,
- intersection segment-triangle,
- filtrage AABB.


!!! abstract "Implémentation"
    `get_obstruction(cell1, cell2, obstacle, ...)`


### 5.3 Prétraitement géométrique

Pour accélérer les calculs :

- stockage des normales, centres, aires,
- mise en cache des triangles.

Voir les structures de prétraitement dans le code.


## 6. Impact sur les facteurs de forme

Les tests de visibilité et d'obstruction conditionnent directement :

- quelles paires de surfaces sont intégrées,
- la sparsité de la matrice des facteurs de forme,
- la cohérence physique du modèle.

!!! important "À retenir"
    Une erreur de visibilité ou d'obstruction peut avoir un impact plus important que l'erreur d'intégration elle-même.


## 7. Conclusion

Les tests de visibilité et d'obstruction sont :

- indispensables pour le calcul des facteurs de forme,
- fortement dépendants de la qualité géométrique,
- souvent la partie la plus délicate du calcul.

Ils constituent un compromis entre :

- précision,
- robustesse,
- performance.

Dans `pyViewFactor`, ces tests sont conçus pour être :

- rapides,
- robustes face au bruit géométrique,
- compatibles avec des maillages complexes.
