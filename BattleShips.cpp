#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <set>

using namespace std;

// BattleShips Puzzle Solver
// Input format:
// Line 1: K (max ship length, typically 4)
// Line 2: -1 followed by n column targets
// Lines 3..n+2: row_target followed by n cells
// Cell values: -1=unknown, 0=water, 1=ship_part, 2-6=ship_length_hints

struct Puzzle {
    int n;      // board size
    int K;      // max ship length
    vector<int> row_targets;
    vector<int> col_targets;
    vector<vector<int>> board;
    
    void read() {
        cin >> K;
        
        // Read first line: -1 and column targets
        int dummy;
        cin >> dummy; // -1
        row_targets.clear();
        col_targets.clear();
        board.clear();
        
        // Read column targets
        string line;
        getline(cin, line); // consume rest of line
        getline(cin, line);
        istringstream iss(line);
        int val;
        while (iss >> val) {
            col_targets.push_back(val);
        }
        n = col_targets.size();
        
        // Read n rows
        for (int i = 0; i < n; i++) {
            int rt;
            cin >> rt;
            row_targets.push_back(rt);
            
            vector<int> row;
            for (int j = 0; j < n; j++) {
                int cell;
                cin >> cell;
                row.push_back(cell);
            }
            board.push_back(row);
        }
    }
};

struct Solver {
    Puzzle puzzle;
    vector<vector<vector<int>>> solutions;
    
    void solve() {
        vector<vector<int>> current = puzzle.board;
        search(current, 0);
    }
    
    bool isValid(const vector<vector<int>>& board, int r, int c) {
        return r >= 0 && r < puzzle.n && c >= 0 && c < puzzle.n;
    }
    
    bool checkConstraints(const vector<vector<int>>& board) {
        // Check row/column counts
        for (int r = 0; r < puzzle.n; r++) {
            int count = 0;
            for (int c = 0; c < puzzle.n; c++) {
                if (board[r][c] == 1) count++;
            }
            if (count != puzzle.row_targets[r]) return false;
        }
        
        for (int c = 0; c < puzzle.n; c++) {
            int count = 0;
            for (int r = 0; r < puzzle.n; r++) {
                if (board[r][c] == 1) count++;
            }
            if (count != puzzle.col_targets[c]) return false;
        }
        
        // Check no diagonal adjacency of ships
        for (int r = 0; r < puzzle.n; r++) {
            for (int c = 0; c < puzzle.n; c++) {
                if (board[r][c] == 1) {
                    // Check all 4 diagonals
                    int dr[] = {-1, -1, 1, 1};
                    int dc[] = {-1, 1, -1, 1};
                    for (int d = 0; d < 4; d++) {
                        int nr = r + dr[d];
                        int nc = c + dc[d];
                        if (isValid(board, nr, nc) && board[nr][nc] == 1) {
                            return false;
                        }
                    }
                }
            }
        }
        
        // Verify ship lengths
        vector<int> ships;
        vector<vector<bool>> visited(puzzle.n, vector<bool>(puzzle.n, false));
        
        for (int r = 0; r < puzzle.n; r++) {
            for (int c = 0; c < puzzle.n; c++) {
                if (board[r][c] == 1 && !visited[r][c]) {
                    int len = 0;
                    bool horizontal = false, vertical = false;
                    
                    // Try horizontal
                    int cc = c;
                    while (cc < puzzle.n && board[r][cc] == 1) {
                        visited[r][cc] = true;
                        len++;
                        cc++;
                    }
                    
                    if (len > 1) {
                        horizontal = true;
                    } else {
                        // Try vertical
                        visited[r][c] = false;
                        len = 0;
                        int rr = r;
                        while (rr < puzzle.n && board[rr][c] == 1) {
                            visited[rr][c] = true;
                            len++;
                            rr++;
                        }
                        if (len > 1) vertical = true;
                    }
                    
                    if (len > puzzle.K) return false;
                    ships.push_back(len);
                }
            }
        }
        
        return true;
    }
    
    void search(vector<vector<int>>& board, int pos) {
        if (pos == puzzle.n * puzzle.n) {
            if (checkConstraints(board)) {
                solutions.push_back(board);
            }
            return;
        }
        
        int r = pos / puzzle.n;
        int c = pos % puzzle.n;
        
        // If cell is already determined (not -1), skip it
        if (puzzle.board[r][c] != -1) {
            board[r][c] = puzzle.board[r][c];
            search(board, pos + 1);
            return;
        }
        
        // Try water (0)
        board[r][c] = 0;
        if (isPossible(board, r, c)) {
            search(board, pos + 1);
        }
        
        // Try ship (1)
        board[r][c] = 1;
        if (isPossible(board, r, c)) {
            search(board, pos + 1);
        }
        
        board[r][c] = -1;
    }
    
    bool isPossible(const vector<vector<int>>& board, int r, int c) {
        // Quick pruning checks
        
        // Check diagonal constraint
        if (board[r][c] == 1) {
            int dr[] = {-1, -1, 1, 1};
            int dc[] = {-1, 1, -1, 1};
            for (int d = 0; d < 4; d++) {
                int nr = r + dr[d];
                int nc = c + dc[d];
                if (isValid(board, nr, nc) && board[nr][nc] == 1) {
                    return false;
                }
            }
        }
        
        // Check row doesn't exceed target
        int rowCount = 0;
        for (int cc = 0; cc < puzzle.n; cc++) {
            if (board[r][cc] == 1) rowCount++;
        }
        if (rowCount > puzzle.row_targets[r]) return false;
        
        // Check column doesn't exceed target
        int colCount = 0;
        for (int rr = 0; rr < puzzle.n; rr++) {
            if (board[rr][c] == 1) colCount++;
        }
        if (colCount > puzzle.col_targets[c]) return false;
        
        return true;
    }
    
    void printSolutions() {
        cout << "SOLUTIONS: " << solutions.size() << endl;
        for (size_t s = 0; s < solutions.size(); s++) {
            cout << "--- Solution " << (s + 1) << " ---" << endl;
            for (int r = 0; r < puzzle.n; r++) {
                for (int c = 0; c < puzzle.n; c++) {
                    cout << solutions[s][r][c];
                    if (c < puzzle.n - 1) cout << " ";
                }
                cout << endl;
            }
        }
    }
};

int main() {
    Puzzle puzzle;
    puzzle.read();
    
    Solver solver;
    solver.puzzle = puzzle;
    solver.solve();
    solver.printSolutions();
    
    return 0;
}
