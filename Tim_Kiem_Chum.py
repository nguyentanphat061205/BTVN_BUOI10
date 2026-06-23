import tkinter as tk
from tkinter import messagebox
import time


class Node:
    def __init__(self, state, parent=None, action=None, depth=0, h_cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.depth = depth
        self.h_cost = h_cost


def find_zero(state):
    for i in range(3):
        for j in range(3):
            if state[i][j] == 0:
                return i, j


def calculate_manhattan_distance(current_state, goal_state):
    goal_pos = {}
    for r in range(3):
        for c in range(3):
            goal_pos[goal_state[r][c]] = (r, c)
    distance = 0
    for r in range(3):
        for c in range(3):
            val = current_state[r][c]
            if val != 0:
                target_r, target_c = goal_pos[val]
                distance += abs(r - target_r) + abs(c - target_c)
    return distance


def generate_children(node, goal_state):
    children = []
    x, y = find_zero(node.state)
    moves = [(-1, 0, "UP"), (1, 0, "DOWN"), (0, -1, "LEFT"), (0, 1, "RIGHT")]
    for dx, dy, action in moves:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 3 and 0 <= ny < 3:
            new_state = [row[:] for row in node.state]
            new_state[x][y], new_state[nx][ny] = new_state[nx][ny], new_state[x][y]
            h_cost = calculate_manhattan_distance(new_state, goal_state)
            child = Node(state=new_state, parent=node, action=action, depth=node.depth + 1, h_cost=h_cost)
            children.append(child)
    return children


def get_solution(goal_node):
    path = []
    current = goal_node
    while current is not None:
        path.append(current)
        current = current.parent
    path.reverse()
    return path


def state_to_tuple(state):
    return tuple(tuple(row) for row in state)


def beam_search_generator(initial_state, goal_state, beam_width):
    initial_h = calculate_manhattan_distance(initial_state, goal_state)
    root = Node(initial_state, depth=0, h_cost=initial_h)

    current_level = [root]
    visited = {state_to_tuple(initial_state)}
    level_count = 0

    while current_level:
        level_count += 1
        best_node_in_level = min(current_level, key=lambda n: n.h_cost)
        yield best_node_in_level, False, None, f"Đang xét tầng {level_count}"
        for node in current_level:
            if node.state == goal_state:
                yield node, True, get_solution(node), "Thành công!"
                return

        next_level_candidates = []
        for node in current_level:
            children = generate_children(node, goal_state)
            for child in children:
                child_tuple = state_to_tuple(child.state)
                if child_tuple not in visited:
                    visited.add(child_tuple)
                    next_level_candidates.append(child)

        if not next_level_candidates:
            yield best_node_in_level, False, None, f"Thất bại: Hết trạng thái để duyệt."
            return

        next_level_candidates.sort(key=lambda n: n.h_cost)
        current_level = next_level_candidates[:beam_width]


class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle - Beam Search")
        self.root.geometry("850x680")
        self.root.configure(bg="#f0f2f5")

        self.TILE_SIZE = 80
        self.GAP = 5
        self.tiles = {}
        self.current_display_state = None
        self.is_running = False

        self.algo_generator = None
        self.nodes_explored = 0
        
        self.create_widgets()
        self.set_default_values()

    def create_widgets(self):
        title_lbl = tk.Label(self.root, text="BEAM SEARCH ", font=("Helvetica", 16, "bold"), bg="#f0f2f5", fg="#1e293b")
        title_lbl.pack(pady=10)

        input_frame = tk.Frame(self.root, bg="#f0f2f5")
        input_frame.pack(pady=5)

        init_box = tk.LabelFrame(input_frame, text=" Trạng thái ban đầu ", font=("Arial", 11, "bold"), bg="#f0f2f5", fg="#475569")
        init_box.grid(row=0, column=0, padx=20)
        self.initial_entries = []
        for i in range(3):
            row_entries = []
            for j in range(3):
                e = tk.Entry(init_box, width=3, font=("Arial", 16), justify="center", bd=2)
                e.grid(row=i, column=j, padx=6, pady=6)
                row_entries.append(e)
            self.initial_entries.append(row_entries)

        goal_box = tk.LabelFrame(input_frame, text=" Trạng thái đích ", font=("Arial", 11, "bold"), bg="#f0f2f5", fg="#475569")
        goal_box.grid(row=0, column=1, padx=20)
        self.goal_entries = []
        for i in range(3):
            row_entries = []
            for j in range(3):
                e = tk.Entry(goal_box, width=3, font=("Arial", 16), justify="center", bd=2)
                e.grid(row=i, column=j, padx=6, pady=6)
                row_entries.append(e)
            self.goal_entries.append(row_entries)

        # Frame chứa cấu hình Beam Width
        config_frame = tk.Frame(self.root, bg="#f0f2f5")
        config_frame.pack(pady=5)
        
        tk.Label(config_frame, text="Beam Width (k): ", font=("Arial", 11, "bold"), bg="#f0f2f5", fg="#334155").pack(side=tk.LEFT)
        self.beam_width_entry = tk.Entry(config_frame, width=5, font=("Arial", 12), justify="center")
        self.beam_width_entry.pack(side=tk.LEFT, padx=5)

        main_layout = tk.Frame(self.root, bg="#f0f2f5")
        main_layout.pack(pady=10, fill=tk.BOTH, expand=True)

        canvas_container = tk.Frame(main_layout, bg="#cbd5e1", padx=4, pady=4)
        canvas_container.pack(side=tk.LEFT, padx=40)
        canvas_width_height = 3 * self.TILE_SIZE + 4 * self.GAP
        self.canvas = tk.Canvas(canvas_container, width=canvas_width_height, height=canvas_width_height, bg="#e2e8f0", highlightthickness=0)
        self.canvas.pack()

        right_frame = tk.Frame(main_layout, bg="#f0f2f5")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        
        self.btn_solve = tk.Button(
            right_frame, text=" CHẠY THUẬT TOÁN ", font=("Arial", 12, "bold"),
            bg="#0d9488", fg="white", activebackground="#0f766e", activeforeground="white",
            command=self.start_solving, padx=8, pady=8
        )
        self.btn_solve.pack(fill=tk.X, pady=5)

        self.status_label = tk.Label(right_frame, text="Trạng thái: Sẵn sàng", font=("Arial", 11, "italic"), bg="#f0f2f5", fg="#64748b", anchor="w")
        self.status_label.pack(fill=tk.X, pady=5)

        self.result_text = tk.Text(right_frame, width=40, height=14, font=("Consolas", 10), bd=2, relief=tk.SUNKEN)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def set_default_values(self):
        self.beam_width_entry.insert(0, "2")
        
        start_matrix = [[1, 2, 3], [4, 5, 0], [7, 8, 6]]
        goal_matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
        for i in range(3):
            for j in range(3):
                self.initial_entries[i][j].insert(0, str(start_matrix[i][j]))
                self.goal_entries[i][j].insert(0, str(goal_matrix[i][j]))
        self.draw_puzzle(start_matrix)

    def read_matrix(self, entries):
        matrix = []
        for i in range(3):
            row = []
            for j in range(3):
                val = entries[i][j].get().strip()
                row.append(int(val) if val else 0)
            matrix.append(row)
        return matrix

    def draw_puzzle(self, state, tile_bg="#ffffff", text_fg="#1e293b"):
        self.canvas.delete("all")
        self.tiles = {}
        self.current_display_state = [row[:] for row in state]
        for i in range(3):
            for j in range(3):
                val = state[i][j]
                if val != 0:
                    x1 = j * self.TILE_SIZE + (j + 1) * self.GAP
                    y1 = i * self.TILE_SIZE + (i + 1) * self.GAP
                    x2 = x1 + self.TILE_SIZE
                    y2 = y1 + self.TILE_SIZE
                    rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill=tile_bg, outline="#94a3b8", width=2)
                    text_id = self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=str(val), font=("Arial", 22, "bold"), fill=text_fg)
                    self.tiles[val] = (rect_id, text_id)

    def start_solving(self):
        if self.is_running:
            return

        try:
            initial = self.read_matrix(self.initial_entries)
            goal = self.read_matrix(self.goal_entries)
            all_nums = sorted([num for row in initial for num in row])
            if all_nums != list(range(9)):
                raise ValueError("Ma trận nhập vào phải chứa đầy đủ các số từ 0 đến 8")

            # Lấy Beam Width từ UI
            bw_val = self.beam_width_entry.get().strip()
            if not bw_val.isdigit() or int(bw_val) < 1:
                raise ValueError("k phải là số nguyên dương lớn hơn 0")
            k_width = int(bw_val)

            self.canvas.config(bg="#e2e8f0")
            self.result_text.delete(1.0, tk.END)
            self.btn_solve.config(state=tk.DISABLED)
            self.beam_width_entry.config(state=tk.DISABLED)
            self.is_running = True
            self.nodes_explored = 0

            self.algo_generator = beam_search_generator(initial, goal, k_width)
            self.process_next_step()

        except ValueError as ve:
            messagebox.showerror("Lỗi dữ liệu", str(ve))
            self.btn_solve.config(state=tk.NORMAL)
            self.beam_width_entry.config(state=tk.NORMAL)
            self.is_running = False

    def process_next_step(self):
        if not self.is_running:
            return

        try:
            current_node, success, solution, status_msg = next(self.algo_generator)
            self.nodes_explored += 1

            self.draw_puzzle(current_node.state, tile_bg="#f0fdfa", text_fg="#0f766e")
            self.status_label.config(text=f"{status_msg} | Best h(n) = {current_node.h_cost}")

            if success and solution:
                self.status_label.config(text=status_msg)
                self.result_text.insert(tk.END, f"{status_msg}\n")
                self.result_text.insert(tk.END, f"Số bước di chuyển: {len(solution) - 1}\n\n")

                for step, node in enumerate(solution):
                    self.result_text.insert(tk.END, f"Bước {step} (h = {node.h_cost})\n")
                    if node.action:
                        self.result_text.insert(tk.END, f" | Trống dịch: {node.action}\n")
                    for row in node.state:
                        self.result_text.insert(tk.END, f"  {row}\n")
                    self.result_text.insert(tk.END, "\n")

                self.draw_puzzle(solution[-1].state, tile_bg="#10b981", text_fg="#ffffff")
                self.canvas.config(bg="#d1fae5")
                self.is_running = False
                self.btn_solve.config(state=tk.NORMAL)
                self.beam_width_entry.config(state=tk.NORMAL)
                return

            if "Thất bại" in status_msg:
                self.status_label.config(text="Không tìm thấy đường đi")
                self.result_text.insert(tk.END, f"{status_msg}\n\nMẹo: Hãy thử tăng giá trị k lên!")
                self.draw_puzzle(current_node.state, tile_bg="#fef2f2", text_fg="#dc2626")
                self.canvas.config(bg="#fee2e2")
                self.is_running = False
                self.btn_solve.config(state=tk.NORMAL)
                self.beam_width_entry.config(state=tk.NORMAL)
                return

            self.root.after(200, self.process_next_step)

        except StopIteration:
            self.is_running = False
            self.btn_solve.config(state=tk.NORMAL)
            self.beam_width_entry.config(state=tk.NORMAL)

if __name__ == "__main__":
    window = tk.Tk()
    app = PuzzleApp(window)
    window.mainloop()