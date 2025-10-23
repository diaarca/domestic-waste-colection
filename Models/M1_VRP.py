import pulp as pl
import matplotlib.pyplot as plt
import networkx as nx



def visualiser_graphe(D):
     n = len(D)
     noms = ['A', 'B', 'C', 'D', 'E', 'F','OUT']
     G = nx.Graph()
     # Ajouter les sommets avec noms
     G.add_nodes_from(noms[:n])
     # Ajouter les arêtes avec poids
     for i in range(n):
          for j in range(i+1, n):
               if D[i][j] != 0:
                    G.add_edge(noms[i], noms[j], weight=D[i][j])
     pos = nx.spring_layout(G, seed=42)
     edge_labels = nx.get_edge_attributes(G, 'weight')
     nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=700, font_size=14)
     nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
     plt.title('Graphe des distances')
     plt.show()

# 1. Définir le problème
M1 = pl.LpProblem("M1_VRP", pl.LpMinimize)

# 2 données
Nc = 2 #nombre de camions
Np = 4 #nombre de points de collecte
Nd = 1 #nombre de dépôts

D = [[0, 1, 3, 2, 999],  # Distances depuis le dépôt 0
     [1, 0, 1, 3, 999], 
     [3, 1, 0, 2, 1],
     [2, 3, 2, 0, 1],
     [999, 999, 1, 1, 0]]

Dv = [[0, 1, 3, 2, 0],  # Distances depuis le dépôt 0
     [1, 0, 1, 3, 0], 
     [3, 1, 0, 2, 1],
     [2, 3, 2, 0, 1],
     [0, 0, 1, 1, 0]]

visualiser_graphe(Dv)


# 3. Variables
X = pl.LpVariable.dicts("X", ((i,j) for i in range(Np + Nd) for j in range(Np + Nd) for c in range(Nc)), cat="Binary") # X[c,i,j] = 1 si le camion c va de i à j

# 4. Fonction objectif
M1 += pl.lpSum(D[i][j] * X[i,j] for i in range(Np + Nd) for j in range(Np + Nd))

# 5. Contraintes
for c in range(Nc):
    for j in range(1, Np + Nd):
          M1 += pl.lpSum(X[i,j] for i in range(Np + Nd) if i != j) == 1  # Chaque point de collecte est visité une fois
    for i in range(1, Np + Nd):
          M1 += pl.lpSum(X[i,j] for j in range(Np + Nd) if i != j) == 1  # Chaque point de collecte est quitté une fois

M1 += pl.lpSum(X[0,j] for j in range(1, Np + Nd)) <= Nc  # Limite le nombre de camions partant du dépôt
M1 += pl.lpSum(X[i,0] for i in range(1, Np + Nd)) <= Nc  # Limite le nombre de camions revenant au dépôt



# 7. Résultats
print("Statut:", pl.LpStatus[M1.status])
for v in M1.variables():
    if v.varValue > 0:
        print(v.name, "=", v.varValue)