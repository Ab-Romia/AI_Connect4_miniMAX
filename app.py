"""
Connect 4 AI - Beautiful Interactive Interface
Click directly on board columns to play!
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
    }

def create_board_html(state):
    """Create clickable HTML/CSS board"""
    board = state['board']
    p1 = board.connect_4s(1)
    p2 = board.connect_4s(2)

    # Status
    if state['game_over']:
        if state['winner'] == 1:
            status = "🎉 YOU WIN!"
            status_class = "winner"
        elif state['winner'] == 2:
            status = "🤖 AI WINS!"
            status_class = "loser"
        else:
            status = "🤝 DRAW!"
            status_class = "draw"
    elif state['current_player'] == 1:
        status = "🔴 Your Turn - Click a column!"
        status_class = "your-turn"
    else:
        status = "🟡 AI Thinking..."
        status_class = "ai-turn"

    # Build board HTML
    cells = ""
    for row in range(5, -1, -1):  # Top to bottom
        for col in range(7):
            bit_pos = 1 << (row * 7 + col)
            if board.player1 & bit_pos:
                piece_class = "red"
            elif board.player2 & bit_pos:
                piece_class = "yellow"
            else:
                piece_class = "empty"

            cells += f'<div class="cell" data-col="{col}"><div class="piece {piece_class}"></div></div>'

    html = f'''
    <div class="connect4-game">
        <div class="status-bar {status_class}">{status}</div>
        <div class="score-display">
            <span class="score red-score">🔴 You: {p1}</span>
            <span class="score yellow-score">🟡 AI: {p2}</span>
        </div>
        <div class="board-frame">
            <div class="column-hints">
                <div class="hint">1</div>
                <div class="hint">2</div>
                <div class="hint">3</div>
                <div class="hint">4</div>
                <div class="hint">5</div>
                <div class="hint">6</div>
                <div class="hint">7</div>
            </div>
            <div class="board" id="game-board">
                {cells}
            </div>
        </div>
    </div>
    '''
    return html

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

def player_move(col, state):
    """Handle player move only - returns immediately"""
    if state is None:
        state = create_initial_state()

    state = copy.deepcopy(state)

    if state['game_over'] or state['current_player'] != 1:
        return state, create_board_html(state), "Game over or not your turn."

    valid = state['board'].valid_moves()
    if col not in valid:
        return state, create_board_html(state), f"❌ Column {col+1} is full!"

    # Make move immediately
    state['board'].move(col, 1)
    check_winner(state)

    if state['game_over']:
        return state, create_board_html(state), "🎮 Game Over!"

    state['current_player'] = 2
    return state, create_board_html(state), "🤖 AI analyzing your move..."

def ai_think_phase1(state):
    """AI thinking phase 1 - initialization"""
    if state['game_over'] or state['current_player'] != 2:
        return "Your turn!"

    time.sleep(0.2)
    depth = state['ai_depth']
    valid = state['board'].valid_moves()

    return f"""🧠 **AI ANALYSIS STARTED**

```
Search Depth: {depth} moves ahead
Valid Columns: {len(valid)}
Status: Initializing...
```

⏳ **Computing position scores...**"""

def ai_think_phase2(state):
    """AI thinking phase 2 - evaluate columns"""
    if state['game_over'] or state['current_player'] != 2:
        return "Your turn!"

    time.sleep(0.3)
    board = state['board']
    valid = board.valid_moves()

    text = """🧠 **POSITION EVALUATION**

```
"""
    for col in valid:
        board.move(col, 2)
        score = evaluate_board(board)
        board.undo(col, 2)

        bar_len = int(min(10, max(0, (score + 5000) / 1000)))
        bar = "█" * bar_len + "░" * (10 - bar_len)
        text += f"Col {col+1}: [{bar}] {score:+,}\n"

    text += """```

🔍 **Running minimax search...**"""
    return text

def ai_think_phase3(state):
    """AI thinking phase 3 - final decision and move"""
    if state['game_over'] or state['current_player'] != 2:
        return state, create_board_html(state), "Your turn!"

    time.sleep(0.4)
    state = copy.deepcopy(state)
    board = state['board']
    depth = state['ai_depth']
    valid = board.valid_moves()

    if not valid:
        state['game_over'] = True
        return state, create_board_html(state), "No moves!"

    # Get best move
    best_col, best_score = minimax(
        board, depth=depth,
        alpha=float('-inf'), beta=float('inf'),
        maximizing_player=True, return_tree=False
    )

    # Build final text
    text = """🧠 **DECISION COMPLETE**

**Column Scores:**
```
"""
    for col in valid:
        board.move(col, 2)
        score = evaluate_board(board)
        board.undo(col, 2)
        bar_len = int(min(10, max(0, (score + 5000) / 1000)))
        bar = "█" * bar_len + "░" * (10 - bar_len)
        marker = " ◄ BEST" if col == best_col else ""
        text += f"Col {col+1}: [{bar}] {score:+,}{marker}\n"

    text += f"""```

✅ **CHOSEN: Column {best_col + 1}**
💯 **Score: {best_score:+,}**

"""
    # Strategy
    if best_score > 100000:
        text += "🎯 **WINNING MOVE!**"
    elif best_score > 10000:
        text += "💪 **Strong Attack**"
    elif best_score > 1000:
        text += "📈 **Building Position**"
    elif best_score > 0:
        text += "⚖️ **Slight Advantage**"
    elif best_score > -5000:
        text += "🛡️ **Defensive Play**"
    else:
        text += "⚠️ **Damage Control**"

    # Make AI move
    if best_col in valid:
        state['board'].move(best_col, 2)
        check_winner(state)
        if not state['game_over']:
            state['current_player'] = 1

    return state, create_board_html(state), text

def reset_game(difficulty):
    """Reset game"""
    state = create_initial_state()
    depth_map = {"Easy (2)": 2, "Medium (4)": 4, "Hard (6)": 6, "Expert (8)": 8}
    state['ai_depth'] = depth_map.get(difficulty, 4)

    welcome = f"""🎮 **NEW GAME STARTED!**

**Difficulty:** {difficulty}

🔴 **You** = Red pieces
🟡 **AI** = Yellow pieces

**Click directly on any column** to drop your piece!

The AI will show its thought process as it calculates the optimal move."""

    return state, create_board_html(state), welcome

# Complete CSS for dark theme with animations
custom_css = """
/* Dark theme for entire page */
.gradio-container {
    background: linear-gradient(135deg, #0d0d1a 0%, #1a1a3e 50%, #0d1a2d 100%) !important;
    min-height: 100vh !important;
}

.connect4-game {
    font-family: 'Segoe UI', system-ui, sans-serif;
    max-width: 750px;
    margin: 0 auto;
}

.status-bar {
    padding: 18px 25px;
    border-radius: 16px;
    font-size: 1.5em;
    font-weight: 700;
    text-align: center;
    margin-bottom: 15px;
    transition: all 0.4s ease;
    animation: fadeInDown 0.5s ease;
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

.status-bar.your-turn {
    background: linear-gradient(135deg, #ff4757, #ff6b7a);
    color: white;
    box-shadow: 0 10px 40px rgba(255, 71, 87, 0.4);
}

.status-bar.ai-turn {
    background: linear-gradient(135deg, #ffa502, #ffbe0b);
    color: #1a1a1a;
    box-shadow: 0 10px 40px rgba(255, 165, 2, 0.4);
    animation: fadeInDown 0.5s ease, pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

.status-bar.winner {
    background: linear-gradient(135deg, #2ed573, #7bed9f);
    color: white;
    box-shadow: 0 10px 40px rgba(46, 213, 115, 0.5);
}

.status-bar.loser {
    background: linear-gradient(135deg, #ff4757, #c44569);
    color: white;
}

.status-bar.draw {
    background: linear-gradient(135deg, #ffa502, #ff7f50);
    color: white;
}

.score-display {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-bottom: 20px;
}

.score {
    background: rgba(255, 255, 255, 0.1);
    padding: 12px 25px;
    border-radius: 12px;
    font-size: 1.3em;
    font-weight: 600;
    color: white;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.15);
}

.board-frame {
    background: linear-gradient(180deg, #1e3a8a, #1e40af);
    padding: 20px;
    border-radius: 24px;
    box-shadow:
        0 30px 80px rgba(0, 0, 0, 0.6),
        0 0 60px rgba(30, 58, 138, 0.3),
        inset 0 2px 4px rgba(255, 255, 255, 0.1);
    animation: slideUp 0.6s ease;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.column-hints {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 10px;
    margin-bottom: 12px;
}

.hint {
    text-align: center;
    color: rgba(255, 255, 255, 0.7);
    font-size: 1.2em;
    font-weight: 600;
}

.board {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 10px;
    background: transparent;
}

.cell {
    aspect-ratio: 1;
    background: rgba(0, 0, 0, 0.4);
    border-radius: 50%;
    padding: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: inset 0 4px 12px rgba(0, 0, 0, 0.5);
}

.cell:hover {
    background: rgba(255, 255, 255, 0.15);
    transform: scale(1.08);
}

.piece {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.piece.empty {
    background: radial-gradient(circle at 35% 35%, #3b5998, #1e3a8a);
    box-shadow: inset 0 4px 20px rgba(0, 0, 0, 0.6);
}

.piece.red {
    background: radial-gradient(circle at 35% 35%, #ff6b7a, #ff4757, #c0392b);
    box-shadow:
        0 6px 20px rgba(255, 71, 87, 0.6),
        inset 0 -6px 15px rgba(0, 0, 0, 0.3),
        inset 0 6px 15px rgba(255, 255, 255, 0.3);
    animation: dropIn 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.piece.yellow {
    background: radial-gradient(circle at 35% 35%, #ffbe0b, #ffa502, #f39c12);
    box-shadow:
        0 6px 20px rgba(255, 165, 2, 0.6),
        inset 0 -6px 15px rgba(0, 0, 0, 0.3),
        inset 0 6px 15px rgba(255, 255, 255, 0.3);
    animation: dropIn 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes dropIn {
    0% {
        transform: translateY(-500px) scale(0.7);
        opacity: 0;
    }
    60% {
        transform: translateY(15px) scale(1.1);
        opacity: 1;
    }
    80% {
        transform: translateY(-8px) scale(0.95);
    }
    100% {
        transform: translateY(0) scale(1);
    }
}

/* Thinking panel */
.thinking-panel {
    background: linear-gradient(180deg, #0a0a1a 0%, #0f0f2a 100%) !important;
    border: 3px solid #00ff88 !important;
    border-radius: 20px !important;
    padding: 25px !important;
    color: #00ff88 !important;
    font-family: 'Fira Code', 'Consolas', monospace !important;
    font-size: 1.05em !important;
    line-height: 1.8 !important;
    min-height: 500px !important;
    box-shadow:
        0 0 50px rgba(0, 255, 136, 0.2),
        inset 0 0 80px rgba(0, 255, 136, 0.05) !important;
    animation: glowPulse 3s infinite !important;
}

@keyframes glowPulse {
    0%, 100% { box-shadow: 0 0 50px rgba(0, 255, 136, 0.2); }
    50% { box-shadow: 0 0 80px rgba(0, 255, 136, 0.4); }
}

/* Control styling */
.controls-area {
    background: rgba(255, 255, 255, 0.05) !important;
    padding: 20px !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px) !important;
    margin-top: 20px !important;
}

.info-panel {
    background: rgba(255, 255, 255, 0.08) !important;
    padding: 20px !important;
    border-radius: 16px !important;
    color: #c8d6e8 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    margin-top: 15px !important;
}

h1, h2, h3 {
    color: #00d4ff !important;
    text-shadow: 0 0 30px rgba(0, 212, 255, 0.4) !important;
}

button.primary {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    font-weight: 700 !important;
    font-size: 1.1em !important;
    transition: all 0.3s ease !important;
}

button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
}

label, .label-wrap span {
    color: #a8b8d8 !important;
}

footer { display: none !important; }
"""

# JavaScript for click handling
click_js = """
() => {
    const setupClicks = () => {
        const cells = document.querySelectorAll('.cell');
        cells.forEach(cell => {
            cell.onclick = (e) => {
                const col = parseInt(cell.getAttribute('data-col'));
                if (!isNaN(col)) {
                    const btn = document.getElementById('col-btn-' + col);
                    if (btn) btn.click();
                }
            };
        });
    };

    // Setup immediately and on any changes
    setupClicks();

    // Watch for DOM changes
    const observer = new MutationObserver(() => {
        setTimeout(setupClicks, 50);
    });

    const container = document.querySelector('.gradio-container');
    if (container) {
        observer.observe(container, { childList: true, subtree: true });
    }

    // Also setup after delays
    setTimeout(setupClicks, 100);
    setTimeout(setupClicks, 500);
    setTimeout(setupClicks, 1000);
}
"""

# Build the interface
with gr.Blocks(title="Connect 4 AI", css=custom_css, theme=gr.themes.Base()) as demo:

    state = gr.State(create_initial_state())

    gr.Markdown("""
    # 🎮 CONNECT 4 AI
    ### Click directly on the board to play!
    """)

    with gr.Row():
        with gr.Column(scale=3):
            board_html = gr.HTML(
                value=create_board_html(create_initial_state())
            )

            with gr.Group(elem_classes=["controls-area"]):
                with gr.Row():
                    difficulty = gr.Dropdown(
                        choices=["Easy (2)", "Medium (4)", "Hard (6)", "Expert (8)"],
                        value="Medium (4)",
                        label="🎯 AI Difficulty",
                        scale=2
                    )
                    new_game_btn = gr.Button("🔄 New Game", variant="primary", scale=1)

            # Hidden buttons for column clicks
            with gr.Row(visible=False):
                col_btns = []
                for i in range(7):
                    btn = gr.Button(f"{i}", elem_id=f"col-btn-{i}")
                    col_btns.append(btn)

        with gr.Column(scale=2):
            gr.Markdown("### 🧠 AI Thought Process")
            thinking = gr.Markdown(
                value="Click on a column to make your move!\n\nWatch the AI analyze positions here.",
                elem_classes=["thinking-panel"]
            )

            with gr.Group(elem_classes=["info-panel"]):
                gr.Markdown("""
                ### 📖 How to Play

                **Click directly on any column** on the board!

                - 🔴 **You** = Red
                - 🟡 **AI** = Yellow
                - Connect 4 in a row to score
                - Vertical = **11× bonus!**
                - Most points = **WIN**

                Watch the AI's progressive analysis!
                """)

    # Wire up hidden buttons with progressive AI thinking
    for i in range(7):
        col_btns[i].click(
            fn=lambda s, col=i: player_move(col, s),
            inputs=[state],
            outputs=[state, board_html, thinking]
        ).then(
            fn=ai_think_phase1,
            inputs=[state],
            outputs=[thinking]
        ).then(
            fn=ai_think_phase2,
            inputs=[state],
            outputs=[thinking]
        ).then(
            fn=ai_think_phase3,
            inputs=[state],
            outputs=[state, board_html, thinking]
        )

    new_game_btn.click(
        fn=reset_game,
        inputs=[difficulty],
        outputs=[state, board_html, thinking]
    )

    # Initialize
    demo.load(
        fn=lambda: reset_game("Medium (4)"),
        outputs=[state, board_html, thinking],
        js=click_js
    )

if __name__ == "__main__":
    demo.launch()
