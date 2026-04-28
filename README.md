# SIMUREX 2026 — Facteurs de Formes & Echanges Radiatifs

Dépôt associé à la session **SIMUREX 2026 ([IBPSA France](https://conference2026.ibpsa.fr/))**
dédiée au calcul des **facteurs de forme** et à leur utilisation dans les calculs radiatifs, 
dans le domaine de la thermique du bâtiment ou du confort thermique.

## 🔗 Accès au site

👉 https://matbog.github.io/simurex2026-pvf/

Le site contient :
- une introduction scientifique aux facteurs de forme,
- un guide de prise en main Python,
- des exercices progressifs,
- une présentation de la bibliothèque `pyviewfactor`.

## 📁 Contenu du dépôt

Ce dépôt regroupe :
```bash
.
├── docs/ # Sources du site MkDocs
├── session/ # Scripts Python des exercices
├── session/src_data/ # Données et géométries
├── requirements.txt
└── README.md
```

### 📘 Documentation
- [`get-started.md`](docs/get-started.md) — installation et environnement Python,
- [`scientific-background.md`](docs/scientific-background.md) — rappels physiques,
- [`exercises.md`](docs/exercises.md) — exercices guidés,
- [`about-pyviewfactor.md`](docs/about-pyviewfactor.md) — présentation de la bibliothèque.

## 🚀 Démarrage rapide

```bash
git clone https://github.com/matbog/simurex2026-pvf.git
cd simurex2026-pvf/session

conda create -n simurex-pvf python=3.11
conda activate simurex-pvf

pip install -r requirements.txt
pip install pyviewfactor
```
Ensuite, lancez un script dans le dossier `session/.`
    
Voir le guide complet : [Get Started](https://matbog.github.io/simurex2026-pvf/get-started/)


## 📄 Licence

- Le contenu pédagogique de ce dépôt (cours, documentation, exercices) est sous licence  [**CC BY 4.0**](https://creativecommons.org/licenses/by/4.0/)
- La bibliothèque `pyviewfactor` est sous licence **MIT** (voir [dépôt dédié](https://gitlab.com/arep-dev/pyViewFactor))


## 👨‍🏫 Auteurs

[Mateusz Bogdan — AREP L’hypercube](https://github.com/matbog)

[Edouard Walther — INSA Strasbourg / ICube](https://github.com/eddes)
