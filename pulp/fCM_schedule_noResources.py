import pulp as pl

# initialize the Problem
prob = pl.LpProblem("fCM_room_Schedule", pl.LpMinimize)
""" 
schedules the activities to build 3 rooms in a house. 
No resources, no time constraints, every activity takes 1 timeslot. 
"""

######################################
### define variables for the house ###
######################################

rooms_to_build = 3
kitchens_to_build = 1
bathrooms_to_build = 1
empty_rooms_to_build = 1
last_time = 20
first_time = 0

#########################
### define activities ###
#########################

# start and finish are fixed
end_activity = 7
start_activity = 0
# start, build room, install shower(t), install shower(b), install toilet(s), install toilet(b), install kitchen, finish house (end)
build_room = 1
install_shower_t = 2
install_shower_b = 3
install_toilet_s = 4
install_toilet_b = 5
install_kitchen = 6

duration = [1, 1, 2, 2, 1, 1, 2, 1]

#####################################
### define the decision variables ###
#####################################

# rooms
ROOMS = range(rooms_to_build)
# activities
ACTIVITIES = range(start_activity, end_activity + 1)
# time slots
TIMESLOTS = range(first_time, last_time + 1)

# we have a decision variable whether the activity is done in the room at the time slot for all possibilities
actions = pl.LpVariable.dicts("Action", (TIMESLOTS, ACTIVITIES, ROOMS), cat=pl.LpBinary)
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

# start and finish only happen once each
prob += pl.lpSum(actions[t][start_activity][0] for t in TIMESLOTS) == 1
prob += pl.lpSum(actions[t][end_activity][0] for t in TIMESLOTS) == 1

for t in TIMESLOTS:
    # start and finish happen in all rooms at the same time
    prob += (
        pl.lpSum(actions[t][start_activity][r] for r in ROOMS)
        == rooms_to_build * actions[t][start_activity][0]
    )
    prob += (
        pl.lpSum(actions[t][end_activity][r] for r in ROOMS)
        == rooms_to_build * actions[t][end_activity][0]
    )

# after finish and before start nothing happens
# before start and after end, no activity is done
for t in TIMESLOTS:
    for a in ACTIVITIES:
        for r in ROOMS:
            # endtime is the last time a task is done
            prob += actions[t][a][r] * t <= endtime
            # starttime is the first time a task is done
            # if task a is not done at t, the value is set to last_tim with 1-0*last_time and thus satisfies the constraint because last_time >= starttime
            prob += (
                actions[t][a][r] * t + (1 - actions[t][a][r]) * last_time >= starttime
            )

# end task is done at endtime and only then
prob += (
    pl.lpSum(actions[t][end_activity][r] for t in TIMESLOTS for r in ROOMS)
    == rooms_to_build
)
prob += (
    pl.lpSum(actions[t][end_activity][r] * t for t in TIMESLOTS for r in ROOMS)
    == endtime * rooms_to_build
)
# start task is done at starttime and only then
prob += (
    pl.lpSum(actions[t][start_activity][r] for t in TIMESLOTS for r in ROOMS)
    == rooms_to_build
)
prob += (
    pl.lpSum(actions[t][start_activity][r] * t for t in TIMESLOTS for r in ROOMS)
    == starttime * rooms_to_build
)

### general activity constraints ###

for t in TIMESLOTS:
    # in every room there can be max 1 real activity at a time
    for r in ROOMS:
        prob += pl.lpSum(actions[t][a][r] for a in ACTIVITIES) <= 1

    # all real activities only affect one room
    for a in range(start_activity + 1, end_activity):
        prob += pl.lpSum(actions[t][a][r] for r in ROOMS) <= 1

# durations are considered -> if an activity is started at t, it blocks the next time slots during it's duration
for time in TIMESLOTS:
    for act in ACTIVITIES:
        for r in ROOMS:
            # duration can not exeed time limit if a started at t
            prob += (time + duration[act]) * actions[time][act][r] <= endtime + 1
            # if a started and duration > 1, the next time slots are also blocked
            for i in range(1, min((duration[act] - 1, last_time - time))):
                for a in ACTIVITIES:
                    prob += actions[time + i][a][r] <= 1 - actions[time][act][r]

### activity / data dependencies
for r in ROOMS:
    for time in TIMESLOTS:
        # start before build room (redundant)
        prob += pl.lpSum(
            actions[t][start_activity][r] for t in range(0, time)
        ) >= pl.lpSum(actions[t][build_room][r] for t in range(0, time))

        # build room or install toilet before install shower
        prob += pl.lpSum(
            actions[t][build_room][r] - actions[t][install_toilet_b]
            for t in range(0, time)
        ) >= pl.lpSum(actions[t][install_shower_b][r] for t in range(0, time))
        prob += pl.lpSum(
            actions[t][install_toilet_b][r] for t in range(0, time)
        ) >= pl.lpSum(actions[t][install_shower_t][r] for t in range(0, time))

        # build room or install shower before install toilet
        prob += pl.lpSum(
            actions[t][build_room][r] - actions[t][install_shower_b][r]
            for t in range(0, time)
        ) >= pl.lpSum(actions[t][install_toilet_b][r] for t in range(0, time))
        prob += pl.lpSum(
            actions[t][install_shower_b][r] for t in range(0, time)
        ) >= pl.lpSum(actions[t][install_toilet_s][r] for t in range(0, time))

        # build room before install kitchen (and not bathroom)
        prob += pl.lpSum(
            actions[t][build_room][r]
            - actions[t][install_toilet_b][r]
            - actions[t][install_shower_b][r]
            for t in range(0, time)
        ) >= pl.lpSum(actions[t][install_kitchen][r] for t in range(0, time))

########################
### define the goals ###
########################

### goal = empty rooms, kitchens, bathrooms
# kitchens
prob += (
    pl.lpSum(actions[t][install_kitchen][r] for t in TIMESLOTS for r in ROOMS)
    >= kitchens_to_build
)
# bathrooms
prob += (
    pl.lpSum(
        actions[t][install_toilet_s][r] + actions[t][install_shower_t][r]
        for t in TIMESLOTS
        for r in ROOMS
    )
    >= bathrooms_to_build
)
# empty rooms
prob += (
    pl.lpSum(
        pl.lpSum(actions[t][build_room][r] for t in TIMESLOTS)
        - pl.lpSum(
            actions[t][install_kitchen][r]
            + actions[t][install_toilet_b][r]
            + actions[t][install_shower_b][r]
            for t in TIMESLOTS
        )
        for r in ROOMS
    )
    >= empty_rooms_to_build
)

# solve the problem
prob.solve()

# print the solution
for cell in prob.variables():
    if cell.varValue == 1:
        print(cell.name, "=", cell.varValue)
