# SIMUREX 2026 - Facteurs de forme et échanges radiatifs

Dépôt associé à la session **SIMUREX 2026** organisée dans le cadre de
[IBPSA France 2026](https://conference2026.ibpsa.fr/).

La formation introduit le calcul des **facteurs de forme** et leur utilisation
dans des calculs radiatifs appliqués à la thermique du bâtiment, au confort
thermique et aux scènes urbaines, avec la bibliothèque Python
[`pyviewfactor`](https://gitlab.com/arep-dev/pyViewFactor).

## 🌐 Site de la formation

Le site est disponible ici :

https://matbog.github.io/simurex2026-pvf/

Il contient les supports de cours, la prise en main Python, les rappels
scientifiques, les exercices et le mini-projet guidé.

## 📁 Contenu du dépôt

```text
.
├── docs/              # Sources Markdown du site MkDocs
├── session/           # Scripts Python utilisés pendant la formation
├── session/src_data/  # Géométries, fichiers météo et données d'entrée
├── requirements.txt   # Dépendances Python de la session
├── mkdocs.yml         # Configuration du site
└── README.md
```

Les sorties générées par les scripts sont écrites dans `session/output/`.

## 📘 Parties du support

- [Démarrer](docs/get-started.md) : installation, environnement Python et vérification des dépendances.
- [Rappels scientifiques](docs/scientific-background.md) : contexte physique des facteurs de forme et des échanges radiatifs.
- [Visibilité et obstruction](docs/visibility_obstruction.md) : normales, visibilité entre faces et tests d'obstruction.
- [Exercices & mini-projet](docs/exercises.md) : progression des scripts de la session.
- [A propos de pyviewfactor](docs/about-pyviewfactor.md) : présentation de la bibliothèque utilisée.

## 🗂️ Organisation des exercices

Les scripts du dossier `session/` sont préfixés selon leur usage pendant la
formation :

- `0_...` : supports de cours pour les notions de base et les comparaisons analytiques ;
- `1_...` : exercice guidé sur visibilité, normales et obstruction ;
- `2_...` : exemples autonomes que les participants peuvent lancer seuls ;
- `3_...` : mini-projet réalisé pas à pas sur une scène urbaine.

Le mini-projet `3_scene_LR_calcul_GLO.py` calcule le **facteur de vue du ciel** (`SVF`) puis
des flux grandes longueurs d'onde sur 24 h à partir d'une géométrie urbaine,
d'un fichier météo EPW et d'un modèle thermique simplifié de surface.

## 🚀 Démarrage rapide

```bash
git clone https://github.com/matbog/simurex2026-pvf.git
cd simurex2026-pvf

conda create -n simurex-pvf python=3.11
conda activate simurex-pvf

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Les exercices peuvent ensuite être lancés depuis le dossier `session/`, par
exemple :

```bash
python session/2_example_viewfactor.py
```

Voir le guide complet : [Démarrer](https://matbog.github.io/simurex2026-pvf/get-started/).

## 🔗 Dépendances principales

Les dépendances de la session sont listées dans `requirements.txt`. Elles
incluent notamment :

- `pyviewfactor` pour les facteurs de forme ;
- `pyvista` pour la lecture, l'écriture et la visualisation des géométries ;
- `numpy`, `pandas` et `matplotlib` pour les calculs et graphiques ;
- `pvlib` pour la position solaire et le rayonnement incident dans le mini-projet.

## © Licence

- Le contenu pédagogique de ce dépôt est sous licence
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- La bibliothèque `pyviewfactor` est sous licence MIT, voir le
  [dépôt dédié](https://gitlab.com/arep-dev/pyViewFactor).

## Auteurs 👨🏻‍🎓 & 👨🏻‍🎓

[Mateusz Bogdan - AREP L'hypercube](https://github.com/matbog)

[Edouard Walther - INSA Strasbourg / ICube](https://github.com/eddes)
