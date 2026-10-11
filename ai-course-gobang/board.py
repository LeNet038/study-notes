# board.py —— 五子棋棋盘模块
# 负责：棋盘数据结构、落子、胜负/和棋判定、棋盘显示

EMPTY = 0  # 常量：空位
BLACK = 1  # 常量：黑方棋子
WHITE = 2  # 常量：白方棋子
SIZE = 15  # 常量：标准五子棋棋盘为 15×15


class Board:
    """棋盘类：封装 15×15 棋盘的状态与基本操作"""

    def __init__(self):
        # 用 SIZE×SIZE 的二维列表表示棋盘，初始全部为空位 EMPTY
        self.board = [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]
        self.last_move = None  # 记录上一步落子位置 (row, col)，便于胜负判定
        self.move_count = 0  # 记录已落子总数，用于判断是否和棋

    def is_in_board(self, row, col):
        # 判断给定坐标是否在棋盘范围内（0 <= row,col < SIZE）
        return 0 <= row < SIZE and 0 <= col < SIZE

    def is_empty(self, row, col):
        # 判断某位置是否为空位（必须先保证坐标合法）
        return self.board[row][col] == EMPTY

    def place(self, row, col, player):
        # 在 (row, col) 处落下 player 方的棋子；返回是否落子成功
        if not self.is_in_board(row, col):  # 坐标越界，非法
            return False
        if not self.is_empty(row, col):  # 该位置已有棋子，非法
            return False
        self.board[row][col] = player  # 写入棋子
        self.last_move = (row, col)  # 更新最后一步
        self.move_count += 1  # 落子数加一
        return True

    def undo(self, row, col):
        # 悔棋：清除 (row, col) 处棋子（选做功能）
        if self.is_in_board(row, col) and self.board[row][col] != EMPTY:
            self.board[row][col] = EMPTY
            self.move_count -= 1  # 落子数减一
            self.last_move = None
            return True
        return False

    def get_winner(self):
        # 判断是否有一方五连获胜，返回获胜方；无则返回 None
        if self.last_move is None:  # 还没落子，不可能获胜
            return None
        row, col = self.last_move  # 只需从最后一步向四个方向检查即可
        player = self.board[row][col]
        # 四个方向：水平、垂直、主对角线、副对角线
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1  # 至少包含最后一步这一颗棋子
            # 向正方向延伸计数
            r, c = row + dr, col + dc
            while self.is_in_board(r, c) and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # 向反方向延伸计数
            r, c = row - dr, col - dc
            while self.is_in_board(r, c) and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 5:  # 同色连续达到 5 颗即获胜
                return player
        return None  # 无人获胜

    def is_full(self):
        # 判断棋盘是否已满（和棋）
        return self.move_count >= SIZE * SIZE

    def get_empty_neighbors(self, radius=2):
        # 启发式候选点生成：返回已有棋子周围 radius 范围内的空位（提高搜索效率）
        candidates = set()  # 用集合去重，避免同一位置被多次加入
        for r in range(SIZE):
            for c in range(SIZE):
                if self.board[r][c] != EMPTY:  # 找到已有棋子
                    # 遍历其周围 radius×radius 邻域
                    for dr in range(-radius, radius + 1):
                        for dc in range(-radius, radius + 1):
                            nr, nc = r + dr, c + dc
                            # 只收集棋盘内的空位
                            if self.is_in_board(nr, nc) and self.is_empty(nr, nc):
                                candidates.add((nr, nc))
        if not candidates:  # 棋盘为空时，返回天元附近作为起始候选
            return [(SIZE // 2, SIZE // 2)]
        return list(candidates)

    def print_board(self):
        # 命令行打印棋盘（供调试/CLI 模式使用）
        # 打印列号
        print("   " + " ".join(f"{c:2d}" for c in range(SIZE)))
        for r in range(SIZE):
            row_str = []
            for c in range(SIZE):
                v = self.board[r][c]
                if v == EMPTY:
                    row_str.append(" .")  # 空位用 . 表示
                elif v == BLACK:
                    row_str.append(" X")  # 黑方用 X 表示
                else:
                    row_str.append(" O")  # 白方用 O 表示
            print(f"{r:2d} " + " ".join(row_str))
