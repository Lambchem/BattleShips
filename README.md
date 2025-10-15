# BattleShips
C++ BattleShips Puzzle Engine and Python UI, easy to use.

## Overview

This project provides a complete BattleShips puzzle solver with:
- **BattleShips.cpp**: A fast C++ constraint-based solver engine
- **BattleShipsUI.py**: An intuitive Python Tkinter GUI for puzzle editing and solving

## Features

- Interactive puzzle editor with visual grid interface
- Compile C++ solver directly from the UI
- Support for custom board sizes (2-20)
- Multiple solution navigation
- Import/export puzzle configurations
- Real-time constraint visualization

## Requirements

### For the C++ Solver
- g++ compiler with C++17 support
- Standard C++ library

### For the Python UI
- Python 3.6 or higher
- tkinter (usually included with Python)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Lambchem/BattleShips.git
cd BattleShips
```

2. Compile the C++ solver:
```bash
g++ -std=c++17 -O2 -o battleship_solver BattleShips.cpp
```

Or use the "编译引擎" button in the UI to compile it interactively.

## Usage

### Using the Python UI (Recommended)

Run the UI application:
```bash
python3 BattleShipsUI.py
```

#### UI Controls:
- **Left Click on cell**: Toggle between unknown (?) and water (~)
- **Right Click on cell**: Cycle through ship length hints (0→2→3→4→5→6→-1)
- **Row/Column entries**: Set target number of ship cells per row/column
- **求解 (Solve)**: Run the solver with current configuration
- **导入引擎文本 (Import)**: Load puzzle from text format
- **查看引擎输入/输出 (View Input/Output)**: Debug solver communication

### Using the C++ Solver Directly

The solver reads from stdin and writes to stdout.

**Input Format:**
```
K                          # Maximum ship length (e.g., 4)
-1 c1 c2 ... cn           # Column targets
r1 v11 v12 ... v1n        # Row 1: target + cells
r2 v21 v22 ... v2n        # Row 2: target + cells
...
rn vn1 vn2 ... vnn        # Row n: target + cells
```

**Cell Values:**
- `-1`: Unknown (to be determined by solver)
- `0`: Water (fixed)
- `1`: Ship part (fixed)
- `2-6`: Ship length hint (for specific ship sizes)

**Output Format:**
```
SOLUTIONS: <count>
--- Solution 1 ---
0 1 0 0 1
0 1 0 0 1
...
--- Solution 2 ---
...
```

**Example:**
```bash
# example_easy.txt contains a 4x4 puzzle with two single-cell ships
cat example_easy.txt | ./battleship_solver
```

This will output:
```
SOLUTIONS: 2
--- Solution 1 ---
0 0 1 0
1 0 0 0
0 0 0 0
0 0 0 0
--- Solution 2 ---
1 0 0 0
0 0 1 0
0 0 0 0
0 0 0 0
```

## Puzzle Rules

BattleShips is a logic puzzle where you must place ships on a grid according to constraints:

1. Numbers outside the grid indicate how many ship cells are in that row/column
2. Ships are rectangular (1xN or Nx1)
3. Ships cannot touch each other, even diagonally
4. Maximum ship length is K (typically 4)

## Creating Valid Puzzles

When creating puzzles, keep in mind:
- The sum of all row targets must equal the sum of all column targets (total ship cells)
- With the diagonal constraint, placing ships can be challenging
- Start with simple configurations (single-cell ships separated by empty rows/columns)
- Use the UI to experiment and visualize placements

**Example Valid Puzzle (4x4 with two single ships):**
```
K=2, Row targets=[1,1,0,0], Column targets=[1,0,1,0]
Valid solutions exist at positions (0,0)+(1,2) or (0,2)+(1,0)
```

## Development

### Provided Examples

The repository includes example puzzle files to help you get started:

1. **example_easy.txt** - Simple 4x4 puzzle with two single-cell ships
   - K=2, Row targets=[1,1,0,0], Column targets=[1,0,1,0]
   - Has 2 solutions
   
2. **example_ships.txt** - 6x6 puzzle with multiple single-cell ships
   - K=4, Row targets=[2,0,2,0,2,0], Column targets=[2,0,2,0,2,0]
   - Has 6 solutions demonstrating various valid placements

Try them with:
```bash
./battleship_solver < example_easy.txt
./battleship_solver < example_ships.txt
```

### Project Structure
```
BattleShips/
├── BattleShips.cpp      # C++ solver engine
├── BattleShipsUI.py     # Python GUI
├── example_easy.txt     # Simple 4x4 example puzzle
├── example_ships.txt    # 6x6 example with multiple ships
├── README.md            # This file
├── LICENSE              # GPL-3.0 License
└── .gitignore           # Git ignore rules
```

### Building and Testing

```bash
# Compile the solver
g++ -std=c++17 -O2 -o battleship_solver BattleShips.cpp

# Run tests with examples
./battleship_solver < example_easy.txt
./battleship_solver < example_ships.txt

# Test the Python UI (requires tkinter)
python3 BattleShipsUI.py
```

### Contributing

Contributions are welcome! Please ensure:
- C++ code compiles with g++ -std=c++17
- Python code follows PEP 8 style guidelines
- Test your changes with various puzzle configurations

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Author

Created by Lambchem

## Acknowledgments

This solver uses constraint propagation and backtracking search to efficiently find all valid solutions to BattleShips puzzles.
