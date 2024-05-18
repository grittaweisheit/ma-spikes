import array
from memory_profiler import profile
import pulp as pl

# TODO: think aubout data links.

# TODO: think about parallel usage (no blocking anymore) of data instances if they are not modified by the activities.
# TODO:     Maybe split activities into categories and formulate constraints on those as a base


@profile
def do():
    # initialize the Problem
    prob = pl.LpProblem("fCM_room_Schedule", pl.LpMinimize)
    """ 
    schedules the activities to build 3 rooms in a house. 
    No resources, no time constraints, every activity takes 1 timeslot. 
    """

    ########################################
    ### define variables for the process ###
    ########################################

    claims = 3
    assessments = 1
    instance_count = claims + assessments

    claims_to_decide = 3
    assessments_to_make = 1

    last_time = 10
    first_time = 0

    #######################################
    ### define activities and resources ###
    #######################################

    ### activities ###

    # start and finish are fixed
    start_activity = 0
    end_activity = 5
    # start, record, assess, question, decide, finish (end)
    record_claim = 1
    assess_claim = 2
    question_claim_b = 3
    question_claim_a = 4
    decide_claim_b = 5
    decide_claim_a = 4
    activity_names = [
        "start",
        "record claim",
        "assess claim",
        "question claim (basic)",
        "question claim (request assessment)",
        "decide claim (basic)",
        "decide claim (with assessment)",
        "finish",
    ]

    duration = [1, 1, 1, 1, 1, 2, 2, 1]
    role_requirement = [0, 1, 2, 1, 1, 1, 1, 0]
    resource_consumption = [0, 1, 1, 1, 1, 2, 2, 0]

    data_types = [0, 1]  # claim, assessment
    input_sets = [[0], [0], [1], [0], [0], [0, 1], [0], [0]]

    ### resources ###

    resource_names = ["-", "Wanda", "Willy", "Emil", "Erika"]
    role_names = ["-", "worker", "expert"]
    availability = [
        range(first_time, last_time + 1),
        range(first_time, last_time + 1),
        range(first_time, last_time + 1),
        range(first_time, last_time + 1),
        range(first_time, last_time + 1),
        range(first_time, 2),
        range(first_time, last_time + 1),
    ]
    resource_ids = [0, 1, 2, 3, 4]  # no resource / started, Wanda, Willy, Emil, Erika
    roles = [0, 1, 2]  # nothing, builder, shower-crew, toilet-crew, kitchen-crew, buyer
    resource_roles_map = [
        [0],  # no role, no resource / started
        [1],  # Wanda -> worker
        [1],  # Willy -> worker
        [2],  # Emil -> expert, worker
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
    INSTANCES = array.array("b", range(instance_count))
    claims_range = range(claims)
    assessments_range = range(claims, claims + assessments)
    type_range_map = [claims_range, assessments_range]

    def get_type(instance_index):
        for type_index in range(len(type_range_map)):
            if instance_index in type_range_map[type_index]:
                return type_index

    # activities
    ACTIVITIES = array.array("b", range(start_activity, end_activity + 1))
    RACTIVITIES = array.array(
        "b", range(start_activity + 1, end_activity)
    )  # real activities (not start and end)
    # time slots
    TIMESLOTS = array.array("b", range(first_time, last_time + 1))
    # resources
    RESOURCES = array.array("b", resource_ids)

    # we have a decision variable whether the activity is done in the room at the time slot with this resource for all possibilities
    # actions[t][a][i][0] symbolizes whether the activity is started at time t in room i
    actions = pl.LpVariable.dicts(
        "Action", (TIMESLOTS, ACTIVITIES, INSTANCES, RESOURCES), cat=pl.LpBinary
    )
    endtime = pl.LpVariable("Endtime", lowBound=0, upBound=last_time, cat=pl.LpInteger)
    starttime = pl.LpVariable(
        "Starttime", lowBound=0, upBound=last_time, cat=pl.LpInteger
    )

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
        prob += pl.lpSum(
            actions[t][start_activity][i][0] for i in INSTANCES
        ) == pl.lpSum(actions[t][start_activity][i][0] for i in INSTANCES)
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
        pl.lpSum(
            actions[t][end_activity][i][0] * t for t in TIMESLOTS for i in INSTANCES
        )
        == endtime * instance_count
    )
    # start task is done at starttime and only then
    prob += (
        pl.lpSum(actions[t][start_activity][i][0] for t in TIMESLOTS for i in INSTANCES)
        == instance_count
    )
    prob += (
        pl.lpSum(
            actions[t][start_activity][i][0] * t for t in TIMESLOTS for i in INSTANCES
        )
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
                        prob += (
                            actions[time + j][a][i][0] <= 1 - actions[time][act][i][0]
                        )
                for r in RESOURCES:
                    prob += pl.lpSum(
                        actions[time + j][a][ins][r]
                        for j in range(1, min((duration[act], last_time - time)))
                        for a in ACTIVITIES
                        for ins in INSTANCES
                    ) <= (1 - actions[time][act][i][0]) * len(ACTIVITIES) * len(
                        INSTANCES
                    ) * min((duration[act], last_time - time))
                    # if r used this time, r is blocked for the next duration-1 time slots
                    # for j in range(1, min((duration[act], last_time - time))):
                    #     for a in ACTIVITIES:
                    #         for ins in INSTANCES:  # TODO muss das hier sein oder geht auch auf einer höheren ebene?
                    #             prob += (
                    #                 actions[time + j][a][ins][r]
                    #                 <= 1 - actions[time][act][i][r]
                    #            )

    ### resource constraints ###

    for t in TIMESLOTS:
        for r in RESOURCES[1:]:
            for a in ACTIVITIES:
                # if there is one instance affected by resource r, the activity is done with r --> no other activity can use r at the same time
                # taken from https://stackoverflow.com/a/26875847
                other_as = ACTIVITIES[:]  # fastest way to copy
                other_as.remove(a)
                # NOTE: (1 - pl.lpSum(actions[t][a][i][r] for i in INSTANCES)) can be negative if a is started with several instances. Can only be as many as input set allows -> divided by input set it is 1 or 0
                prob += pl.lpSum(
                    actions[t][other_a][i][r] for other_a in other_as for i in INSTANCES
                ) <= (
                    1
                    - pl.lpSum(actions[t][a][i][r] for i in INSTANCES)
                    / len(input_sets[a])
                ) * len(other_as) * len(INSTANCES)
                # for ins in INSTANCES:
                #     prob += pl.lpSum(
                #         actions[t][other_a][i][r]
                #         for other_a in other_as
                #         for i in INSTANCES
                #     ) <= (1 - actions[t][a][ins][r]) * len(other_as) * len(INSTANCES)
                # for ins in INSTANCES:
                #     for other_a in ACTIVITIES:
                #         if a != other_a:
                #             for i in INSTANCES:
                #                 prob += (
                #                     actions[t][other_a][i][r]
                #                     <= 1 - actions[t][a][ins][r]
                #                 )

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
                    actions[t][a][i][r]
                    for r in roles_resources_map[role_requirement[a]]
                ) == pl.lpSum(actions[t][a][i][r] for r in RESOURCES[1:])

        ### OLC constraints ###
        # all states of claim can only be reached once (same activity only executed once on same instance)
        for i in claims_range:
            for a in ACTIVITIES:
                prob += pl.lpSum(actions[t][a][i][0] for t in TIMESLOTS) <= 1
            # only question_claim_b or question_claim_a
            prob += (
                pl.lpSum(
                    actions[t][question_claim_b][i][0]
                    + actions[t][question_claim_a][i][0]
                    for t in TIMESLOTS
                )
                <= 1
            )
            # only decide_claim_b or decide_claim_a
            prob += (
                pl.lpSum(
                    actions[t][decide_claim_a][i][0] + actions[t][decide_claim_b][i][0]
                    for t in TIMESLOTS
                )
                <= 1
            )
        # same for assessments
        for i in assessments_range:
            for a in ACTIVITIES:
                prob += pl.lpSum(actions[t][a][i][0] for t in TIMESLOTS) <= 1

    ### activity / data dependencies ###
    for i in INSTANCES:
        for time in TIMESLOTS:
            times_before = range(0, time)

            # question_a before assess
            if i in assess_claim:
                prob += pl.lpSum(
                    actions[t][question_claim_a][i][0] for t in times_before
                ) >= pl.lpSum(actions[t][assess_claim][i][0] for t in times_before)

            # record before question
            if i in assessments_range:
                prob += pl.lpSum(
                    actions[t][record_claim][i][0] for t in times_before
                ) >= pl.lpSum(
                    actions[t][question_claim_a][i][0]
                    + actions[t][question_claim_b][i][0]
                    for t in times_before
                )

            # question_b before decide_b
            if i in claims_range:
                prob += pl.lpSum(
                    actions[t][question_claim_b][i][0] for t in times_before
                ) >= pl.lpSum(actions[t][decide_claim_b][i][0] for t in times_before)

            # assess and question_a before decide_a
            if i in claims_range:
                # questoion_a before decide_a on claim
                prob += pl.lpSum(
                    actions[t][question_claim_a][i][0] for t in times_before
                ) >= pl.lpSum(actions[t][decide_claim_a][i][0] for t in times_before)
            if i in assessments_range:
                # assess before decide_a on assessment
                prob += pl.lpSum(
                    actions[t][assess_claim][i][0] for t in times_before
                ) >= pl.lpSum(actions[t][decide_claim_a][i][0] for t in times_before)

    ########################
    ### define the goals ###
    ########################

    ### goal = claims, assessments
    # claims to decide
    prob += (
        pl.lpSum(
            actions[t][decide_claim_a][i][0] + actions[t][decide_claim_b][i][0]
            for t in TIMESLOTS
            for i in claims_range
        )
        >= claims_to_decide
    )
    # assessments to make
    prob += (
        pl.lpSum(
            actions[t][assess_claim][i][0] for t in TIMESLOTS for i in assessments_range
        )
        >= assessments_to_make
    )
    prob += (
        pl.lpSum(
            actions[t][decide_claim_a][i][0]
            for t in TIMESLOTS
            for i in assessments_range
        )
        >= assessments_to_make
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


do()
