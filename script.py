import random
import streamlit as st

st.set_page_config(page_title="Maze Adventure Game", page_icon="🎮", layout="centered")

DIRECTIONS = {
    "w": (-1, 0),
    "s": (1, 0),
    "a": (0, -1),
    "d": (0, 1),
}

DEVELOPERS = [
    {"name": "حسين الأسدي", "role": "Game Dev", "telegram": "https://t.me/A_SDE"},
    {"name": "سيد فؤاد", "role": "UI/UX Dev", "telegram": "https://t.me/F2004_u"},
    {"name": "علي حسن", "role": "Backend Dev", "telegram": "https://t.me/E12_er"},
]

LEVELS = [
    [
        "#########",
        "#P..#..K#",
        "#.#.#.#.#",
        "#.#T..#T#",
        "#.####..#",
        "#H.X..#D#",
        "#########",
    ],
    [
        "###########",
        "#P....#..T#",
        "#.###.#.#.#",
        "#.#K..#.#.#",
        "#.#X###.#H#",
        "#..G.T..#D#",
        "###########",
    ],
    [
        "###########",
        "#P..#.T.#K#",
        "#.#.#.#.#.#",
        "#.#...#...#",
        "#.###.###.#",
        "#T..G.X.HD#",
        "###########",
    ],
]


# ==========================================
# PART 1: Position, GameObject, Items, Player
# ==========================================
class Position:
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def moved(self, dr, dc):
        return Position(self.row + dr, self.col + dc)

    def same_as(self, other):
        return self.row == other.row and self.col == other.col

    def copy(self):
        return Position(self.row, self.col)


class GameObject:
    symbol = "❓"
    consumable = True

    def __init__(self, position):
        self.position = position

    def is_blocked(self, player):
        return False

    def block_text(self):
        return ""

    def on_touch(self, player):
        return ""


class Treasure(GameObject):
    symbol = "🪙"

    def __init__(self, position, value=10):
        super().__init__(position)
        self.value = value

    def on_touch(self, player):
        player.score += self.value
        player.treasures += 1
        return f"عثرت على كنز! +{self.value} نقطة"


class Key(GameObject):
    symbol = "🔑"

    def on_touch(self, player):
        player.keys += 1
        return "التقطت مفتاحاً!"


class Door(GameObject):
    symbol = "🚪"
    consumable = False

    def is_blocked(self, player):
        return player.keys == 0

    def block_text(self):
        return "الباب مقفل! ابحث عن المفتاح أولاً."

    def on_touch(self, player):
        player.keys -= 1
        player.reached_exit = True
        return "انفتح الباب! أحسنت!"


class Trap(GameObject):
    symbol = "💥"

    def on_touch(self, player):
        player.lose_life(1)
        return "وقعت في فخ! خسرت قلباً."


class Potion(GameObject):
    symbol = "🧪"

    def on_touch(self, player):
        if player.lives < player.max_lives:
            player.heal(1)
            return "جرعة صحة! استعدت قلباً."
        return "قلوبك ممتلئة بالفعل."


class Player:
    def __init__(self, name):
        self.name = name
        self.position = Position(0, 0)
        self.lives = 3
        self.max_lives = 3
        self.score = 0
        self.keys = 0
        self.treasures = 0
        self.moves = 0
        self.reached_exit = False

    def start_level(self, position):
        self.position = position.copy()
        self.reached_exit = False
        self.keys = 0

    def lose_life(self, amount):
        self.lives = max(0, self.lives - amount)

    def heal(self, amount):
        self.lives = min(self.max_lives, self.lives + amount)

    def is_alive(self):
        return self.lives > 0


# ==========================================
# PART 2: Guard, Maze
# ==========================================
class Guard(GameObject):
    symbol = "👹"

    def __init__(self, position):
        super().__init__(position)
        self.home = position.copy()

    def move(self, maze):
        dirs = list(DIRECTIONS.values())
        random.shuffle(dirs)
        for dr, dc in dirs:
            target = self.position.moved(dr, dc)
            if maze.is_free(target):
                self.position = target
                return

    def go_home(self):
        self.position = self.home.copy()


class Maze:
    CLASSES = {"T": Treasure, "K": Key, "D": Door, "X": Trap, "H": Potion}

    def __init__(self, layout):
        self.layout = layout
        self.rows = len(layout)
        self.cols = len(layout[0])
        self.walls = set()
        self.items = []
        self.guards = []
        self.start = Position(1, 1)
        self.build()

    def build(self):
        for r, line in enumerate(self.layout):
            for c, ch in enumerate(line):
                pos = Position(r, c)
                if ch == "#":
                    self.walls.add((r, c))
                elif ch == "P":
                    self.start = pos
                elif ch == "G":
                    self.guards.append(Guard(pos))
                elif ch in Maze.CLASSES:
                    self.items.append(Maze.CLASSES[ch](pos))

    def is_inside(self, pos):
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def is_wall(self, pos):
        return (pos.row, pos.col) in self.walls

    def item_at(self, pos):
        for item in self.items:
            if item.position.same_as(pos):
                return item
        return None

    def is_free(self, pos):
        if not self.is_inside(pos) or self.is_wall(pos):
            return False
        return self.item_at(pos) is None

    def render_html(self, player):
        lines = []
        for r in range(self.rows):
            row_str = ""
            for c in range(self.cols):
                pos = Position(r, c)
                if player.position.same_as(pos):
                    row_str += "🧙‍♂️"
                elif any(g.position.same_as(pos) for g in self.guards):
                    row_str += "👹"
                elif (r, c) in self.walls:
                    row_str += "🧱"
                else:
                    item = self.item_at(pos)
                    row_str += item.symbol if item else "⬜"
            lines.append(row_str)
        grid = "<br>".join(lines)
        return (
            "<div style='font-size:24px; line-height:1.1; text-align:center; "
            "background:#1e1e1e; padding:14px; border-radius:10px;'>"
            f"{grid}</div>"
        )


# ==========================================
# PART 3: Web Game Controller (Streamlit UI)
# ==========================================
def load_level():
    layout = LEVELS[st.session_state.level_index]
    st.session_state.maze = Maze(layout)
    st.session_state.player.start_level(st.session_state.maze.start)


def start_new_game(name):
    st.session_state.player = Player(name.strip() or "البطل")
    st.session_state.level_index = 0
    st.session_state.message = "ابدأ المغامرة!"
    st.session_state.status = "playing"
    load_level()


def check_guards(player, maze):
    for guard in maze.guards:
        if guard.position.same_as(player.position):
            player.lose_life(1)
            guard.go_home()
            st.session_state.message = "هجم عليك الوحش! خسرت قلباً."


def move_player(key):
    player = st.session_state.player
    maze = st.session_state.maze
    dr, dc = DIRECTIONS[key]
    target = player.position.moved(dr, dc)

    if not maze.is_inside(target) or maze.is_wall(target):
        st.session_state.message = "لا يمكنك المرور، يوجد جدار!"
        return

    item = maze.item_at(target)
    if item is not None and item.is_blocked(player):
        st.session_state.message = item.block_text()
        return

    player.position = target
    player.moves += 1
    check_guards(player, maze)

    if item is not None and player.is_alive():
        st.session_state.message = item.on_touch(player)
        if item.consumable:
            maze.items.remove(item)

    if player.reached_exit:
        bonus = player.lives * 10
        player.score += bonus
        if st.session_state.level_index < len(LEVELS) - 1:
            st.session_state.level_index += 1
            load_level()
            st.session_state.message = f"أكملت المرحلة! مكافأة +{bonus} نقطة."
        else:
            st.session_state.status = "won"
        return

    if player.is_alive():
        for guard in maze.guards:
            guard.move(maze)
        check_guards(player, maze)

    if not player.is_alive():
        st.session_state.status = "lost"


if "status" not in st.session_state:
    st.session_state.status = "menu"

with st.sidebar:
    st.title("🎓 مشروع الجامعة")
    st.write("🛠️ **فريق المطورين:**")
    for dev in DEVELOPERS:
        st.markdown(f"**{dev['name']}** ({dev['role']})")
        st.link_button("حساب التليجرام", dev["telegram"])
    st.markdown("---")
    st.caption("Maze Adventure Game - Python OOP")

if st.session_state.status == "menu":
    st.title("🎮 لعبة مغامرة المتاهة")
    names = " | ".join(d["name"] for d in DEVELOPERS)
    st.caption(f"تطوير: {names}")
    player_name = st.text_input("أدخل اسمك:", "البطل")
    if st.button("ابدأ اللعب", use_container_width=True):
        start_new_game(player_name)
        st.rerun()

elif st.session_state.status == "playing":
    player = st.session_state.player
    maze = st.session_state.maze
    st.title(f"مرحباً {player.name}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("المرحلة", st.session_state.level_index + 1)
    c2.metric("القلوب", "❤️" * player.lives)
    c3.metric("النقاط", player.score)
    c4.metric("المفاتيح", player.keys)

    st.info(st.session_state.message)
    st.markdown(maze.render_html(player), unsafe_allow_html=True)
    st.write("")

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button("⬆️ أعلى (W)", use_container_width=True):
            move_player("w")
            st.rerun()
        left_col, right_col = st.columns(2)
        with left_col:
            if st.button("⬅️ يسار (A)", use_container_width=True):
                move_player("a")
                st.rerun()
        with right_col:
            if st.button("➡️ يمين (D)", use_container_width=True):
                move_player("d")
                st.rerun()
        if st.button("⬇️ أسفل (S)", use_container_width=True):
            move_player("s")
            st.rerun()

    if st.button("إعادة البدء", use_container_width=True):
        st.session_state.status = "menu"
        st.rerun()

elif st.session_state.status == "won":
    player = st.session_state.player
    st.success(f"🏆 مبروك يا {player.name}! هربت من جميع المتاهات!")
    st.write(f"النقاط النهائية: **{player.score}** | عدد الحركات: **{player.moves}**")
    if st.button("العب مجدداً", use_container_width=True):
        start_new_game(player.name)
        st.rerun()

elif st.session_state.status == "lost":
    player = st.session_state.player
    st.error(f"💀 انتهت اللعبة يا {player.name}! نفدت قلوبك.")
    st.write(f"النقاط: **{player.score}** | عدد الحركات: **{player.moves}**")
    if st.button("حاول مجدداً", use_container_width=True):
        start_new_game(player.name)
        st.rerun()