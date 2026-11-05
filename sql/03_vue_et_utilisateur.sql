-- =====================================================
-- 03 : VUE D'ANALYSE ET UTILISATEUR DE L'APPLI
-- =====================================================
USE pizza_db;

-- Création de la vue (les 4 tables réunies + le montant)
CREATE OR REPLACE VIEW v_ventes AS
SELECT od.order_details_id, od.order_id, o.order_date, o.order_time,
       od.pizza_id, p.size, p.price, od.quantity,
       od.quantity * p.price AS montant,
       pt.name, pt.category
FROM order_details od
JOIN orders o       ON od.order_id = o.order_id
JOIN pizzas p       ON od.pizza_id = p.pizza_id
JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id;

-- Création de l'utilisateur de l'appli Streamlit (lecture seule)
CREATE USER IF NOT EXISTS 'pizza_user'@'localhost' IDENTIFIED BY 'pizza2026';
GRANT SELECT ON pizza_db.* TO 'pizza_user'@'localhost';