import pulp as pl
import sys

print(sys.argv)
# initialize the Problem
prob = pl.LpProblem("Computes_Optimal_Room_Selection_For_Hostel", pl.LpMaximize)

# define the decision variables
kitchens = pl.LpVariable("Kitchens", lowBound=0, upBound=100, cat=pl.LpInteger)
bathrooms = pl.LpVariable("Bathrooms", lowBound=0, upBound=100, cat=pl.LpInteger)
emptyRooms = pl.LpVariable("EmptyRooms", lowBound=0, upBound=100, cat=pl.LpInteger)

# define the objective
prob += (kitchens * 5 + bathrooms * 2 + emptyRooms * 5) - (
    kitchens * 9 + bathrooms * 6 + emptyRooms * 2
)
prob += kitchens <= emptyRooms
prob += bathrooms <= emptyRooms
prob += kitchens >= 1
prob += bathrooms >= 1
prob += kitchens * 6 >= emptyRooms
prob += bathrooms * 3 >= emptyRooms
prob += kitchens + bathrooms + emptyRooms <= 100

# solve the problem
prob.solve()

# print the results
print("Kitchens: ", kitchens.varValue)
print("Bathrooms: ", bathrooms.varValue)
print("Empty Rooms: ", emptyRooms.varValue)
