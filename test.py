import requests
import chess
import chess.pgn
from stockfish import Stockfish

# Lichess opening explorer API URL
url = "https://explorer.lichess.ovh/lichess"

# Initialize Stockfish
stockfish = Stockfish(path="C:\\Apps\\stockfish\\stockfish-windows-x86-64-avx2.exe")

# Function to get Black's moves from Lichess
def get_black_moves(moves):
    moves_str = ",".join(moves)  # Convert the list of moves to a comma-separated string
    params = {
        "play": moves_str,
        "topGames": 0,
        "recentGames": 0,
        "moves": 10  # Maximum moves to fetch
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        moves_data = data.get('moves', [])
        total_games = data.get('white', 0) + data.get('draws', 0) + data.get('black', 0)
        valid_moves = []
        for move in moves_data:
            move_percentage = (move['white'] + move['draws'] + move['black']) / total_games
            if move_percentage > 0.1:  # Filter moves based on popularity
                valid_moves.append(move['uci'])
        return valid_moves
    except requests.RequestException as e:
        print(f"API error for {moves}: {e}")
        return []
    except KeyError as e:
        print(f"Missing data in Lichess response for {moves}: {e}")
        return []

# Recursive function to build the opening repertoire
def build_opening_repertoire(board, moves, depth=10, repertoire=None):
    if repertoire is None:
        repertoire = []

    if depth == 0:
        print(f"Reached max depth with moves: {moves}")
        return repertoire

    # Get White's best move from Stockfish
    stockfish.set_position(moves)
    white_move = stockfish.get_best_move()
    if not white_move or not board.is_legal(chess.Move.from_uci(white_move)):
        print(f"Stockfish suggested illegal move: {white_move} for moves {moves}")
        return repertoire

    # Play White's move
    board.push_uci(white_move)
    moves.append(white_move)
    print(f"White plays: {white_move}")

    # Get Black's common responses
    black_moves = get_black_moves(moves)
    if not black_moves:
        print(f"No valid Black moves for {moves}")
        moves.pop()
        board.pop()
        return repertoire

    for black_move in black_moves:  # Limit to top 3 Black responses
        if not board.is_legal(chess.Move.from_uci(black_move)):
            print(f"Skipping illegal Black move: {black_move}")
            continue

        board.push_uci(black_move)
        moves.append(black_move)
        print(f"Black plays: {black_move}")

        # Create a PGN node without headers
        game = chess.pgn.Game()
        node = game
        for move in board.move_stack:
            node = node.add_main_variation(move)

        repertoire.append(game)

        # Recursively explore further moves
        build_opening_repertoire(board, moves, depth - 1, repertoire)

        # Backtrack moves
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
    repertoire = build_opening_repertoire(board, initial_moves, depth=10)

    # Save repertoire to a PGN file without headers
    with open("opening_repertoire.pgn", "w") as file:
        for game in repertoire:
            exporter = chess.pgn.StringExporter(headers=False, variations=True, comments=False)
            file.write(game.accept(exporter) + "\n\n")

    print("Opening repertoire saved to 'opening_repertoire.pgn'")
