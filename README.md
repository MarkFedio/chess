# chess
Chess made with Pygame. No AI (including the pieces which I drew in MS Paint...)

Run using
python main.py {0 or 1}.
  0 will make the board flip after each turn.
  1 will make the board keep its orientation. (Recommended)


By default the engine looks 3 moves in advance and uses a heuristic approach
to evaluating postions (piece value, piece movement, king danger). The 
engine depth can be changed in constants.py if you really want, but 
3 is a reasonable depth for a competetive match (Somewhere between 300-1000 elo if I had to guess) that won't take absurdly long.
