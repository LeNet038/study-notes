# main.py —— 五子棋主控制模块
# 负责：图形界面(tkinter)、对弈流程控制、人机/双人模式切换、悔棋/重开

import tkinter as tk  # 导入 tkinter GUI 库（Python 标准库，无需安装）
from tkinter import messagebox  # 用于弹出胜负提示框
from board import Board, EMPTY, BLACK, WHITE, SIZE
from ai import AI

CELL_SIZE = 36        # 每个格子的像素大小
MARGIN = 30           # 棋盘边距
BOARD_PX = CELL_SIZE * (SIZE - 1) + MARGIN * 2  # 画布总尺寸


class GomokuApp:
    """五子棋图形界面应用类"""

    def __init__(self, root):
        self.root = root  # 主窗口
        self.root.title("五子棋 AI —— Minimax + α-β 剪枝")  # 窗口标题
        self.board = Board()  # 创建棋盘对象
        self.mode = "pve"     # 对弈模式："pve" 人机，"pvp" 双人
        self.human_player = BLACK  # 人机模式下人类执黑(先手)
        self.current_player = BLACK  # 当前轮到谁，黑方先行
        self.ai = AI(ai_player=WHITE, depth=4)  # 创建 AI，执白，搜索深度 4
        self.ai_thinking = False  # AI 是否正在思考，避免重复点击
        self.history = []  # 落子历史栈，用于悔棋

        # ---- 顶部控制栏 ----
        control = tk.Frame(root)
        control.pack(pady=5)
        tk.Label(control, text="模式:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="pve")  # 模式单选变量
        tk.Radiobutton(control, text="人机对战", variable=self.mode_var,
                       value="pve", command=self.reset_game).pack(side=tk.LEFT)
        tk.Radiobutton(control, text="双人对战", variable=self.mode_var,
                       value="pvp", command=self.reset_game).pack(side=tk.LEFT)
        tk.Label(control, text="  AI 深度:").pack(side=tk.LEFT)
        self.depth_var = tk.IntVar(value=4)  # 搜索深度变量
        tk.Spinbox(control, from_=2, to=6, textvariable=self.depth_var,
                   width=4, command=self.on_depth_change).pack(side=tk.LEFT)
        tk.Button(control, text="重新开始", command=self.reset_game).pack(side=tk.LEFT, padx=5)
        tk.Button(control, text="悔棋", command=self.undo_move).pack(side=tk.LEFT)

        # ---- 状态提示 ----
        self.status = tk.StringVar(value="黑方先行，请落子")
        tk.Label(root, textvariable=self.status, font=("Arial", 12)).pack(pady=5)

        # ---- 棋盘画布 ----
        self.canvas = tk.Canvas(root, width=BOARD_PX, height=BOARD_PX, bg="#DEB887")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)  # 绑定鼠标左键点击事件

        self.draw_board()  # 初始绘制棋盘

    def on_depth_change(self):
        # 当用户修改搜索深度时，更新 AI 的深度
        try:
            self.ai.depth = int(self.depth_var.get())
        except tk.TclError:
            pass

    def draw_board(self):
        # 绘制棋盘网格线与星位
        self.canvas.delete("all")  # 清空画布
        # 绘制横竖各 SIZE 条线
        for i in range(SIZE):
            x = MARGIN + i * CELL_SIZE
            self.canvas.create_line(MARGIN, x, MARGIN + (SIZE - 1) * CELL_SIZE, x)
            self.canvas.create_line(x, MARGIN, x, MARGIN + (SIZE - 1) * CELL_SIZE)
        # 绘制天元与四个星位
        stars = [(3, 3), (3, 11), (7, 7), (11, 3), (11, 11)]
        for r, c in stars:
            x = MARGIN + c * CELL_SIZE
            y = MARGIN + r * CELL_SIZE
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="black")
        # 绘制所有已有棋子
        for r in range(SIZE):
            for c in range(SIZE):
                if self.board.board[r][c] != EMPTY:
                    self.draw_stone(r, c, self.board.board[r][c])
        # 标记最后一步
        if self.board.last_move:
            r, c = self.board.last_move
            x = MARGIN + c * CELL_SIZE
            y = MARGIN + r * CELL_SIZE
            self.canvas.create_rectangle(x - 4, y - 4, x + 4, y + 4,
                                         outline="red", width=2)

    def draw_stone(self, row, col, player):
        # 在 (row, col) 处绘制一颗 player 颜色的棋子
        x = MARGIN + col * CELL_SIZE
        y = MARGIN + row * CELL_SIZE
        color = "black" if player == BLACK else "white"
        self.canvas.create_oval(x - CELL_SIZE // 2 + 2, y - CELL_SIZE // 2 + 2,
                                x + CELL_SIZE // 2 - 2, y + CELL_SIZE // 2 - 2,
                                fill=color, outline="black")

    def on_click(self, event):
        # 鼠标点击棋盘事件处理
        if self.ai_thinking:  # AI 思考中，忽略点击
            return
        # 将像素坐标转换为棋盘行列
        col = round((event.x - MARGIN) / CELL_SIZE)
        row = round((event.y - MARGIN) / CELL_SIZE)
        if not self.board.is_in_board(row, col):  # 点击越界，忽略
            return
        # 双人模式下任何人都可落子；人机模式下只允许人类方落子
        if self.mode == "pve" and self.current_player != self.human_player:
            return
        self.make_move(row, col, self.current_player)

    def make_move(self, row, col, player):
        # 执行一次落子，并处理后续逻辑（胜负判定、轮换、AI 触发）
        if not self.board.place(row, col, player):  # 落子失败（非空位），直接返回
            return
        self.history.append((row, col, player))  # 记入历史栈供悔棋
        self.draw_board()  # 重绘棋盘

        winner = self.board.get_winner()  # 检查是否有获胜方
        if winner is not None:
            name = "黑方" if winner == BLACK else "白方"
            self.status.set(f"{name}获胜！")
            messagebox.showinfo("对局结束", f"{name}获胜！")
            return
        if self.board.is_full():  # 棋盘已满，和棋
            self.status.set("和棋！棋盘已满。")
            messagebox.showinfo("对局结束", "和棋！棋盘已满。")
            return

        # 轮换到下一方
        self.current_player = WHITE if player == BLACK else BLACK
        self.update_status()

        # 人机模式且轮到 AI 时，触发 AI 思考
        if self.mode == "pve" and self.current_player == self.ai.ai_player:
            self.ai_thinking = True
            self.status.set("AI 思考中...")
            # 使用 after 延迟调用，避免阻塞界面重绘
            self.root.after(100, self.ai_move)

    def ai_move(self):
        # AI 执行走子
        move = self.ai.get_best_move(self.board)  # 搜索最佳走法
        self.ai_thinking = False
        if move is None:  # 无合法走法（理论上棋盘已满，前面已判定）
            return
        self.make_move(move[0], move[1], self.ai.ai_player)

    def update_status(self):
        # 更新状态栏文字
        name = "黑方" if self.current_player == BLACK else "白方"
        who = "你" if (self.mode == "pve" and self.current_player == self.human_player) else name
        self.status.set(f"轮到 {name}（{who}）落子")

    def undo_move(self):
        # 悔棋功能
        if self.ai_thinking or not self.history:  # AI 思考中或无历史可悔
            return
        # 人机模式：一次撤销两步（AI + 人类），回到人类回合
        steps = 2 if (self.mode == "pve" and len(self.history) >= 2) else 1
        for _ in range(steps):
            if not self.history:
                break
            r, c, p = self.history.pop()
            self.board.undo(r, c)
            self.current_player = p  # 恢复到该步的执棋方
        self.draw_board()
        self.update_status()

    def reset_game(self):
        # 重新开始一局
        self.mode = self.mode_var.get()  # 读取当前选择的模式
        self.board = Board()  # 新建空棋盘
        self.history = []  # 清空历史
        self.ai = AI(ai_player=WHITE, depth=int(self.depth_var.get()))  # 重建 AI
        self.current_player = BLACK  # 黑方先行
        self.ai_thinking = False
        self.draw_board()
        self.update_status()


def main():
    # 程序入口
    root = tk.Tk()  # 创建主窗口
    GomokuApp(root)  # 启动五子棋应用
    root.mainloop()  # 进入事件循环


if __name__ == "__main__":
    main()
