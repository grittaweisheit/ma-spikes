% different approach
% :- use_module(library(clpfd)).
% activity(start).
% activity(end).
% activity(do1).
% activity(do2).

% schedule a dynamic amount of tasks with order constraints
% tasks(Tasks, Starts, End, Produces), labeling([min(End)], Starts).
activity(1,1,1,1). % id, duration, resource consumption, produces
activity(2,1,1,1).
activity(3,2,1,3).
activity(4,3,1,2).
activity(5,1,1,1).

tasks(Tasks,Starts,End,Produce) :-  
    % maplist(task_map,Tasks,Starts,TaskIDs), (don't use this. slows down the program)
    maplist(task_start,Tasks,Starts),
    Starts ins 0..50,
    chain(Starts, #=<), % Starts are sorted from last to first timestamp
    maplist(task_id,Tasks,TaskIDs),
    maplist(task_end,Tasks,Ends),
    Ends ins 0..60,

    % --- RULES --- %  
    rule_X_before_Y(4,3,TaskIDs,0,0),
    % TODO: adjust global_cardinality to be more dynamic
    global_cardinality(TaskIDs, [1-1,2-1,3-_,4-_, 5-_]), % start and end must be executed exactly once
    foldl(produced, Tasks, 0, Produce), % makes sure enough was produced
    cumulative(Tasks, [limit(1)]), % limit specifies the resource limit
    % --- RULES --- %  

    foldl(max_end, Tasks, 0, End), % finds latest (max) End time
    write(TaskIDs), 
    labeling([min(End)], Starts),
    write(Starts). 

% task(start_time, duration, end_time, resource_consumption, ID)
task_start(task(Start,1,_,1,_),Start). % duration and consumption 1
task_id(task(_,_,_,_,TaskID),TaskID).
task_end(task(_,_,End,_,_),End).
/* task_map(task(Start,Duration,_,ResourceConsumtion,ID),Start,ID) :- 
    %End #= Start + Duration,
    activity(ID,Duration,ResourceConsumtion,_). */

max_end(task(_,_,End,_,_), E0, E) :-
E #= max(E0, End). % finds latest (max) End time.

produced(task(_,_,_,_,ID), Produce0, Produce) :-
    activity(ID,_,_,B),
    Produce #= Produce0 + B.

% one task 1 must end before any task 2 can start in list Tasks
follows_task_in(ID_1, ID_2, TaskIDs, Starts) :- 
    % TaskIDs and Starts should be mapped the same over Tasks
    End_2 #< Start_1, 
    activity(ID_2,D,_,_),
    End_2 #= Start_2 + D, 
    %foldl(is_task_before(ID_1, ID_2), TaskIDs, Starts, 0, ID_2_s).
    element(N_1, TaskIDs, ID_1),
    element(N_2, TaskIDs, ID_2),
    element(N_1, Starts, Start_1),
    element(N_2, Starts, Start_2).  

% before every task Y there must have been a corresponding task X somewhere
rule_X_before_Y(_,_,[],_,_).
rule_X_before_Y(X,Y,[HID|TaskIDs], Count_X,Count_Y) :-
    X #= HID #<==> B_X,
    Y #= HID #<==> B_Y,
    Next_Count_X #= Count_X + B_X,
    Next_Count_Y #= Count_Y + B_Y,
    Next_Count_X #>= Next_Count_Y,
    rule_X_before_Y(X, Y, TaskIDs, Next_Count_X, Next_Count_Y).

% counts tasks with ID that ended before Time
tasks_before(_, _, [], [], 0).
tasks_before(ID, Time, [HID|TaskIDs], [HEnd|Ends], Counter) :-
    (HID #= ID #/\ HEnd #< Time) #<==> B,
    Counter #= PrevCounter + B,
    tasks_before(ID, Time, TaskIDs, Ends, PrevCounter).