from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class ClarkeWrightResult:
    routes: List[List[int]]
    total_cost: float


class ClarkeWrightReverseIRP:
    """
    Implémentation de base de l'algorithme de Clarke & Wright
    pour un problème de collecte (reverse routing) mono-période.
    """

    def __init__(
        self,
        distance_matrix: List[List[float]],
        returns: Dict[int, float],
        vehicle_capacity: float,
        depot: int = 0,
    ):
        """
        :param distance_matrix: matrice des distances (c_ij)
        :param returns: dict {i: q_i} quantités à collecter chez le client i
                        (i != depot)
        :param vehicle_capacity: capacité maximale d'un véhicule
        :param depot: index du dépôt (par défaut 0)
        """
        self.d = distance_matrix
        self.n = len(distance_matrix)  # nb de noeuds (dépôt + clients)
        self.returns = returns
        self.Q = vehicle_capacity
        self.depot = depot

        self.routes: List[List[int]] = []
        self.route_loads: List[float] = []
        self.route_of_customer: Dict[int, int] = {}  # client -> index de route

    # ---------- Helpers de base ----------

    def route_cost(self, route: List[int]) -> float:
        """Coût d'une tournée (somme des distances)."""
        cost = 0.0
        for i in range(len(route) - 1):
            cost += self.d[route[i]][route[i + 1]]
        return cost

    def total_cost(self, routes: List[List[int]]) -> float:
        return sum(self.route_cost(r) for r in routes)

    def compute_savings(self) -> List[Tuple[float, int, int]]:
        """
        Calcul des savings s_ij = c_0i + c_0j - c_ij
        pour tous les couples de clients i < j.
        """
        savings = []
        customers = [i for i in range(self.n) if i != self.depot]
        for i in customers:
            for j in customers:
                if j <= i:
                    continue
                s_ij = (
                    self.d[self.depot][i]
                    + self.d[self.depot][j]
                    - self.d[i][j]
                )
                savings.append((s_ij, i, j))
        # tri décroissant des savings
        savings.sort(reverse=True, key=lambda x: x[0])
        return savings

    def init_routes(self):
        """
        Initialisation : une tournée par client : 0 - i - 0
        """
        self.routes = []
        self.route_loads = []
        self.route_of_customer = {}

        customers = [i for i in range(self.n) if i != self.depot]

        for idx, i in enumerate(customers):
            route = [self.depot, i, self.depot]
            load = self.returns.get(i, 0.0)
            self.routes.append(route)
            self.route_loads.append(load)
            self.route_of_customer[i] = idx

    # ---------- Conditions de fusion de tournées ----------

    def can_merge(self, i: int, j: int) -> bool:
        """
        Vérifie si l'on peut fusionner les tournées contenant i et j
        sans violer la capacité, et en maintenant une tournée simple
        (pas de cycle intermédiaire).
        """
        ri = self.route_of_customer[i]
        rj = self.route_of_customer[j]

        if ri == rj:
            # déjà dans la même tournée
            return False

        route_i = self.routes[ri]
        route_j = self.routes[rj]

        # i doit être à une extrémité de route_i (juste après ou juste avant le dépôt)
        # j doit être à une extrémité de route_j
        i_is_start = (route_i[1] == i)
        i_is_end = (route_i[-2] == i)
        j_is_start = (route_j[1] == j)
        j_is_end = (route_j[-2] == j)

        if not (i_is_start or i_is_end):
            return False
        if not (j_is_start or j_is_end):
            return False

        # Vérification de la capacité si on fusionne les deux tournées
        new_load = self.route_loads[ri] + self.route_loads[rj]
        if new_load > self.Q:
            return False

        return True

    def merge(self, i: int, j: int):
        """
        Fusionne les tournées contenant i et j.
        On suppose que can_merge(i, j) = True.
        """
        ri = self.route_of_customer[i]
        rj = self.route_of_customer[j]

        route_i = self.routes[ri]
        route_j = self.routes[rj]

        i_is_start = (route_i[1] == i)
        i_is_end = (route_i[-2] == i)
        j_is_start = (route_j[1] == j)
        j_is_end = (route_j[-2] == j)

        # On considère les quatre cas possibles
        if i_is_end and j_is_start:
            # ... i - 0   et   0 - j ...
            new_route = route_i[:-1] + route_j[1:]
        elif i_is_start and j_is_end:
            # 0 - i ...   et   ... j - 0
            new_route = route_j[:-1] + route_i[1:]
        elif i_is_start and j_is_start:
            # 0 - i ...   et   0 - j ...
            # On inverse l'une des deux tournées (sauf les dépôts)
            new_route = route_i[::-1][:-1] + route_j[1:]
        elif i_is_end and j_is_end:
            # ... i - 0   et   ... j - 0
            new_route = route_i[:-1] + route_j[::-1][1:]
        else:
            # Théoriquement ne devrait pas arriver si can_merge est bien testé
            return

        # Nouvelle charge
        new_load = self.route_loads[ri] + self.route_loads[rj]

        # Remplacement de ri par la nouvelle tournée, suppression de rj
        self.routes[ri] = new_route
        self.route_loads[ri] = new_load

        # Mise à jour mapping client -> index de route
        for node in new_route:
            if node != self.depot:
                self.route_of_customer[node] = ri

        # Pour supprimer rj proprement, on le remplace par la dernière route
        # et on met à jour les indices
        last_idx = len(self.routes) - 1
        if rj != last_idx:
            self.routes[rj] = self.routes[last_idx]
            self.route_loads[rj] = self.route_loads[last_idx]
            # mise à jour des clients qui pointaient sur last_idx
            for node in self.routes[rj]:
                if node != self.depot:
                    self.route_of_customer[node] = rj

        self.routes.pop()
        self.route_loads.pop()

    # ---------- Solveur principal ----------

    def solve(self) -> ClarkeWrightResult:
        """
        Exécute l'algorithme de Clarke & Wright une fois, pour un horizon mono-période.
        """
        # 1. Initialisation
        self.init_routes()

        # 2. Calcul des savings
        savings_list = self.compute_savings()

        # 3. Parcours des savings triés
        for s, i, j in savings_list:
            if self.can_merge(i, j):
                self.merge(i, j)

        return ClarkeWrightResult(
            routes=self.routes,
            total_cost=self.total_cost(self.routes),
        )


# --------------------- Exemple d'utilisation ---------------------

if __name__ == "__main__":
    # Petit exemple jouet

    # 0 = dépôt, 1..4 = clients
    distance_matrix = [
        [0, 10, 20, 30, 40],
        [10, 0, 15, 25, 35],
        [20, 15, 0, 18, 28],
        [30, 25, 18, 0, 14],
        [40, 35, 28, 14, 0],
    ]

    # quantités à collecter (reverse)
    returns = {
        1: 2.0,
        2: 3.0,
        3: 1.0,
        4: 4.0,
    }

    vehicle_capacity = 5.0

    solver = ClarkeWrightReverseIRP(
        distance_matrix=distance_matrix,
        returns=returns,
        vehicle_capacity=vehicle_capacity,
        depot=0,
    )

    result = solver.solve()
    print("Routes trouvées :")
    for r in result.routes:
        print(r, " | coût =", solver.route_cost(r))
    print("Coût total :", result.total_cost)
