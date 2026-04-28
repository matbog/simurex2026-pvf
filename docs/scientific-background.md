# Rappels scientifiques — Rayonnement et facteurs de forme

## 1. Pourquoi le rayonnement est important ?

Dans les problèmes de thermique du bâtiment, de microclimat urbain et de confort thermique, le **rayonnement thermique** joue un rôle central.

Contrairement à la conduction ou à la convection, le rayonnement :

- ne nécessite pas de contact matériel direct ;
- dépend fortement de la géométrie ;
- couple potentiellement toutes les surfaces visibles entre elles ;
- devient très sensible aux masques, aux orientations et aux températures de surface.

!!! info "Idée clé"
    Pour modéliser correctement les échanges radiatifs, il ne suffit pas de connaître les températures : il faut aussi savoir quelles surfaces se voient, et dans quelles proportions.

C'est le rôle des **facteurs de forme** (*view factors*).



## 2. Rappels sur le rayonnement thermique

### 2.1 Émission d'une surface

Une surface à température absolue \(T\) émet un flux radiatif. Pour un corps noir, l'émittance totale est donnée par la loi de Stefan–Boltzmann :

$$
E = \sigma T^4
$$

où \(\sigma\) est la constante de Stefan–Boltzmann.

Pour une surface réelle, on introduit généralement une émissivité \(\varepsilon\) :

$$
E = \varepsilon \sigma T^4
$$

### 2.2 Hypothèses usuelles

Dans de nombreux modèles bâtiment et urbains, on fait les hypothèses suivantes :

- surfaces **diffuses** : l'émission est répartie selon la loi de Lambert ;
- surfaces **grises** : les propriétés radiatives sont moyennées sur le domaine spectral considéré ;
- échanges en **grande longueur d'onde** pour les échanges thermiques entre parois ;
- réflexions spéculaires négligées.

Ces hypothèses simplifient fortement les équations tout en restant adaptées à de nombreux cas d'étude.


## 3. Définition des facteurs de forme

### 3.1 Interprétation physique

Le facteur de forme \(F_{i,j}\) représente la **fraction du rayonnement émis par la surface \(i\)** qui atteint directement la surface \(j\).

Il dépend de :

- la distance entre les deux surfaces ;
- leur orientation relative ;
- leur taille ;
- leur visibilité ;
- la présence éventuelle d'obstacles.

Il ne dépend pas directement des températures.

### 3.2 Formulation intégrale

Pour deux surfaces \(S_i\) et \(S_j\), le facteur de forme s'écrit :

$$
F_{i,j} = \frac{1}{S_i} \iint_{S_i} \iint_{S_j}
\frac{\cos\theta_i \cos\theta_j}{\pi r^2} \, dS_j \, dS_i
$$

où :

- \(r\) est la distance entre deux points des surfaces ;
- \(\theta_i\) est l'angle entre la normale à \(S_i\) et la direction reliant les deux points ;
- \(\theta_j\) est l'angle équivalent côté \(S_j\).

!!! note "Conséquence"
    Les facteurs de forme sont des grandeurs purement géométriques. Une fois la géométrie fixée, ils peuvent être réutilisés pour différents champs de température.


## 4. Propriétés fondamentales

### 4.1 Réciprocité

Les facteurs de forme vérifient :

$$
S_i F_{i,j} = S_j F_{j,i}
$$

Cette propriété est très utile numériquement : si l'on connaît \(F_{i,j}\), on peut déduire \(F_{j,i}\) à partir du rapport des aires.

### 4.2 Relation de sommation

Pour une surface dans une enceinte fermée :

$$
\sum_j F_{i,j} = 1
$$

Tout le rayonnement quittant la surface \(i\) atteint nécessairement une surface de l'enceinte.

Dans une scène ouverte, la somme peut être inférieure à 1 : une partie du rayonnement peut s'échapper vers le ciel ou l'extérieur du domaine.

### 4.3 Additivité

Si une surface \(j\) est découpée en plusieurs sous-surfaces \(j_1, j_2, ...\), alors :

$$
F_{i,j} = F_{i,j_1} + F_{i,j_2} + ...
$$

Cette propriété justifie l'utilisation de maillages : une surface complexe peut être représentée par un ensemble de facettes simples.


## 5. Facteurs de forme et échanges thermiques

Dans un modèle radiatif simplifié entre surfaces diffuses grises, les facteurs de forme permettent de pondérer les échanges entre surfaces.

Une écriture simplifiée du flux net associé à une surface peut prendre la forme :

$$
q_i \propto \sigma \sum_j F_{i,j} \left(T_i^4 - T_j^4\right)
$$

Cette écriture montre que deux surfaces à températures très différentes n'échangent fortement que si elles se voient avec un facteur de forme significatif.

!!! example "Exemple intuitif"
    Une paroi froide située directement devant un occupant influence fortement son bilan radiatif. La même paroi, masquée ou très oblique, aura un effet beaucoup plus faible.


## 6. Lien avec le confort thermique : MRT

### 6.1 Définition

La **température radiante moyenne** (*Mean Radiant Temperature*, MRT) est la température uniforme d'un environnement fictif qui produirait le même échange radiatif avec un individu que l'environnement réel.

Une écriture simplifiée est :

$$
T_r = \left( \sum_i F_i T_i^4 \right)^{1/4}
$$

avec :

- \(F_i\) : facteur de forme entre l'individu et la surface \(i\) ;
- \(T_i\) : température radiative de la surface \(i\).

Dans les situations extérieures, un terme lié au rayonnement solaire peut être ajouté selon les conventions du modèle.

### 6.2 Pourquoi c'est important ?

La MRT est souvent l'une des variables les plus influentes dans les indices de confort thermique.

Elle dépend fortement :

- des températures de surface ;
- du ciel visible ;
- de l'ombrage ;
- de la géométrie urbaine ;
- de la position de l'individu.

🔗 Ressource complémentaire : [Calcul de MRT](https://lhypercube.arep.fr/thematiques/confort/calcul_mrt/)

!!! info "Lien avec `pyViewFactor`"
    Pour calculer une MRT de manière géométriquement cohérente, il faut connaître les facteurs de forme entre le point ou le corps étudié et les surfaces environnantes.



## 7. Pourquoi le calcul est difficile ?

Dans des cas simples, il existe des solutions analytiques. Mais dans des géométries réelles, plusieurs difficultés apparaissent :

- surfaces polygonales quelconques ;
- orientations variées ;
- surfaces adjacentes ou quasi adjacentes ;
- masques et obstructions ;
- scènes ouvertes ;
- grand nombre de paires de surfaces.

Pour un maillage de \(N\) faces, une matrice complète peut contenir \(N^2\) interactions potentielles.

!!! warning "Point numérique"
    Le coût ne vient pas seulement du calcul de l'intégrale. Il vient aussi des tests géométriques : visibilité, obstruction, gestion des cas limites et remplissage de la matrice.


## 8. Méthodes de calcul des facteurs de forme

### 8.1 Méthodes analytiques

Elles donnent des résultats exacts ou quasi exacts pour des configurations simples : plaques parallèles, rectangles perpendiculaires, cylindres, sphères, etc.

Elles sont très utiles pour :

- comprendre les tendances ;
- valider un code ;
- construire des cas tests.

Limite : elles ne couvrent pas les géométries complexes.

### 8.2 Méthodes Monte Carlo

Le principe est de lancer un grand nombre de rayons depuis une surface et de compter les intersections avec les autres surfaces.

Avantages :

- méthode très générale ;
- gestion naturelle des obstructions ;
- adaptée à des scènes complexes.

Limites :

- bruit statistique ;
- convergence parfois lente ;
- besoin d'un grand nombre de rayons pour les faibles facteurs de forme.

### 8.3 Méthodes hémicube ou raster

Ces méthodes projettent la scène sur un hémicube ou une discrétisation angulaire autour d'une surface.

Avantages :

- efficaces dans certains contextes graphiques ;
- gestion possible des masques.

Limites :

- précision dépendante de la résolution ;
- artefacts de discrétisation ;
- moins adaptées lorsque l'on cherche une formulation numérique contrôlée.

### 8.4 Intégration numérique directe

On peut calculer directement l'intégrale surfacique :

$$
F_{i,j} = \frac{1}{S_i} \iint_{S_i} \iint_{S_j}
\frac{\cos\theta_i \cos\theta_j}{\pi r^2} \, dS_j \, dS_i
$$

Cette approche est générale, mais coûteuse : elle nécessite une intégration sur deux surfaces.

### 8.5 Transformation en intégrale de contour

Pour des polygones plans, il est possible de transformer l'intégrale de surface en intégrale de contour.

L'idée est de remplacer l'intégration sur les surfaces par une somme d'intégrales associées aux paires d'arêtes.

!!! success "Lien avec la formation"
    C'est cette famille de méthodes qui est utilisée dans `pyViewFactor` : elle est bien adaptée aux facettes planes issues de maillages.


## 9. Ce qu'il faut retenir avant la pratique

À ce stade, les messages importants sont :

1. Le rayonnement thermique dépend fortement de la géométrie.
2. Les facteurs de forme décrivent cette dépendance géométrique.
3. Ils sont essentiels pour les échanges radiatifs et la MRT.
4. Leur calcul devient difficile dans les scènes maillées avec obstructions.
5. `pyViewFactor` propose une approche numérique dédiée aux facettes planes.
