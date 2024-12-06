import requests
import chess
import chess.pgn
from stockfish import Stockfish

# URL of the Lichess opening explorer
url = "https://explorer.lichess.ovh/lichess"

# Initialize Stockfish
stockfish = Stockfish(path="C:\\Apps\\stockfish\\stockfish-windows-x86-64-avx2.exe")

# Function to get Black's moves from Lichess
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

# Recursive function to build opening repertoire
def build_opening_repertoire(board, moves, depth=3):
    if depth == 0:
        return []

    repertoire = []
    stockfish.set_position(moves)
    white_move = stockfish.get_best_move()

    if not white_move:
        return repertoire

    # Play White's move
    board.push_uci(white_move)
    moves.append(white_move)

    # Get Black's moves
    black_moves = get_black_moves(moves)

    for black_move in black_moves:
        board.push_uci(black_move)
        moves.append(black_move)

        # Recursively build the repertoire
        sub_repertoire = build_opening_repertoire(board, moves, depth - 1)
        repertoire.extend(sub_repertoire)

        # Create a PGN game
        game = chess.pgn.Game()
        game.from_board(board)
        repertoire.append(str(game))

        # Backtrack
        moves.pop()
        board.pop()

    # Backtrack White's move
    moves.pop()
    board.pop()

    return repertoire

# Main execution
if __name__ == "__main__":
    # Start from an empty chess board
    board = chess.Board()
    initial_moves = []

    # Build the repertoire
    repertoire = build_opening_repertoire(board, initial_moves, depth=3)

    # Save repertoire to a PGN file
    with open("opening_repertoire.pgn", "w") as file:
        for game in repertoire:
            file.write(game + "\n\n")

    print("Opening repertoire saved to 'opening_repertoire.pgn'")
