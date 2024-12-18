# Opening Repertoire Generator

This project generates an opening repertoire for both white and black sides in chess using Stockfish and Lichess API. The generated repertoire is saved in PGN format.

## Features

- Uses Stockfish to determine the best moves for the given position.
- Fetches common opponent responses from the Lichess Masters database.
- Caches results to minimize API requests and improve performance.
- Saves the generated opening repertoire in PGN format.

## Requirements

- Python 3.x
- Stockfish chess engine
- Required Python packages: `requests`, `python-chess`, `stockfish`

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/opening-repertoire-generator.git
    cd opening-repertoire-generator
    ```

2. Install the required Python packages:
    ```sh
    pip install requests python-chess stockfish
    ```

3. Download and install Stockfish:
    - Download the Stockfish binary from the [official website](https://stockfishchess.org/download/).
    - Update the `STOCKFISH_PATH` variable in `main.py` with the path to the Stockfish binary.

## Usage

1. Configure the initial settings in `main.py`:
    - `REQUIRED_GAMES`: Minimum number of games required for a move to be considered.
    - `INITIAL_MOVES`: List of initial moves in UCI format.
    - `IAM`: Set to `1` for white and `0` for black.
    - `LOOGINGLEVEL`: Logging level (e.g., `logging.DEBUG`).

2. Run the script:
    ```sh
    python main.py
    ```

3. The generated opening repertoire will be saved in `opening_repertoire.pgn`.

## Caching

The program uses caching to store results and minimize API requests:
- `requests.json`: Cache for opponent moves fetched from Lichess API.
- `stockfish_cache.json`: Cache for Stockfish best moves.
- `pgns_cache.json`: Cache for generated PGNs.

## Logging

The program logs various events and information to the console, including:
- Initialization of Stockfish.
- Loading of caches.
- Building of the opening repertoire.
- Saving of the opening repertoire and caches.
- Total API requests made and moves explored.

## License
This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
