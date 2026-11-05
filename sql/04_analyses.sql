CREATE DATABASE IF NOT EXISTS pizza_db CHARACTER SET utf8mb4;

USE pizza_db;
SHOW TABLES;

SELECT COUNT(*) FROM orders;

SET GLOBAL local_infile = 1;

DROP TABLE pizza_db.orders;

CREATE USER IF NOT EXISTS 'pizza_user'@'localhost' IDENTIFIED BY 'pizza2026';
GRANT ALL PRIVILEGES ON pizza_db.* TO 'pizza_user'@'localhost';
SET GLOBAL local_infile = 1;


USE pizza_db;
SELECT 'pizza_types' AS table_name, COUNT(*) AS nb FROM pizza_types
UNION ALL SELECT 'pizzas', COUNT(*) FROM pizzas
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_details', COUNT(*) FROM order_details;

USE pizza_db;

-- Clés primaires (identifiant unique de chaque ligne)
ALTER TABLE pizza_types MODIFY pizza_type_id VARCHAR(50) NOT NULL, ADD PRIMARY KEY (pizza_type_id);
ALTER TABLE pizzas      MODIFY pizza_id VARCHAR(50) NOT NULL, ADD PRIMARY KEY (pizza_id);
ALTER TABLE orders      ADD PRIMARY KEY (order_id);
ALTER TABLE order_details ADD PRIMARY KEY (order_details_id);

-- Clés étrangères (les liens entre les tables)
ALTER TABLE pizzas        ADD FOREIGN KEY (pizza_type_id) REFERENCES pizza_types(pizza_type_id);
ALTER TABLE order_details ADD FOREIGN KEY (order_id) REFERENCES orders(order_id);
ALTER TABLE order_details ADD FOREIGN KEY (pizza_id) REFERENCES pizzas(pizza_id);

USE pizza_db;

-- ----- Création de la vue -----
CREATE OR REPLACE VIEW v_ventes AS
SELECT  od.order_details_id,
        o.order_id,
        o.order_date,
        o.order_time,
        p.pizza_id,
        p.size,
        p.price,
        od.quantity,
        od.quantity * p.price AS montant,   -- chiffre d'affaires de la ligne
        pt.name,
        pt.category
FROM order_details od
JOIN orders      o  ON od.order_id     = o.order_id        -- lien commande
JOIN pizzas      p  ON od.pizza_id     = p.pizza_id        -- lien pizza (taille, prix)
JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id; -- lien type (nom, catégorie)

-- ----- Vérification : aperçu des 10 premières lignes -----
SELECT * FROM v_ventes LIMIT 10;

-- ÉTAPE 3 : KPI GLOBAUX DE L'ACTIVITÉ (année 2015)

USE pizza_db;

-- ----- Tableau de bord : les 7 indicateurs clés -----
SELECT
    ROUND(SUM(montant), 2)                                   AS chiffre_affaires,      -- total encaissé
    COUNT(DISTINCT order_id)                                 AS nb_commandes,          -- tickets distincts
    SUM(quantity)                                            AS nb_pizzas_vendues,     -- volume
    ROUND(SUM(montant) / COUNT(DISTINCT order_id), 2)        AS panier_moyen,          -- CA par commande
    ROUND(SUM(quantity) / COUNT(DISTINCT order_id), 2)       AS pizzas_par_commande,   -- taille du panier
    COUNT(DISTINCT order_date)                               AS jours_ouverts,         -- jours d'activité
    ROUND(COUNT(DISTINCT order_id) / COUNT(DISTINCT order_date), 1) AS commandes_par_jour -- fréquentation
FROM v_ventes;

-- Q1 : ÉVOLUTION DU CHIFFRE D'AFFAIRES PAR MOIS
-- Objectif : repérer la saisonnalité (mois forts / faibles)

SELECT
    MONTH(order_date)                 AS num_mois,       -- 1 à 12 (pour trier)
    MONTHNAME(order_date)             AS mois,           -- nom du mois
    ROUND(SUM(montant), 2)            AS chiffre_affaires,
    COUNT(DISTINCT order_id)          AS nb_commandes
FROM v_ventes
GROUP BY num_mois, mois
ORDER BY num_mois;

-- =====================================================
-- Q2 : FRÉQUENTATION PAR JOUR DE LA SEMAINE
-- Objectif : adapter le planning du personnel
-- =====================================================

SELECT
    WEEKDAY(order_date)                                AS num_jour,         -- 0 = lundi ... 6 = dimanche
    DAYNAME(order_date)                                AS jour,
    COUNT(DISTINCT order_id)                           AS nb_commandes,
    ROUND(COUNT(DISTINCT order_id)
          / COUNT(DISTINCT order_date), 1)             AS moy_commandes_par_jour,
    ROUND(SUM(montant), 2)                             AS chiffre_affaires
FROM v_ventes
GROUP BY num_jour, jour
ORDER BY num_jour;

-- Q3 : COMMANDES PAR HEURE DE LA JOURNÉE
-- Objectif : identifier les heures de pointe (rush)
SELECT
    HOUR(order_time)              AS heure,
    COUNT(DISTINCT order_id)      AS nb_commandes,
    ROUND(SUM(montant), 2)        AS chiffre_affaires
FROM v_ventes
GROUP BY heure
ORDER BY heure;

-- Q4 bis : LES 5 PIZZAS LES MOINS RENTABLES (FLOP 5)
-- Objectif : candidates au retrait de la carte

SELECT
    name,
    category,
    SUM(quantity)            AS qte_vendue,
    ROUND(SUM(montant), 2)   AS chiffre_affaires
FROM v_ventes
GROUP BY name, category
ORDER BY chiffre_affaires ASC      -- ASC = du plus petit au plus grand
LIMIT 5;

-- Q5 : PART DU CHIFFRE D'AFFAIRES PAR CATÉGORIE
-- Objectif : voir l'équilibre de la carte

SELECT
    category,
    SUM(quantity)                                              AS qte_vendue,
    ROUND(SUM(montant), 2)                                     AS chiffre_affaires,
    ROUND(100 * SUM(montant) / SUM(SUM(montant)) OVER (), 1)   AS part_ca_pct   -- % du total
FROM v_ventes
GROUP BY category
ORDER BY chiffre_affaires DESC;

-- Q6 : VENTES PAR TAILLE DE PIZZA
-- Objectif : orienter les stocks (pâtes, boîtes) et les prix

SELECT
    size                                                         AS taille,
    SUM(quantity)                                                AS qte_vendue,
    ROUND(100 * SUM(quantity) / SUM(SUM(quantity)) OVER (), 1)   AS part_qte_pct,
    ROUND(SUM(montant), 2)                                       AS chiffre_affaires,
    ROUND(100 * SUM(montant) / SUM(SUM(montant)) OVER (), 1)     AS part_ca_pct
FROM v_ventes
GROUP BY size
ORDER BY chiffre_affaires DESC;

-- Q7 : NOMBRE DE PIZZAS PAR COMMANDE
-- Objectif : tester l'idée d'une offre "duo" / "famille"

WITH paniers AS (                                  -- CTE : 1 ligne par commande
    SELECT
        order_id,
        SUM(quantity) AS nb_pizzas
    FROM order_details
    GROUP BY order_id
)
SELECT
    nb_pizzas,
    COUNT(*)                                            AS nb_commandes,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)    AS part_pct
FROM paniers
GROUP BY nb_pizzas
ORDER BY nb_pizzas;

-- Q8 : PIZZA N°1 DE CHAQUE CATÉGORIE
-- Objectif : savoir quelle pizza mettre en avant par gamme
WITH ventes_pizza AS (
    SELECT
        category,
        name,
        ROUND(SUM(montant), 2) AS chiffre_affaires
    FROM v_ventes
    GROUP BY category, name
)
SELECT category, name, chiffre_affaires
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY category     
                              ORDER BY chiffre_affaires DESC) AS rang  
    FROM ventes_pizza
) classement
WHERE rang = 1;                           


-- =====================================================
-- PRÉPARATION STREAMLIT : UTILISATEUR DÉDIÉ À L'APPLI
-- (bonne pratique : l'appli n'utilise jamais root)
-- =====================================================

CREATE USER IF NOT EXISTS 'pizza_user'@'localhost' IDENTIFIED BY 'pizza2026';
GRANT SELECT ON pizza_db.* TO 'pizza_user'@'localhost';   -- lecture seule           