import requests
import chess
import chess.pgn
from stockfish import Stockfish
from concurrent.futures import ThreadPoolExecutor, as_completed

# Lichess opening explorer API URL
url = "https://explorer.lichess.ovh/lichess"

# Initialize Stockfish with improved settings
stockfish = Stockfish(path="C:\\Apps\\stockfish\\stockfish-windows-x86-64-avx2.exe")
stockfish.set_skill_level(20)  # Set skill level for deeper analysis
stockfish.set_depth(15)  # Increase depth for stronger move selection

# Global variables for tracking API requests and progress
api_request_count = 0
total_moves_explored = 0  # Total number of moves explored

# Function to get Black's moves from Lichess
def get_black_moves(moves):
    global api_request_count
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
        api_request_count += 1  # Increment API request counter
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

# Recursive function to build the opening repertoire with parallel processing
def build_opening_repertoire(board, moves, depth=10, repertoire=None):
    global total_moves_explored

    if repertoire is None:
        repertoire = []

    if depth == 0:
        return repertoire

    # Get White's best move from Stockfish
    stockfish.set_position(moves)
    white_move = stockfish.get_best_move()
    if not white_move or not board.is_legal(chess.Move.from_uci(white_move)):
        return repertoire

    # Play White's move
    board.push_uci(white_move)
    moves.append(white_move)
    total_moves_explored += 1  # Increment total moves explored

    # Get Black's common responses
    black_moves = get_black_moves(moves)
    if not black_moves:
        moves.pop()
        board.pop()
        return repertoire

    # Use ThreadPoolExecutor for parallel exploration of Black's moves
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_move = {executor.submit(explore_black_move, board, moves, black_move, depth - 1): black_move for black_move in black_moves}
        
        for future in as_completed(future_to_move):
            black_move = future_to_move[future]
            try:
                child_repertoire = future.result()
                if child_repertoire:
                    repertoire.extend(child_repertoire)
            except Exception as e:
                print(f"Error processing {black_move}: {e}")

    # Backtrack White's move
    moves.pop()
    board.pop()

    return repertoire

# Helper function to explore a single Black move and build the repertoire recursively
def explore_black_move(board, moves, black_move, depth):
    global total_moves_explored

    if not board.is_legal(chess.Move.from_uci(black_move)):
        return None

    board.push_uci(black_move)
    moves.append(black_move)
    total_moves_explored += 1  # Increment total moves explored

    # Create a PGN node without headers
    game = chess.pgn.Game()
    node = game
    for move in board.move_stack:
        node = node.add_main_variation(move)

    # Recurse further
    child_repertoire = build_opening_repertoire(board, moves, depth=depth)
    board.pop()
    moves.pop()

    return child_repertoire

# Main execution
if __name__ == "__main__":
    # Start from an empty chess board
    board = chess.Board()
    initial_moves = []

    # Set the depth for exploration
    depth = 5  # You can adjust this value

    # Build the repertoire
    repertoire = build_opening_repertoire(board, initial_moves, depth=depth)

    # Save repertoire to a PGN file without headers
    with open("opening_repertoire.pgn", "w") as file:
        for game in repertoire:
            exporter = chess.pgn.StringExporter(headers=False, variations=True, comments=False)
            file.write(game.accept(exporter) + "\n\n")

    print(f"Opening repertoire saved to 'opening_repertoire.pgn'")
    print(f"Total API requests made: {api_request_count}")
