# =====================================================
# APPLICATION STREAMLIT — PLATO'S PIZZA
# Tableau de bord interactif branché sur MySQL (pizza_db)
# =====================================================

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import bindparam, create_engine, text

# ----- Configuration de la page -----
st.set_page_config(page_title="Plato's Pizza", page_icon="🍕", layout="wide")

# ----- Palette accessible (daltonisme) : bleus + gris, ni rouge ni vert -----
COULEUR = "#1F4E79"      # bleu foncé : la valeur mise en avant
MOYEN = "#4A7BB7"        # bleu moyen
CLAIR = "#BDD7EE"        # bleu clair : les autres valeurs
GRIS = "#8C8C8C"         # gris : la valeur la plus faible
PALETTE = [COULEUR, MOYEN, "#9DC3E6", GRIS]
px.defaults.color_discrete_sequence = PALETTE   # appliquée à tous les graphiques
px.defaults.template = "plotly_white"           # fond blanc épuré

# ----- Animations CSS : graphiques qui apparaissent, barres qui poussent, courbes qui se tracent -----
st.html("""
<style>
    /* 1. Chaque bloc (graphique, KPI) apparaît en glissant vers le haut */
    [data-testid="stPlotlyChart"], [data-testid="stMetric"] {
        animation: apparition 0.8s ease-out both;
    }
    @keyframes apparition {
        from { opacity: 0; transform: translateY(25px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    /* 2. Les barres verticales poussent depuis le bas */
    [data-testid="stPlotlyChart"] .bars path {
        transform-box: fill-box; transform-origin: bottom;
        animation: pousse 1s ease-out both;
    }
    @keyframes pousse { from { transform: scaleY(0); } to { transform: scaleY(1); } }
    /* 3. Les barres horizontales (Top / Flop) poussent depuis la gauche */
    .st-key-barres-h [data-testid="stPlotlyChart"] .bars path {
        transform-origin: left; animation-name: pousse-h;
    }
    @keyframes pousse-h { from { transform: scaleX(0); } to { transform: scaleX(1); } }
    /* 4. Les courbes se dessinent de gauche à droite */
    [data-testid="stPlotlyChart"] .scatterlayer .js-line {
        stroke-dasharray: 3000; stroke-dashoffset: 3000;
        animation: trace 1.8s ease-out forwards;
    }
    @keyframes trace { to { stroke-dashoffset: 0; } }
    /* 5. Les parts de camembert s'ouvrent depuis le centre */
    [data-testid="stPlotlyChart"] .slice path.surface {
        transform-box: fill-box; transform-origin: center;
        animation: ouvre 0.9s ease-out both;
    }
    @keyframes ouvre { from { transform: scale(0.3); opacity: 0; } to { transform: scale(1); opacity: 1; } }
    /* 6. Les cartes ETL et les étapes du rôle arrivent une par une */
    .etl-carte, .suivi-etape { animation: apparition 0.6s ease-out both; }
    .etl-carte:nth-of-type(3), .suivi-etape:nth-child(2) { animation-delay: 0.15s; }
    .etl-carte:nth-of-type(5), .suivi-etape:nth-child(3) { animation-delay: 0.30s; }
    .etl-carte:nth-of-type(7), .suivi-etape:nth-child(4) { animation-delay: 0.45s; }
    .etl-carte:nth-of-type(9) { animation-delay: 0.60s; }
</style>
""")

MOIS = ["Janv", "Févr", "Mars", "Avr", "Mai", "Juin",
        "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


# =====================================================
# CONNEXION À MYSQL + FONCTIONS UTILES
# =====================================================
@st.cache_resource
def get_engine():
    return create_engine("mysql+pymysql://pizza_user:pizza2026@localhost:3306/pizza_db")


@st.cache_data
def run_query(sql, params=None):
    """Exécute une requête SQL (avec paramètres) et renvoie un DataFrame pandas."""
    requete = text(sql)
    if params:
        for nom, valeur in params.items():
            if isinstance(valeur, list):          # une liste devient IN (...)
                requete = requete.bindparams(bindparam(nom, expanding=True))
    with get_engine().connect() as conn:
        return pd.read_sql(requete, conn, params=params)


def afficher(fig):
    """Affiche un graphique plotly avec un style sobre et professionnel."""
    fig.update_layout(margin=dict(t=60, b=10, l=10, r=10),
                      font=dict(size=13), title_font=dict(size=17))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def couleurs_barres(valeurs, nb_top=1):
    """Bleu foncé = meilleures valeurs, gris = la plus faible, bleu clair = le reste."""
    seuil = sorted(valeurs, reverse=True)[nb_top - 1]
    mini = min(valeurs)
    return [COULEUR if v >= seuil else GRIS if v == mini else CLAIR for v in valeurs]


def en_k(v):
    """Formate un montant : 72557 -> '72,6 k$'."""
    return f"{v / 1000:.1f} k$".replace(".", ",")


# =====================================================
# BARRE LATÉRALE : NAVIGATION
# =====================================================
st.sidebar.title("🍕 Plato's Pizza")
page = st.sidebar.radio("Navigation", [
    "🏠 Accueil & profil",
    "📊 KPI",
    "📈 Ventes dans le temps",
    "🍕 Produits",
    "🛒 Paniers",
    "💡 Recommandations",
])

# ----- Pas de filtres : on analyse toute l'année 2015 et toutes les pizzas -----
mois_debut, mois_fin = 1, 12
liste_categories = run_query(
    "SELECT DISTINCT category FROM pizza_types ORDER BY category")["category"].tolist()
categories = liste_categories
tailles = ["S", "M", "L", "XL", "XXL"]

# Clause WHERE commune (requêtes paramétrées = pas d'injection SQL)
FILTRE = """
    WHERE MONTH(order_date) BETWEEN :m1 AND :m2
      AND category IN :cats
      AND size IN :tailles
"""
P = {"m1": mois_debut, "m2": mois_fin, "cats": categories, "tailles": tailles}
PERIODE = f"{MOIS[mois_debut - 1]} → {MOIS[mois_fin - 1]} 2015"


# =====================================================
# PAGE 1 : ACCUEIL & PROFIL
# =====================================================
if page == "🏠 Accueil & profil":
    st.title("🍕 Plato's Pizza — Analyse de l'activité 2015")

    col_g, col_d = st.columns([1, 2])
    with col_g:
        st.subheader("👩‍💻 Profil")
        st.markdown("**Suz** — Data Analyst")
        st.caption("Formation Data Analyst · Simplon")

        # ----- Mon rôle : schéma de suivi vertical (HTML + CSS) -----
        roles = [
            ("🗂️", "Gestion du dataset", "4 fichiers CSV Pizza"),
            ("🗄️", "Base MySQL", "Création et contrôle qualité"),
            ("🔎", "Analyse", "Requêtes SQL et traitement Python"),
            ("📊", "Tableau de bord", "Conception Streamlit"),
        ]
        etapes_html = "".join(f"""
            <div class="suivi-etape">
                <div class="suivi-rond">{icone}</div>
                <div class="suivi-texte"><b>{titre}</b><span>{detail}</span></div>
                <div class="suivi-ok">✔</div>
            </div>""" for icone, titre, detail in roles)
        st.html(f"""
            <style>
                .suivi-titre {{ font-weight: 700; color: #1F4E79; margin: 4px 0 6px; }}
                .suivi {{ position: relative; }}
                .suivi::before {{ content: ""; position: absolute; left: 21px; top: 24px;
                                  bottom: 24px; width: 3px; background: #C9D9EC; }}
                .suivi-etape {{ display: flex; align-items: center; gap: 12px;
                                margin: 10px 0; position: relative; }}
                .suivi-rond {{ width: 44px; height: 44px; flex-shrink: 0; border-radius: 50%;
                               background: #1F4E79; border: 3px solid #DCE8F5; z-index: 1;
                               display: flex; align-items: center; justify-content: center;
                               font-size: 20px; }}
                .suivi-texte {{ flex: 1; display: flex; flex-direction: column;
                                background: #F4F8FC; border: 1px solid #C9D9EC;
                                border-radius: 10px; padding: 8px 12px; }}
                .suivi-texte b {{ color: #1F4E79; }}
                .suivi-texte span {{ font-size: 0.85rem; color: #555; }}
                .suivi-ok {{ color: #1F4E79; font-weight: 700; font-size: 18px; }}
            </style>
            <div class="suivi-titre">Mon rôle sur ce dossier</div>
            <div class="suivi">{etapes_html}</div>
        """)
    with col_d:
        st.subheader("🎯 La mission")
        st.markdown("""
La direction de **Plato's Pizza** souhaite **mieux comprendre son activité**
et **appuyer ses décisions commerciales** : quand les clients commandent,
quelles pizzas rapportent, comment augmenter le panier moyen.
""")

    st.divider()
    # ----- Schéma du processus ETL (HTML + CSS) -----
    st.subheader("🔄 Le processus ETL : de la donnée brute au tableau de bord")
    etapes = [
        ("📥", "1. EXTRACT", "Extraction",
         ["Source : Maven Analytics", "Pizza Place Sales (2015)", "4 fichiers CSV"]),
        ("🧹", "2. TRANSFORM", "Nettoyage & contrôle",
         ["Encodage corrigé en UTF-8", "Dates et heures typées", "COUNT(*) : 2 imports corrigés"]),
        ("🗄️", "3. LOAD", "Chargement MySQL",
         ["Base pizza_db", "4 tables reliées", "Clés PK / FK, 0 orphelin"]),
        ("🔎", "4. ANALYSE", "SQL & Python",
         ["Vue v_ventes (3 JOIN)", "KPI + 8 questions métier", "CTE, fonctions de fenêtre"]),
        ("📊", "5. RESTITUTION", "Streamlit",
         ["Requêtes SQL en direct", "6 pages + Top / Flop interactif", "Recommandations"]),
    ]
    cartes = []
    for icone, titre, sous_titre, points in etapes:
        liste = "".join(f"<li>{p}</li>" for p in points)
        cartes.append(f"""
            <div class="etl-carte">
                <div class="etl-icone">{icone}</div>
                <div class="etl-titre">{titre}</div>
                <div class="etl-sous-titre">{sous_titre}</div>
                <ul>{liste}</ul>
            </div>""")
    fleche = '<div class="etl-fleche">➜</div>'
    st.html(f"""
        <style>
            .etl-flux {{ display: flex; flex-wrap: nowrap; align-items: stretch;
                         gap: 6px; margin: 10px 0 20px; }}
            .etl-carte {{ flex: 1 1 0; min-width: 0; background: #F4F8FC;
                          border: 1px solid #C9D9EC; border-top: 5px solid #1F4E79;
                          border-radius: 12px; padding: 14px 12px;
                          box-shadow: 0 2px 6px rgba(31, 78, 121, 0.12); }}
            .etl-icone {{ font-size: 30px; text-align: center; }}
            .etl-titre {{ font-weight: 700; color: #1F4E79; text-align: center;
                          letter-spacing: 1px; margin-top: 4px; }}
            .etl-sous-titre {{ color: #4A7BB7; text-align: center; font-size: 0.85rem;
                               margin-bottom: 8px; }}
            .etl-carte ul {{ padding-left: 18px; margin: 0; font-size: 0.85rem; color: #333; }}
            .etl-fleche {{ display: flex; align-items: center; font-size: 26px; color: #4A7BB7; }}
            @media (max-width: 900px) {{
                .etl-flux {{ flex-wrap: wrap; }}
                .etl-carte {{ flex: 1 1 45%; }}
                .etl-fleche {{ display: none; }}
            }}
        </style>
        <div class="etl-flux">{fleche.join(cartes)}</div>
    """)

    st.subheader("🧱 Les données dans la base MySQL")
    nb = run_query("""
        SELECT 'orders' AS table_sql, 'Commandes (date, heure)' AS contenu, COUNT(*) AS lignes FROM orders
        UNION ALL SELECT 'order_details', 'Lignes de commande (pizza, quantité)', COUNT(*) FROM order_details
        UNION ALL SELECT 'pizzas', 'Pizzas (taille, prix)', COUNT(*) FROM pizzas
        UNION ALL SELECT 'pizza_types', 'Types (nom, catégorie, ingrédients)', COUNT(*) FROM pizza_types
    """)
    st.dataframe(nb, width="stretch", hide_index=True)

# =====================================================
# PAGE 2 : KPI
# =====================================================
elif page == "📊 KPI":
    st.title("📊 Indicateurs clés")
    st.caption(f"Période : {PERIODE} · données lues en direct dans MySQL")

    kpi = run_query(f"""
        SELECT ROUND(SUM(montant), 2)                             AS ca,
               COUNT(DISTINCT order_id)                           AS commandes,
               SUM(quantity)                                      AS pizzas,
               ROUND(SUM(montant) / COUNT(DISTINCT order_id), 2)  AS panier,
               ROUND(SUM(quantity) / COUNT(DISTINCT order_id), 2) AS pizzas_cmd,
               ROUND(COUNT(DISTINCT order_id) / COUNT(DISTINCT order_date), 1) AS cmd_jour
        FROM v_ventes {FILTRE}
    """, P).iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Chiffre d'affaires", f"{kpi['ca']:,.0f} $".replace(",", " "), border=True)
    c2.metric("🧾 Commandes", f"{int(kpi['commandes']):,}".replace(",", " "), border=True)
    c3.metric("🍕 Pizzas vendues", f"{int(kpi['pizzas']):,}".replace(",", " "), border=True)
    c4, c5, c6 = st.columns(3)
    c4.metric("🛒 Panier moyen", f"{kpi['panier']:.2f} $", border=True)
    c5.metric("📦 Pizzas / commande", f"{kpi['pizzas_cmd']:.2f}", border=True)
    c6.metric("📅 Commandes / jour", f"{kpi['cmd_jour']:.1f}", border=True)

    st.divider()
    st.subheader("Évolution mensuelle des KPI")
    df = run_query(f"""
        SELECT MONTH(order_date)                                  AS num_mois,
               ROUND(SUM(montant), 2)                             AS ca,
               COUNT(DISTINCT order_id)                           AS commandes,
               ROUND(SUM(montant) / COUNT(DISTINCT order_id), 2)  AS panier,
               ROUND(SUM(quantity) / COUNT(DISTINCT order_id), 2) AS pizzas_cmd
        FROM v_ventes {FILTRE}
        GROUP BY num_mois ORDER BY num_mois
    """, P)
    df["mois"] = df["num_mois"].apply(lambda m: MOIS[m - 1])

    col_g, col_d = st.columns(2)
    with col_g:
        afficher(px.area(df, x="mois", y="ca", title="💰 Chiffre d'affaires",
                         labels={"mois": "", "ca": "CA ($)"},
                         color_discrete_sequence=[COULEUR]))
        afficher(px.line(df, x="mois", y="panier", markers=True, title="🛒 Panier moyen",
                         labels={"mois": "", "panier": "Panier moyen ($)"},
                         color_discrete_sequence=[MOYEN]))
    with col_d:
        afficher(px.bar(df, x="mois", y="commandes", title="🧾 Nombre de commandes",
                        labels={"mois": "", "commandes": "Commandes"},
                        color_discrete_sequence=["#9DC3E6"]))
        afficher(px.line(df, x="mois", y="pizzas_cmd", markers=True,
                         title="📦 Pizzas par commande",
                         labels={"mois": "", "pizzas_cmd": "Pizzas / commande"},
                         color_discrete_sequence=[GRIS]))

# =====================================================
# PAGE 3 : VENTES DANS LE TEMPS
# =====================================================
elif page == "📈 Ventes dans le temps":
    st.title("📈 Quand les clients commandent-ils ?")
    st.caption(f"Période : {PERIODE} · bleu foncé = meilleure valeur, gris = plus faible")

    # Q1 : CA par mois -> histogramme avec étiquettes
    df_mois = run_query(f"""
        SELECT MONTH(order_date) AS num_mois, ROUND(SUM(montant), 2) AS chiffre_affaires
        FROM v_ventes {FILTRE}
        GROUP BY num_mois ORDER BY num_mois
    """, P)
    df_mois["mois"] = df_mois["num_mois"].apply(lambda m: MOIS[m - 1])
    fig = px.bar(df_mois, x="mois", y="chiffre_affaires",
                 text=df_mois["chiffre_affaires"].apply(en_k),
                 title="Chiffre d'affaires par mois",
                 labels={"mois": "", "chiffre_affaires": "CA ($)"})
    fig.update_traces(marker_color=couleurs_barres(df_mois["chiffre_affaires"].tolist()),
                      textposition="outside", textfont_size=13, cliponaxis=False)
    fig.update_yaxes(range=[0, df_mois["chiffre_affaires"].max() * 1.15], showgrid=False,
                     visible=False)
    afficher(fig)

    col_g, col_d = st.columns(2)
    with col_g:   # Q2 : jours de la semaine
        df_jour = run_query(f"""
            SELECT WEEKDAY(order_date) AS num_jour,
                   ROUND(COUNT(DISTINCT order_id) / COUNT(DISTINCT order_date), 1) AS moy_commandes
            FROM v_ventes {FILTRE}
            GROUP BY num_jour ORDER BY num_jour
        """, P)
        df_jour["jour"] = df_jour["num_jour"].apply(lambda j: JOURS[j])
        fig = px.bar(df_jour, x="jour", y="moy_commandes", text="moy_commandes",
                     title="Commandes moyennes par jour",
                     labels={"jour": "", "moy_commandes": "Commandes / jour"})
        fig.update_traces(marker_color=couleurs_barres(df_jour["moy_commandes"].tolist()),
                          textposition="outside", cliponaxis=False)
        fig.update_yaxes(range=[0, df_jour["moy_commandes"].max() * 1.15], visible=False)
        afficher(fig)
    with col_d:   # Q3 : heures (les 5 heures de rush en bleu foncé)
        df_heure = run_query(f"""
            SELECT HOUR(order_time) AS heure, COUNT(DISTINCT order_id) AS commandes
            FROM v_ventes {FILTRE}
            GROUP BY heure ORDER BY heure
        """, P)
        df_heure["heure_txt"] = df_heure["heure"].astype(str) + "h"
        fig = px.bar(df_heure, x="heure_txt", y="commandes",
                     title="Commandes par heure : 2 rushs (midi et soir)",
                     labels={"heure_txt": "", "commandes": "Commandes"})
        fig.update_traces(marker_color=couleurs_barres(df_heure["commandes"].tolist(), nb_top=5))
        fig.update_yaxes(showgrid=True, gridcolor="#EEEEEE")
        afficher(fig)

    # Carte de chaleur jour x heure (bleus, valeurs affichées)
    df_hm = run_query(f"""
        SELECT WEEKDAY(order_date) AS num_jour, HOUR(order_time) AS heure,
               COUNT(DISTINCT order_id) AS commandes
        FROM v_ventes {FILTRE} AND HOUR(order_time) BETWEEN 11 AND 22
        GROUP BY num_jour, heure
    """, P)
    df_hm["jour"] = df_hm["num_jour"].apply(lambda j: JOURS[j])
    pivot = df_hm.pivot_table(index="jour", columns="heure", values="commandes", fill_value=0)
    pivot = pivot.reindex([j for j in JOURS if j in pivot.index])
    pivot.columns = [f"{h}h" for h in pivot.columns]
    fig = px.imshow(pivot, aspect="auto", text_auto=True, color_continuous_scale="Blues",
                    title="Carte de chaleur : commandes par jour et par heure (11h-22h)",
                    labels={"x": "", "y": "", "color": "Commandes"})
    fig.update_traces(xgap=3, ygap=3, textfont_size=11)
    fig.update_xaxes(side="top")
    afficher(fig)

# =====================================================
# PAGE 4 : PRODUITS
# =====================================================
elif page == "🍕 Produits":
    st.title("🍕 Quelles pizzas rapportent ?")
    st.caption(f"Période : {PERIODE}")

    col_g, col_d = st.columns([1, 3])
    with col_g:
        sens = st.radio("Classement", ["🏆 Top", "📉 Flop"], horizontal=True)
        nb = st.slider("Nombre de pizzas", 3, 15, 5)
    ordre = "DESC" if sens == "🏆 Top" else "ASC"

    # Q4 : top / flop des pizzas
    df_pizzas = run_query(f"""
        SELECT REPLACE(REPLACE(name, 'The ', ''), ' Pizza', '') AS pizza,
               category AS categorie,
               SUM(quantity) AS qte_vendue, ROUND(SUM(montant), 2) AS chiffre_affaires
        FROM v_ventes {FILTRE}
        GROUP BY name, category
        ORDER BY chiffre_affaires {ordre}
        LIMIT :nb
    """, {**P, "nb": nb})
    with col_d, st.container(key="barres-h"):   # clé utilisée par l'animation horizontale
        df_top = df_pizzas.sort_values("chiffre_affaires")
        fig = px.bar(df_top, x="chiffre_affaires", y="pizza", orientation="h",
                     text=df_top["chiffre_affaires"].apply(en_k),
                     color="categorie",
                     color_discrete_map=dict(zip(sorted(liste_categories), PALETTE)),
                     title=f"{sens} {nb} des pizzas par chiffre d'affaires",
                     labels={"chiffre_affaires": "", "pizza": "", "categorie": "Catégorie"})
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_xaxes(visible=False, range=[0, df_top["chiffre_affaires"].max() * 1.18])
        fig.update_layout(legend=dict(orientation="h", y=-0.05))
        afficher(fig)

    col_g, col_d = st.columns(2)
    with col_g:   # Q5 : catégories -> donut avec étiquettes extérieures + total au centre
        df_cat = run_query(f"""
            SELECT category AS categorie, ROUND(SUM(montant), 2) AS chiffre_affaires
            FROM v_ventes {FILTRE}
            GROUP BY category
            ORDER BY chiffre_affaires DESC
        """, P)
        fig = px.pie(df_cat, names="categorie", values="chiffre_affaires", hole=0.55,
                     color="categorie",
                     color_discrete_map=dict(zip(sorted(liste_categories), PALETTE)),
                     title="Part du CA par catégorie")
        fig.update_traces(textinfo="label+percent", textposition="outside",
                          marker=dict(line=dict(color="white", width=3)), sort=False)
        fig.update_layout(showlegend=False, annotations=[dict(
            text=f"<b>{en_k(df_cat['chiffre_affaires'].sum())}</b><br>CA total",
            x=0.5, y=0.5, showarrow=False, font_size=16)])
        afficher(fig)
    with col_d:   # Q6 : tailles -> barres groupées (% volume vs % CA)
        df_taille = run_query(f"""
            SELECT size AS taille, SUM(quantity) AS qte_vendue,
                   ROUND(SUM(montant), 2) AS chiffre_affaires
            FROM v_ventes {FILTRE}
            GROUP BY size
            ORDER BY FIELD(size, 'S', 'M', 'L', 'XL', 'XXL')
        """, P)
        df_taille["Part des pizzas vendues"] = (100 * df_taille["qte_vendue"]
                                                / df_taille["qte_vendue"].sum()).round(1)
        df_taille["Part du CA"] = (100 * df_taille["chiffre_affaires"]
                                   / df_taille["chiffre_affaires"].sum()).round(1)
        df_long = df_taille.melt(id_vars="taille",
                                 value_vars=["Part des pizzas vendues", "Part du CA"],
                                 var_name="indicateur", value_name="pct")
        fig = px.bar(df_long, x="taille", y="pct", color="indicateur", barmode="group",
                     text=df_long["pct"].apply(lambda v: f"{v:.0f} %"),
                     color_discrete_sequence=["#9DC3E6", COULEUR],
                     title="Tailles : la L pèse plus en CA qu'en volume",
                     labels={"taille": "", "pct": "", "indicateur": ""})
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_yaxes(visible=False, range=[0, df_long["pct"].max() * 1.2])
        fig.update_layout(legend=dict(orientation="h", y=1.08, x=0))
        afficher(fig)

    with st.expander("📋 Voir le détail de toutes les pizzas"):
        df_detail = run_query(f"""
            SELECT name AS pizza, category AS categorie,
                   SUM(quantity) AS qte_vendue, ROUND(SUM(montant), 2) AS chiffre_affaires
            FROM v_ventes {FILTRE}
            GROUP BY name, category
            ORDER BY chiffre_affaires DESC
        """, P)
        st.dataframe(df_detail, width="stretch", hide_index=True)

# =====================================================
# PAGE 5 : PANIERS
# =====================================================
elif page == "🛒 Paniers":
    st.title("🛒 Combien de pizzas par commande ?")
    st.caption(f"Période : {PERIODE}")

    # Q7 : nombre de pizzas par commande (CTE)
    df_panier = run_query(f"""
        WITH paniers AS (
            SELECT order_id, SUM(quantity) AS nb_pizzas
            FROM v_ventes {FILTRE}
            GROUP BY order_id
        )
        SELECT CASE WHEN nb_pizzas >= 4 THEN 4 ELSE nb_pizzas END AS groupe,
               COUNT(*) AS commandes
        FROM paniers
        GROUP BY groupe
        ORDER BY groupe
    """, P)
    noms = {1: "1 pizza", 2: "2 pizzas", 3: "3 pizzas", 4: "4 pizzas et +"}
    df_panier["panier"] = df_panier["groupe"].map(noms)
    df_panier["part_pct"] = (100 * df_panier["commandes"]
                             / df_panier["commandes"].sum()).round(1)
    part_solo = df_panier.loc[df_panier["groupe"] == 1, "part_pct"].sum()

    st.metric("Commandes avec une seule pizza", f"{part_solo:.1f} %", border=True)

    # camembert avec la part "1 pizza" détachée
    fig = px.pie(df_panier, names="panier", values="commandes",
                 color="panier",
                 color_discrete_map={"1 pizza": COULEUR, "2 pizzas": MOYEN,
                                     "3 pizzas": "#9DC3E6", "4 pizzas et +": CLAIR},
                 title="Répartition des commandes selon le nombre de pizzas")
    fig.update_traces(sort=False, direction="clockwise", rotation=0,
                      pull=[0.12 if g == 1 else 0 for g in df_panier["groupe"]],
                      textinfo="label+percent", textfont_size=14,
                      marker=dict(line=dict(color="white", width=3)))
    fig.update_layout(showlegend=False, height=500)
    afficher(fig)

# =====================================================
# PAGE 6 : RECOMMANDATIONS
# =====================================================
elif page == "💡 Recommandations":
    st.title("💡 Recommandations à la direction")
    st.caption("Basées sur l'analyse de l'année complète 2015")
    st.markdown("""
| Thème | Constat | Recommandation |
|---|---|---|
| ⏰ Horaires | Rushs 12-13 h et 17-19 h ; quasi aucune commande avant 11 h | Renforcer l'équipe aux heures de pointe, ouvrir à 11 h |
| 📅 Semaine | Vendredi = jour record (~71 cmd/j) ; dimanche = creux (~50) | Renfort le vendredi, offre spéciale le dimanche |
| 📈 Saison | Activité stable, pic en juillet, creux sept.-oct. | Promotions ciblées à la rentrée |
| 🍕 Produits | Podium 100 % Chicken ; Brie Carre dernière (3,7× moins que la n°1) | Mettre en avant les 4 pizzas phares, retirer la Brie Carre |
| 📏 Tailles | La L fait 46 % du CA ; XL + XXL = 1,2 % des ventes | Supprimer la XXL, pousser la taille L |
| 🛒 Panier | 38 % des commandes = 1 seule pizza | Offre « Duo » pour augmenter le panier moyen |
""")
    st.info("**Limites** : une seule année (2015), pas de coûts ni de marges, "
            "pas de données clients (fidélité, livraison ou sur place).")

st.sidebar.divider()
st.sidebar.caption("Source : Maven Analytics — Pizza Place Sales\n\nSQL · Python · Streamlit")