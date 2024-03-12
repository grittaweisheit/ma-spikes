import pulp as pl

# initialize the Problem
prob = pl.LpProblem("Production_Schedule_with_Cardinalities", pl.LpMinimize)
""" 
One resource, no time constraints, every activity takes 1 timeslot, production goal should be met exactly. 
"""

production_goal = 20

ACTIVITIES = range(4)
# start and finish are fixed
end_activity = 1
start_activity = 0

# time slots
last_time = 20
first_time = 0
TIMESLOTS = range(first_time, last_time + 1)

produces = [1, 1, 2, 3]

#####################################
### define the decision variables ###
#####################################

# we have a decision variable if the activity is done at the time slot for all possibilities
actions = pl.LpVariable.dicts("Action", (TIMESLOTS, ACTIVITIES), cat=pl.LpBinary)
endtime = pl.LpVariable("Endtime", lowBound=0, upBound=last_time, cat=pl.LpInteger)
starttime = pl.LpVariable("Starttime", lowBound=0, upBound=last_time, cat=pl.LpInteger)

############################
### define the objective ###
############################

# we want to minimize the time it takes to build the house (minimize the endtime)
prob += endtime

##############################
### define the constraints ###
##############################

### start and end constraints ###

# before start and after end, no activity is done
for t in TIMESLOTS:
    for a in ACTIVITIES:
        # endtime is the last time a task is done
        prob += actions[t][a] * t <= endtime
        # starttime is the first time a task is done
        # if task a is not done at t, the value is set to starttime with 1-0*last_time and thus satisfies the constraint last_time >= starttime
        prob += actions[t][a] * t + (1 - actions[t][a]) * last_time >= starttime

# end task is done at endtime and only then
prob += pl.lpSum(actions[t][end_activity] for t in TIMESLOTS) == 1
prob += pl.lpSum(actions[t][end_activity] * t for t in TIMESLOTS) == endtime
# start task is done at starttime and only then
prob += pl.lpSum(actions[t][start_activity] for t in TIMESLOTS) == 1
prob += pl.lpSum(actions[t][start_activity] * t for t in TIMESLOTS) == starttime

### the activitie constraints ###

# there can be max 1 activity at a time
for t in TIMESLOTS:
    prob += pl.lpSum(actions[t][a] for a in ACTIVITIES) <= 1

# the production goal is met
prob += (
    pl.lpSum(actions[t][a] * produces[a] for t in TIMESLOTS for a in ACTIVITIES)
    == production_goal
)

#########################
### generate solution ###
#########################

# solve the problem
prob.solve()

# print the solution
for cell in prob.variables():
    if cell.varValue == 1:
        print(cell.name, "=", cell.varValue)
print(prob.objective.value())
