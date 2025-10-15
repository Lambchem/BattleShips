#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <set>
#include <map>
#include <stack>
#include <optional>
#include <tuple>
#include <algorithm>
#include <stdexcept>

// Coord type
using Coord = std::pair<int, int>;

// Helper functions
std::vector<int> _parse_ints(const std::string& line) {
    std::vector<int> parts;
    std::string token;

    for (char ch : line) {
        if (ch == ' ' || ch == '\t' || ch == ',' || ch == ';') {
            if (!token.empty()) {
                try {
                    parts.push_back(std::stoi(token));
                    token.clear();
                }
                catch (const std::exception& e) {
                    throw std::runtime_error("无法解析为整数: " + line);
                }
            }
        }
        else {
            token += ch;
        }
    }

    if (!token.empty()) {
        try {
            parts.push_back(std::stoi(token));
        }
        catch (const std::exception& e) {
            throw std::runtime_error("无法解析为整数: " + line);
        }
    }

    return parts;
}

std::pair<int, std::vector<std::vector<int>>> parse_input() {
    std::string line;
    int K;

    // Read K
    if (!std::getline(std::cin, line)) {
        throw std::runtime_error("第一行必须是整数 K");
    }
    try {
        K = std::stoi(line);
    }
    catch (...) {
        throw std::runtime_error("第一行必须是整数 K");
    }

    // Read first row of matrix
    if (!std::getline(std::cin, line)) {
        throw std::runtime_error("读取矩阵首行失败");
    }
    std::vector<int> first_row;
    try {
        first_row = _parse_ints(line);
    }
    catch (std::exception& e) {
        throw std::runtime_error("读取矩阵首行失败: " + std::string(e.what()));
    }

    int m = (int)first_row.size();
    if (m < 2) {
        throw std::runtime_error("矩阵首行长度不足，应为 (n+1) 个数");
    }

    std::vector<std::vector<int>> grid = { first_row };

    for (int i = 0; i < m - 1; ++i) {
        if (!std::getline(std::cin, line)) {
            throw std::runtime_error("矩阵行数不足，期望 " + std::to_string(m) + " 行（含首行）");
        }
        try {
            std::vector<int> row = _parse_ints(line);
            grid.push_back(row);
        }
        catch (std::exception& e) {
            throw std::runtime_error("读取矩阵第" + std::to_string(i + 2) + "行失败: " + std::string(e.what()));
        }
    }

    for (const auto& row : grid) {
        if ((int)row.size() != m) {
            throw std::runtime_error("矩阵应为方阵 (n+1)×(n+1)");
        }
    }

    if (grid[0][0] != -1) {
        throw std::runtime_error("矩阵左上角(0,0)应为-1");
    }

    return { K, grid };
}

class BattleshipDirectionalSolver {
public:
    BattleshipDirectionalSolver(int K, const std::vector<std::vector<int>>& matrix) : K(K), M(matrix) {
        n = (int)matrix.size() - 1;

        // Initialize row_target and col_target
        for (int i = 0; i < n; ++i) {
            row_target.push_back(_nonneg(matrix[i + 1][0]));
            col_target.push_back(_nonneg(matrix[0][i + 1]));
        }

        // Initialize board and dir_hint
        board.assign(n, std::vector<int>(n, -1));
        dir_hint.assign(n, std::vector<std::optional<char>>(n, std::nullopt));
        // Hints: 'U','D','L','R' 与新增 'S' (solo, 上下左右皆水)

        for (int r = 0; r < n; ++r) {
            for (int c = 0; c < n; ++c) {
                int v = matrix[r + 1][c + 1];
                if (v >= -1 && v <= 6) {
                    if (v == 1) {
                        board[r][c] = 1;
                    }
                    else if (v == 0) {
                        board[r][c] = 0;
                    }
                    else if (v == -1) {
                        board[r][c] = -1;
                    }
                    else if (v == 2) {
                        board[r][c] = 0;
                        dir_hint[r][c] = 'U';
                    }
                    else if (v == 3) {
                        board[r][c] = 0;
                        dir_hint[r][c] = 'D';
                    }
                    else if (v == 4) {
                        board[r][c] = 0;
                        dir_hint[r][c] = 'L';
                    }
                    else if (v == 5) {
                        board[r][c] = 0;
                        dir_hint[r][c] = 'R';
                    }
                    else if (v == 6) {
                        board[r][c] = 0;
                        dir_hint[r][c] = 'S'; // 新增：独立单格舰，四邻皆水
                    }
                }
                else {
                    throw std::runtime_error("内部格子仅允许 -1/0/1/2/3/4/5/6");
                }
            }
        }

        // Initialize counters
        row_zero.assign(n, 0);
        row_unknown.assign(n, 0);
        col_zero.assign(n, 0);
        col_unknown.assign(n, 0);

        for (int r = 0; r < n; ++r) {
            for (int c = 0; c < n; ++c) {
                int v = board[r][c];
                if (v == 0) {
                    row_zero[r]++;
                    col_zero[c]++;
                }
                else if (v == -1) {
                    row_unknown[r]++;
                    col_unknown[c]++;
                }
            }
        }

        // Basic validity checks
        for (int i = 0; i < n; ++i) {
            if (!(0 <= row_target[i] && row_target[i] <= n)) {
                throw std::runtime_error("第" + std::to_string(i + 1) + "行提示无效: " + std::to_string(row_target[i]));
            }
            if (!(0 <= col_target[i] && col_target[i] <= n)) {
                throw std::runtime_error("第" + std::to_string(i + 1) + "列提示无效: " + std::to_string(col_target[i]));
            }
            if (row_zero[i] > row_target[i]) {
                throw std::runtime_error("第" + std::to_string(i + 1) + "行已知战船数超出行提示");
            }
            if (col_zero[i] > col_target[i]) {
                throw std::runtime_error("第" + std::to_string(i + 1) + "列已知战船数超出列提示");
            }
        }

        // Expected fleet
        expected_fleet = _expected_fleet(K);
        int total_target_cells = 0;
        for (int t : row_target) total_target_cells += t;

        int expected_cells = 0;
        if (!expected_fleet.empty()) {
            for (const auto& kv : expected_fleet) {
                expected_cells += kv.first * kv.second;
            }
        }

        // 始终启用舰队构成校验（不再依赖 expected_cells 与行列总和是否一致）
        enforce_fleet = !expected_fleet.empty();

        // Initial diagonal check
        for (int r = 0; r < n; ++r) {
            for (int c = 0; c < n; ++c) {
                if (board[r][c] == 0 && _has_diag_zero(r, c)) {
                    throw std::runtime_error("初始矩阵违反对角相邻规则于(" + std::to_string(r + 1) + "," + std::to_string(c + 1) + ")");
                }
            }
        }
    }

    int mark() { return (int)trail.size(); }

    void undo(int mk) {
        while ((int)trail.size() > mk) {
            auto [r, c, prev, d_r0, d_ru, d_c0, d_cu] = trail.back();
            trail.pop_back();

            if (d_r0) row_zero[r] -= d_r0;
            row_unknown[r] -= d_ru;
            if (d_c0) col_zero[c] -= d_c0;
            col_unknown[c] -= d_cu;

            board[r][c] = prev;
        }
    }

    bool assign(int r, int c, int val) {
        int cur = board[r][c];
        if (cur == val) return true;
        if (cur != -1) return false;

        // Capacity constraints
        if (val == 0) {
            if (row_zero[r] + 1 > row_target[r]) return false;
            if (col_zero[c] + 1 > col_target[c]) return false;
            // Diagonal prohibition
            for (const auto& nb : neighbors_diag(r, c)) {
                if (board[nb.first][nb.second] == 0) return false;
            }
        }
        else {
            if (row_zero[r] + (row_unknown[r] - 1) < row_target[r]) return false;
            if (col_zero[c] + (col_unknown[c] - 1) < col_target[c]) return false;
        }

        int mk = mark();
        _apply_set(r, c, val);

        // If set to 0, check straight line local validity
        if (val == 0) {
            if (!_check_straight_local(r, c)) {
                undo(mk);
                return false;
            }
            for (const auto& nb : neighbors4(r, c)) {
                int rr = nb.first, cc = nb.second;
                if (board[rr][cc] == 0 && !_check_straight_local(rr, cc)) {
                    undo(mk);
                    return false;
                }
            }
        }
        return true;
    }

    bool propagate() {
        bool changed = true;
        while (changed) {
            changed = false;

            // Row constraints
            for (int r = 0; r < n; ++r) {
                int need = row_target[r] - row_zero[r];
                int rem = row_unknown[r];
                if (need < 0 || need > rem) return false;

                if (rem > 0) {
                    if (need == 0) {
                        for (int c = 0; c < n; ++c) {
                            if (board[r][c] == -1) {
                                if (!assign(r, c, 1)) return false;
                                changed = true;
                            }
                        }
                    }
                    else if (need == rem) {
                        for (int c = 0; c < n; ++c) {
                            if (board[r][c] == -1) {
                                if (!assign(r, c, 0)) return false;
                                changed = true;
                            }
                        }
                    }
                }
            }

            // Column constraints
            for (int c = 0; c < n; ++c) {
                int need = col_target[c] - col_zero[c];
                int rem = col_unknown[c];
                if (need < 0 || need > rem) return false;

                if (rem > 0) {
                    if (need == 0) {
                        for (int r = 0; r < n; ++r) {
                            if (board[r][c] == -1) {
                                if (!assign(r, c, 1)) return false;
                                changed = true;
                            }
                        }
                    }
                    else if (need == rem) {
                        for (int r = 0; r < n; ++r) {
                            if (board[r][c] == -1) {
                                if (!assign(r, c, 0)) return false;
                                changed = true;
                            }
                        }
                    }
                }
            }

            // Diagonal prohibition: unknown with diagonal 0 -> set to 1
            for (int r = 0; r < n; ++r) {
                for (int c = 0; c < n; ++c) {
                    if (board[r][c] == -1) {
                        for (const auto& nb : neighbors_diag(r, c)) {
                            if (board[nb.first][nb.second] == 0) {
                                if (!assign(r, c, 1)) return false;
                                changed = true;
                                break;
                            }
                        }
                    }
                }
            }

            // Directional cell enforcement (includes new 'S')
            for (int r = 0; r < n; ++r) {
                for (int c = 0; c < n; ++c) {
                    if (dir_hint[r][c].has_value()) {
                        int mk = mark();
                        if (!_enforce_directional_cell(r, c)) {
                            undo(mk);
                            return false;
                        }
                        if ((int)trail.size() > mk) changed = true;
                    }
                }
            }

            // Local straight line validity
            for (int r = 0; r < n; ++r) {
                for (int c = 0; c < n; ++c) {
                    if (board[r][c] == 0 && !_check_straight_local(r, c)) return false;
                }
            }

            // Pruning
            for (int r = 0; r < n; ++r) {
                if (row_zero[r] > row_target[r]) return false;
                if (row_zero[r] + row_unknown[r] < row_target[r]) return false;
            }
            for (int c = 0; c < n; ++c) {
                if (col_zero[c] > col_target[c]) return false;
                if (col_zero[c] + col_unknown[c] < col_target[c]) return false;
            }
        }
        return true;
    }

    std::optional<Coord> choose_var() {
        std::optional<Coord> best_rc;
        std::optional<std::pair<int, int>> best_key;

        for (int r = 0; r < n; ++r) {
            for (int c = 0; c < n; ++c) {
                if (board[r][c] != -1) continue;

                std::vector<int> domain;
                if (_can_be(r, c, 0)) domain.push_back(0);
                if (_can_be(r, c, 1)) domain.push_back(1);

                if (domain.empty()) return std::make_pair(r, c);

                int heuristic = row_unknown[r] + col_unknown[c];
                std::pair<int, int> key = { (int)domain.size(), heuristic };
                if (!best_key.has_value() || key < best_key.value()) {
                    best_key = key;
                    best_rc = std::make_pair(r, c);
                }
            }
        }
        return best_rc;
    }

    bool is_complete() {
        for (int r = 0; r < n; ++r)
            for (int c = 0; c < n; ++c)
                if (board[r][c] == -1) return false;
        return true;
    }

    void enumerate_all(std::vector<std::vector<std::vector<int>>>& solutions, std::optional<int> limit = std::nullopt) {
        if (limit.has_value() && solutions.size() >= (size_t)limit.value()) return;

        int mk0 = mark();
        if (!propagate()) {
            undo(mk0);
            return;
        }

        if (is_complete()) {
            if (_final_check()) {
                std::vector<std::vector<int>> sol(n, std::vector<int>(n));
                for (int r = 0; r < n; ++r)
                    for (int c = 0; c < n; ++c)
                        sol[r][c] = board[r][c];
                solutions.push_back(sol);
            }
            undo(mk0);
            return;
        }

        auto rc = choose_var();
        if (!rc.has_value()) {
            if (_final_check()) {
                std::vector<std::vector<int>> sol(n, std::vector<int>(n));
                for (int r = 0; r < n; ++r)
                    for (int c = 0; c < n; ++c)
                        sol[r][c] = board[r][c];
                solutions.push_back(sol);
            }
            undo(mk0);
            return;
        }

        int r = rc->first, c = rc->second;
        for (int val : {0, 1}) {
            if (limit.has_value() && solutions.size() >= (size_t)limit.value()) break;
            if (!_can_be(r, c, val)) continue;

            int mk1 = mark();
            if (assign(r, c, val)) {
                enumerate_all(solutions, limit);
            }
            undo(mk1);
        }

        undo(mk0);
    }

    int getN() const { return n; }

private:
    int K;
    std::vector<std::vector<int>> M;
    int n;
    std::vector<int> row_target;
    std::vector<int> col_target;
    std::vector<std::vector<int>> board; // -1 unknown, 0 ship, 1 water
    std::vector<std::vector<std::optional<char>>> dir_hint; // U,D,L,R,S
    std::vector<int> row_zero, row_unknown, col_zero, col_unknown;
    std::vector<std::tuple<int, int, int, int, int, int, int>> trail; // r,c,prev, d_r0,d_ru,d_c0,d_cu
    std::map<int, int> expected_fleet;
    bool enforce_fleet = false;

    int _nonneg(int x) {
        if (x < 0) throw std::runtime_error("行/列提示必须为非负整数");
        return x;
    }

    std::vector<Coord> neighbors4(int r, int c) {
        std::vector<Coord> res;
        if (r > 0) res.push_back({ r - 1, c });
        if (r + 1 < n) res.push_back({ r + 1, c });
        if (c > 0) res.push_back({ r, c - 1 });
        if (c + 1 < n) res.push_back({ r, c + 1 });
        return res;
    }

    std::vector<Coord> neighbors_diag(int r, int c) {
        std::vector<Coord> res;
        if (r > 0 && c > 0) res.push_back({ r - 1, c - 1 });
        if (r > 0 && c + 1 < n) res.push_back({ r - 1, c + 1 });
        if (r + 1 < n && c > 0) res.push_back({ r + 1, c - 1 });
        if (r + 1 < n && c + 1 < n) res.push_back({ r + 1, c + 1 });
        return res;
    }

    bool _has_diag_zero(int r, int c) {
        for (const auto& nb : neighbors_diag(r, c)) {
            if (board[nb.first][nb.second] == 0) return true;
        }
        return false;
    }

    void _apply_set(int r, int c, int val) {
        int prev = board[r][c];
        int d_r0 = (val == 0) ? 1 : 0;
        int d_c0 = (val == 0) ? 1 : 0;
        int d_ru = (prev == -1) ? -1 : 0;
        int d_cu = (prev == -1) ? -1 : 0;

        trail.emplace_back(r, c, prev, d_r0, d_ru, d_c0, d_cu);
        board[r][c] = val;

        if (d_r0) row_zero[r] += d_r0;
        if (d_c0) col_zero[c] += d_c0;
        if (d_ru) row_unknown[r] += d_ru;
        if (d_cu) col_unknown[c] += d_cu;
    }

    bool _check_straight_local(int r, int c) {
        if (board[r][c] != 0) return true;

        int horiz = 0;
        if (c > 0 && board[r][c - 1] == 0) horiz++;
        if (c + 1 < n && board[r][c + 1] == 0) horiz++;

        int vert = 0;
        if (r > 0 && board[r - 1][c] == 0) vert++;
        if (r + 1 < n && board[r + 1][c] == 0) vert++;

        // No bending or T-shapes
        if (horiz > 0 && vert > 0) return false;
        if (horiz > 2 || vert > 2) return false;
        return true;
    }

    bool _enforce_directional_cell(int r, int c) {
        if (!dir_hint[r][c].has_value()) return true;

        char d = dir_hint[r][c].value();

        // Ensure self is ship (0)
        if (board[r][c] == 1) return false;
        if (board[r][c] == -1) {
            if (!assign(r, c, 0)) return false;
        }

        // Define expectations
        std::optional<Coord> need; // required neighbor that must be ship
        std::vector<Coord> forbid; // neighbors that must be water

        if (d == 'U') {
            if (r == 0) return false;
            need = std::make_pair(r - 1, c);
            if (r + 1 < n) forbid.push_back({ r + 1, c });
            if (c > 0) forbid.push_back({ r, c - 1 });
            if (c + 1 < n) forbid.push_back({ r, c + 1 });
        }
        else if (d == 'D') {
            if (r + 1 == n) return false;
            need = std::make_pair(r + 1, c);
            if (r > 0) forbid.push_back({ r - 1, c });
            if (c > 0) forbid.push_back({ r, c - 1 });
            if (c + 1 < n) forbid.push_back({ r, c + 1 });
        }
        else if (d == 'L') {
            if (c == 0) return false;
            need = std::make_pair(r, c - 1);
            if (c + 1 < n) forbid.push_back({ r, c + 1 });
            if (r > 0) forbid.push_back({ r - 1, c });
            if (r + 1 < n) forbid.push_back({ r + 1, c });
        }
        else if (d == 'R') {
            if (c + 1 == n) return false;
            need = std::make_pair(r, c + 1);
            if (c > 0) forbid.push_back({ r, c - 1 });
            if (r > 0) forbid.push_back({ r - 1, c });
            if (r + 1 < n) forbid.push_back({ r + 1, c });
        }
        else if (d == 'S') {
            // 独立单格：四邻皆水，无 need
            if (r > 0) forbid.push_back({ r - 1, c });
            if (r + 1 < n) forbid.push_back({ r + 1, c });
            if (c > 0) forbid.push_back({ r, c - 1 });
            if (c + 1 < n) forbid.push_back({ r, c + 1 });
        }

        // Enforce required neighbor if any
        if (need.has_value()) {
            int nr = need->first;
            int nc = need->second;
            if (board[nr][nc] == 1) return false;
            if (board[nr][nc] == -1) {
                if (!assign(nr, nc, 0)) return false;
            }
        }

        // Other adjacencies must be water
        for (const auto& frfc : forbid) {
            int fr = frfc.first, fc = frfc.second;
            if (board[fr][fc] == 0) return false;
            if (board[fr][fc] == -1) {
                if (!assign(fr, fc, 1)) return false;
            }
        }

        return true;
    }

    bool _can_be(int r, int c, int val) {
        if (board[r][c] != -1) return board[r][c] == val;

        if (val == 0) {
            if (row_zero[r] + 1 > row_target[r]) return false;
            if (col_zero[c] + 1 > col_target[c]) return false;

            // Diagonal prohibition
            for (const auto& nb : neighbors_diag(r, c)) {
                if (board[nb.first][nb.second] == 0) return false;
            }

            // Local straight line check
            int horiz = 0;
            if (c > 0 && board[r][c - 1] == 0) horiz++;
            if (c + 1 < n && board[r][c + 1] == 0) horiz++;

            int vert = 0;
            if (r > 0 && board[r - 1][c] == 0) vert++;
            if (r + 1 < n && board[r + 1][c] == 0) vert++;

            if (horiz > 0 && vert > 0) return false;
            if (horiz > 2 || vert > 2) return false;
            return true;
        }
        else {
            if (row_zero[r] + (row_unknown[r] - 1) < row_target[r]) return false;
            if (col_zero[c] + (col_unknown[c] - 1) < col_target[c]) return false;
            return true;
        }
    }

    bool _final_check() {
        // Row and column counts
        for (int r = 0; r < n; ++r) if (row_zero[r] != row_target[r]) return false;
        for (int c = 0; c < n; ++c) if (col_zero[c] != col_target[c]) return false;

        // Diagonal non-adjacency
        for (int r = 0; r < n; ++r)
            for (int c = 0; c < n; ++c)
                if (board[r][c] == 0 && _has_diag_zero(r, c)) return false;

        // Component linearity and continuity
        auto compsOpt = _collect_components();
        if (!compsOpt.has_value()) return false;

        // Direction consistency (re-validate hints)
        for (int r = 0; r < n; ++r)
            for (int c = 0; c < n; ++c)
                if (dir_hint[r][c].has_value())
                    if (!_enforce_directional_cell(r, c)) return false;

        // Fleet matching（严格匹配）
        if (enforce_fleet) {
            std::map<int, int> got;
            for (const auto& comp : compsOpt.value()) {
                int L = (int)comp.size();
                got[L] = got.count(L) ? got[L] + 1 : 1;
            }
            // 禁止出现未在期望中的长度
            for (const auto& kv : got) {
                if (!expected_fleet.count(kv.first)) return false;
            }
            // 逐一匹配数量
            for (const auto& kv : expected_fleet) {
                int L = kv.first, cnt = kv.second;
                if (!got.count(L) || got[L] != cnt) return false;
            }
        }
        return true;
    }

    std::optional<std::vector<std::set<Coord>>> _collect_components() {
        std::vector<std::vector<bool>> seen(n, std::vector<bool>(n, false));
        std::vector<std::set<Coord>> comps;

        for (int r = 0; r < n; ++r) {
            for (int c = 0; c < n; ++c) {
                if (board[r][c] != 0 || seen[r][c]) continue;

                std::set<Coord> comp;
                std::stack<Coord> st;
                st.push({ r, c });
                seen[r][c] = true;

                while (!st.empty()) {
                    auto [cr, cc] = st.top();
                    st.pop();
                    comp.insert({ cr, cc });

                    for (const auto& nb : neighbors4(cr, cc)) {
                        int nr = nb.first, nc = nb.second;
                        if (!seen[nr][nc] && board[nr][nc] == 0) {
                            seen[nr][nc] = true;
                            st.push({ nr, nc });
                        }
                    }
                }

                if (!_component_is_straight_and_contiguous(comp)) return std::nullopt;
                comps.push_back(comp);
            }
        }
        return comps;
    }

    bool _component_is_straight_and_contiguous(const std::set<Coord>& comp) {
        if (comp.empty()) return true;
        if (comp.size() == 1) return true;

        std::set<int> rows, cols;
        for (const auto& p : comp) {
            rows.insert(p.first);
            cols.insert(p.second);
        }

        if (rows.size() == 1) {
            std::vector<int> cs;
            cs.reserve(comp.size());
            for (const auto& p : comp) cs.push_back(p.second);
            std::sort(cs.begin(), cs.end());
            for (size_t i = 1; i < cs.size(); ++i)
                if (cs[i] != cs[i - 1] + 1) return false;
            return true;
        }

        if (cols.size() == 1) {
            std::vector<int> rs;
            rs.reserve(comp.size());
            for (const auto& p : comp) rs.push_back(p.first);
            std::sort(rs.begin(), rs.end());
            for (size_t i = 1; i < rs.size(); ++i)
                if (rs[i] != rs[i - 1] + 1) return false;
            return true;
        }

        return false;
    }

    std::map<int, int> _expected_fleet(int K) {
        // Expected fleet: length L ships count is K-L+1, L=1..K
        std::map<int, int> expected;
        int total_cells = 0;
        for (int L = 1; L <= K; ++L) {
            int cnt = K - L + 1;
            expected[L] = cnt;
            total_cells += L * cnt;
        }
        if (total_cells > n * n) return {};
        return expected;
    }
};

int main() {
    try {
        auto [K, grid] = parse_input();
        BattleshipDirectionalSolver solver(K, grid);

        std::vector<std::vector<std::vector<int>>> solutions;
        solver.enumerate_all(solutions);

        if (solutions.empty()) {
            std::cout << "No solution" << std::endl;
            return 0;
        }

        std::cout << "Solutions: " << solutions.size() << std::endl;
        for (size_t idx = 0; idx < solutions.size(); ++idx) {
            const auto& sol = solutions[idx];
            for (int r = 0; r < solver.getN(); ++r) {
                for (int c = 0; c < solver.getN(); ++c) {
                    if (c > 0) std::cout << " ";
                    std::cout << sol[r][c];
                }
                std::cout << std::endl;
            }
            if (idx + 1 < solutions.size()) std::cout << std::endl;
        }
    }
    catch (const std::exception& e) {
        std::cerr << "输入/求解错误: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}