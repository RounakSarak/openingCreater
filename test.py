import requests
import chess
import chess.pgn
from stockfish import Stockfish
import json

# Lichess opening explorer API URL
url = "https://explorer.lichess.ovh/masters"

# Global variables for tracking API requests and progress
api_request_count = 0
total_moves_explored = 0  # Total number of moves explored
initial_moves = []  # Initial moves to start the opening repertoire
requiredGames = 200000  # Minimum number of games required for a move to be considered

# Initialize Stockfish
stockfish = Stockfish(path="C:\\Apps\\stockfish\\stockfish-windows-x86-64-avx2.exe")
stockfish.update_engine_parameters({
    "Threads": 4,  # Number of CPU threads to use
    "Hash": 1024,  # Hash size in MB
    "Skill Level": 20  # Skill level (0-20, 20 being the strongest)
})

# Import the json data from the file
with open('requests.json', 'r') as file:
    requests_masters = json.load(file)

def get_my_moves(moves):
    stockfish.set_position(moves)
    best_move = stockfish.get_best_move()
    print(f"My move: {best_move}")
    return best_move

# Function to get opponent's moves from Lichess
def get_opponent_moves(moves):
    global api_request_count
    moves_str = ",".join(moves)  # Convert the list of moves to a comma-separated string
    params = {
        "play": moves_str,
        "topGames": 0,
        "recentGames": 0,
        "moves": 20  # Maximum moves to fetch
    }
    valid_moves = []
    if any(moves_str in entry for entry in requests_masters):
        for entry in requests_masters:
            if moves_str in entry:
                print('Using cached data')
                print(entry[moves_str])
                for move in entry[moves_str]:
                    if move[1] > requiredGames:
                        valid_moves.append(move[0])
                    print(valid_moves)
                    return valid_moves
    else:
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
            data = response.json()
            api_request_count += 1  # Increment API request counter
            moves_data = data.get('moves', [])
            toappend = []
            for move in moves_data:
                total_games = (move['white'] + move['draws'] + move['black'])
                if total_games > requiredGames:  # Filter moves based on popularity
                    valid_moves.append(move['uci'])
                toappend.append([move['uci'], total_games])
            
            # Save the data to the requests_masters list
            requests_masters.append({moves_str: toappend})
            print(f"Opponent moves for {moves}: {valid_moves}")
            return valid_moves
        except requests.RequestException as e:
            print(f"API error for {moves}: {e}")
            return []
        except KeyError as e:
            print(f"Missing data in Lichess response for {moves}: {e}")
            return []

# Recursive function to build the opening repertoire
def build_opening_repertoire(board, moves, repertoire=None):
    global total_moves_explored

    if repertoire is None:
        repertoire = []

    my_move = get_my_moves(moves)
    if not my_move or not board.is_legal(chess.Move.from_uci(my_move)):
        return repertoire

    # Play my's move
    board.push_uci(my_move)
    moves.append(my_move)
    total_moves_explored += 1  # Increment total moves explored
    print(f"Played my move: {my_move}")

    # Get opponent's common responses
    opponent_moves = get_opponent_moves(moves)
    if not opponent_moves:

        # Save the game to the repertoire
        game = chess.pgn.Game()
        node = game
        for move in board.move_stack:
            node = node.add_main_variation(move)
        repertoire.append(game)


        moves.pop()
        board.pop()


        return repertoire

    for opponent_move in opponent_moves:  
        if not board.is_legal(chess.Move.from_uci(opponent_move)):
            continue

        board.push_uci(opponent_move)
        moves.append(opponent_move)
        total_moves_explored += 1  # Increment total moves explored
        print(f"Played opponent move: {opponent_move}")

        # Recursively explore further moves
        build_opening_repertoire(board, moves, repertoire)

        # Backtrack moves
        moves.pop()
        board.pop()
        print(f"Backtracked opponent move: {opponent_move}")

    # Backtrack my's move
    moves.pop()
    board.pop()
    print(f"Backtracked my move: {my_move}")

    return repertoire

# Main execution
if __name__ == "__main__":
    # Start from an empty chess board
    board = chess.Board()
    
    for move in initial_moves:
        board.push_uci(move)
        total_moves_explored += 1

    # Initialize evalmultiplier based on the number of moves in initial_moves
    evalmultiplier = 1 if len(initial_moves) % 2 == 0 else -1

    # Build the repertoire
    repertoire = build_opening_repertoire(board, initial_moves)

    # Save repertoire to a PGN file without headers
    with open("opening_repertoire.pgn", "w") as file:
        for game in repertoire:
            exporter = chess.pgn.StringExporter(headers=False, variations=True, comments=False)
            file.write(game.accept(exporter) + "\n\n")


    # Save the requests_masters list to a json file
    print(requests_masters)
    with open('requests.json', 'w') as file:
        json.dump(requests_masters, file, indent=4)

    print(f"Opening repertoire saved to 'opening_repertoire.pgn'")
    print(f"Total API requests made: {api_request_count}")
    print(f"Total moves explored: {total_moves_explored}")
