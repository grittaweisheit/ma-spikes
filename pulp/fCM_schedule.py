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

#######################################
### define activities and resources ###
#######################################

### activities ###

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
role_requirement = [0, 1, 2, 3, 3, 3, 4, 0]
resource_consumption = [0, 1, 1, 1, 1, 1, 2, 0]
### resources ###

resource_ids = [0, 1, 2, 3, 4]  # no resource, Bob, Sandy, Kay, Tina
roles = [0, 1, 2, 3, 4]  # builder, shower-crew, toilet-crew, kitchen-crew
resource_roles_map = [
    [0], # no role, no resource
    [1],  # Bob -> builder
    [2, 4],  # Sandy -> shower-crew, kitchen-crew
    [4],  # Kay -> kitchen-crew
    [3],  # Tina -> toilet-crew
]
roles_resources_map = [
    [0], # no role, no resource
    [1], # Builder: Bob
    [2], # Shower-Crew: Sandy
    [4], # Toilet-Crew: Tina
    [2,3] # Kitchen-Crew: Sandy, Kay
]

#####################################
### define the decision variables ###
#####################################

# rooms
INSTANCES = range(rooms_to_build)
# activities
ACTIVITIES = range(start_activity, end_activity + 1)
# time slots
TIMESLOTS = range(first_time, last_time + 1)
# resources
RESOURCES = resource_ids

# we have a decision variable whether the activity is done in the room at the time slot for all possibilities
actions = pl.LpVariable.dicts(
    "Action", (TIMESLOTS, ACTIVITIES, INSTANCES, RESOURCES), cat=pl.LpBinary
)
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

# start and finish do not need resources
for t in TIMESLOTS:
    prob += pl.lpSum(actions[t][start_activity][0][i] for i in INSTANCES) <= 1
    prob += (
        pl.lpSum(actions[t][start_activity][0][i] for i in INSTANCES)
        <= actions[t][start_activity][0][0]
    )

# start and finish only happen once each
prob += pl.lpSum(actions[t][start_activity][0][0] for t in TIMESLOTS) == 1
prob += pl.lpSum(actions[t][end_activity][0][0] for t in TIMESLOTS) == 1

for t in TIMESLOTS:
    # start and finish happen in all rooms at the same time
    prob += (
        pl.lpSum(actions[t][start_activity][i][0] for i in INSTANCES)
        == rooms_to_build * actions[t][start_activity][0][0]
    )
    prob += (
        pl.lpSum(actions[t][end_activity][i][0] for i in INSTANCES)
        == rooms_to_build * actions[t][end_activity][0][0]
    )

# after finish and before start nothing happens
# before start and after end, no activity is done
for t in TIMESLOTS:
    for a in ACTIVITIES:
        for i in INSTANCES:
            for r in RESOURCES:
                # endtime is the last time a task is done
                prob += actions[t][a][i][r] * t <= endtime
                # starttime is the first time a task is done
                # if task a is not done at t, the value is set to last_tim with 1-0*last_time and thus satisfies the constraint because last_time >= starttime
                prob += (
                    actions[t][a][i][r] * t + (1 - actions[t][a][i][r]) * last_time
                    >= starttime
                )

# end task is done at endtime and only then
prob += (
    pl.lpSum(actions[t][end_activity][i][0] for t in TIMESLOTS for i in INSTANCES)
    == rooms_to_build
)
prob += (
    pl.lpSum(actions[t][end_activity][i][0] * t for t in TIMESLOTS for i in INSTANCES)
    == endtime * rooms_to_build
)
# start task is done at starttime and only then
prob += (
    pl.lpSum(actions[t][start_activity][i][0] for t in TIMESLOTS for i in INSTANCES)
    == rooms_to_build
)
prob += (
    pl.lpSum(actions[t][start_activity][i][0] * t for t in TIMESLOTS for i in INSTANCES)
    == starttime * rooms_to_build
)

### general activity constraints ###

for t in TIMESLOTS:
    # in every room there can be max 1 real activity at a time
    for i in INSTANCES:
        prob += (
            pl.lpSum(actions[t][a][i][role_requirement[a]] for a in ACTIVITIES) <= 1
        )

    # all real activities only affect one room
    for a in range(start_activity + 1, end_activity):
        prob += (
            pl.lpSum(actions[t][a][i][role_requirement[a]] for i in INSTANCES) <= 1
        )

### durations are considered -> if an activity is started at t with i, it blocks the next time slots during it's duration
for time in TIMESLOTS:
    for act in ACTIVITIES:
        for i in INSTANCES:
            # duration can not exeed time limit if a started at t
            prob += (time + duration[act]) * actions[time][act][i][
                role_requirement[act]
            ] <= endtime + 1
            # if a started and duration > 1, the next time slots are also blocked
            for j in range(1, min((duration[act] - 1, last_time - time))):
                for a in ACTIVITIES:
                    prob += (
                        actions[time + j][a][i][role_requirement[a]]
                        <= 1 - actions[time][act][i][role_requirement[act]]
                    )
            # TODO: also block resources

### resource constraints ###
for t in TIMESLOTS:
    # each resource is only used once at each point of time
    for r in RESOURCES:
        prob += (
            pl.lpSum(actions[t][a][i][r] for a in ACTIVITIES for i in INSTANCES) <= 1
        )
    # each activity is executed with its required resources
    for a in ACTIVITIES:
        for i in INSTANCES:
            # TODO: fix this. should be consumption or 0
            # consumption is satisfied
            prob += pl.lpSum(actions[t][a][i][r] for r in RESOURCES) == resource_consumption[a]
            # satisfied only with required role
            prob += pl.lpSum(actions[t][a][i][r] for r in roles_resources_map[role_requirement[a]]) == resource_consumption[a]

### activity / data dependencies ###
# TODO: fix resources. maybe build sum and divide by requirement to get 0 / 1
for i in INSTANCES:
    for time in TIMESLOTS:
        # start before build room (redundant)
        prob += pl.lpSum(
            actions[t][start_activity][i][role_requirement[start_activity]]
            for t in range(0, time)
        ) >= pl.lpSum(
            actions[t][build_room][i][role_requirement[build_room]]
            for t in range(0, time)
        )

        # build room or install toilet before install shower
        prob += pl.lpSum(
            actions[t][build_room][i][role_requirement[build_room]]
            - actions[t][install_toilet_b][i][role_requirement[install_toilet_b]]
            for t in range(0, time)
        ) >= pl.lpSum(
            actions[t][install_shower_b][i][role_requirement[install_shower_b]]
            for t in range(0, time)
        )
        prob += pl.lpSum(
            actions[t][install_toilet_b][i][role_requirement[install_toilet_b]]
            for t in range(0, time)
        ) >= pl.lpSum(
            actions[t][install_shower_t][i][role_requirement[install_shower_t]]
            for t in range(0, time)
        )

        # build room or install shower before install toilet
        prob += pl.lpSum(
            actions[t][build_room][i][role_requirement[build_room]]
            - actions[t][install_shower_b][i][role_requirement[install_shower_b]]
            for t in range(0, time)
        ) >= pl.lpSum(
            actions[t][install_toilet_b][i][role_requirement[install_toilet_b]]
            for t in range(0, time)
        )
        prob += pl.lpSum(
            actions[t][install_shower_b][i][role_requirement[install_shower_b]]
            for t in range(0, time)
        ) >= pl.lpSum(
            actions[t][install_toilet_s][i][role_requirement[install_toilet_s]]
            for t in range(0, time)
        )

        # build room before install kitchen (and not bathroom)
        prob += pl.lpSum(
            actions[t][build_room][i][role_requirement[build_room]]
            - actions[t][install_toilet_b][i][role_requirement[install_toilet_b]]
            - actions[t][install_shower_b][i][role_requirement[install_shower_b]]
            for t in range(0, time)
        ) >= pl.lpSum(
            actions[t][install_kitchen][i][role_requirement[install_kitchen]]
            for t in range(0, time)
        )

########################
### define the goals ###
########################

### goal = empty rooms, kitchens, bathrooms
# kitchens
prob += (
    pl.lpSum(
        actions[t][install_kitchen][i][role_requirement[install_kitchen]]
        for t in TIMESLOTS
        for i in INSTANCES
    )
    >= kitchens_to_build
)
# bathrooms
prob += (
    pl.lpSum(
        actions[t][install_toilet_s][i][role_requirement[install_toilet_s]]
        + actions[t][install_shower_t][i][role_requirement[install_shower_t]]
        for t in TIMESLOTS
        for i in INSTANCES
    )
    >= bathrooms_to_build
)
# empty rooms
prob += (
    pl.lpSum(
        pl.lpSum(
            actions[t][build_room][i][role_requirement[build_room]]
            for t in TIMESLOTS
        )
        - pl.lpSum(
            actions[t][install_kitchen][i][role_requirement[install_kitchen]]
            + actions[t][install_toilet_b][i][role_requirement[install_toilet_b]]
            + actions[t][install_shower_b][i][role_requirement[install_shower_b]]
            for t in TIMESLOTS
        )
        for i in INSTANCES
    )
    >= empty_rooms_to_build
)

# solve the problem
prob.solve()

# print the solution
for cell in prob.variables():
    if cell.varValue == 1:
        print(cell.name, "=", cell.varValue)
