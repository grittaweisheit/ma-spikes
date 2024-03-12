activity(N) :- N #>= 0, N #< 4.
% activity(start).
% activity(do1).
% activity(do2).
% activity(end).

action(Activity, Start, End) :- 
    activity(Activity), 
    Start #< End, 
    Start #> -1, 
    End #< 10.

schedule([]).
schedule([action(Action, S, E) | L_Actions]):- 
    action(Action, S, E), 
    length(L_Actions, N), 
    N #< 3, 
    schedule(L_Actions). 

activities([]).
activities([H | L]) :- activity(H), activities(L), length(L, N), N #< 2.

% https://github.com/triska/clpfd/blob/master/tasks.pl
% tasks(Tasks, Starts, End), labeling([min(End)], Starts).
tasksE(Tasks, Starts, End) :-
    Tasks = [task(_,3,_,1,_), % task(start_time, duration, end_time, resource_consumption)
             task(_,4,_,1,_),
             task(_,2,_,1,_),
             task(_,3,_,1,_)],
    maplist(task_start, Tasks, Starts),
    Starts ins 0..100,
    cumulative(Tasks, [limit(2)]), % limit specifies the resource limit
    foldl(max_end, Tasks, 0, End). % finds latest (max) End time

task_start(task(Start,_,_,_,_), Start).

max_end(task(_,_,End,_,_), E0, E) :-
    E #= max(E0, End).

% my take; tasks(Tasks, Starts, End), labeling([min(End)], Starts).
% makes a schedule where start activity starts before all and end only starts when everything else is finished

tasks(Tasks, Starts, End) :-
    Tasks = [task(_,1,Ee,1,end),
             task(_,1,_,1,do1),
             task(Ss,1,_,1,start),
             task(_,1,_,1,do2)],
    maplist(task_start, Tasks, Starts),
    Starts ins 0..100,
    cumulative(Tasks, [limit(1)]),
    maplist(task_starts_after(Ss),Tasks),
    maplist(task_ends_before(Ee),Tasks),
    foldl(max_end, Tasks, 0, End).

task_starts_after(Time, task(Start,_,_,_,_)) :- Start #>= Time.

task_ends_before(_, task(_,_,_,_,end)).
task_ends_before(Time, task(_,_,End,_,_)) :- Time #>= End.