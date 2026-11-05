-- =====================================================
-- 01 : CRÉATION DE LA BASE ET DES TABLES
-- =====================================================

-- Création de la base
CREATE DATABASE IF NOT EXISTS pizza_db CHARACTER SET utf8mb4;
USE pizza_db;

-- Suppression des anciennes tables (pour pouvoir rejouer le script)
DROP VIEW IF EXISTS v_ventes;
DROP TABLE IF EXISTS order_details, orders, pizzas, pizza_types;

-- Table des types de pizza
CREATE TABLE pizza_types (
    pizza_type_id VARCHAR(50) PRIMARY KEY,
    name          VARCHAR(100),
    category      VARCHAR(30),
    ingredients   VARCHAR(255)
);

-- Table des pizzas (type + taille + prix)
CREATE TABLE pizzas (
    pizza_id      VARCHAR(50) PRIMARY KEY,
    pizza_type_id VARCHAR(50),
    size          VARCHAR(5),
    price         DECIMAL(5,2),
    FOREIGN KEY (pizza_type_id) REFERENCES pizza_types(pizza_type_id)
);

-- Table des commandes
CREATE TABLE orders (
    order_id   INT PRIMARY KEY,
    order_date DATE,
    order_time TIME
);

-- Table des lignes de commande (table de faits)
CREATE TABLE order_details (
    order_details_id INT PRIMARY KEY,
    order_id         INT,
    pizza_id         VARCHAR(50),
    quantity         INT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (pizza_id) REFERENCES pizzas(pizza_id)
);