import requests
from stockfish import Stockfish

# URL of the Lichess opening explorer
url = "https://explorer.lichess.ovh/lichess"

# Initialize Stockfish
stockfish = Stockfish(path="C:\\Apps\\stockfish\\stockfish-windows-x86-64-avx2.exe")

# Function to get opening data for Black's responses
def get_black_moves(moves):
    moves_str = ",".join(moves)  # Convert the list of moves to a comma-separated string
    params = {
        "play": moves_str,  # Moves in UCI notation
        "topGames": 0,  # Number of top games to display
        "recentGames": 0,  # Number of recent games to display
        "moves": 10  # Number of most common moves to display
    }
    try:
        # Send GET request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors

        # Parse the JSON response
        data = response.json()
        moves_data = data.get('moves', [])
        total_games = data.get('white', 0) + data.get('draws', 0) + data.get('black', 0)
        
        # Filter moves with at least 10% frequency
        valid_moves = []
        for move in moves_data:
            move_percentage = (move['white'] + move['draws'] + move['black']) / total_games
            if move_percentage > 0.1:
                valid_moves.append(move['uci'])
        return valid_moves
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return []
    except KeyError as e:
        print(f"Missing data in the response: {e}")
        return []

# Function to recursively build the opening repertoire
def build_opening_repertoire(moves, depth=3, repertoire=None):
    if repertoire is None:
        repertoire = []

    # Base case: if the depth is 0, return
    if depth == 0:
        return repertoire

    # White's move from Stockfish
    stockfish.set_position(moves)
    white_move = stockfish.get_best_move()

    if not white_move:
        return repertoire  # Stop if Stockfish fails to generate a move

    # Add White's move
    moves.append(white_move)

    # Get Black's responses from Lichess
    black_moves = get_black_moves(moves)

    # Iterate over Black's valid moves
    for black_move in black_moves:
        moves.append(black_move)

        # Recursively build the repertoire for the next depth level
        build_opening_repertoire(moves, depth - 1, repertoire)

        # Convert moves to PGN and add to repertoire
        stockfish.set_position(moves)
        pgn = stockfish.get_pgn()
        repertoire.append(pgn)

        # Backtrack
        moves.pop()

    # Backtrack White's move
    moves.pop()

    return repertoire

# Start building the opening repertoire from the root position
initial_moves = []
repertoire = build_opening_repertoire(initial_moves)

# Save the repertoire to a PGN file
with open("opening_repertoire.pgn", "w") as file:
    for line in repertoire:
        file.write(line + "\n\n")

print("Opening repertoire saved to 'opening_repertoire.pgn'")
