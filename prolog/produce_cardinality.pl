% different approach

% activity(start).
% activity(end).
% activity(do1).
% activity(do2).

% schedule a dynamic amount of tasks 
% works like a charm
% tasks(Tasks, Starts, End, Produces), labeling([min(End)], Starts).
produces(1,1).
produces(2,1).
produces(3,2).
produces(4,3).
tasks(Tasks,Starts,End,Produce) :-
    maplist(task_map,Tasks,Starts),
    Starts ins 0..20,
    maplist(task_id,Tasks,TaskIDs),
    % TODO: adjust global_cardinality to be more dynamic
    global_cardinality(TaskIDs, [1-1,2-1,3-_,4-_]), % start and end must be executed exactly once
    cumulative(Tasks, [limit(1)]), % limit specifies the resource limit
    foldl(produced, Tasks, 0, Produce), % finds amount of produced items
    foldl(max_end, Tasks, 0, End). % finds latest (max) End time

% task(start_time, duration, end_time, resource_consumption, ID)
task_map(task(Start,1,_,1,TaskID),Start):- TaskID in 1..4. % duration and consumption 1
task_id(task(_,_,_,_,TaskID),TaskID).

max_end(task(_,_,End,_,_), E0, E) :-
E #= max(E0, End). % finds latest (max) End time.

produced(task(_,_,_,_,ID), Produce0, Produce) :-
    produces(ID,B),
    Produce #= Produce0 + B.