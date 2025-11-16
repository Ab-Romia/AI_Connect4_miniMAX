"""
Connect 4 AI - Beautiful Interactive Interface with Live AI Thinking
Click anywhere on a column to drop your piece!
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
        return f"🔴 **Your Turn** - Click a column! | You: {p1} | AI: {p2}"
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

def process_click(state, evt: gr.SelectData):
    """Handle click - player move only"""
    if state is None:
        state = create_initial_state()

    if state['game_over'] or state['current_player'] != 1:
        return state, render_board(state), get_status(state)

    x = evt.index[0]
    col = x // CELL_SIZE

    if col < 0 or col > 6:
        return state, render_board(state), get_status(state)

    valid = state['board'].valid_moves()
    if col not in valid:
        return state, render_board(state), get_status(state)

    # Make player move immediately
    state = copy.deepcopy(state)
    state['board'].move(col, 1)
    check_winner(state)

    if not state['game_over']:
        state['current_player'] = 2

    return state, render_board(state), get_status(state)

def ai_analysis_step1(state):
    """AI thinking step 1"""
    if state is None or state['game_over'] or state['current_player'] != 2:
        return "Waiting for your move..."

    time.sleep(0.3)

    depth = state['ai_depth']
    valid = state['board'].valid_moves()

    text = "🧠 **AI ANALYSIS STARTED**\n\n"
    text += "```\n"
    text += f"Search Depth: {depth} moves\n"
    text += f"Evaluating: {len(valid)} columns\n"
    text += "```\n\n"
    text += "⏳ Computing position scores..."

    return text

def ai_analysis_step2(state):
    """AI thinking step 2 - column evaluation"""
    if state is None or state['game_over'] or state['current_player'] != 2:
        return "Waiting..."

    time.sleep(0.4)

    board = state['board']
    depth = state['ai_depth']
    valid = board.valid_moves()

    text = "🧠 **POSITION EVALUATION**\n\n"
    text += "```\n"

    for col in valid:
        board.move(col, 2)
        score = evaluate_board(board)
        board.undo(col, 2)

        bar_len = int(min(12, max(0, (score + 5000) / 850)))
        bar = "█" * bar_len + "░" * (12 - bar_len)
        text += f"Col {col+1}: [{bar}] {score:+,}\n"

    text += "```\n\n"
    text += "🔍 Running minimax with alpha-beta pruning..."

    return text

def ai_analysis_final(state):
    """AI thinking final step and make move"""
    if state is None or state['game_over'] or state['current_player'] != 2:
        return state, render_board(state) if state else None, get_status(state) if state else "", "Waiting..."

    time.sleep(0.5)

    state = copy.deepcopy(state)
    board = state['board']
    depth = state['ai_depth']
    valid = board.valid_moves()

    if not valid:
        state['game_over'] = True
        return state, render_board(state), get_status(state), "No valid moves!"

    # Get best move
    best_col, best_score = minimax(
        board, depth=depth,
        alpha=float('-inf'), beta=float('inf'),
        maximizing_player=True, return_tree=False
    )

    # Build final analysis text
    text = "🧠 **DECISION COMPLETE**\n\n"
    text += "**Column Scores:**\n```\n"

    for col in valid:
        board.move(col, 2)
        score = evaluate_board(board)
        board.undo(col, 2)
        bar_len = int(min(12, max(0, (score + 5000) / 850)))
        bar = "█" * bar_len + "░" * (12 - bar_len)
        marker = " ◄ BEST" if col == best_col else ""
        text += f"Col {col+1}: [{bar}] {score:+,}{marker}\n"

    text += "```\n\n"
    text += f"✅ **CHOSEN: Column {best_col + 1}**\n"
    text += f"💯 **Score: {best_score:+,}**\n\n"

    # Strategy
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

    text += f"Strategy: {strat}"

    # Make the move
    if best_col in valid:
        state['board'].move(best_col, 2)
        check_winner(state)
        if not state['game_over']:
            state['current_player'] = 1

    return state, render_board(state), get_status(state), text

def reset_game(difficulty):
    """Reset game"""
    state = create_initial_state()
    depth_map = {"Easy (2)": 2, "Medium (4)": 4, "Hard (6)": 6, "Expert (8)": 8}
    state['ai_depth'] = depth_map.get(difficulty, 4)

    welcome = f"🎮 **NEW GAME - {difficulty}**\n\n"
    welcome += "🔴 You are **RED**\n"
    welcome += "🟡 AI is **YELLOW**\n\n"
    welcome += "**Click anywhere on a column** to drop!\n\n"
    welcome += "Watch the AI think in real-time!"

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
    cursor: pointer !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    animation: slideIn 0.5s ease-out !important;
}

.board-wrapper img:hover {
    transform: scale(1.03) translateY(-5px) !important;
    box-shadow: 0 40px 120px rgba(0, 0, 0, 0.8), 0 0 100px rgba(26, 60, 138, 0.5) !important;
}

.board-wrapper img:active {
    transform: scale(0.98) !important;
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
    transition: all 0.3s ease !important;
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
    transition: all 0.3s ease !important;
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

button:active {
    transform: translateY(-2px) scale(0.98) !important;
}

label, .label-wrap span {
    color: #b0c4e8 !important;
    font-weight: 500 !important;
}

footer { display: none !important; }

/* Remove image toolbar */
.image-frame > div:last-child {
    display: none !important;
}
"""

# Build interface
with gr.Blocks(title="Connect 4 AI", css=css, theme=gr.themes.Base()) as demo:

    state = gr.State(create_initial_state())

    gr.Markdown("""
    # 🎮 CONNECT 4 AI
    ### Click on the board to play • Watch AI think in real-time!
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
                value="Click on the board to make your move!\n\nWatch the AI's real-time analysis here.",
                elem_classes=["thinking-panel"]
            )

            with gr.Group(elem_classes=["info-panel"]):
                gr.Markdown("""
                ### 📖 How to Play

                **Click directly on any column** to drop your piece!

                - 🔴 **You** = Red
                - 🟡 **AI** = Yellow
                - Connect 4: ↔️ ↕️ ↗️ ↘️
                - Vertical = **11× bonus!**
                - Most points = **WIN**

                AI uses minimax with alpha-beta pruning to find optimal moves!
                """)

    # Event chain: Click -> Player move -> AI thinks (3 steps) -> AI moves
    board_img.select(
        fn=process_click,
        inputs=[state],
        outputs=[state, board_img, status_box]
    ).then(
        fn=ai_analysis_step1,
        inputs=[state],
        outputs=[thinking_box]
    ).then(
        fn=ai_analysis_step2,
        inputs=[state],
        outputs=[thinking_box]
    ).then(
        fn=ai_analysis_final,
        inputs=[state],
        outputs=[state, board_img, status_box, thinking_box]
    )

    new_game_btn.click(
        fn=reset_game,
        inputs=[difficulty],
        outputs=[state, board_img, status_box, thinking_box]
    )

    demo.load(
        fn=lambda: reset_game("Medium (4)"),
        outputs=[state, board_img, status_box, thinking_box]
    )

if __name__ == "__main__":
    demo.launch()
