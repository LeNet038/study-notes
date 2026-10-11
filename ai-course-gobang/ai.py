# ai.py —— 五子棋 AI 模块
# 负责：走法生成、局面评估函数、极大极小(Minimax)搜索 + α-β 剪枝

from board import Board, EMPTY, BLACK, WHITE, SIZE

# 进攻与防守权重：防守权重 >= 进攻权重，避免 AI 忽视对手的冲四/活三威胁
OFFENSE_WEIGHT = 1.0  # 进攻权重
DEFENSE_WEIGHT = 1.1  # 防守权重（略高于进攻，使 AI 更重视防守）

# 各棋型参考分值（越大优先级越高）
SCORE_FIVE = 10_000_000       # 五连：直接获胜
SCORE_OPEN_FOUR = 1_000_000   # 活四：两端均空的四连，必胜
SCORE_FOUR = 100_000          # 冲四：一端被堵的四连（含跳冲四）
SCORE_OPEN_THREE = 50_000     # 活三：可发展成活四的三连
SCORE_SLEEP_THREE = 1_000     # 眠三：一端被堵的三连
SCORE_OPEN_TWO = 500          # 活二：可发展的二连

# 棋型模式表：(模式字符串, 分值)
# 约定：'1' 表示己方棋子，'2' 表示对方棋子(含边界)，'0' 表示空位
PATTERNS = [
    ("11111", SCORE_FIVE),                 # 五连
    ("011110", SCORE_OPEN_FOUR),           # 活四
    ("211110", SCORE_FOUR),                # 冲四：左端被堵
    ("011112", SCORE_FOUR),                # 冲四：右端被堵
    ("10111", SCORE_FOUR),                 # 跳冲四：1_111
    ("11101", SCORE_FOUR),                 # 跳冲四：111_1
    ("11011", SCORE_FOUR),                 # 跳冲四：11_11
    ("01110", SCORE_OPEN_THREE),           # 活三
    ("010110", SCORE_OPEN_THREE),          # 跳活三：1_11
    ("011010", SCORE_OPEN_THREE),          # 跳活三：11_1
    ("211100", SCORE_SLEEP_THREE),         # 眠三：左端被堵，右端两空位
    ("001112", SCORE_SLEEP_THREE),         # 眠三：右端被堵，左端两空位
    ("211010", SCORE_SLEEP_THREE),         # 跳眠三
    ("010112", SCORE_SLEEP_THREE),         # 跳眠三
    ("210110", SCORE_SLEEP_THREE),         # 跳眠三
    ("011012", SCORE_SLEEP_THREE),         # 跳眠三
    ("0110", SCORE_OPEN_TWO),              # 活二
    ("01010", SCORE_OPEN_TWO),             # 跳活二
    ("010010", SCORE_OPEN_TWO),            # 跳活二
]


class AI:
    """AI 类：基于 Minimax + α-β 剪枝的五子棋智能体"""

    def __init__(self, ai_player=WHITE, depth=4):
        # ai_player：AI 执棋颜色（默认白方，后手）
        self.ai_player = ai_player
        # opponent：对手执棋颜色
        self.opponent = BLACK if ai_player == WHITE else WHITE
        # 搜索深度（核心要求不低于 2 层，这里默认 4 层）
        self.depth = depth
        # 统计变量：分别记录带剪枝与不带剪枝时搜索的节点数，用于效率对比
        self.nodes_with_pruning = 0
        self.nodes_without_pruning = 0

    def _line_to_string(self, line, player):
        # 将一条线(list of 0/1/2)转为字符串：己方='1'，对方或边界='2'，空位='0'
        opp = self.opponent if player == self.ai_player else self.ai_player
        s = []
        for v in line:
            if v == player:
                s.append('1')  # 己方棋子
            elif v == EMPTY:
                s.append('0')  # 空位
            else:
                s.append('2')  # 对方棋子
        # 两端补 '2'，把棋盘边界也视作被对方堵住，便于模式匹配
        return '2' + ''.join(s) + '2'

    def _score_line(self, line_str):
        # 对一条已转换的线字符串按棋型表计分，返回该线的总分
        score = 0
        for pattern, value in PATTERNS:
            # str.count 统计非重叠出现次数，乘以该棋型分值
            score += line_str.count(pattern) * value
        return score

    def _collect_lines(self, board):
        # 收集棋盘上所有行、列、两条对角线方向的线，供评估函数扫描
        lines = []
        # 1) 所有行
        for r in range(SIZE):
            lines.append([board.board[r][c] for c in range(SIZE)])
        # 2) 所有列
        for c in range(SIZE):
            lines.append([board.board[r][c] for r in range(SIZE)])
        # 3) 主对角线方向 (\)：遍历所有起点
        for k in range(-(SIZE - 1), SIZE):
            diag = []
            for r in range(SIZE):
                c = r + k
                if 0 <= c < SIZE:
                    diag.append(board.board[r][c])
            if len(diag) >= 5:  # 长度不足 5 的对角线不可能成五连，忽略
                lines.append(diag)
        # 4) 副对角线方向 (/)
        for k in range(0, 2 * SIZE - 1):
            diag = []
            for r in range(SIZE):
                c = k - r
                if 0 <= c < SIZE:
                    diag.append(board.board[r][c])
            if len(diag) >= 5:
                lines.append(diag)
        return lines

    def evaluate(self, board):
        # 局面评估函数：返回对 AI 方(MAX)有利的分数
        # 评估值 = 己方棋型总分 × 进攻权重 - 对方棋型总分 × 防守权重
        own_score = 0  # AI 方棋型总分
        opp_score = 0  # 对手方棋型总分
        for line in self._collect_lines(board):
            own_str = self._line_to_string(line, self.ai_player)
            opp_str = self._line_to_string(line, self.opponent)
            own_score += self._score_line(own_str)
            opp_score += self._score_line(opp_str)
        # 防守权重不低于进攻权重，确保 AI 重视对手威胁
        return own_score * OFFENSE_WEIGHT - opp_score * DEFENSE_WEIGHT

    def get_best_move(self, board):
        # 返回 AI 的最佳落子位置 (row, col)
        best_move = None
        best_score = -float('inf')  # MAX 方初始化为负无穷
        alpha = -float('inf')       # 根层 alpha，跨子节点共享以触发 β 剪枝
        beta = float('inf')
        # 生成候选走法：仅考虑已有棋子邻域的空位（启发式，提高剪枝效率）
        candidates = board.get_empty_neighbors(radius=2)

        # 先对候选点按启发式分值排序，使更可能的好走法排在前面，提升 α-β 剪枝效率
        def heuristic(move):
            r, c = move
            # 临时落子后评估，分值越高排序越靠前
            board.place(r, c, self.ai_player)
            s = self.evaluate(board)
            board.undo(r, c)
            return s

        candidates.sort(key=heuristic, reverse=True)

        for move in candidates:
            r, c = move
            board.place(r, c, self.ai_player)  # 尝试落子
            # 递归进行 Minimax + α-β 搜索，下一层为对手(MIN 方)
            score = self._minimax(board, self.depth - 1, alpha, beta, False)
            board.undo(r, c)  # 撤销落子，恢复局面
            if score > best_score:  # MAX 方取最大值
                best_score = score
                best_move = move
            alpha = max(alpha, score)  # 更新根层 alpha，供后续子节点剪枝
        return best_move

    def _minimax(self, board, depth, alpha, beta, is_max):
        # Minimax + α-β 剪枝递归函数
        # depth: 剩余搜索深度；alpha: MAX 方下界；beta: MIN 方上界；is_max: 当前是否 MAX 层
        self.nodes_with_pruning += 1  # 统计带剪枝时访问的节点数

        # 终止条件：深度为 0，或已有一方获胜，或棋盘已满
        winner = board.get_winner()
        if depth == 0 or winner is not None or board.is_full():
            return self.evaluate(board)

        # 生成候选走法
        candidates = board.get_empty_neighbors(radius=2)

        if is_max:
            # MAX 层（AI 行棋）：目标是最大化评估值
            max_eval = -float('inf')
            for move in candidates:
                r, c = move
                board.place(r, c, self.ai_player)
                ev = self._minimax(board, depth - 1, alpha, beta, False)
                board.undo(r, c)
                max_eval = max(max_eval, ev)
                alpha = max(alpha, ev)  # 更新 alpha 下界
                if beta <= alpha:
                    break  # β 剪枝：MIN 方不会选择此分支，剪去剩余兄弟节点
            return max_eval
        else:
            # MIN 层（对手行棋）：目标是最小化评估值
            min_eval = float('inf')
            for move in candidates:
                r, c = move
                board.place(r, c, self.opponent)
                ev = self._minimax(board, depth - 1, alpha, beta, True)
                board.undo(r, c)
                min_eval = min(min_eval, ev)
                beta = min(beta, ev)  # 更新 beta 上界
                if beta <= alpha:
                    break  # α 剪枝：MAX 方不会选择此分支，剪去剩余兄弟节点
            return min_eval

    # ---- 以下为“不剪枝”版本，仅用于统计对比剪枝效率（选做要求）----
    def get_best_move_no_pruning(self, board):
        # 不带 α-β 剪枝的最佳走法，用于对比搜索节点数
        best_move = None
        best_score = -float('inf')
        candidates = board.get_empty_neighbors(radius=2)
        for move in candidates:
            r, c = move
            board.place(r, c, self.ai_player)
            score = self._minimax_no_pruning(board, self.depth - 1, False)
            board.undo(r, c)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _minimax_no_pruning(self, board, depth, is_max):
        # 不带 α-β 剪枝的 Minimax，仅用于统计对比
        self.nodes_without_pruning += 1
        winner = board.get_winner()
        if depth == 0 or winner is not None or board.is_full():
            return self.evaluate(board)
        candidates = board.get_empty_neighbors(radius=2)
        if is_max:
            max_eval = -float('inf')
            for move in candidates:
                r, c = move
                board.place(r, c, self.ai_player)
                ev = self._minimax_no_pruning(board, depth - 1, False)
                board.undo(r, c)
                max_eval = max(max_eval, ev)
            return max_eval
        else:
            min_eval = float('inf')
            for move in candidates:
                r, c = move
                board.place(r, c, self.opponent)
                ev = self._minimax_no_pruning(board, depth - 1, True)
                board.undo(r, c)
                min_eval = min(min_eval, ev)
            return min_eval
