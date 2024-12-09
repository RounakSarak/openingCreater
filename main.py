import requests
import chess
import chess.pgn
from stockfish import Stockfish
import json
import os
import logging

# Constants
REQUIRED_GAMES = 5000
INITIAL_MOVES = []
IAM = 1 # 1 for white, 0 for black
LOOGINGLEVEL = logging.DEBUG
LICHESS_API_URL = "https://explorer.lichess.ovh/masters"
CACHE_REQUESTS_FILE = "requests.json"
CACHE_STOCKFISH_FILE = "stockfish_cache.json"
CACHE_PGNS_FILE = "pgns_cache.json"
OUTPUT_FILE = "opening_repertoire.pgn"


# Global Variables
api_request_count = 0
total_moves_explored = 0
STOCKFISH_PATH = "C:\\Apps\\stockfish\\stockfish-windows-x86-64-avx2.exe"
# Configure logging
logging.basicConfig(level=LOOGINGLEVEL, format='%(levelname)s - %(message)s')

# Initialize Stockfish
stockfish = Stockfish(path=STOCKFISH_PATH)
stockfish.update_engine_parameters({
    "Threads": 4,
    "Hash": 1024,
    "Skill Level": 20
})
logging.info("Stockfish initialized.")

# Load cached Stockfish results
def load_cache(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            return json.load(file)
    return {}

stockfish_cache = load_cache(CACHE_STOCKFISH_FILE)
logging.info("Loaded Stockfish cache.")
requests_masters = load_cache(CACHE_REQUESTS_FILE)
logging.info("Loaded requests cache.")
pgn_cache = load_cache(CACHE_PGNS_FILE)
logging.info("Loaded PGNs cache.")

def save_cache(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

def get_best_stockfish_move(moves, board):
    moves_str = ",".join(moves)
    if moves_str in stockfish_cache:
        return stockfish_cache[moves_str]

    stockfish.set_fen_position(board.fen())
    best_move = stockfish.get_best_move()
    stockfish_cache[moves_str] = best_move
    return best_move

def fetch_opponent_moves(moves):
    global api_request_count
    moves_str = ",".join(moves)

    if moves_str in requests_masters:
        return [move[0] for move in requests_masters[moves_str] if move[1] >= REQUIRED_GAMES]

    try:
        response = requests.get(LICHESS_API_URL, params={"play": moves_str, "topGames": 0, "recentGames": 0, "moves": 20})
        response.raise_for_status()
        api_request_count += 1

        data = response.json()
        moves_data = data.get('moves', [])

        valid_moves = []
        cached_data = []
        for move in moves_data:
            total_games = move['white'] + move['draws'] + move['black']
            if total_games >= REQUIRED_GAMES:
                valid_moves.append(move['uci'])
            cached_data.append([move['uci'], total_games])
        
        requests_masters[moves_str] = valid_moves
        
        return valid_moves
    except requests.RequestException as e:
        logging.error(f"API request failed for {moves}: {e}")
    return []

def build_opening_repertoire(board, moves, repertoire=None, ismyturn=True):
    global total_moves_explored
    print(total_moves_explored)
    if repertoire is None:
        repertoire = []
    if ismyturn:
        my_move = get_best_stockfish_move(moves, board)
        if not my_move or not board.is_legal(chess.Move.from_uci(my_move)):
            logging.warning(f"Stockfish suggested an illegal or no move: {my_move}")
            return repertoire

        board.push_uci(my_move)
        moves.append(my_move)
        total_moves_explored += 1
    
    opponent_moves = fetch_opponent_moves(moves)
    if not opponent_moves:
        game = chess.pgn.Game()
        node = game
        for move in board.move_stack:
            node = node.add_main_variation(move)
        repertoire.append(game)
        board.pop()
        moves.pop()
        return repertoire

    for opponent_move in opponent_moves:
        if not board.is_legal(chess.Move.from_uci(opponent_move)):
            logging.warning(f"Opponent move is illegal: {opponent_move}")
            continue

        board.push_uci(opponent_move)
        moves.append(opponent_move)
        build_opening_repertoire(board, moves, repertoire)
        board.pop()
        moves.pop()
    if ismyturn:
        board.pop()
        moves.pop()
    return repertoire

if __name__ == "__main__":
    board = chess.Board()
    for move in INITIAL_MOVES:
        board.push_uci(move)
        total_moves_explored += 1
    
   

    if (total_moves_explored % 2) != IAM:
        ismyturn = True
    else:
        ismyturn = False

    move_str = ",".join(INITIAL_MOVES)
    toFind = move_str + str(IAM) + str(REQUIRED_GAMES)

    if toFind in pgn_cache:
        repertoire = pgn_cache[toFind]
        logging.info("Found cached PGNs")
        usedCache = True
        with open(OUTPUT_FILE, "w") as file:
            file.write(repertoire)

    else:
        logging.info("Building opening repertoire...")
        repertoire = build_opening_repertoire(board, INITIAL_MOVES, ismyturn=ismyturn)
        usedCache = False
        with open(OUTPUT_FILE, "w") as file:
            for game in repertoire:
                exporter = chess.pgn.StringExporter(headers=False, variations=True, comments=False)
                file.write(game.accept(exporter) + "\n\n")
        with open(OUTPUT_FILE, 'r') as file:
                pgn_data = file.read()
                pgn_cache[toFind] = pgn_data
                logging.info("PGNs details saved to cache.")
   
    save_cache(CACHE_REQUESTS_FILE, requests_masters)
    save_cache(CACHE_STOCKFISH_FILE, stockfish_cache)
    save_cache(CACHE_PGNS_FILE, pgn_cache)


    logging.info(f"Opening repertoire saved to '{OUTPUT_FILE}'.")
    logging.info(f"Total API requests made: {api_request_count}")
    logging.info(f"Total moves explored: {total_moves_explored}")
    logging.info("Done!")
