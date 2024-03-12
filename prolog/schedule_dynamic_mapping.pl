% different approach

% activity(start).
% activity(end).
% activity(do1).
% activity(do2).

% only a simple goal of producing one thing
% not terminating
% schedule(TaskIDs, Starts, Ends, 10, End), labeling([min(End)], Starts).
task(1,1,0). % id, duration, produced
task(2,1,0).
task(3,1,1).
task(4,2,3).
schedule(TaskIDs, Starts, Ends, Produced, End) :-
    % Produced #=10, as parameter
    maplist(task_mapping, TaskIDs, Starts, Ends),
    TaskIDs ins 1..4,
    Starts ins 0..20,
    Ends ins 0..30,
    global_cardinality(TaskIDs, [1-1,2-1]), % start and end must be executed exactly once
    foldl(produced, TaskIDs, 0, Produced),
    max_list(Ends, End). % finds latest (max) End time.

produced(TaskID, PrevProduced, NewProduced) :- 
    task(TaskID,_,CurrProduced), 
    NewProduced #= (PrevProduced + CurrProduced).
task_mapping(TaskID, Start, End):- 
    task(TaskID,Duration,_), 
    End #= Start + Duration.

% with DOs, not continued
% 1 - room, 2 - house
data_obj(1).
data_obj(2).

obj_state(1, 1). % clean
obj_state(1, 2). % final
obj_state(1, 3). % dirty

obj_state(2, 1). % started
obj_state(2, 2). % one_roomed
obj_state(2, 3). % two_roomed
obj_state(2, 4). % final

instance(Obj, State, _) :- obj_state(Obj, State), data_obj(Obj).
%instance_assoc(Inst1, Inst2).
% schedule(Tasks, Starts, Ends, Resources, DataObjects).



%state(Time, RunningActivities, AvailableDOs, BlockedDOs) :- GoalDos = .
