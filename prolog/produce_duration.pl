% different approach
% :- use_module(library(clpfd)).
% activity(start).
% activity(end).
% activity(do1).
% activity(do2).

% schedule a dynamic amount of tasks with durations
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