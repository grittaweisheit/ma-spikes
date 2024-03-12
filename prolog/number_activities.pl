activity(N) :- N #>= 0, N #< 4.
% with this only start gets assigned before loading forever
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
