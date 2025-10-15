# BattleShips

BattleShips 是一个基于 C++ 和 Python 的战舰拼图求解工具。它结合了高效的 C++ 核心引擎与易用的 Python 图形用户界面 (GUI)，适合游戏玩家、开发者和研究人员学习和使用。

BattleShips is a Battleship puzzle-solving tool based on C++ and Python. It combines an efficient C++ core engine with an easy-to-use Python graphical user interface (GUI), suitable for gamers, developers, and researchers.

## 功能特点 / Features
- **C++ 核心引擎 / C++ Core Engine**: 提供高性能的战舰拼图求解算法 / Provides a high-performance algorithm for solving Battleship puzzles.
- **Python 用户界面 / Python GUI**: 提供直观的图形界面与求解引擎交互 / Offers an intuitive graphical interface to interact with the solver engine.
- **自定义棋盘 / Customizable Board**: 支持动态调整棋盘大小和目标设置 / Supports dynamic adjustment of board size and targets.
- **引擎编译支持 / Engine Compilation Support**: 内置 C++ 求解器编译功能，方便用户使用 / Built-in support for compiling the C++ solver for user convenience.

## 安装与运行 / Installation and Running

### 依赖 / Dependencies
- Python 3.7 或更高版本 / Python 3.7 or later
- Tkinter 图形库 / Tkinter GUI library
- GCC 编译器（用于编译 C++ 引擎）/ GCC Compiler (for compiling the C++ engine)

### 下载与安装 / Download and Installation
```bash
git clone https://github.com/Lambchem/BattleShips.git
cd BattleShips
```

### 运行用户界面 / Running the GUI
```bash
python BattleShipsUI.py
```

## 使用说明 / Usage Instructions
1. **设置棋盘大小 / Set Board Size**:
   - 在界面顶部输入所需的棋盘大小（如 10x10）/ Enter the desired board size (e.g., 10x10) at the top of the interface.
2. **加载引擎 / Load Engine**:
   - 提供 BattleShips.cpp 文件路径，并点击“编译引擎”/ Provide the path to the `BattleShips.cpp` file and click "Compile Engine".
3. **编辑棋盘与目标 / Edit Board and Targets**:
   - 使用界面按钮或直接点击棋盘格子设置船只位置 / Use the interface buttons or click directly on board cells to set ship positions.
4. **求解拼图 / Solve Puzzle**:
   - 点击“求解”按钮，等待引擎返回解决方案 / Click the "Solve" button and wait for the engine to return solutions.
5. **查看与导出 / View and Export**:
   - 浏览不同解决方案，并将其导出为文本 / Browse different solutions and export them as text.

## 许可证 / License
本项目基于 [GNU General Public License v3.0](LICENSE)。  
This project is licensed under the [GNU General Public License v3.0](LICENSE).

## 贡献 / Contributions
欢迎提交问题 (Issue) 和拉取请求 (PR)，帮助改进此项目。  
Contributions are welcome through Issues and Pull Requests (PRs) to help improve this project.

## 联系方式 / Contact
作者：Lambchem  
GitHub: [https://github.com/Lambchem](https://github.com/Lambchem)  
单位 / Affiliation: Xiamen University  
