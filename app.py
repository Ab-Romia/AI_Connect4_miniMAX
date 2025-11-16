"""
Connect 4 AI - Beautiful Interactive Gradio Interface
An intelligent Connect 4 game with stunning animations and intuitive gameplay
"""

import gradio as gr
from Board import Connect4Board
from MiniMax import minimax
import json
import copy
import time

def create_initial_state():
    """Create initial game state dictionary"""
    return {
        'board': Connect4Board(),
        'current_player': 1,
        'game_over': False,
        'move_history': [],
        'ai_depth': 4,
        'winner': None,
        'last_move': None,
        'animating': False
    }

def get_board_html(state):
    """Generate beautiful HTML board with animations"""
    board = state['board']
    current_player = state['current_player']
    game_over = state['game_over']
    winner = state['winner']
    last_move = state.get('last_move', None)

    # Build the board grid
    cells_html = ""
    for row in range(5, -1, -1):  # Top to bottom
        for col in range(7):
            bit_position = 1 << (row * 7 + col)

            if board.player1 & bit_position:
                piece_class = "player1"
                is_new = last_move == (col, 1) and row == get_piece_row(board, col, 1)
            elif board.player2 & bit_position:
                piece_class = "player2"
                is_new = last_move == (col, 2) and row == get_piece_row(board, col, 2)
            else:
                piece_class = "empty"
                is_new = False

            animation_class = "drop-animation" if is_new else ""

            cells_html += f'''
                <div class="cell" data-col="{col}">
                    <div class="piece {piece_class} {animation_class}"></div>
                </div>
            '''

    # Determine status message
    if game_over:
        if winner == 1:
            status = "🎉 You Win! Amazing!"
            status_class = "winner"
        elif winner == 2:
            status = "🤖 AI Wins! Try Again!"
            status_class = "loser"
        else:
            status = "🤝 It's a Draw!"
            status_class = "draw"
    else:
        if current_player == 1:
            status = "🔴 Your Turn - Hover & Click!"
            status_class = "your-turn"
        else:
            status = "🟡 AI is Thinking..."
            status_class = "ai-turn"

    # Get scores
    p1_score = board.connect_4s(1)
    p2_score = board.connect_4s(2)

    # Column indicators for hover
    column_indicators = ""
    if not game_over and current_player == 1:
        for col in range(7):
            if board.height(col) < 6:
                column_indicators += f'''
                    <div class="column-indicator" data-col="{col}">
                        <div class="hover-piece"></div>
                        <div class="drop-arrow">▼</div>
                    </div>
                '''
            else:
                column_indicators += '<div class="column-indicator full"></div>'
    else:
        for _ in range(7):
            column_indicators += '<div class="column-indicator disabled"></div>'

    html = f'''
    <div class="game-wrapper">
        <div class="game-title">
            <h1>🎮 Connect 4 AI</h1>
            <p>Challenge the AI with smooth, intuitive gameplay</p>
        </div>

        <div class="status-bar {status_class}">
            <span class="status-text">{status}</span>
        </div>

        <div class="score-board">
            <div class="score player1-score">
                <span class="score-label">🔴 You</span>
                <span class="score-value">{p1_score}</span>
            </div>
            <div class="score player2-score">
                <span class="score-label">🟡 AI</span>
                <span class="score-value">{p2_score}</span>
            </div>
        </div>

        <div class="board-container">
            <div class="column-indicators">
                {column_indicators}
            </div>
            <div class="board">
                {cells_html}
            </div>
        </div>

        <div class="instructions">
            <p>💡 <strong>Hover</strong> over a column to preview • <strong>Click</strong> to drop your piece</p>
        </div>
    </div>
    '''

    return html

def get_piece_row(board, col, player):
    """Get the row of the last piece placed in a column"""
    height = board.height(col)
    if height > 0:
        return height - 1
    return -1

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
            state['winner'] = 0  # Draw

    return state

def make_ai_move(state):
    """Make AI move and update state"""
    if state['game_over'] or state['current_player'] != 2:
        return state

    valid_moves = state['board'].valid_moves()
    if not valid_moves:
        state['game_over'] = True
        return state

    try:
        best_col, _ = minimax(
            state['board'],
            depth=state['ai_depth'],
            alpha=float('-inf'),
            beta=float('inf'),
            maximizing_player=True,
            return_tree=False
        )

        if best_col is not None and best_col in valid_moves:
            state['board'].move(best_col, 2)
            state['move_history'].append((best_col, 2))
            state['last_move'] = (best_col, 2)
            check_winner(state)
            if not state['game_over']:
                state['current_player'] = 1
    except Exception as e:
        print(f"AI Error: {e}")
        import random
        col = random.choice(valid_moves)
        state['board'].move(col, 2)
        state['move_history'].append((col, 2))
        state['last_move'] = (col, 2)
        check_winner(state)
        if not state['game_over']:
            state['current_player'] = 1

    return state

def play_column(col_idx, state, difficulty):
    """Handle player clicking a column"""
    state = copy.deepcopy(state)

    if state['game_over'] or state['current_player'] != 1:
        return state, get_board_html(state)

    valid_moves = state['board'].valid_moves()
    if col_idx not in valid_moves:
        return state, get_board_html(state)

    # Player move
    state['board'].move(col_idx, 1)
    state['move_history'].append((col_idx, 1))
    state['last_move'] = (col_idx, 1)
    check_winner(state)

    # Return immediately to show player move with animation
    if not state['game_over']:
        state['current_player'] = 2
        # AI move
        state = make_ai_move(state)

    return state, get_board_html(state)

def reset_game(difficulty):
    """Reset the game with new difficulty"""
    state = create_initial_state()

    difficulty_map = {
        "Easy": 2,
        "Medium": 4,
        "Hard": 6,
        "Expert": 8,
    }
    state['ai_depth'] = difficulty_map.get(difficulty, 4)

    return state, get_board_html(state)

# Beautiful CSS styling
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.game-wrapper {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    max-width: 700px;
    margin: 0 auto;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 24px;
    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
}

.game-title {
    text-align: center;
    margin-bottom: 20px;
}

.game-title h1 {
    font-size: 2.5em;
    font-weight: 800;
    color: #fff;
    margin: 0;
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.game-title p {
    color: rgba(255, 255, 255, 0.9);
    margin: 8px 0 0 0;
    font-size: 1.1em;
    font-weight: 500;
}

.status-bar {
    background: rgba(255, 255, 255, 0.95);
    padding: 16px 24px;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.status-bar.your-turn {
    border-left: 6px solid #FF4757;
}

.status-bar.ai-turn {
    border-left: 6px solid #FFA502;
    animation: pulse-glow 1.5s ease-in-out infinite;
}

.status-bar.winner {
    background: linear-gradient(135deg, #a8ff78 0%, #78ffd6 100%);
    border-left: 6px solid #00d26a;
}

.status-bar.loser {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    border-left: 6px solid #ff6b6b;
}

.status-bar.draw {
    background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
    border-left: 6px solid #ffa502;
}

@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1); }
    50% { box-shadow: 0 8px 40px rgba(255, 165, 2, 0.4); }
}

.status-text {
    font-size: 1.3em;
    font-weight: 700;
    color: #2d3436;
}

.score-board {
    display: flex;
    justify-content: center;
    gap: 30px;
    margin-bottom: 20px;
}

.score {
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    padding: 12px 24px;
    border-radius: 12px;
    text-align: center;
    min-width: 100px;
}

.score-label {
    display: block;
    font-size: 1em;
    color: #fff;
    font-weight: 600;
    margin-bottom: 4px;
}

.score-value {
    display: block;
    font-size: 2em;
    color: #fff;
    font-weight: 800;
}

.board-container {
    background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    padding: 20px;
    border-radius: 20px;
    box-shadow:
        0 20px 60px rgba(0, 0, 0, 0.3),
        inset 0 2px 10px rgba(255, 255, 255, 0.1);
}

.column-indicators {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 8px;
    margin-bottom: 10px;
    height: 50px;
}

.column-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border-radius: 10px;
    transition: all 0.2s ease;
    position: relative;
}

.column-indicator:not(.full):not(.disabled):hover {
    background: rgba(255, 255, 255, 0.1);
}

.column-indicator:not(.full):not(.disabled):hover .hover-piece {
    opacity: 1;
    transform: scale(1);
}

.column-indicator:not(.full):not(.disabled):hover .drop-arrow {
    opacity: 1;
    animation: bounce-arrow 0.6s ease-in-out infinite;
}

.hover-piece {
    width: 40px;
    height: 40px;
    background: radial-gradient(circle at 30% 30%, #ff6b7a, #FF4757);
    border-radius: 50%;
    opacity: 0;
    transform: scale(0.8);
    transition: all 0.2s ease;
    box-shadow: 0 4px 15px rgba(255, 71, 87, 0.5);
}

.drop-arrow {
    color: #fff;
    font-size: 1.2em;
    opacity: 0;
    position: absolute;
    bottom: -5px;
    transition: opacity 0.2s ease;
}

@keyframes bounce-arrow {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(5px); }
}

.column-indicator.full,
.column-indicator.disabled {
    cursor: not-allowed;
    opacity: 0.5;
}

.board {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 8px;
    background: transparent;
}

.cell {
    aspect-ratio: 1;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 6px;
    box-shadow: inset 0 4px 8px rgba(0, 0, 0, 0.4);
}

.piece {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    transition: all 0.3s ease;
}

.piece.empty {
    background: radial-gradient(circle at 30% 30%, #4a6fa5, #2c3e50);
    box-shadow: inset 0 4px 15px rgba(0, 0, 0, 0.5);
}

.piece.player1 {
    background: radial-gradient(circle at 30% 30%, #ff6b7a, #FF4757);
    box-shadow:
        0 4px 15px rgba(255, 71, 87, 0.6),
        inset 0 -4px 10px rgba(0, 0, 0, 0.3),
        inset 0 4px 10px rgba(255, 255, 255, 0.3);
}

.piece.player2 {
    background: radial-gradient(circle at 30% 30%, #ffb142, #FFA502);
    box-shadow:
        0 4px 15px rgba(255, 165, 2, 0.6),
        inset 0 -4px 10px rgba(0, 0, 0, 0.3),
        inset 0 4px 10px rgba(255, 255, 255, 0.3);
}

.piece.drop-animation {
    animation: drop-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes drop-in {
    0% {
        transform: translateY(-400px) scale(0.8);
        opacity: 0;
    }
    60% {
        transform: translateY(10px) scale(1.05);
        opacity: 1;
    }
    80% {
        transform: translateY(-5px) scale(0.98);
    }
    100% {
        transform: translateY(0) scale(1);
    }
}

.instructions {
    background: rgba(255, 255, 255, 0.1);
    padding: 16px;
    border-radius: 12px;
    text-align: center;
    margin-top: 20px;
}

.instructions p {
    color: #fff;
    margin: 0;
    font-size: 1em;
}

/* Gradio overrides */
.gradio-container {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
    min-height: 100vh;
}

.contain {
    max-width: 900px !important;
}

button.primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
}

button.primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
}
"""

# Create Gradio interface
with gr.Blocks(
    title="Connect 4 AI",
    css=custom_css,
    theme=gr.themes.Soft()
) as demo:

    game_state = gr.State(create_initial_state())

    with gr.Column():
        # Main game board
        board_html = gr.HTML(
            value=get_board_html(create_initial_state()),
            elem_id="game-board"
        )

        # Controls
        with gr.Row():
            difficulty = gr.Radio(
                choices=["Easy", "Medium", "Hard", "Expert"],
                value="Medium",
                label="🎯 AI Difficulty",
                info="Easy=2 moves ahead, Expert=8 moves ahead"
            )
            reset_btn = gr.Button(
                "🔄 New Game",
                variant="primary",
                size="lg"
            )

        # Hidden column buttons for click handling
        with gr.Row(visible=False):
            col_buttons = []
            for i in range(7):
                btn = gr.Button(f"Col {i}", elem_id=f"col-btn-{i}")
                col_buttons.append(btn)

    # Connect button clicks to game logic
    for idx, btn in enumerate(col_buttons):
        btn.click(
            fn=lambda state, diff, i=idx: play_column(i, state, diff),
            inputs=[game_state, difficulty],
            outputs=[game_state, board_html]
        )

    # Reset button
    reset_btn.click(
        fn=reset_game,
        inputs=[difficulty],
        outputs=[game_state, board_html]
    )

    # JavaScript for interactive column clicking
    demo.load(
        fn=lambda: None,
        inputs=None,
        outputs=None,
        js="""
        () => {
            // Wait for board to render
            setTimeout(() => {
                const setupClickHandlers = () => {
                    const indicators = document.querySelectorAll('.column-indicator:not(.full):not(.disabled)');
                    indicators.forEach(indicator => {
                        const col = indicator.getAttribute('data-col');
                        if (col !== null) {
                            indicator.onclick = () => {
                                const btn = document.getElementById('col-btn-' + col);
                                if (btn) btn.click();
                            };
                        }
                    });

                    // Also make cells clickable
                    const cells = document.querySelectorAll('.cell');
                    cells.forEach(cell => {
                        const col = cell.getAttribute('data-col');
                        if (col !== null) {
                            cell.onclick = () => {
                                const btn = document.getElementById('col-btn-' + col);
                                if (btn) btn.click();
                            };
                        }
                    });
                };

                setupClickHandlers();

                // Re-setup after any board update
                const observer = new MutationObserver(() => {
                    setTimeout(setupClickHandlers, 100);
                });

                const boardContainer = document.getElementById('game-board');
                if (boardContainer) {
                    observer.observe(boardContainer, { childList: true, subtree: true });
                }
            }, 500);
        }
        """
    )

if __name__ == "__main__":
    demo.launch()
