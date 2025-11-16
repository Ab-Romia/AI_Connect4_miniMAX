"""
Connect 4 AI - Interactive Gradio Interface with Progressive AI Thinking
"""

import gradio as gr
from Board import Connect4Board
from MiniMax import minimax, evaluate_board
import copy
import time
from PIL import Image, ImageDraw

# Constants for board rendering
CELL_SIZE = 80
BOARD_COLOR = (30, 60, 114)  # Deep blue
EMPTY_COLOR = (44, 62, 80)   # Dark gray-blue
PLAYER1_COLOR = (255, 71, 87)  # Vibrant red
PLAYER2_COLOR = (255, 165, 2)  # Vibrant yellow/orange
HIGHLIGHT_COLOR = (100, 255, 218)  # Cyan highlight

def create_initial_state():
    """Create initial game state"""
    return {
        'board': Connect4Board(),
        'current_player': 1,
        'game_over': False,
        'ai_depth': 4,
        'winner': None,
        'last_move': None
    }

def render_board_image(state, hover_col=-1):
    """Render the board as an image"""
    board = state['board']
    width = 7 * CELL_SIZE
    height = 6 * CELL_SIZE

    # Create image with board color
    img = Image.new('RGB', (width, height), BOARD_COLOR)
    draw = ImageDraw.Draw(img)

    # Draw column highlight if hovering
    if hover_col >= 0 and not state['game_over'] and state['current_player'] == 1:
        x = hover_col * CELL_SIZE
        draw.rectangle([x, 0, x + CELL_SIZE, height], fill=(40, 80, 140))

    # Draw cells
    for row in range(6):
        for col in range(7):
            # Calculate center position (row 0 is bottom, but we draw from top)
            display_row = 5 - row
            cx = col * CELL_SIZE + CELL_SIZE // 2
            cy = display_row * CELL_SIZE + CELL_SIZE // 2
            radius = CELL_SIZE // 2 - 8

            # Determine piece color
            bit_position = 1 << (row * 7 + col)
            if board.player1 & bit_position:
                color = PLAYER1_COLOR
            elif board.player2 & bit_position:
                color = PLAYER2_COLOR
            else:
                color = EMPTY_COLOR

            # Draw piece with slight 3D effect
            # Shadow
            draw.ellipse([cx - radius + 2, cy - radius + 2,
                         cx + radius + 2, cy + radius + 2],
                        fill=(20, 40, 60))
            # Main piece
            draw.ellipse([cx - radius, cy - radius,
                         cx + radius, cy + radius],
                        fill=color)
            # Highlight
            if color != EMPTY_COLOR:
                highlight_radius = radius // 3
                draw.ellipse([cx - radius + 10, cy - radius + 10,
                             cx - radius + 10 + highlight_radius,
                             cy - radius + 10 + highlight_radius],
                            fill=(255, 255, 255, 100))

    return img

def check_winner(state):
    """Check for winner"""
    p1_score = state['board'].connect_4s(1)
    p2_score = state['board'].connect_4s(2)

    if not state['board'].valid_moves():
        state['game_over'] = True
        if p1_score > p2_score:
            state['winner'] = 1
        elif p2_score > p1_score:
            state['winner'] = 2
        else:
            state['winner'] = 0
    return state

def get_status(state):
    """Get current game status"""
    p1_score = state['board'].connect_4s(1)
    p2_score = state['board'].connect_4s(2)

    if state['game_over']:
        if state['winner'] == 1:
            status = "🎉 YOU WIN!"
        elif state['winner'] == 2:
            status = "🤖 AI WINS!"
        else:
            status = "🤝 DRAW!"
    elif state['current_player'] == 1:
        status = "🔴 Your Turn - Click a column!"
    else:
        status = "🟡 AI Thinking..."

    return f"{status} | Score - You: {p1_score} | AI: {p2_score}"

def handle_click(state, evt: gr.SelectData):
    """Handle click on the board image"""
    if state['game_over'] or state['current_player'] != 1:
        return state, render_board_image(state), get_status(state), "Not your turn"

    # Get column from click position
    col = evt.index[0] // CELL_SIZE

    if col < 0 or col > 6:
        return state, render_board_image(state), get_status(state), "Invalid click"

    valid_moves = state['board'].valid_moves()
    if col not in valid_moves:
        return state, render_board_image(state), get_status(state), "❌ Column is full!"

    state = copy.deepcopy(state)

    # Make player move
    state['board'].move(col, 1)
    state['last_move'] = (col, 1)
    check_winner(state)

    if state['game_over']:
        return state, render_board_image(state), get_status(state), "🎮 Game Over!"

    state['current_player'] = 2
    return state, render_board_image(state), get_status(state), "🤖 AI analyzing..."

def ai_thinking_generator(state):
    """Generator that yields progressive AI thinking updates"""
    if state['game_over'] or state['current_player'] != 2:
        yield "Waiting for your move..."
        return

    board = state['board']
    depth = state['ai_depth']
    valid_moves = board.valid_moves()

    # Phase 1: Initial analysis
    yield "🧠 **AI ANALYSIS STARTING...**\n\n"
    time.sleep(0.3)

    yield f"🧠 **AI ANALYSIS STARTING...**\n\n📊 Search Depth: {depth} moves ahead\n"
    time.sleep(0.2)

    yield f"🧠 **AI ANALYSIS STARTING...**\n\n📊 Search Depth: {depth} moves ahead\n🎯 Evaluating {len(valid_moves)} possible columns...\n\n"
    time.sleep(0.3)

    # Phase 2: Evaluate each column
    log = f"🧠 **AI ANALYSIS STARTING...**\n\n📊 Search Depth: {depth} moves ahead\n🎯 Evaluating {len(valid_moves)} possible columns...\n\n"
    log += "─" * 35 + "\n\n"

    move_scores = []
    for col in valid_moves:
        board.move(col, 2)
        score = evaluate_board(board)
        board.undo(col, 2)
        move_scores.append((col, score))

        # Visual bar
        bar_len = int(min(15, max(0, (score + 5000) / 700)))
        bar = "█" * bar_len + "░" * (15 - bar_len)

        log += f"Col {col + 1}: [{bar}] {score:+,}\n"
        yield log
        time.sleep(0.15)

    log += "\n" + "─" * 35 + "\n\n"
    log += "🔍 **DEEP MINIMAX SEARCH...**\n\n"
    yield log
    time.sleep(0.4)

    # Phase 3: Deep search
    best_col, best_score = minimax(
        board,
        depth=depth,
        alpha=float('-inf'),
        beta=float('inf'),
        maximizing_player=True,
        return_tree=False
    )

    log += f"✅ **DECISION MADE!**\n\n"
    yield log
    time.sleep(0.2)

    log += f"📍 Best Column: **{best_col + 1}**\n"
    yield log
    time.sleep(0.2)

    log += f"💯 Expected Score: **{best_score:+,}**\n\n"
    yield log
    time.sleep(0.2)

    # Strategy explanation
    if best_score > 50000:
        strategy = "🎯 **WINNING MOVE!**"
    elif best_score > 10000:
        strategy = "💪 Strong Attack"
    elif best_score > 0:
        strategy = "📈 Building Position"
    elif best_score > -5000:
        strategy = "🛡️ Defensive Play"
    else:
        strategy = "⚠️ Minimizing Damage"

    log += f"Strategy: {strategy}\n"
    yield log

def make_ai_move(state):
    """Execute the AI move after thinking"""
    if state['game_over'] or state['current_player'] != 2:
        return state, render_board_image(state), get_status(state)

    state = copy.deepcopy(state)
    board = state['board']
    valid_moves = board.valid_moves()

    if not valid_moves:
        state['game_over'] = True
        return state, render_board_image(state), get_status(state)

    # Get best move
    best_col, _ = minimax(
        board,
        depth=state['ai_depth'],
        alpha=float('-inf'),
        beta=float('inf'),
        maximizing_player=True,
        return_tree=False
    )

    if best_col is not None and best_col in valid_moves:
        state['board'].move(best_col, 2)
        state['last_move'] = (best_col, 2)
        check_winner(state)
        if not state['game_over']:
            state['current_player'] = 1

    return state, render_board_image(state), get_status(state)

def reset_game(difficulty):
    """Reset the game"""
    state = create_initial_state()

    difficulty_map = {
        "Easy (2)": 2,
        "Medium (4)": 4,
        "Hard (6)": 6,
        "Expert (8)": 8,
    }
    state['ai_depth'] = difficulty_map.get(difficulty, 4)

    welcome = "🎮 **NEW GAME!**\n\n"
    welcome += f"Difficulty: {difficulty}\n\n"
    welcome += "You: 🔴 Red\n"
    welcome += "AI: 🟡 Yellow\n\n"
    welcome += "Click on any column to drop your piece!"

    return state, render_board_image(state), get_status(state), welcome

# Dark theme CSS
dark_css = """
.gradio-container {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important;
    min-height: 100vh;
}

.main-title {
    text-align: center;
    color: #00d4ff;
    font-size: 2.5em;
    font-weight: bold;
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    color: #a0a0ff;
    font-size: 1.2em;
    margin-bottom: 20px;
}

.board-container {
    background: linear-gradient(180deg, #1e3c72, #2a5298);
    padding: 20px;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(30, 60, 114, 0.3);
}

.status-bar {
    background: linear-gradient(90deg, #667eea, #764ba2);
    color: white;
    padding: 15px;
    border-radius: 12px;
    font-size: 1.3em;
    font-weight: bold;
    text-align: center;
    box-shadow: 0 5px 20px rgba(118, 75, 162, 0.4);
    margin: 15px 0;
}

.thinking-panel {
    background: #0a0a1a;
    border: 2px solid #00ff88;
    border-radius: 12px;
    padding: 20px;
    color: #00ff88;
    font-family: 'Courier New', monospace;
    font-size: 1em;
    line-height: 1.8;
    min-height: 300px;
    max-height: 400px;
    overflow-y: auto;
    box-shadow: 0 0 30px rgba(0, 255, 136, 0.2), inset 0 0 50px rgba(0, 255, 136, 0.05);
}

.control-panel {
    background: rgba(255, 255, 255, 0.05);
    padding: 20px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

button {
    transition: all 0.3s ease !important;
}

button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3) !important;
}

.info-panel {
    background: rgba(255, 255, 255, 0.05);
    padding: 15px;
    border-radius: 10px;
    color: #c0c0ff;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

footer {
    display: none !important;
}

label {
    color: #a0a0ff !important;
}
"""

# Build the interface
with gr.Blocks(title="Connect 4 AI", css=dark_css, theme=gr.themes.Base()) as demo:

    game_state = gr.State(create_initial_state())

    gr.HTML('<div class="main-title">🎮 CONNECT 4 AI</div>')
    gr.HTML('<div class="subtitle">Challenge an Intelligent Opponent</div>')

    with gr.Row():
        # Left: Game Board
        with gr.Column(scale=3):
            with gr.Group(elem_classes=["board-container"]):
                board_image = gr.Image(
                    value=render_board_image(create_initial_state()),
                    label=None,
                    show_label=False,
                    interactive=False,
                    show_download_button=False,
                    show_fullscreen_button=False,
                    height=500,
                    width=560
                )

            status_text = gr.Markdown(
                value=get_status(create_initial_state()),
                elem_classes=["status-bar"]
            )

            with gr.Group(elem_classes=["control-panel"]):
                with gr.Row():
                    difficulty = gr.Dropdown(
                        choices=["Easy (2)", "Medium (4)", "Hard (6)", "Expert (8)"],
                        value="Medium (4)",
                        label="🎯 AI Difficulty",
                        scale=2
                    )
                    new_game_btn = gr.Button("🔄 New Game", variant="primary", scale=1)

        # Right: AI Thinking
        with gr.Column(scale=2):
            gr.Markdown("### 🧠 AI Thought Process")
            thinking_box = gr.Markdown(
                value="Click on the board to make your move!\n\nThe AI will show its analysis here.",
                elem_classes=["thinking-panel"]
            )

            with gr.Group(elem_classes=["info-panel"]):
                gr.Markdown("""
                ### 📖 How to Play

                **Click directly on any column** to drop your piece!

                - 🔴 You are Red
                - 🟡 AI is Yellow
                - Connect 4 in a row (↔️ ↕️ ↗️) to score
                - Vertical connects = 11x bonus!
                - Most points wins!

                Watch the AI's real-time analysis as it calculates the best move!
                """)

    # Event handlers
    board_image.select(
        fn=handle_click,
        inputs=[game_state],
        outputs=[game_state, board_image, status_text, thinking_box]
    ).then(
        fn=ai_thinking_generator,
        inputs=[game_state],
        outputs=[thinking_box]
    ).then(
        fn=make_ai_move,
        inputs=[game_state],
        outputs=[game_state, board_image, status_text]
    )

    new_game_btn.click(
        fn=reset_game,
        inputs=[difficulty],
        outputs=[game_state, board_image, status_text, thinking_box]
    )

    # Load initial state
    demo.load(
        fn=lambda: reset_game("Medium (4)"),
        outputs=[game_state, board_image, status_text, thinking_box]
    )

if __name__ == "__main__":
    demo.launch()
