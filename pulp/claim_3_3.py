import array
#from memory_profiler import profile
import pulp as pl

# TODO: think aubout data links.

# TODO: think about parallel usage (no blocking anymore) of data objects if they are not modified by the activities.
# TODO:     Maybe split activities into categories and formulate constraints on those as a base


# @profile
def do():
    # initialize the Problem
    prob = pl.LpProblem("fCM_claim_Schedule", pl.LpMinimize)
    """ 
    XXXXXXXXXXX
    """

    ########################################
    ### define variables for the process ###
    ########################################

    claims = 3
    assessments = 3
    object_count = claims + assessments

    claims_to_decide = 3
    assessments_to_make = 3

    deadline = 10

    #######################################
    ### define activities and resources ###
    #######################################

    ### activities ###

    # start and finish are fixed
    finish = 6
    # start, record, assess, question, decide, finish (end)
    record_claim = 0
    assess_claim = 1
    question_claim_b = 2
    question_claim_a = 3
    decide_claim_b = 4
    decide_claim_a = 5
    activity_names = [
        "record claim",
        "assess claim",
        "question claim (basic)",
        "question claim (request assessment)",
        "decide claim (basic)",
        "decide claim (with assessment)",
        "finish",
    ]

    duration = [1, 2, 1, 1, 1, 1, 1]
    role_req = [1, 2, 1, 1, 1, 1, 0]
    res_cons = [1, 1, 1, 1, 2, 2, 0]

    data_types = [0, 1]  # claim, assessment
    type_names = ["claim", "assessment"]
    class_reqs = [[0], [1], [0], [0, 1], [0], [0, 1], [0]]

    ### resources ###

    resource_names = ["-", "Wanda", "Willy", "Emil", "Erika"]
    roles = [[0], [1], [1], [1, 2], [2]]
    role_names = ["-", "worker", "expert"]
    availability = [
        range(0, deadline + 1),  # no resource / started, always available
        range(0, 5 + 1),
        range(0, deadline + 1),
        range(0, deadline + 1),
        range(3, deadline + 1),
    ]
    resource_ids = [0, 1, 2, 3, 4]  # no resource / started, Wanda, Willy, Emil, Erika
    role_ids = [0, 1, 2]  # nothing, worker, expert
    resource_roles_map = [
        [0],  # no role, no resource / started
        [1],  # Wanda -> worker
        [1],  # Willy -> worker
        [1, 2],  # Emil -> expert, worker
        [2],  # Erika -> expert
    ]
    roles_resources_map = [
        [0],  # no role, no resource / started
        [1, 2, 3],  # Worker: Wanda, Willy, Emil
        [3, 4],  # Expert: Emil, Erika
    ]

    #####################################
    ### define the decision variables ###
    #####################################

    # claims, assessments
    OBJECTS = array.array("b", range(object_count))
    claims_range = range(claims)
    assessments_range = range(claims, claims + assessments)
    type_range_map = [claims_range, assessments_range]

    def get_type(object_index):
        for type_index in range(len(type_range_map)):
            if object_index in type_range_map[type_index]:
                return type_index

    ACTIVITIES_BUFFER = array.array("b", range(finish + 1))
    ACTIVITIES = array.array("b", range(finish))  # real activities (not start and end)
    TIMESLOTS = array.array("b", range(0, deadline + 1))
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

    ### activity / data dependencies ###
    # state requirements
    for o in OBJECTS:
        for t in TIMESLOTS:
            times_before = range(0, t)

            # NOTE:
            # if they would require several objects of the same class in different
            # states, we would constraint this using the common resources.

            # record before question
            if o in claims_range:
                prob += pl.lpSum(
                    actions[t][record_claim][o][0] for t in times_before
                ) >= pl.lpSum(
                    actions[t][question_claim_a][o][0]
                    + actions[t][question_claim_b][o][0]
                    for t in times_before
                )

            # question_a before assess
            if o in assessments_range:
                prob += pl.lpSum(
                    actions[t][question_claim_a][o][0] for t in times_before
                ) >= pl.lpSum(actions[t][assess_claim][o][0] for t in times_before)

            # question_b before decide_b
            if o in claims_range:
                prob += pl.lpSum(
                    actions[t][question_claim_b][o][0] for t in times_before
                ) >= pl.lpSum(actions[t][decide_claim_b][o][0] for t in times_before)

            # assess and question_a before decide_a
            if o in claims_range:
                # question_a before decide_a on claim
                prob += pl.lpSum(
                    actions[t][question_claim_a][o][0] for t in times_before
                ) >= pl.lpSum(actions[t][decide_claim_a][o][0] for t in times_before)
            if o in assessments_range:
                # assess before decide_a on assessment
                prob += pl.lpSum(
                    actions[t][assess_claim][o][0] for t in times_before
                ) >= pl.lpSum(actions[t][decide_claim_a][o][0] for t in times_before)

    # decide_a on claim and assessment only if question_a on them before (data link)
    # order is already ensured
    for c in type_range_map[0]:
        for a in type_range_map[1]:
            prob += pl.lpSum(
                (
                    actions[t][question_claim_a][c][r]
                    == actions[t][question_claim_a][a][r]
                    and actions[t][question_claim_a][a][r] == 1
                )
                for t in TIMESLOTS
                for r in RESOURCES[1:]
            ) >= pl.lpSum(
                (
                    actions[t][decide_claim_a][a][r] == actions[t][decide_claim_a][c][r]
                    and actions[t][question_claim_a][a][r] == 1
                )
                for t in TIMESLOTS
                for r in RESOURCES[1:]
            )

    ### durations are considered -> if an activity is started at t with o, it blocks the next time slots during it's duration
    for t in TIMESLOTS:
        # on every object there can be max 1 activity at a time
        for o in OBJECTS:
            prob += pl.lpSum(actions[t][a][o][0] for a in ACTIVITIES_BUFFER) <= 1

        for act in ACTIVITIES_BUFFER:
            for o in OBJECTS:
                # duration can not exeed time limit if a started at t
                prob += (t + duration[act]) * actions[t][act][o][0] <= endtime + 1
                # if a started and duration > 1, the next time slots for o are also blocked
                for j in range(1, min((duration[act], deadline - t))):
                    for a in ACTIVITIES_BUFFER:
                        prob += actions[t + j][a][o][0] <= 1 - actions[t][act][o][0]
                for r in RESOURCES[1:]:
                    prob += pl.lpSum(
                        actions[t + j][a][ins][r]
                        for j in range(1, min((duration[act], deadline - t)))
                        for a in ACTIVITIES_BUFFER
                        for ins in OBJECTS
                    ) <= (1 - actions[t][act][o][r]) * len(ACTIVITIES_BUFFER) * len(
                        OBJECTS
                    ) * min((duration[act], deadline - t))
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
                # no resources not fitting the role are used. Already ensured by the above constraints
                # for r in RESOURCES[1:]:
                #     if r not in roles_resources_map[role_req[a]]:
                #         prob += actions[t][a][o][r] == 0

    print("resource constraints done")

    ### OLC constraints ###
    for o in claims_range:
        # all states of claim can only be reached once (same activity only executed once on same object)
        for a in ACTIVITIES:
            prob += pl.lpSum(actions[t][a][o][0] for t in TIMESLOTS) <= 1
        # only question_claim_b or question_claim_a
        prob += (
            pl.lpSum(
                actions[t][question_claim_b][o][0] + actions[t][question_claim_a][o][0]
                for t in TIMESLOTS
            )
            <= 1
        )
        # only decide_claim_b or decide_claim_a
        prob += (
            pl.lpSum(
                actions[t][decide_claim_a][o][0] + actions[t][decide_claim_b][o][0]
                for t in TIMESLOTS
            )
            <= 1
        )
    # all states of assessment can only be reached once (same activity only executed once on same object)
    for o in assessments_range:
        for a in ACTIVITIES:
            prob += pl.lpSum(actions[t][a][o][0] for t in TIMESLOTS) <= 1

    ########################
    ### define the goals ###
    ########################

    ### goal = claims, assessments
    # claims to decide
    prob += (
        pl.lpSum(
            actions[t][decide_claim_a][o][0] + actions[t][decide_claim_b][o][0]
            for t in TIMESLOTS
            for o in claims_range
        )
        >= claims_to_decide
    )
    # assessments to make
    prob += (
        pl.lpSum(
            actions[t][assess_claim][o][0] for t in TIMESLOTS for o in assessments_range
        )
        >= assessments_to_make
    )
    prob += (
        pl.lpSum(
            actions[t][decide_claim_a][o][0]
            for t in TIMESLOTS
            for o in assessments_range
        )
        >= assessments_to_make
    )

    # prob += (
    #     pl.lpSum(
    #         (
    #             (actions[t][question_claim_a][0][r] + actions[t][question_claim_a][a][r])
    #             and (actions[t][question_claim_a][a][r] == 1)
    #         )
    #         for t in TIMESLOTS
    #         for r in RESOURCES[1:]
    #         for a in assessments_range
    #     )
    #     #/ (res_cons[question_claim_a])
    #     >= 1
    # )
    
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
