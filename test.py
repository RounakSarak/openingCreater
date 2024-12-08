import requests
import chess
import chess.pgn
from stockfish import Stockfish
import json
import os
import logging

# Lichess opening explorer API URL
url = "https://explorer.lichess.ovh/masters"

# Global variables for tracking API requests and progress
api_request_count = 0
total_moves_explored = 0  # Total number of moves explored
initial_moves = ['e2e4','e7e5']  # Initial moves to start the opening repertoire
iam = 1  # 1 for white, 0 for black
requiredGames = 10  # Minimum number of games required for a move to be considered



# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')

# Initialize Stockfish
stockfish = Stockfish(path="C:\\Apps\\stockfish\\stockfish-windows-x86-64-avx2.exe")
stockfish.update_engine_parameters({
    "Threads": 4,  # Number of CPU threads to use
    "Hash": 1024,  # Hash size in MB
    "Skill Level": 20  # Skill level (0-20, 20 being the strongest)
})
logging.info("Stockfish initialized.")

# Load the cached requests data from the file
if os.path.exists('requests.json'):
    with open('requests.json', 'r') as file:
        requests_masters = json.load(file)
    logging.info("Loaded cached Lichess API data.")
else:
    requests_masters = []
    logging.info("No cached Lichess API data found.")

# Load the cached Stockfish results from the file
if os.path.exists('stockfish_cache.json'):
    with open('stockfish_cache.json', 'r') as file:
        stockfish_cache = json.load(file)
    logging.info("Loaded cached Stockfish data.")
else:
    stockfish_cache = {}
    logging.info("No cached Stockfish data found.")

def get_my_moves(moves):
    moves_str = ",".join(moves)
    logging.debug(f"Fetching my move for: {moves_str}")
    if moves_str in stockfish_cache:
        logging.debug("Cache hit for Stockfish move.")
        best_move = stockfish_cache[moves_str]
    else:
        stockfish.set_fen_position(board.fen())
        best_move = stockfish.get_best_move()
        stockfish_cache[moves_str] = best_move
        logging.debug(f"Stockfish suggests move: {best_move}")
    return best_move

def get_opponent_moves(moves):
    global api_request_count
    moves_str = ",".join(moves)
    logging.debug(f"Fetching opponent moves for: {moves_str}")
    valid_moves = []
    if any(moves_str in entry for entry in requests_masters):
        logging.debug("Cache hit for Lichess API data.")
        for entry in requests_masters:
            if moves_str in entry:
                for move in entry[moves_str]:
                    if move[1] > requiredGames:
                        valid_moves.append(move[0])
                return valid_moves
    else:
        try:
            response = requests.get(url, params={"play": moves_str, "topGames": 0, "recentGames": 0, "moves": 20})
            response.raise_for_status()
            data = response.json()
            api_request_count += 1
            logging.debug(f"API request count: {api_request_count}")

            moves_data = data.get('moves', [])
            toappend = []
            for move in moves_data:
                total_games = (move['white'] + move['draws'] + move['black'])
                if total_games > requiredGames:
                    valid_moves.append(move['uci'])
                toappend.append([move['uci'], total_games])

            requests_masters.append({moves_str: toappend})
            return valid_moves
        except requests.RequestException as e:
            logging.error(f"API error for {moves}: {e}")
            return []
        except KeyError as e:
            logging.error(f"Missing data in Lichess response for {moves}: {e}")
            return []

def build_opening_repertoire(board, moves, repertoire=None):
    global total_moves_explored
    print('Total Moves Explored',total_moves_explored)
    if repertoire is None:
        repertoire = []

    logging.debug(f"Exploring moves: {moves}")
    my_move = get_my_moves(moves)
    if not my_move or not board.is_legal(chess.Move.from_uci(my_move)):
        logging.warning(f"Stockfish suggested an illegal move: {my_move}")
        breakpoint()
        return repertoire

    board.push_uci(my_move)
    moves.append(my_move)
    total_moves_explored += 1
    logging.debug(f"Pushed move: {my_move}, total moves explored: {total_moves_explored}")

    opponent_moves = get_opponent_moves(moves)
    if not opponent_moves:
        logging.info("No valid opponent moves found, saving the game.")
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
            logging.warning(f"Opponent suggested an illegal move: {opponent_move}")
            continue

        board.push_uci(opponent_move)
        moves.append(opponent_move)
        total_moves_explored += 1

        build_opening_repertoire(board, moves, repertoire)

        moves.pop()
        board.pop()

    moves.pop()
    board.pop()
    return repertoire

if __name__ == "__main__":
    board = chess.Board()
    for move in initial_moves:
        board.push_uci(move)
        total_moves_explored += 1
    
    repertoire = build_opening_repertoire(board, initial_moves)

    with open("opening_repertoire.pgn", "w") as file:
        for game in repertoire:
            exporter = chess.pgn.StringExporter(headers=False, variations=True, comments=False)
            file.write(game.accept(exporter) + "\n\n")

    with open('requests.json', 'w') as file:
        json.dump(requests_masters, file, indent=4)

    with open('stockfish_cache.json', 'w') as file:
        json.dump(stockfish_cache, file, indent=4)

    logging.info("Opening repertoire saved to 'opening_repertoire.pgn'")
    logging.info(f"Total API requests made: {api_request_count}")
    logging.info(f"Total moves explored: {total_moves_explored}")