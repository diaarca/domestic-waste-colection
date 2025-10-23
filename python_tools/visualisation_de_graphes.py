import networkx as nx
import matplotlib.pyplot as plt



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

def matrice_adjacence_vers_distance(D):
    n = len(D)
    G = nx.Graph()
    for i in range(n):
        for j in range(n):
            if D[i][j] != 0:
                G.add_edge(i, j, weight=D[i][j])
    # Calculer toutes les distances minimales
    dist = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                dist[i][j] = 0
            else:
                try:
                    dist[i][j] = nx.shortest_path_length(G, i, j, weight='weight')
                except nx.NetworkXNoPath:
                    dist[i][j] = float('inf')  # ou une grande valeur
    return dist

if __name__ == "__main__":
    D = [[0,1,0,0,0,0],
        [1,0,2,0,4,0],
        [0,2,0,1,0,0],
        [0,0,1,0,2,3],
        [0,4,0,2,0,2],
        [0,0,0,3,2,0]]
    visualiser_graphe(D)
    D_distance = matrice_adjacence_vers_distance(D)
    for row in D_distance:
        print(row)