import pulp as pl

# TODO: think aubout data links.

# TODO: think about parallel usage (no blocking anymore) of data instances if they are not modified by the activities.
# TODO:     Maybe split activities into categories and formulate constraints on those as a base

# initialize the Problem
prob = pl.LpProblem("fCM_room_Schedule", pl.LpMinimize)
""" 
schedules the activities to build 3 rooms in a house. 
No resources, no time constraints, every activity takes 1 timeslot. 
"""

######################################
### define variables for the house ###
######################################

rooms = 50
kitchens = 10
showers = 15
toilets = 15
instance_count = rooms + kitchens + showers + toilets

kitchens_to_build = 10
bathrooms_to_build = 15
empty_rooms_to_build = 25
last_time = 70
first_time = 0

#######################################
### define activities and resources ###
#######################################

### activities ###

# start and finish are fixed
end_activity = 10
start_activity = 0
# start, build room, install shower(t), install shower(b), install toilet(s), install toilet(b), install kitchen, buy kitchen, buy shower, buy toilet,  finish house (end)
build_room = 1
install_shower_t = 2
install_shower_b = 3
install_toilet_s = 4
install_toilet_b = 5
install_kitchen = 6
buy_kitchen = 7
buy_shower = 8
buy_toilet = 9
activity_names = [
    "finish shell",
    "build_room",
    "install_shower_t",
    "install_shower_b",
    "install_toilet_s",
    "install_toilet_b",
    "install_kitchen",
    "buy_kitchen",
    "buy_shower",
    "buy_toilet",
    "finish",
]

duration = [1, 1, 2, 2, 1, 1, 2, 1, 1, 1, 1]
role_requirement = [0, 1, 2, 2, 3, 3, 4, 5, 5, 5, 0]
resource_consumption = [0, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0]

data_types = [0, 1, 2, 3]  # room, kitchen, shower, toilet
input_sets = [[], [0], [0, 2], [0, 2], [0, 3], [0, 3], [0, 1], [1], [2], [3], []]

### resources ###

resource_names = ["-", "Bob", "Sandy", "Kay", "Tina", "Finn", "Fiona"]
role_names = ["-", "builder", "shower-crew", "toilet-crew", "kitchen-crew", "buyer"]
availability = [
    range(first_time, last_time + 1),
    range(first_time, last_time + 1),
    range(first_time, last_time + 1),
    range(first_time, last_time + 1),
    range(first_time, last_time + 1),
    range(first_time, last_time + 1),
    range(first_time, last_time + 1),
]
resource_ids = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
]  # no resource / started, Bob, Sandy, Kay, Tina, Finn, Fiona
roles = [
    0,
    1,
    2,
    3,
    4,
    5,
]  # nothing, builder, shower-crew, toilet-crew, kitchen-crew, buyer
resource_roles_map = [
    [0],  # no role, no resource / started
    [1],  # Bob -> builder
    [2, 4],  # Sandy -> shower-crew, kitchen-crew
    [4],  # Kay -> kitchen-crew
    [3],  # Tina -> toilet-crew
    [5],  # Finn -> buyer
    [5],  # Fiona -> buyer
]
roles_resources_map = [
    [0],  # no role, no resource / started
    [1],  # Builder: Bob
    [2],  # Shower-Crew: Sandy
    [4],  # Toilet-Crew: Tina
    [2, 3],  # Kitchen-Crew: Sandy, Kay
    [5, 6],  # Buyer: Finn, Fiona
]

#####################################
### define the decision variables ###
#####################################

# rooms, kitchens, showers, toilets
INSTANCES = range(instance_count)
rooms_range = range(rooms)
kitchen_range = range(rooms, rooms + kitchens)
shower_range = range(rooms + kitchens, rooms + kitchens + showers)
toilet_range = range(rooms + kitchens + showers, rooms + kitchens + showers + toilets)
type_range_map = [rooms_range, kitchen_range, shower_range, toilet_range]


def get_type(instance_index):
    for type_index in range(len(type_range_map)):
        if instance_index in type_range_map[type_index]:
            return type_index

ACTIVITIES = range(start_activity, end_activity + 1)
RACTIVITIES = range(
    start_activity + 1, end_activity
)  # real activities (not start and end)
TIMESLOTS = range(first_time, last_time + 1)
RESOURCES = resource_ids

# we have a decision variable whether the activity is done in the room at the time slot with this resource for all possibilities
# actions[t][a][i][0] symbolizes whether the activity is started at time t with instance i
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
    prob += pl.lpSum(actions[t][start_activity][0][r] for r in RESOURCES) <= 1
    prob += (
        pl.lpSum(actions[t][start_activity][0][r] for r in RESOURCES)
        <= actions[t][start_activity][0][0]
    )

# start and finish only happen once each
prob += pl.lpSum(actions[t][start_activity][0][0] for t in TIMESLOTS) == 1
prob += pl.lpSum(actions[t][end_activity][0][0] for t in TIMESLOTS) == 1

for t in TIMESLOTS:
    # start and finish happen on all instances at the same time
    prob += (
        pl.lpSum(actions[t][start_activity][i][0] for i in INSTANCES)
        == instance_count * actions[t][start_activity][0][0]
    )
    prob += pl.lpSum(actions[t][start_activity][i][0] for i in INSTANCES) == pl.lpSum(
        actions[t][start_activity][i][0] for i in INSTANCES
    )
    prob += (
        pl.lpSum(actions[t][end_activity][i][0] for i in INSTANCES)
        == instance_count * actions[t][end_activity][0][0]
    )
    prob += pl.lpSum(actions[t][end_activity][i][0] for i in INSTANCES) == pl.lpSum(
        actions[t][end_activity][i][0] for i in INSTANCES
    )

# after finish and before start nothing happens
# before start and after end, no activity is done
for t in TIMESLOTS:
    for a in ACTIVITIES:
        for i in INSTANCES:
            # endtime is the last time a task is done
            prob += actions[t][a][i][0] * t <= endtime
            # starttime is the first time a task is done
            # if task a is not done at t, the value is set to last_tim with 1-0*last_time and thus satisfies the constraint because last_time >= starttime
            prob += (
                actions[t][a][i][0] * t + (1 - actions[t][a][i][0]) * last_time
                >= starttime
            )


# end task is done at endtime and only then
prob += (
    pl.lpSum(actions[t][end_activity][i][0] for t in TIMESLOTS for i in INSTANCES)
    == instance_count
)
prob += (
    pl.lpSum(actions[t][end_activity][i][0] * t for t in TIMESLOTS for i in INSTANCES)
    == endtime * instance_count
)
# start task is done at starttime and only then
prob += (
    pl.lpSum(actions[t][start_activity][i][0] for t in TIMESLOTS for i in INSTANCES)
    == instance_count
)
prob += (
    pl.lpSum(actions[t][start_activity][i][0] * t for t in TIMESLOTS for i in INSTANCES)
    == starttime * instance_count
)

### general activity instance constraints ###

for t in TIMESLOTS:
    # on every instance there can be max 1 activity at a time
    for i in INSTANCES:
        prob += pl.lpSum(actions[t][a][i][0] for a in ACTIVITIES) <= 1

    # all real activities affect instances in line with their input set requirements
    for a in RACTIVITIES:
        # amount of instances of each type matches with occurrences in input set (or all zero) / relations are the same
        first_type = input_sets[a][0]
        for input_type_index in range(1, len(input_sets[a])):
            input_type = input_sets[a][input_type_index]
            prob += pl.lpSum(
                actions[t][a][i][0] for i in type_range_map[input_type]
            ) * input_sets[a].count(first_type) == pl.lpSum(
                actions[t][a][i][0] for i in type_range_map[first_type]
            ) * input_sets[a].count(input_type)
        for i in INSTANCES:
            # no instances of other types are affected
            if get_type(i) not in input_sets[a]:
                prob += actions[t][a][i][0] == 0

### durations are considered -> if an activity is started at t with i, it blocks the next time slots during it's duration
for time in TIMESLOTS:
    for act in ACTIVITIES:
        for i in INSTANCES:
            # duration can not exeed time limit if a started at t
            prob += (time + duration[act]) * actions[time][act][i][0] <= endtime + 1
            # if a started and duration > 1, the next time slots for i are also blocked
            for j in range(1, min((duration[act], last_time - time))):
                for a in ACTIVITIES:
                    prob += actions[time + j][a][i][0] <= 1 - actions[time][act][i][0]
            for r in RESOURCES:
                # if r used this time, r is blocked for the next duration-1 time slots
                for j in range(1, min((duration[act], last_time - time))):
                    for a in ACTIVITIES:
                        for ins in INSTANCES:
                            prob += (
                                actions[time + j][a][ins][r]
                                <= 1 - actions[time][act][i][r]
                            )

### resource constraints ###

for t in TIMESLOTS:
    for r in RESOURCES[1:]:
        for a in ACTIVITIES:
            # if there is one instance affected by resource r, the activity is done with r --> no other activity can use r at the same time
            for ins in INSTANCES:
                for other_a in ACTIVITIES:
                    if a != other_a:
                        for i in INSTANCES:
                            prob += (
                                actions[t][other_a][i][r] <= 1 - actions[t][a][ins][r]
                            )

            # the same activity does not use a resource at the same time in different action-instances
            # one resource is not used with more instances than the activity's input set allows
            prob += pl.lpSum(actions[t][a][i][r] for i in INSTANCES) <= len(
                input_sets[a]
            )
            # the instances that the resource is used on must be in line with input set requirements
            if len(input_sets[a]) > 0:
                first_type = input_sets[a][0]
                for input_type_index in range(1, len(input_sets[a])):
                    input_type = input_sets[a][input_type_index]
                    # instances in right relation
                    prob += pl.lpSum(
                        actions[t][a][i][r] for i in type_range_map[input_type]
                    ) * input_sets[a].count(first_type) == pl.lpSum(
                        actions[t][a][i][r] for i in type_range_map[first_type]
                    ) * input_sets[a].count(input_type)
                    # amount of instances of instances not bigger than input set allows (so not more than one action per activity with resource r)
                    prob += pl.lpSum(
                        actions[t][a][i][r] for i in type_range_map[input_type]
                    ) <= input_sets[a].count(input_type)
                for i in INSTANCES:
                    if get_type(i) not in input_sets[a]:
                        prob += actions[t][a][i][r] == 0

        # each resource is available when it is used
        if t not in availability[r]:
            prob += (
                pl.lpSum(actions[t][a][i][r] for a in ACTIVITIES for i in INSTANCES)
                == 0
            )

    # each activity is executed with its required resources
    for a in ACTIVITIES[start_activity + 1 : end_activity]:
        for i in INSTANCES:
            # consumption is satisfied
            # actions[t][a][i][0] symbolizes whether the activity is started at time t in room i
            prob += (
                pl.lpSum(actions[t][a][i][r] for r in RESOURCES[1:])
                == resource_consumption[a] * actions[t][a][i][0]
            )
            # satisfied only with required role
            prob += pl.lpSum(
                actions[t][a][i][r] for r in roles_resources_map[role_requirement[a]]
            ) == pl.lpSum(actions[t][a][i][r] for r in RESOURCES[1:])


### activity / data dependencies ###
# TODO: maybe adjust for reacurring of activities on one instance
for i in INSTANCES:
    for time in TIMESLOTS:
        times_before = range(0, time)
        # start before build room (redundant)
        if i in rooms_range:
            prob += pl.lpSum(
                actions[t][start_activity][i][0] for t in times_before
            ) >= pl.lpSum(actions[t][build_room][i][0] for t in times_before)

        # build room or install toilet before install shower,
        if i in rooms_range:
            prob += pl.lpSum(
                actions[t][build_room][i][0] - actions[t][install_toilet_b][i][0]
                for t in times_before
            ) >= pl.lpSum(actions[t][install_shower_b][i][0] for t in times_before)
            prob += pl.lpSum(
                actions[t][install_toilet_b][i][0] for t in times_before
            ) >= pl.lpSum(actions[t][install_shower_t][i][0] for t in times_before)
        # and buy shower before install shower
        if i in shower_range:
            prob += pl.lpSum(
                actions[t][buy_shower][i][0] for t in times_before
            ) >= pl.lpSum(
                actions[t][install_shower_t][i][0] for t in times_before
            ) + pl.lpSum(actions[t][install_shower_b][i][0] for t in times_before)

        # build room or install shower before install toilet,
        if i in rooms_range:
            prob += pl.lpSum(
                actions[t][build_room][i][0] - actions[t][install_shower_b][i][0]
                for t in times_before
            ) >= pl.lpSum(actions[t][install_toilet_b][i][0] for t in times_before)
            prob += pl.lpSum(
                actions[t][install_shower_b][i][0] for t in times_before
            ) >= pl.lpSum(actions[t][install_toilet_s][i][0] for t in times_before)
        # and buy toilet before install toilet
        if i in toilet_range:
            prob += pl.lpSum(
                actions[t][buy_toilet][i][0] for t in times_before
            ) >= pl.lpSum(
                actions[t][install_toilet_s][i][0] for t in times_before
            ) + pl.lpSum(actions[t][install_toilet_b][i][0] for t in times_before)

        # build room before install kitchen (and not bathroom),
        if i in rooms_range:
            prob += pl.lpSum(
                actions[t][build_room][i][0]
                - actions[t][install_toilet_b][i][0]
                - actions[t][install_shower_b][i][0]
                for t in times_before
            ) >= pl.lpSum(actions[t][install_kitchen][i][0] for t in times_before)
        # and buy kitchen before install kitchen
        if i in kitchen_range:
            prob += pl.lpSum(
                actions[t][buy_kitchen][i][0] for t in times_before
            ) >= pl.lpSum(actions[t][install_kitchen][i][0] for t in times_before)
########################
### define the goals ###
########################

### goal = empty rooms, kitchens, bathrooms
# kitchens
prob += (
    pl.lpSum(actions[t][install_kitchen][i][0] for t in TIMESLOTS for i in rooms_range)
    >= kitchens_to_build
)
# bathrooms
prob += (
    pl.lpSum(
        actions[t][install_toilet_s][i][0] + actions[t][install_shower_t][i][0]
        for t in TIMESLOTS
        for i in rooms_range
    )
    >= bathrooms_to_build
)
# empty rooms
prob += (
    pl.lpSum(
        pl.lpSum(actions[t][build_room][i][0] for t in TIMESLOTS)
        - pl.lpSum(
            actions[t][install_kitchen][i][0]
            + actions[t][install_toilet_b][i][0]
            + actions[t][install_shower_b][i][0]
            for t in TIMESLOTS
        )
        for i in rooms_range
    )
    >= empty_rooms_to_build
)

# solve the problem
prob.solve()

# print the solution
for t in TIMESLOTS:
    print("\nTime slot ", t)
    for a in ACTIVITIES:
        for i in INSTANCES:
            for r in RESOURCES:
                if actions[t][a][i][r].varValue == 1:
                    print(
                        activity_names[a],
                        " on instance ",
                        i,
                        " with ",
                        resource_names[r],
                    )

# for cell in prob.variables():
#     if cell.varValue == 1:
#         print(cell.name, "=", cell.varValue)
