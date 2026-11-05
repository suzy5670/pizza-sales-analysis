# 🍕 Plato's Pizza – Analyse des ventes 2015 (SQL + Python + Streamlit)

## Objectif
Analyser une année de ventes d'une pizzeria pour aider le gérant à décider :
horaires et personnel, carte, tailles et offres.

## Données
4 fichiers CSV (Maven Analytics) :

| Table | Lignes | Contenu |
|---|---|---|
| orders | 21 350 | date et heure des commandes |
| order_details | 48 620 | pizzas et quantités par commande |
| pizzas | 96 | taille et prix |
| pizza_types | 32 | nom, catégorie, ingrédients |

## Structure du projet
```
pizza-sales/
├── Pizza+Place+Sales/       # CSV d'origine
├── sql/
│   ├── 01_creation_base.sql       # base + tables (clés primaires / étrangères)
│   ├── 02_insertion_donnees.sql   # chargement des données
│   ├── 03_vue_et_utilisateur.sql  # vue v_ventes + utilisateur lecture seule
│   └── 04_analyses.sql            # KPI et questions métier Q1 à Q8
├── notebooks/analyse_python.ipynb # contrôle qualité + Pareto (pandas)
├── app.py                          # application Streamlit
└── requirements.txt
```

## Lancer le projet
1. Dans MySQL Workbench, exécuter dans l'ordre : `01` → `02` → `03`.
2. Installer les librairies : `pip install -r requirements.txt`
3. Lancer l'application : `python -m streamlit run app.py`

## Démarche
- **SQL** : modèle relationnel (clés primaires / étrangères), vue `v_ventes` qui réunit les 4 tables, KPI et 8 questions métier.
- **Python (pandas)** : contrôle qualité (0 manquant, 0 doublon) et analyse de Pareto.
- **Streamlit** : 6 pages (Accueil, KPI, Ventes dans le temps, Produits, Paniers, Recommandations), lues directement depuis la base MySQL.

## Principaux résultats
- **CA 2015 : 817 860 $**, panier moyen **38,31 $**, **2,32 pizzas** par commande.
- **Rush** de 12h à 13h et de 17h à 19h ; le **vendredi** est le jour le plus fort, le **dimanche** le plus creux ; pic des ventes en **juillet**.
- La taille **L** fait **46 %** du CA ; la **XXL** est marginale.
- **38 %** des commandes ne contiennent qu'une seule pizza.
- **22 pizzas sur 32** font 80 % du CA : la carte est équilibrée.

## Recommandations
- Renforcer le personnel aux heures de rush et le vendredi.
- Créer une **offre duo** pour augmenter les commandes à 1 pizza.
- Simplification **ciblée** de la carte : retirer la Brie Carre et la XXL, pas de réduction massive.

## Limites
- Une seule année (2015) : impossible de mesurer une tendance d'une année sur l'autre.
- Pas de coûts, donc on analyse le **CA**, pas la **marge**.
- Pas de données clients (fidélité, livraison ou sur place).
- Anomalie : la Brie Carre existe seulement en taille S, à 23,65 $.