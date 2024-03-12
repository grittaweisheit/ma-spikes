% room(empty).
% room(kitchen).
% room(bathroom).
% room(N) :- N in 0..2.

% house([],0).
% house([HRoom | Rooms], NumberOfRooms) :- 
%     room(HRoom), 
%     NewNumberOfRooms #= NumberOfRooms - 1,  
%     length(Rooms, NewNumberOfRooms),
%     house(Rooms, NewNumberOfRooms),
%     all_different([HRoom | Rooms]) .

hostel(Kitchens, Bathrooms, Empty, Value) :- 
    Kitchens in 0..100,
    Bathrooms in 0..100,
    Empty in 0..100,
    Value in 0..100,
    Kitchens * 6 #>= Empty,
    Bathrooms *3 #>= Empty,
    Kitchens + Bathrooms + Empty #=< 100,
    Value #= (Kitchens * 5 + Bathrooms * 2 + 5*Empty) - (Kitchens * 9 + Bathrooms * 6 + Empty * 2).