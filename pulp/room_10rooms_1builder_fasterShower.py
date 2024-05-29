import array
# from memory_profiler import profile
import pulp as pl

# TODO: think aubout data links.

# TODO: think about parallel usage (no blocking anymore) of data objects if they are not modified by the activities.
# TODO:     Maybe split activities into categories and formulate constraints on those as a base


# @profile
def do():
    # initialize the Problem
    prob = pl.LpProblem("fCM_room_Schedule", pl.LpMinimize)
    """ 
    no buying
    """

    ########################################
    ### define variables for the process ###
    ########################################

    rooms = 10
    object_count = rooms

    kitchens_to_build = 2
    bathrooms_to_build = 3
    empty_rooms_to_build = 5
    deadline = 15
    first_time = 0

    #######################################
    ### define activities and resources ###
    #######################################

    ### activities ###

    # start and finish are fixed
    finish = 6
    # start, record, assess, question, decide, finish (end)
    build_room = 0
    install_shower_t = 1
    install_shower_b = 2
    install_toilet_s = 3
    install_toilet_b = 4
    install_kitchen = 5
    activity_names = [
        "build_room",
        "install_shower_t",
        "install_shower_b",
        "install_toilet_s",
        "install_toilet_b",
        "install_kitchen",
        "finish",
    ]

    duration = [1, 1,1, 1, 1, 2, 1]
    role_req = [1, 2, 2, 3, 3, 4, 0]
    res_cons = [1, 1, 1, 1, 1, 2, 0]

    data_types = [0]  # room
    type_names = ["room"]
    class_reqs = [[0], [0], [0], [0], [0], [0], [0]]

    ### resources ###

    resource_names = ["-", "Bob", "Sandy", "Kay", "Tina"]
    role_names = ["-", "builder", "shower-crew", "toilet-crew", "kitchen-crew"]
    availability = [
        range(first_time, deadline + 1),
        range(first_time, deadline + 1),
        range(first_time, deadline + 1),
        range(first_time, deadline + 1),
        range(first_time, deadline + 1),
    ]
    resource_ids = [
        0,
        1,
        2,
        3,
        4
    ]  # no resource / started, Bob, Bill, Sandy, Kay, Tina
    roles = [0, 1, 2, 3, 4]  # nothing, builder, shower-crew, toilet-crew, kitchen-crew
    resource_roles_map = [
        [0],  # no role, no resource / started
        [1],  # Bob -> builder
        [2, 4],  # Sandy -> shower-crew, kitchen-crew
        [4],  # Kay -> kitchen-crew
        [3],  # Tina -> toilet-crew
    ]
    roles_resources_map = [
        [0],  # no role, no resource / started
        [1],  # Builder: Bob, Bill
        [2],  # Shower-Crew: Sandy
        [4],  # Toilet-Crew: Tina
        [2,3],  # Kitchen-Crew: Sandy, Kay
    ]

    #####################################
    ### define the decision variables ###
    #####################################

    # claims, assessments
    OBJECTS = array.array("b", range(object_count))
    rooms_range = range(rooms)
    type_range_map = [rooms_range]

    def get_type(object_index):
        for type_index in range(len(type_range_map)):
            if object_index in type_range_map[type_index]:
                return type_index

    ACTIVITIES_BUFFER = array.array("b", range(finish + 1))
    ACTIVITIES = array.array("b", range(finish))  # real activities (not start and end)
    TIMESLOTS = array.array("b", range(first_time, deadline + 1))
    RESOURCES = array.array("b", resource_ids)

    # we have a decision variable whether the activity is done in the room at the time slot with this resource for all possibilities
    # actions[t][a][o][0] symbolizes whether the activity is started at time t with object o
    actions = pl.LpVariable.dicts(
        "Action", (TIMESLOTS, ACTIVITIES_BUFFER, OBJECTS, RESOURCES), cat=pl.LpBinary
    )
    endtime = pl.LpVariable("Endtime", lowBound=0, upBound=deadline, cat=pl.LpInteger)

    ############################
    ### define the objective ###
    ############################

    # we want to minimize the time it takes (minimize the endtime)
    prob += endtime

    ##############################
    ### define the constraints ###
    ##############################

    ### start and end constraints ###
    # finish only happens once
    prob += pl.lpSum(actions[t][finish][0][0] for t in TIMESLOTS) == 1

    for t in TIMESLOTS:
        # finish happens on all objects at the same time
        prob += (
            pl.lpSum(actions[t][finish][o][0] for o in OBJECTS)
            == object_count * actions[t][finish][0][0]
        )
        prob += pl.lpSum(actions[t][finish][o][0] for o in OBJECTS) == pl.lpSum(
            actions[t][finish][o][0] for o in OBJECTS
        )

    # after finish nothing happens
    # after end, no activity is done
    for t in TIMESLOTS:
        for a in ACTIVITIES_BUFFER:
            for o in OBJECTS:
                # endtime is the last time a task is done
                prob += actions[t][a][o][0] * t <= endtime

    # end task is done at endtime and only then
    prob += (
        pl.lpSum(actions[t][finish][o][0] for t in TIMESLOTS for o in OBJECTS)
        == object_count
    )
    prob += (
        pl.lpSum(actions[t][finish][o][0] * t for t in TIMESLOTS for o in OBJECTS)
        == endtime * object_count
    )

    print("end constraints done")

    ### general activity object constraints ###

    for t in TIMESLOTS:
        # on every object there can be max 1 activity at a time
        for o in OBJECTS:
            prob += pl.lpSum(actions[t][a][o][0] for a in ACTIVITIES_BUFFER) <= 1

        # all real activities affect objects in line with their input set requirements
        for a in ACTIVITIES:
            # amount of objects of each type matches with occurrences in input set (or all zero) / relations are the same
            # first_type = object_sets[a][0]
            # for input_type_index in range(1, len(object_sets[a])):
            #     input_type = object_sets[a][input_type_index]
            #     prob += pl.lpSum(
            #         actions[t][a][o][0] for o in type_range_map[input_type]
            #     ) * object_sets[a].count(first_type) == pl.lpSum(
            #         actions[t][a][o][0] for o in type_range_map[first_type]
            #     ) * object_sets[a].count(input_type)

            # no objects of other types are affected
            for o in OBJECTS:
                if get_type(o) not in class_reqs[a]:
                    prob += actions[t][a][o][0] == 0

            # amount of objects of each type matches with occurrences in input set (or all zero) / relations are the same (r = 0)
            # and same resources used on objects forming a valid input set (r > 0)
            first_class = class_reqs[a][0]
            for r in RESOURCES:
                for c in class_reqs[a]:
                    prob += pl.lpSum(
                        actions[t][a][o][r] for o in type_range_map[c]
                    ) * class_reqs[a].count(first_class) == pl.lpSum(
                        actions[t][a][o][r] for o in type_range_map[first_class]
                    ) * class_reqs[a].count(c)

    print("general activity object constraints done")

    ### durations are considered -> if an activity is started at t with o, it blocks the next time slots during it's duration
    for time in TIMESLOTS:
        for act in ACTIVITIES_BUFFER:
            for o in OBJECTS:
                # duration can not exeed time limit if a started at t
                prob += (time + duration[act]) * actions[time][act][o][0] <= endtime + 1
                # if a started and duration > 1, the next time slots for o are also blocked
                for j in range(1, min((duration[act], deadline - time))):
                    for a in ACTIVITIES_BUFFER:
                        prob += (
                            actions[time + j][a][o][0] <= 1 - actions[time][act][o][0]
                        )
                for r in RESOURCES:
                    prob += pl.lpSum(
                        actions[time + j][a][ins][r]
                        for j in range(1, min((duration[act], deadline - time)))
                        for a in ACTIVITIES_BUFFER
                        for ins in OBJECTS
                    ) <= (1 - actions[time][act][o][0]) * len(ACTIVITIES_BUFFER) * len(
                        OBJECTS
                    ) * min((duration[act], deadline - time))
                    # if r used this time, r is blocked for the next duration-1 time slots
                    # for j in range(1, min((duration[act], last_time - time))):
                    #     for a in ACTIVITIES:
                    #         for ins in OBJECTS:
                    #             prob += (
                    #                 actions[time + j][a][ins][r]
                    #                 <= 1 - actions[time][act][o][r]
                    #            )
    print("duration constraints done")

    ### resource constraints ###

    for t in TIMESLOTS:
        for r in RESOURCES[1:]:
            # each resource is only used on objects that are involved in the activity anyways 
            # actions[t][a][o][r] => actions[t][a][o][0] 
            for o in OBJECTS:
                for a in ACTIVITIES:
                    prob += actions[t][a][o][0] >= actions[t][a][o][r]
                    
            # each resource is available when it is used
            if t not in availability[r]:
                prob += (
                    pl.lpSum(
                        actions[t][a][o][r] for a in ACTIVITIES_BUFFER for o in OBJECTS
                    )
                    == 0
                )
                pass
            for a in ACTIVITIES_BUFFER:
                # if there is at least one object affected by resource r, the activity is done with r --> no other activity can use r at the same time
                # TODO / DONE? make this RAM freindly
                # taken from https://stackoverflow.com/a/26875847
                other_as = ACTIVITIES_BUFFER[:]  # fastest way to copy
                other_as.remove(a)
                # NOTE: (1 - pl.lpSum(actions[t][a][o][r] for o in OBJECTS)) can be negative if a is started with several objects. Can only be as many as input set allows -> divided by input set it is 1 or 0
                prob += pl.lpSum(
                    actions[t][other_a][o][r] for other_a in other_as for o in OBJECTS
                ) <= (
                    1
                    - pl.lpSum(actions[t][a][o][r] for o in OBJECTS)
                    / len(class_reqs[a])
                ) * len(other_as) * len(OBJECTS)

                # for ins in OBJECTS:
                #     prob += pl.lpSum(
                #         actions[t][other_a][o][r]
                #         for other_a in other_as
                #         for o in OBJECTS
                #     ) <= (1 - actions[t][a][ins][r]) * len(other_as) * len(OBJECTS)
                # for ins in OBJECTS:
                #     for other_a in ACTIVITIES:
                #         if a != other_a:
                #             for o in OBJECTS:
                #                 prob += (
                #                     actions[t][other_a][o][r]
                #                     <= 1 - actions[t][a][ins][r]
                #                 )

                # the same activity does not use a resource at the same time in different action-objects
                # one resource is not used with more objects than the activity's input set allows
                prob += pl.lpSum(actions[t][a][o][r] for o in OBJECTS) <= len(
                    class_reqs[a]
                )
                # the objects that the resource is used on must be in line with input set requirements
                if len(class_reqs[a]) > 0:
                    first_class = class_reqs[a][0]
                    for input_type_index in range(1, len(class_reqs[a])):
                        input_type = class_reqs[a][input_type_index]
                        # objects in right relation
                        prob += pl.lpSum(
                            actions[t][a][o][r] for o in type_range_map[input_type]
                        ) * class_reqs[a].count(first_class) == pl.lpSum(
                            actions[t][a][o][r] for o in type_range_map[first_class]
                        ) * class_reqs[a].count(input_type)
                        # amount of objects of objects not bigger than input set allows (so not more than one action per activity with resource r)
                        prob += pl.lpSum(
                            actions[t][a][o][r] for o in type_range_map[input_type]
                        ) <= class_reqs[a].count(input_type)
                    for o in OBJECTS:
                        if get_type(o) not in class_reqs[a]:
                            prob += actions[t][a][o][r] == 0

        # each activity is executed with its required resources
        for a in ACTIVITIES:
            for o in OBJECTS:
                # consumption is satisfied
                # actions[t][a][o][0] symbolizes whether the activity is started at time t in room o
                prob += (
                    pl.lpSum(actions[t][a][o][r] for r in RESOURCES[1:])
                    == res_cons[a] * actions[t][a][o][0]
                )
                # satisfied only with required role
                prob += pl.lpSum(
                    actions[t][a][o][r] for r in roles_resources_map[role_req[a]]
                ) == pl.lpSum(actions[t][a][o][r] for r in RESOURCES[1:])

    print("resource constraints done")

    ### activity / data dependencies ###
    # state requirements
    for i in OBJECTS:
        for time in TIMESLOTS:
            times_before = range(0, time)
            # build room or install toilet before install shower,
            if i in rooms_range:
                prob += pl.lpSum(
                    actions[t][build_room][i][0] - actions[t][install_toilet_b][i][0]
                    for t in times_before
                ) >= pl.lpSum(actions[t][install_shower_b][i][0] for t in times_before)
                prob += pl.lpSum(
                    actions[t][install_toilet_b][i][0] for t in times_before
                ) >= pl.lpSum(actions[t][install_shower_t][i][0] for t in times_before)

            # build room or install shower before install toilet,
            if i in rooms_range:
                prob += pl.lpSum(
                    actions[t][build_room][i][0] - actions[t][install_shower_b][i][0]
                    for t in times_before
                ) >= pl.lpSum(actions[t][install_toilet_b][i][0] for t in times_before)
                prob += pl.lpSum(
                    actions[t][install_shower_b][i][0] for t in times_before
                ) >= pl.lpSum(actions[t][install_toilet_s][i][0] for t in times_before)

            # build room before install kitchen (and not bathroom),
            if i in rooms_range:
                prob += pl.lpSum(
                    actions[t][build_room][i][0]
                    - actions[t][install_toilet_b][i][0]
                    - actions[t][install_shower_b][i][0]
                    for t in times_before
                ) >= pl.lpSum(actions[t][install_kitchen][i][0] for t in times_before)

    ########################
    ### define the goals ###
    ########################

    ### goal = claims, assessments
    # kitchens
    prob += (
        pl.lpSum(
            actions[t][install_kitchen][i][0] for t in TIMESLOTS for i in rooms_range
        )
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
    print("goals done... start solving")

    # solve the problem
    prob.solve(pl.PULP_CBC_CMD(timeLimit=18000))

    # print the solution
    for t in TIMESLOTS:
        print("\nTime slot ", t)
        for a in ACTIVITIES_BUFFER:
            for o in OBJECTS:
                for r in RESOURCES:
                    if actions[t][a][o][r].varValue == 1:
                        print(
                            activity_names[a],
                            " on object ",
                            o,
                            "(",
                            type_names[get_type(o)],
                            ")",
                            " with ",
                            resource_names[r],
                        )

    # for cell in prob.variables():
    #     if cell.varValue == 1:
    #         print(cell.name, "=", cell.varValue)


do()
