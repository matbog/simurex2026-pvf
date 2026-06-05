# Rappels scientifiques — Rayonnement et facteurs de forme

## 0. STL / VTK : pourquoi travailler sur des maillages ?

Dans les applications de thermique du bâtiment ou d'environnement urbain, les géométries utilisées proviennent généralement d'outils de modélisation (BIM, CAD, SIG). Ces géométries sont riches mais rarement adaptées directement à des calculs physiques précis.

En pratique, plusieurs difficultés apparaissent :

- les surfaces ne sont pas parfaitement planes,
- les coordonnées contiennent du **bruit numérique** (valeurs proches de zéro mais non nulles),
- les faces peuvent être mal orientées,
- des incohérences topologiques peuvent exister (trous, recouvrements, intersections).

Pour rendre ces géométries exploitables, on les convertit en **maillages surfaciques** (formats STL, VTK, ...), composés de facettes planes (triangles ou polygones).

Cette représentation présente plusieurs avantages :

- elle permet de traiter des géométries arbitraires,
- elle est compatible avec les méthodes numériques d'intégration,
- elle facilite les calculs massivement parallèles.

En contrepartie, cette discrétisation introduit également de nouveaux enjeux numériques :

!!! warning "Impact du maillage"
    Le bruit géométrique, les erreurs d'orientation ou les surfaces quasi coïncidentes
    ont un impact direct sur les calculs de visibilité, d'obstruction et d'intégration.

Ces aspects doivent donc être explicitement pris en compte dans les algorithmes.

## 1. Rayonnement thermique : bases physiques

Dans les problèmes de thermique du bâtiment, de microclimat urbain et de confort 
thermique, le **rayonnement thermique** joue un rôle central.

Contrairement à la conduction ou à la convection, le rayonnement :

- ne nécessite pas de contact matériel direct,
- dépend fortement de la géométrie,
- couple potentiellement toutes les surfaces visibles entre elles,
- est très sensible aux masques, aux orientations et aux températures de surface.

!!! info "Idée clé"
    Pour modéliser correctement les échanges radiatifs, il ne suffit pas de connaître
    les températures : il faut aussi savoir quelles surfaces se voient et dans quelles
    proportions.

C'est le rôle des **facteurs de forme** (*view factors*).

### 1.1 Loi de Stefan–Boltzmann

Une surface à température absolue \(T\) émet un flux radiatif. Pour un corps noir,
l'émittance totale est donnée par la loi de 
[Stefan–Boltzmann](https://fr.wikipedia.org/wiki/Loi_de_Stefan-Boltzmann) :

$$
E = \sigma T^4
$$

où \(\sigma\) est la [constante de Stefan–Boltzmann](https://fr.wikipedia.org/wiki/Constante_de_Stefan-Boltzmann).

Pour une surface réelle, on introduit généralement une
[émissivité](https://fr.wikipedia.org/wiki/%C3%89missivit%C3%A9) \(\varepsilon\) :

$$
E = \varepsilon \sigma T^4
$$

### 1.2 Hypothèses usuelles

Dans de nombreux modèles bâtiment et urbains, on fait les hypothèses suivantes :

- surfaces **diffuses** : l'émission est répartie selon la [loi de Lambert](https://fr.wikipedia.org/wiki/Loi_de_Lambert),
- surfaces **grises** : les propriétés radiatives sont moyennées sur le domaine spectral considéré, 
- échanges en **grande longueur d'onde** pour les échanges thermiques entre parois,
- réflexions spéculaires négligées.

Ces hypothèses simplifient fortement les équations tout en restant adaptées à de nombreux cas d'étude.


## 2. Facteurs de forme : géométrie des échanges radiatifs

### 2.1 Définition physique

Le [facteur de forme](https://fr.wikipedia.org/wiki/Facteur_de_forme_(rayonnement_thermique)) \(F_{i,j}\) représente la **fraction du rayonnement émis par la surface \(i\)** qui atteint directement la surface \(j\).

_Dit autrement, \(F_{i,j}\) est la fraction du champ de vision de la facette \(i\) occupée par la facette \(j\)_


Il dépend de :

- la distance entre les deux surfaces,
- leur orientation relative,
- leur taille,
- leur visibilité,
- la présence éventuelle d'obstacles.

Il ne dépend pas directement des températures.

### 2.2 Formulation intégrale

Pour deux surfaces \(S_i\) et \(S_j\), le facteur de forme s'écrit :

$$
F_{i,j} = \frac{1}{S_i} \iint_{S_i} \iint_{S_j}
\frac{\cos\theta_i \cos\theta_j}{\pi r^2} \, dS_j \, dS_i
$$

où :

- \(r\) est la distance entre deux points des surfaces,
- \(\theta_i\) est l'angle entre la normale à \(S_i\) et la direction reliant les deux points,
- \(\theta_j\) est l'angle équivalent côté \(S_j\).

!!! note "Conséquence"
    Les facteurs de forme sont des grandeurs purement géométriques. Une fois la géométrie fixée, ils peuvent être réutilisés pour différents champs de température.


### 2.3 Propriétés fondamentales

#### Réciprocité

Les facteurs de forme vérifient :

$$
S_i F_{i,j} = S_j F_{j,i}
$$

Cette propriété est très utile numériquement : si l'on connaît \(F_{i,j}\), on peut déduire \(F_{j,i}\) à partir du rapport des aires.

#### Relation de sommation

Pour une surface dans une enceinte fermée :

$$
\sum_j F_{i,j} = 1
$$

Tout le rayonnement quittant la surface \(i\) atteint nécessairement une surface de l'enceinte.

Dans une scène ouverte, la somme peut être inférieure à 1 : une partie du rayonnement peut s'échapper vers le ciel ou l'extérieur du domaine.

#### Additivité

Si une surface \(j\) est découpée en plusieurs sous-surfaces \(j_1, j_2, ...\), alors :

$$
F_{i,j} = F_{i,j_1} + F_{i,j_2} + ...
$$

Cette propriété justifie l'utilisation de maillages : une surface complexe peut être représentée par un ensemble de facettes simples.


## 3. Facteurs de forme et échanges thermiques

Dans un modèle radiatif simplifié entre surfaces diffuses grises, les facteurs de forme permettent de pondérer les échanges entre surfaces.

Une écriture simplifiée du flux net associé à une surface peut prendre la forme :

$$
q_i \propto \sigma \sum_j F_{i,j} \left(T_i^4 - T_j^4\right)
$$

Cette écriture montre que deux surfaces à températures très différentes n'échangent fortement que si elles se voient avec un facteur de forme significatif.



## 4. Lien avec le confort thermique : MRT

### 4.1 Définition


La **température radiante moyenne** (*Mean Radiant Temperature*, MRT) est la température uniforme d'un environnement fictif qui produirait le même échange radiatif avec un individu que l'environnement réel.

Une écriture simplifiée est :

$$
T_{\text{r}} = \sqrt[4] { \frac{ \sum_{i=1}^{n} S_i F_i T_i^4 }{\sum_{i=1}^{n} S_i F_{i} } }
$$

avec :

- \(F_i\) : facteur de forme entre l'individu et la surface \(i\) ;
- \(T_i\) : température radiative de la surface \(i\).



Dans les situations extérieures, un terme lié au rayonnement solaire peut être ajouté selon les conventions du modèle.

🔗 Ressource complémentaire : [Calcul de MRT](https://lhypercube.arep.fr/thematiques/confort/calcul_mrt/)


## 5. Méthodes de calcul des facteurs de forme

### 5.1 Méthodes analytiques

Elles donnent des résultats exacts ou quasi exacts pour des configurations simples : plaques parallèles, rectangles perpendiculaires, cylindres, sphères, etc.

Quelques sources de cas analytiques : [thermalradiation.net](https://thermalradiation.net/tablecon.html) ou [Fchart.com](https://fchart.com/ees/heat_transfer_library/shape_factors/hs22.htm). 

Elles sont très utiles pour :

- comprendre les tendances,
- valider un code,
- construire des cas tests.

Limite : elles ne couvrent pas les géométries complexes.

### 5.2 Méthodes Monte Carlo

Le principe est de lancer un grand nombre de rayons depuis une surface et de compter les intersections avec les autres surfaces.

Avantages :

- méthode très générale,
- gestion naturelle des obstructions,
- adaptée à des scènes complexes.

Limites :

- bruit statistique,
- convergence parfois lente,
- besoin d'un grand nombre de rayons pour les faibles facteurs de forme.

### 5.3 Méthodes hémicube ou raster

Ces méthodes projettent la scène sur un hémicube ou une discrétisation angulaire autour d'une surface.

Avantages :

- efficaces dans certains contextes graphiques,
- gestion possible des masques.

Limites :

- précision dépendante de la résolution,
- artefacts de discrétisation,
- moins adaptées lorsque l'on cherche une formulation numérique contrôlée.

### 5.4 Intégration numérique directe

On peut calculer directement l'intégrale surfacique :

$$
F_{i,j} = \frac{1}{S_i} \iint_{S_i} \iint_{S_j}
\frac{\cos\theta_i \cos\theta_j}{\pi r^2} \, dS_j \, dS_i
$$

Cette approche est générale, mais coûteuse : elle nécessite une intégration sur deux surfaces.



### 5.5 Transformation en intégrale de contour

Pour des polygones plans, il est possible de transformer l'intégrale de surface en intégrale de contour.

L'idée est de remplacer l'intégration sur les surfaces par une somme d'intégrales associées aux paires d'arêtes. 

!!! success "Lien avec la formation"
    C'est cette famille de méthodes qui est utilisée dans `pyViewFactor` : elle est bien adaptée aux facettes planes issues de maillages.

<figure>
  <img src="../assets/schema_elem_faces.png"
       alt="Caractéristiques géométriques des surfaces élémentaires">

  <figcaption>
    Caractéristiques géométriques des surfaces élémentaires
  </figcaption>
</figure>

L'idée clé provient de **Mazumder _et al._, 2012**[^1] qui permettent de passer de la première intégrale ci-dessous à la seconde : 

\begin{equation}\label{eq:dbl_integral}
F_{i,j} = \frac{1}{S_i} \iint_{S_i} \iint_{S_j}  \frac{\cos(\theta_i)\cos(\theta_j)}{\delta^2} \,dS_j \,dS_j
\end{equation}

\begin{equation}\label{eq:cont_integral}
F_{i,j} = \frac{1}{2\pi S_i} \oint_{\Gamma_i} \oint_{\Gamma_j}  \ln(\delta_{k,l}) \,d\gamma_l \,d\gamma_k
\end{equation}

Et surtout, dans cette seconde intégrale, d'opérer un changement de variable : 

$$
\begin{cases}
d\overrightarrow{\gamma_{k,k+1}} = \overrightarrow{P_k P_{k+1}} \, d\lambda_P \\
d\overrightarrow{\gamma_{l,l+1}} = \overrightarrow{Q_l Q_{l+1}} \, d\lambda_Q
\end{cases}
$$

Puis de décomposer la distance \(\delta_{k,l}\) suivant : 

$$
\overrightarrow{\delta_{k,l}} =
\overrightarrow{P_k Q_l}
+ \lambda_Q \, \overrightarrow{Q_l Q_{l+1}}
- \lambda_P \, \overrightarrow{P_k P_{k+1}}
$$

On se retrouve à intégrer le \(\log \) d'un polynôme de degré 2, entre 0 et 1. _Et là, de nombreuses méthodes numériques existent !_

Plus de détails [dans le papier IBPSA 2022](https://www.researchgate.net/publication/360835982_Calcul_des_facteurs_de_forme_entre_polygones_-Application_a_la_thermique_urbaine_et_aux_etudes_de_confort).
 
[^1]: Mazumder and Ravishankar, 2012, __General procedure for calculation of diffuse view factors between arbitrary planar polygons__ [DOI](https://www.sciencedirect.com/science/article/pii/S0017931012006023)




# 6. Intégration numérique : le noyau SA-30

Une fois l'intégrale transformée en intégrale de contour, il reste à évaluer numériquement une expression de la forme :

$$
I = \int_0^1 \int_0^1 \ln\!\left(A\,s^2 + B\,s\,t + C\,t^2 + \cdots\right) ds\, dt
$$

où les coefficients dépendent de la paire d'arêtes considérée.

Depuis la **v1.1.0**, `pyViewFactor` utilise le noyau **SA-30** (*semi-analytique, 30 points*) : l'intégrale intérieure est évaluée **en forme fermée**, pour chaque point de quadrature de Gauss–Legendre sur l'intégrale extérieure.

### 6.1 Idée centrale

Le discriminant \(\Delta = 4AC - B^2\) détermine la branche analytique :

| Cas | Condition | Traitement |
|---|---|---|
| Faces disjointes | \(\Delta > 0\) | Formule arc-tangente |
| Faces adjacentes / coplanaires | \(\Delta \leq 0\) | Décomposition en racines réelles |

Les faces adjacentes (sommet ou arête en commun) — cas les plus délicats — sont ainsi traitées **exactement**, sans décalage `epsilon` ni biais structurel.

### 6.2 Avantages par rapport à l'ancienne stratégie hybride

Les versions antérieures à v1.1.0 utilisaient Gauss–Legendre pour les faces disjointes et `scipy.dblquad` avec un décalage `epsilon` pour les faces adjacentes. Cette approche induisait un biais systématique d'environ 0,16 % sur les maillages fermés.

Le noyau SA-30 :

- **supprime ce biais** en traitant les cas adjacents de manière exacte,
- est **compilé avec Numba** (`prange`) pour une parallélisation automatique,
- atteint un **gain de ×33** sur un cas urbain de 382 faces.

!!! success "Pour aller plus loin"
    Le détail mathématique complet (dérivation de la forme fermée, mesures de performance, diagramme de Pareto précision/vitesse) est présenté dans [l'article de blog dédié à la v1.1.0](https://lhypercube.arep.fr/blog/pyviewfactor_v110/).
