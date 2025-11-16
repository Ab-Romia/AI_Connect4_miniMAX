"""
Connect 4 AI - Beautiful Interactive Interface with Live AI Thinking
Click anywhere on a column to drop your piece!
"""

import gradio as gr
from Board import Connect4Board
from MiniMax import minimax, evaluate_board
import copy
from PIL import Image, ImageDraw, ImageFont

# Visual constants
CELL_SIZE = 85
PADDING = 12
BOARD_WIDTH = 7 * CELL_SIZE
BOARD_HEIGHT = 6 * CELL_SIZE

# Colors (RGB)
COLORS = {
    'board': (26, 60, 138),      # Deep blue
    'board_dark': (20, 45, 105),  # Darker blue for gradient
    'empty': (35, 50, 85),        # Dark slot
    'player1': (255, 71, 87),     # Vibrant red
    'player2': (255, 193, 7),     # Golden yellow
    'highlight': (100, 200, 255), # Light blue highlight
    'shadow': (15, 30, 60),       # Dark shadow
}

def create_initial_state():
    """Create initial game state"""
    return {
        'board': Connect4Board(),
        'current_player': 1,
        'game_over': False,
        'ai_depth': 4,
        'winner': None,
    }

def render_board(state):
    """Render beautiful board as image"""
    board = state['board']

    # Create image with gradient background
    img = Image.new('RGB', (BOARD_WIDTH, BOARD_HEIGHT), COLORS['board'])
    draw = ImageDraw.Draw(img)

    # Add subtle gradient effect
    for y in range(BOARD_HEIGHT):
        alpha = y / BOARD_HEIGHT
        r = int(COLORS['board'][0] * (1 - alpha * 0.3) + COLORS['board_dark'][0] * alpha * 0.3)
        g = int(COLORS['board'][1] * (1 - alpha * 0.3) + COLORS['board_dark'][1] * alpha * 0.3)
        b = int(COLORS['board'][2] * (1 - alpha * 0.3) + COLORS['board_dark'][2] * alpha * 0.3)
        draw.line([(0, y), (BOARD_WIDTH, y)], fill=(r, g, b))

    # Draw cells
    for row in range(6):
        for col in range(7):
            display_row = 5 - row
            cx = col * CELL_SIZE + CELL_SIZE // 2
            cy = display_row * CELL_SIZE + CELL_SIZE // 2
            radius = CELL_SIZE // 2 - PADDING

            # Determine piece color
            bit_pos = 1 << (row * 7 + col)
            if board.player1 & bit_pos:
                color = COLORS['player1']
            elif board.player2 & bit_pos:
                color = COLORS['player2']
            else:
                color = COLORS['empty']

            # Draw shadow
            draw.ellipse([
                cx - radius + 3, cy - radius + 3,
                cx + radius + 3, cy + radius + 3
            ], fill=COLORS['shadow'])

            # Draw main piece
            draw.ellipse([
                cx - radius, cy - radius,
                cx + radius, cy + radius
            ], fill=color)

            # Add shine effect for colored pieces
            if color != COLORS['empty']:
                shine_radius = radius // 4
                shine_x = cx - radius // 2
                shine_y = cy - radius // 2
                # Create highlight
                for i in range(shine_radius):
                    alpha = 1 - (i / shine_radius)
                    highlight = (
                        min(255, int(color[0] + 80 * alpha)),
                        min(255, int(color[1] + 80 * alpha)),
                        min(255, int(color[2] + 80 * alpha))
                    )
                    draw.ellipse([
                        shine_x - i, shine_y - i,
                        shine_x + shine_radius - i, shine_y + shine_radius - i
                    ], fill=highlight)

    return img

def get_status(state):
    """Get game status text"""
    p1 = state['board'].connect_4s(1)
    p2 = state['board'].connect_4s(2)

    if state['game_over']:
        if state['winner'] == 1:
            return f"🎉 **YOU WIN!** | Final: You {p1} - {p2} AI"
        elif state['winner'] == 2:
            return f"🤖 **AI WINS!** | Final: You {p1} - {p2} AI"
        else:
            return f"🤝 **DRAW!** | Final: You {p1} - {p2} AI"
    elif state['current_player'] == 1:
        return f"🔴 **Your Turn** - Click any column! | You: {p1} - AI: {p2}"
    else:
        return f"🟡 **AI Playing...** | You: {p1} - AI: {p2}"

def check_winner(state):
    """Check if game is over"""
    p1 = state['board'].connect_4s(1)
    p2 = state['board'].connect_4s(2)

    if not state['board'].valid_moves():
        state['game_over'] = True
        if p1 > p2:
            state['winner'] = 1
        elif p2 > p1:
            state['winner'] = 2
        else:
            state['winner'] = 0
    return state

def click_column(state, evt: gr.SelectData):
    """Handle click on board - get column from click position"""
    if state['game_over'] or state['current_player'] != 1:
        return state, render_board(state), get_status(state), "Game over or not your turn"

    # Calculate column from x coordinate
    x = evt.index[0]
    col = x // CELL_SIZE

    if col < 0 or col > 6:
        return state, render_board(state), get_status(state), "Click on the board"

    valid = state['board'].valid_moves()
    if col not in valid:
        return state, render_board(state), get_status(state), f"❌ Column {col+1} is full!"

    # Make player move
    state = copy.deepcopy(state)
    state['board'].move(col, 1)
    check_winner(state)

    if state['game_over']:
        return state, render_board(state), get_status(state), "🎮 Game Over!"

    state['current_player'] = 2
    return state, render_board(state), get_status(state), "🤖 AI analyzing your move..."

def ai_think_step1(state):
    """First step of AI thinking - show initial analysis"""
    if state['game_over'] or state['current_player'] != 2:
        return "Waiting for your move..."

    depth = state['ai_depth']
    valid = state['board'].valid_moves()

    text = "🧠 **INITIALIZING AI ANALYSIS...**\n\n"
    text += f"```\n"
    text += f"Search Depth: {depth} moves ahead\n"
    text += f"Valid Columns: {len(valid)}\n"
    text += f"```\n\n"
    text += "⏳ Evaluating positions..."

    return text

def ai_think_step2(state):
    """Second step - evaluate each column"""
    if state['game_over'] or state['current_player'] != 2:
        return "Waiting..."

    board = state['board']
    depth = state['ai_depth']
    valid = board.valid_moves()

    text = "🧠 **AI POSITION ANALYSIS**\n\n"
    text += f"📊 Depth: {depth} | Columns: {len(valid)}\n\n"
    text += "**Column Evaluations:**\n```\n"

    for col in valid:
        board.move(col, 2)
        score = evaluate_board(board)
        board.undo(col, 2)

        # Create visual bar
        bar_len = int(min(15, max(0, (score + 5000) / 700)))
        bar = "█" * bar_len + "░" * (15 - bar_len)
        text += f"Col {col+1}: [{bar}] {score:+,}\n"

    text += "```\n\n"
    text += "🔍 Running deep minimax search..."

    return text

def ai_think_step3(state):
    """Third step - show final decision"""
    if state['game_over'] or state['current_player'] != 2:
        return "Waiting..."

    board = state['board']
    depth = state['ai_depth']
    valid = board.valid_moves()

    # Do the actual search
    best_col, best_score = minimax(
        board, depth=depth,
        alpha=float('-inf'), beta=float('inf'),
        maximizing_player=True, return_tree=False
    )

    text = "🧠 **AI DECISION COMPLETE**\n\n"
    text += f"📊 Depth: {depth} moves\n\n"
    text += "**Position Scores:**\n```\n"

    for col in valid:
        board.move(col, 2)
        score = evaluate_board(board)
        board.undo(col, 2)
        bar_len = int(min(15, max(0, (score + 5000) / 700)))
        bar = "█" * bar_len + "░" * (15 - bar_len)
        marker = " ◄── BEST" if col == best_col else ""
        text += f"Col {col+1}: [{bar}] {score:+,}{marker}\n"

    text += "```\n\n"
    text += f"✅ **CHOSEN: Column {best_col + 1}**\n"
    text += f"💯 **Score: {best_score:+,}**\n\n"

    # Strategy explanation
    if best_score > 100000:
        strategy = "🎯 **WINNING MOVE!**"
    elif best_score > 10000:
        strategy = "💪 **Strong Offensive**"
    elif best_score > 1000:
        strategy = "📈 **Building Position**"
    elif best_score > 0:
        strategy = "⚖️ **Slight Advantage**"
    elif best_score > -5000:
        strategy = "🛡️ **Defensive Play**"
    else:
        strategy = "⚠️ **Damage Control**"

    text += f"Strategy: {strategy}"

    return text

def ai_make_move(state):
    """Actually make the AI move"""
    if state['game_over'] or state['current_player'] != 2:
        return state, render_board(state), get_status(state)

    state = copy.deepcopy(state)
    board = state['board']
    valid = board.valid_moves()

    if not valid:
        state['game_over'] = True
        return state, render_board(state), get_status(state)

    best_col, _ = minimax(
        board, depth=state['ai_depth'],
        alpha=float('-inf'), beta=float('inf'),
        maximizing_player=True, return_tree=False
    )

    if best_col in valid:
        state['board'].move(best_col, 2)
        check_winner(state)
        if not state['game_over']:
            state['current_player'] = 1

    return state, render_board(state), get_status(state)

def reset_game(difficulty):
    """Start new game"""
    state = create_initial_state()
    depth_map = {"Easy (2)": 2, "Medium (4)": 4, "Hard (6)": 6, "Expert (8)": 8}
    state['ai_depth'] = depth_map.get(difficulty, 4)

    welcome = f"🎮 **NEW GAME STARTED!**\n\n"
    welcome += f"**Difficulty:** {difficulty}\n\n"
    welcome += "🔴 You are **RED**\n"
    welcome += "🟡 AI is **YELLOW**\n\n"
    welcome += "**Click anywhere on a column** to drop your piece!\n\n"
    welcome += "Watch the AI's thought process as it analyzes each move!"

    return state, render_board(state), get_status(state), welcome

# Custom CSS for dark theme
css = """
.gradio-container {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important;
}

.board-image {
    border-radius: 20px !important;
    box-shadow: 0 25px 80px rgba(0, 0, 0, 0.6), 0 0 60px rgba(26, 60, 138, 0.3) !important;
    cursor: pointer !important;
    transition: transform 0.2s ease !important;
}

.board-image:hover {
    transform: scale(1.02) !important;
}

.status-bar {
    background: linear-gradient(90deg, #667eea, #764ba2) !important;
    padding: 20px !important;
    border-radius: 15px !important;
    color: white !important;
    font-size: 1.3em !important;
    text-align: center !important;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5) !important;
    margin: 15px 0 !important;
}

.thinking-panel {
    background: #0a0f1a !important;
    border: 3px solid #00ff88 !important;
    border-radius: 15px !important;
    padding: 25px !important;
    color: #00ff88 !important;
    font-family: 'Fira Code', 'Courier New', monospace !important;
    font-size: 1.05em !important;
    line-height: 1.8 !important;
    min-height: 400px !important;
    box-shadow: 0 0 40px rgba(0, 255, 136, 0.2), inset 0 0 60px rgba(0, 255, 136, 0.05) !important;
    overflow-y: auto !important;
}

.control-area {
    background: rgba(255, 255, 255, 0.05) !important;
    padding: 20px !important;
    border-radius: 15px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.info-panel {
    background: rgba(255, 255, 255, 0.08) !important;
    padding: 20px !important;
    border-radius: 12px !important;
    color: #c8d4e8 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
}

h1, h2, h3 {
    color: #00d4ff !important;
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.3) !important;
}

button.primary {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    font-weight: bold !important;
    font-size: 1.1em !important;
}

button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3) !important;
}

label {
    color: #a8b8d8 !important;
}

footer { display: none !important; }
"""

# Build the interface
with gr.Blocks(title="Connect 4 AI", css=css, theme=gr.themes.Base()) as demo:

    state = gr.State(create_initial_state())

    gr.Markdown("# 🎮 CONNECT 4 AI\n### Click on the board to play - Watch the AI think in real-time!")

    with gr.Row():
        # Left: Game board
        with gr.Column(scale=3):
            board_img = gr.Image(
                value=render_board(create_initial_state()),
                label=None,
                show_label=False,
                height=520,
                width=595,
                interactive=False,
                show_download_button=False,
                show_fullscreen_button=False,
                elem_classes=["board-image"]
            )

            status = gr.Markdown(
                value=get_status(create_initial_state()),
                elem_classes=["status-bar"]
            )

            with gr.Group(elem_classes=["control-area"]):
                with gr.Row():
                    difficulty = gr.Dropdown(
                        choices=["Easy (2)", "Medium (4)", "Hard (6)", "Expert (8)"],
                        value="Medium (4)",
                        label="🎯 AI Difficulty",
                        scale=2
                    )
                    new_game = gr.Button("🔄 New Game", variant="primary", scale=1, size="lg")

        # Right: AI thinking
        with gr.Column(scale=2):
            gr.Markdown("### 🧠 AI Thought Process")
            thinking = gr.Markdown(
                value="Click on the board to make your move!\n\nThe AI will show its analysis here in real-time.",
                elem_classes=["thinking-panel"]
            )

            with gr.Group(elem_classes=["info-panel"]):
                gr.Markdown("""
                ### 📖 How to Play

                **Click directly on any column** to drop your piece!

                - 🔴 **You** = Red pieces
                - 🟡 **AI** = Yellow pieces
                - Connect 4 in a row: ↔️ ↕️ ↗️ ↘️
                - Vertical connects = **11x bonus!**
                - Most points when board fills = **WIN**

                The AI analyzes positions using minimax with alpha-beta pruning!
                """)

    # Event handling: Click board -> Player move -> AI thinks progressively -> AI moves
    board_img.select(
        fn=click_column,
        inputs=[state],
        outputs=[state, board_img, status, thinking]
    ).success(
        fn=ai_think_step1,
        inputs=[state],
        outputs=[thinking]
    ).success(
        fn=lambda: None,  # Small delay
        inputs=None,
        outputs=None,
        js="() => new Promise(r => setTimeout(r, 400))"
    ).success(
        fn=ai_think_step2,
        inputs=[state],
        outputs=[thinking]
    ).success(
        fn=lambda: None,
        inputs=None,
        outputs=None,
        js="() => new Promise(r => setTimeout(r, 600))"
    ).success(
        fn=ai_think_step3,
        inputs=[state],
        outputs=[thinking]
    ).success(
        fn=lambda: None,
        inputs=None,
        outputs=None,
        js="() => new Promise(r => setTimeout(r, 500))"
    ).success(
        fn=ai_make_move,
        inputs=[state],
        outputs=[state, board_img, status]
    )

    new_game.click(
        fn=reset_game,
        inputs=[difficulty],
        outputs=[state, board_img, status, thinking]
    )

    demo.load(
        fn=lambda: reset_game("Medium (4)"),
        outputs=[state, board_img, status, thinking]
    )

if __name__ == "__main__":
    demo.launch()
