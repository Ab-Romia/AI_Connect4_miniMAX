"""
Connect 4 AI - Interactive Gradio Interface with Progressive AI Thinking
"""

import gradio as gr
from Board import Connect4Board
from MiniMax import minimax, evaluate_board
import copy
import time

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

def board_to_display(state):
    """Convert board state to visual display"""
    board = state['board']

    lines = []
    lines.append("┌─────────────────────────┐")
    lines.append("│  1   2   3   4   5   6   7  │")
    lines.append("├─────────────────────────┤")

    # Board rows (top to bottom)
    for row in range(5, -1, -1):
        row_str = "│ "
        for col in range(7):
            bit_position = 1 << (row * 7 + col)
            if board.player1 & bit_position:
                row_str += " 🔴 "
            elif board.player2 & bit_position:
                row_str += " 🟡 "
            else:
                row_str += " ⚪ "
        row_str += "│"
        lines.append(row_str)

    lines.append("└─────────────────────────┘")

    return "\n".join(lines)

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
        status = "🔴 Your Turn"
    else:
        status = "🟡 AI Thinking..."

    return f"**{status}** | You: {p1_score} pts | AI: {p2_score} pts"

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

def play_column(col, state):
    """Handle player move on a column"""
    if state is None:
        state = create_initial_state()

    state = copy.deepcopy(state)

    if state['game_over'] or state['current_player'] != 1:
        return state, board_to_display(state), get_status(state), "Not your turn or game is over."

    valid_moves = state['board'].valid_moves()
    if col not in valid_moves:
        return state, board_to_display(state), get_status(state), "❌ Column is full! Choose another."

    # Make player move
    state['board'].move(col, 1)
    state['last_move'] = (col, 1)
    check_winner(state)

    if state['game_over']:
        return state, board_to_display(state), get_status(state), "🎮 Game Over!"

    state['current_player'] = 2
    return state, board_to_display(state), get_status(state), "🤖 AI is analyzing..."

def ai_turn(state):
    """Process AI turn with thinking visualization"""
    if state is None:
        state = create_initial_state()
        return state, board_to_display(state), get_status(state), "Start a new game!"

    if state['game_over'] or state['current_player'] != 2:
        return state, board_to_display(state), get_status(state), "Waiting for your move..."

    state = copy.deepcopy(state)
    board = state['board']
    depth = state['ai_depth']
    valid_moves = board.valid_moves()

    if not valid_moves:
        state['game_over'] = True
        return state, board_to_display(state), get_status(state), "No valid moves!"

    # Build thinking log
    thinking = []
    thinking.append("🧠 **AI ANALYSIS**\n")
    thinking.append(f"📊 Depth: {depth} moves ahead\n")
    thinking.append(f"🎯 Analyzing {len(valid_moves)} columns...\n\n")
    thinking.append("─" * 30 + "\n\n")

    # Evaluate each column
    for col in valid_moves:
        board.move(col, 2)
        score = evaluate_board(board)
        board.undo(col, 2)

        # Visual bar
        bar_len = int(min(12, max(0, (score + 5000) / 850)))
        bar = "█" * bar_len + "░" * (12 - bar_len)
        thinking.append(f"Col {col + 1}: [{bar}] {score:+,}\n")

    thinking.append("\n" + "─" * 30 + "\n\n")
    thinking.append("🔍 **MINIMAX SEARCH...**\n\n")

    # Deep search
    best_col, best_score = minimax(
        board,
        depth=depth,
        alpha=float('-inf'),
        beta=float('inf'),
        maximizing_player=True,
        return_tree=False
    )

    thinking.append(f"✅ **BEST MOVE: Column {best_col + 1}**\n")
    thinking.append(f"💯 Score: {best_score:+,}\n\n")

    # Strategy
    if best_score > 50000:
        thinking.append("🎯 Strategy: WINNING MOVE!")
    elif best_score > 10000:
        thinking.append("💪 Strategy: Strong Attack")
    elif best_score > 0:
        thinking.append("📈 Strategy: Building Position")
    elif best_score > -5000:
        thinking.append("🛡️ Strategy: Defensive")
    else:
        thinking.append("⚠️ Strategy: Damage Control")

    # Make the move
    if best_col is not None and best_col in valid_moves:
        state['board'].move(best_col, 2)
        state['last_move'] = (best_col, 2)
        check_winner(state)
        if not state['game_over']:
            state['current_player'] = 1

    return state, board_to_display(state), get_status(state), "".join(thinking)

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

    welcome = f"🎮 **NEW GAME - {difficulty}**\n\n"
    welcome += "You: 🔴 Red\n"
    welcome += "AI: 🟡 Yellow\n\n"
    welcome += "Click a column button to drop your piece!"

    return state, board_to_display(state), get_status(state), welcome

# CSS styling
css = """
.gradio-container {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
}

.board-display {
    font-family: 'Courier New', monospace;
    font-size: 1.4em;
    background: linear-gradient(180deg, #1e3c72, #2a5298);
    padding: 25px;
    border-radius: 15px;
    color: white;
    text-align: center;
    box-shadow: 0 15px 40px rgba(0,0,0,0.4);
    white-space: pre;
    line-height: 1.3;
}

.status-display {
    background: linear-gradient(90deg, #667eea, #764ba2);
    padding: 18px;
    border-radius: 12px;
    color: white;
    text-align: center;
    font-size: 1.2em;
    box-shadow: 0 8px 25px rgba(118, 75, 162, 0.4);
}

.thinking-display {
    background: #0d1117;
    border: 2px solid #00ff88;
    border-radius: 10px;
    padding: 20px;
    color: #00ff88;
    font-family: 'Courier New', monospace;
    font-size: 0.95em;
    line-height: 1.7;
    min-height: 350px;
    box-shadow: 0 0 25px rgba(0, 255, 136, 0.15);
    white-space: pre-wrap;
}

.column-btn {
    font-size: 1.3em !important;
    padding: 18px !important;
    font-weight: bold !important;
    border-radius: 12px !important;
    transition: all 0.2s ease !important;
}

.column-btn:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.3) !important;
}

.info-box {
    background: rgba(255, 255, 255, 0.08);
    padding: 18px;
    border-radius: 12px;
    color: #b8c5d6;
    border: 1px solid rgba(255, 255, 255, 0.15);
}

button.primary {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
}

label, .label-wrap {
    color: #b8c5d6 !important;
}

footer { display: none !important; }
"""

# Build interface
with gr.Blocks(title="Connect 4 AI", css=css, theme=gr.themes.Base()) as demo:

    game_state = gr.State(create_initial_state())

    gr.Markdown("""
    # 🎮 Connect 4 AI
    ### Challenge an Intelligent Opponent with Real-Time Analysis
    """, elem_classes=["title"])

    with gr.Row():
        # Left column - Game
        with gr.Column(scale=3):
            board_display = gr.Markdown(
                value=board_to_display(create_initial_state()),
                elem_classes=["board-display"]
            )

            status_display = gr.Markdown(
                value=get_status(create_initial_state()),
                elem_classes=["status-display"]
            )

            gr.Markdown("### 👇 Click to Drop Your Piece")

            with gr.Row():
                btn1 = gr.Button("1", elem_classes=["column-btn"])
                btn2 = gr.Button("2", elem_classes=["column-btn"])
                btn3 = gr.Button("3", elem_classes=["column-btn"])
                btn4 = gr.Button("4", elem_classes=["column-btn"], variant="primary")
                btn5 = gr.Button("5", elem_classes=["column-btn"])
                btn6 = gr.Button("6", elem_classes=["column-btn"])
                btn7 = gr.Button("7", elem_classes=["column-btn"])

            with gr.Row():
                difficulty = gr.Dropdown(
                    choices=["Easy (2)", "Medium (4)", "Hard (6)", "Expert (8)"],
                    value="Medium (4)",
                    label="🎯 AI Difficulty",
                    scale=2
                )
                new_game_btn = gr.Button("🔄 New Game", variant="primary", scale=1)

        # Right column - AI Thinking
        with gr.Column(scale=2):
            gr.Markdown("### 🧠 AI Thought Process")

            thinking_display = gr.Markdown(
                value="Make your move to see the AI's analysis!",
                elem_classes=["thinking-display"]
            )

            with gr.Group(elem_classes=["info-box"]):
                gr.Markdown("""
                ### 📖 How to Play

                Click column buttons (1-7) to drop your piece.

                - 🔴 You are Red
                - 🟡 AI is Yellow
                - Connect 4 in a row to score
                - Vertical = 11x bonus!
                - Most points when board fills = WIN

                Watch the AI analyze each move in real-time!
                """)

    # Wire up buttons
    all_outputs = [game_state, board_display, status_display, thinking_display]

    def make_move_and_ai(col, state):
        # Player move
        state, board, status, thinking = play_column(col, state)

        # If it's AI's turn, make AI move
        if state['current_player'] == 2 and not state['game_over']:
            time.sleep(0.3)  # Brief pause
            state, board, status, thinking = ai_turn(state)

        return state, board, status, thinking

    btn1.click(fn=lambda s: make_move_and_ai(0, s), inputs=[game_state], outputs=all_outputs)
    btn2.click(fn=lambda s: make_move_and_ai(1, s), inputs=[game_state], outputs=all_outputs)
    btn3.click(fn=lambda s: make_move_and_ai(2, s), inputs=[game_state], outputs=all_outputs)
    btn4.click(fn=lambda s: make_move_and_ai(3, s), inputs=[game_state], outputs=all_outputs)
    btn5.click(fn=lambda s: make_move_and_ai(4, s), inputs=[game_state], outputs=all_outputs)
    btn6.click(fn=lambda s: make_move_and_ai(5, s), inputs=[game_state], outputs=all_outputs)
    btn7.click(fn=lambda s: make_move_and_ai(6, s), inputs=[game_state], outputs=all_outputs)

    new_game_btn.click(
        fn=reset_game,
        inputs=[difficulty],
        outputs=all_outputs
    )

    demo.load(
        fn=lambda: reset_game("Medium (4)"),
        outputs=all_outputs
    )

if __name__ == "__main__":
    demo.launch()
