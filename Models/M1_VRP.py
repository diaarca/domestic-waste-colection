import pulp as pl
from python_tools.visualisation_de_graphes import visualisation_de_graphes

# 1. Définir le problème
M1 = pl.LpProblem("M1_VRP", pl.LpMinimize)

# 2 données
Nc = 2 #nombre de camions
Np = 5 #nombre de points de collecte
Nd = 1 #nombre de dépôts

D = [[0, 10, 15, 20, 25, 30],  # Distances depuis le dépôt 0
     [10, 0, 35, 25, 30, 20], 
     [15, 35, 0, 30, 15, 10],
     [20, 25, 30, 0, 20, 25],
     [25, 30, 15, 20, 0, 15],
     [30, 20, 10, 25, 15, 0]] # Matrice des distances entre points
draw_graph(D)
# 3. Variables

# 4. Fonction objectif

# 5. Contraintes

# 6. Résolution

# 7. Résultats

