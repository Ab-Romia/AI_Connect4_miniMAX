"""
Connect 4 AI - Beautiful Interactive Interface with Live AI Thinking
"""

import gradio as gr
from Board import Connect4Board
from MiniMax import minimax, evaluate_board
import copy
import time
from PIL import Image, ImageDraw

# Visual constants - LARGER BOARD
CELL_SIZE = 100
PADDING = 14
BOARD_WIDTH = 7 * CELL_SIZE
BOARD_HEIGHT = 6 * CELL_SIZE

# Colors (RGB)
COLORS = {
    'board': (26, 60, 138),
    'board_dark': (18, 42, 98),
    'empty': (40, 55, 90),
    'player1': (255, 71, 87),
    'player2': (255, 193, 7),
    'shadow': (12, 25, 50),
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
    """Render beautiful large board as image"""
    board = state['board']

    img = Image.new('RGB', (BOARD_WIDTH, BOARD_HEIGHT), COLORS['board'])
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(BOARD_HEIGHT):
        t = y / BOARD_HEIGHT
        r = int(COLORS['board'][0] * (1 - t * 0.4) + COLORS['board_dark'][0] * t * 0.4)
        g = int(COLORS['board'][1] * (1 - t * 0.4) + COLORS['board_dark'][1] * t * 0.4)
        b = int(COLORS['board'][2] * (1 - t * 0.4) + COLORS['board_dark'][2] * t * 0.4)
        draw.line([(0, y), (BOARD_WIDTH, y)], fill=(r, g, b))

    # Draw cells
    for row in range(6):
        for col in range(7):
            display_row = 5 - row
            cx = col * CELL_SIZE + CELL_SIZE // 2
            cy = display_row * CELL_SIZE + CELL_SIZE // 2
            radius = CELL_SIZE // 2 - PADDING

            bit_pos = 1 << (row * 7 + col)
            if board.player1 & bit_pos:
                color = COLORS['player1']
            elif board.player2 & bit_pos:
                color = COLORS['player2']
            else:
                color = COLORS['empty']

            # Shadow
            draw.ellipse([
                cx - radius + 4, cy - radius + 4,
                cx + radius + 4, cy + radius + 4
            ], fill=COLORS['shadow'])

            # Main piece
            draw.ellipse([
                cx - radius, cy - radius,
                cx + radius, cy + radius
            ], fill=color)

            # Shine effect
            if color != COLORS['empty']:
                shine_r = radius // 3
                for i in range(shine_r, 0, -1):
                    alpha = i / shine_r
                    highlight = (
                        min(255, int(color[0] + 100 * alpha)),
                        min(255, int(color[1] + 100 * alpha)),
                        min(255, int(color[2] + 100 * alpha))
                    )
                    draw.ellipse([
                        cx - radius // 2 - i, cy - radius // 2 - i,
                        cx - radius // 2 + shine_r - i, cy - radius // 2 + shine_r - i
                    ], fill=highlight)

    return img

def get_status(state):
    """Get game status"""
    p1 = state['board'].connect_4s(1)
    p2 = state['board'].connect_4s(2)

    if state['game_over']:
        if state['winner'] == 1:
            return f"🎉 **YOU WIN!** | Final Score - You: {p1} | AI: {p2}"
        elif state['winner'] == 2:
            return f"🤖 **AI WINS!** | Final Score - You: {p1} | AI: {p2}"
        else:
            return f"🤝 **DRAW!** | Final Score - You: {p1} | AI: {p2}"
    elif state['current_player'] == 1:
        return f"🔴 **Your Turn** - Click a column below! | You: {p1} | AI: {p2}"
    else:
        return f"🟡 **AI Analyzing...** | You: {p1} | AI: {p2}"

def check_winner(state):
    """Check if game over"""
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

def play_move(col, state):
    """Handle player move and AI response with progressive thinking"""
    if state is None:
        state = create_initial_state()

    if state['game_over'] or state['current_player'] != 1:
        return state, render_board(state), get_status(state), "Not your turn or game is over."

    valid = state['board'].valid_moves()
    if col not in valid:
        return state, render_board(state), get_status(state), f"❌ Column {col+1} is full!"

    # Make player move
    state = copy.deepcopy(state)
    state['board'].move(col, 1)
    check_winner(state)

    if state['game_over']:
        return state, render_board(state), get_status(state), "🎮 Game Over! You made a great move!"

    state['current_player'] = 2

    # Now do AI analysis with progressive display
    board = state['board']
    depth = state['ai_depth']
    valid_moves = board.valid_moves()

    if not valid_moves:
        state['game_over'] = True
        return state, render_board(state), get_status(state), "No valid moves for AI!"

    # Build progressive thinking display
    thinking = "🧠 **AI ANALYSIS**\n\n"
    thinking += f"```\nSearch Depth: {depth} moves\nEvaluating: {len(valid_moves)} columns\n```\n\n"

    # Evaluate each column
    thinking += "**Position Scores:**\n```\n"
    for c in valid_moves:
        board.move(c, 2)
        score = evaluate_board(board)
        board.undo(c, 2)
        bar_len = int(min(12, max(0, (score + 5000) / 850)))
        bar = "█" * bar_len + "░" * (12 - bar_len)
        thinking += f"Col {c+1}: [{bar}] {score:+,}\n"
    thinking += "```\n\n"

    # Get best move with minimax
    thinking += "🔍 **Minimax Search Complete**\n\n"
    best_col, best_score = minimax(
        board, depth=depth,
        alpha=float('-inf'), beta=float('inf'),
        maximizing_player=True, return_tree=False
    )

    thinking += f"✅ **CHOSEN: Column {best_col + 1}**\n"
    thinking += f"💯 **Score: {best_score:+,}**\n\n"

    # Strategy explanation
    if best_score > 100000:
        strat = "🎯 **WINNING MOVE!**"
    elif best_score > 10000:
        strat = "💪 **Strong Attack**"
    elif best_score > 1000:
        strat = "📈 **Building Position**"
    elif best_score > 0:
        strat = "⚖️ **Slight Edge**"
    elif best_score > -5000:
        strat = "🛡️ **Defensive**"
    else:
        strat = "⚠️ **Damage Control**"

    thinking += f"Strategy: {strat}"

    # Make AI move
    if best_col in valid_moves:
        state['board'].move(best_col, 2)
        check_winner(state)
        if not state['game_over']:
            state['current_player'] = 1

    return state, render_board(state), get_status(state), thinking

def reset_game(difficulty):
    """Reset game"""
    state = create_initial_state()
    depth_map = {"Easy (2)": 2, "Medium (4)": 4, "Hard (6)": 6, "Expert (8)": 8}
    state['ai_depth'] = depth_map.get(difficulty, 4)

    welcome = f"🎮 **NEW GAME - {difficulty}**\n\n"
    welcome += "🔴 You are **RED**\n"
    welcome += "🟡 AI is **YELLOW**\n\n"
    welcome += "**Click a column button below** to drop your piece!\n\n"
    welcome += "Watch the AI's thought process as it analyzes each move!"

    return state, render_board(state), get_status(state), welcome

# CSS with animations
css = """
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 40px rgba(0, 255, 136, 0.2); }
    50% { box-shadow: 0 0 60px rgba(0, 255, 136, 0.4); }
}

@keyframes slideIn {
    from { transform: scale(0.95); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

.gradio-container {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important;
    min-height: 100vh !important;
}

.board-wrapper img {
    border-radius: 25px !important;
    box-shadow: 0 30px 100px rgba(0, 0, 0, 0.7), 0 0 80px rgba(26, 60, 138, 0.4) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    animation: slideIn 0.5s ease-out !important;
}

.board-wrapper:hover img {
    transform: scale(1.02) translateY(-3px) !important;
    box-shadow: 0 40px 120px rgba(0, 0, 0, 0.8), 0 0 100px rgba(26, 60, 138, 0.5) !important;
}

.status-bar {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    padding: 22px 30px !important;
    border-radius: 18px !important;
    color: white !important;
    font-size: 1.4em !important;
    text-align: center !important;
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.6) !important;
    margin: 20px 0 !important;
    animation: fadeIn 0.5s ease-out !important;
}

.thinking-panel {
    background: linear-gradient(180deg, #0a0f1a 0%, #0d1420 100%) !important;
    border: 3px solid #00ff88 !important;
    border-radius: 18px !important;
    padding: 28px !important;
    color: #00ff88 !important;
    font-family: 'Fira Code', 'SF Mono', 'Consolas', monospace !important;
    font-size: 1.1em !important;
    line-height: 1.9 !important;
    min-height: 450px !important;
    box-shadow: 0 0 50px rgba(0, 255, 136, 0.25) !important;
    animation: pulse 3s infinite !important;
    overflow-y: auto !important;
}

.column-buttons {
    display: flex !important;
    gap: 12px !important;
    justify-content: center !important;
    margin: 15px 0 !important;
}

.column-btn {
    width: 90px !important;
    height: 60px !important;
    font-size: 1.4em !important;
    font-weight: bold !important;
    border-radius: 15px !important;
    background: linear-gradient(180deg, #3a7bd5, #00d2ff) !important;
    color: white !important;
    border: none !important;
    cursor: pointer !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 8px 25px rgba(0, 210, 255, 0.3) !important;
}

.column-btn:hover {
    transform: translateY(-6px) scale(1.08) !important;
    box-shadow: 0 15px 35px rgba(0, 210, 255, 0.5) !important;
    background: linear-gradient(180deg, #00d2ff, #3a7bd5) !important;
}

.column-btn:active {
    transform: translateY(-2px) scale(0.95) !important;
}

.control-area {
    background: rgba(255, 255, 255, 0.06) !important;
    padding: 25px !important;
    border-radius: 18px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    backdrop-filter: blur(10px) !important;
}

.info-panel {
    background: rgba(255, 255, 255, 0.08) !important;
    padding: 22px !important;
    border-radius: 15px !important;
    color: #d0daf0 !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    margin-top: 20px !important;
}

h1, h2, h3 {
    color: #00d4ff !important;
    text-shadow: 0 0 30px rgba(0, 212, 255, 0.4) !important;
}

button {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

button.primary {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    font-weight: bold !important;
    font-size: 1.15em !important;
    padding: 12px 28px !important;
}

button:hover {
    transform: translateY(-4px) scale(1.02) !important;
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.4) !important;
}

label, .label-wrap span {
    color: #b0c4e8 !important;
    font-weight: 500 !important;
}

footer { display: none !important; }

/* Hide image toolbar */
.image-frame > div:last-child {
    display: none !important;
}
"""

# Build interface
with gr.Blocks(title="Connect 4 AI", css=css, theme=gr.themes.Base()) as demo:

    state = gr.State(create_initial_state())

    gr.Markdown("""
    # 🎮 CONNECT 4 AI
    ### Beautiful Board • Smart AI • Real-time Analysis
    """)

    with gr.Row():
        with gr.Column(scale=3):
            board_img = gr.Image(
                value=render_board(create_initial_state()),
                label=None,
                show_label=False,
                height=620,
                width=700,
                interactive=False,
                show_download_button=False,
                show_fullscreen_button=False,
                elem_classes=["board-wrapper"]
            )

            # Column selection buttons
            gr.Markdown("### 👇 Click a Column to Drop Your Piece", elem_classes=["column-label"])
            with gr.Row(elem_classes=["column-buttons"]):
                btn1 = gr.Button("1", elem_classes=["column-btn"])
                btn2 = gr.Button("2", elem_classes=["column-btn"])
                btn3 = gr.Button("3", elem_classes=["column-btn"])
                btn4 = gr.Button("4", elem_classes=["column-btn"])
                btn5 = gr.Button("5", elem_classes=["column-btn"])
                btn6 = gr.Button("6", elem_classes=["column-btn"])
                btn7 = gr.Button("7", elem_classes=["column-btn"])

            status_box = gr.Markdown(
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
                    new_game_btn = gr.Button("🔄 New Game", variant="primary", scale=1, size="lg")

        with gr.Column(scale=2):
            gr.Markdown("### 🧠 AI Thought Process")

            thinking_box = gr.Markdown(
                value="Click a column button to make your move!\n\nWatch the AI's real-time analysis here.",
                elem_classes=["thinking-panel"]
            )

            with gr.Group(elem_classes=["info-panel"]):
                gr.Markdown("""
                ### 📖 How to Play

                **Click the numbered buttons** to drop your piece in that column!

                - 🔴 **You** = Red
                - 🟡 **AI** = Yellow
                - Connect 4: ↔️ ↕️ ↗️ ↘️
                - Vertical = **11× bonus!**
                - Most points = **WIN**

                AI uses minimax with alpha-beta pruning!
                """)

    # Wire up column buttons
    outputs = [state, board_img, status_box, thinking_box]

    btn1.click(fn=lambda s: play_move(0, s), inputs=[state], outputs=outputs)
    btn2.click(fn=lambda s: play_move(1, s), inputs=[state], outputs=outputs)
    btn3.click(fn=lambda s: play_move(2, s), inputs=[state], outputs=outputs)
    btn4.click(fn=lambda s: play_move(3, s), inputs=[state], outputs=outputs)
    btn5.click(fn=lambda s: play_move(4, s), inputs=[state], outputs=outputs)
    btn6.click(fn=lambda s: play_move(5, s), inputs=[state], outputs=outputs)
    btn7.click(fn=lambda s: play_move(6, s), inputs=[state], outputs=outputs)

    new_game_btn.click(
        fn=reset_game,
        inputs=[difficulty],
        outputs=outputs
    )

    demo.load(
        fn=lambda: reset_game("Medium (4)"),
        outputs=outputs
    )

if __name__ == "__main__":
    demo.launch()
