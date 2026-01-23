"""Deterministic demo payload generator from PGN."""

import math
from datetime import datetime
from pathlib import Path
from typing import Optional

import chess
import chess.pgn

from renacechess.contracts.models import (
    ContextBridgeMeta,
    ContextBridgePayload,
    HDI,
    HDIComponents,
    HumanWDL,
    HumanWDLContainer,
    NarrativeSeed,
    Policy,
    PolicyMove,
    Position,
    PositionConditioning,
)
from renacechess.determinism import canonical_hash


def generate_demo_payload(
    pgn_path: Path, ply: int = 6, generated_at: Optional[datetime] = None
) -> dict:
    """Generate deterministic demo payload from PGN.

    Args:
        pgn_path: Path to PGN file.
        ply: Target ply number (default: 6).
        generated_at: Override generation timestamp (for testing).

    Returns:
        Dictionary representation of ContextBridgePayload (ready for JSON serialization).
    """
    # Parse PGN
    with pgn_path.open() as f:
        game = chess.pgn.read_game(f)
        if game is None:
            raise ValueError(f"Failed to parse PGN from {pgn_path}")

    # Step to target ply
    board = game.board()
    move_count = 0
    for move in game.mainline_moves():
        if move_count >= ply:
            break
        board.push(move)
        move_count += 1

    # Get position info
    fen = board.fen()
    side_to_move = "white" if board.turn == chess.WHITE else "black"
    legal_moves_uci = [move.uci() for move in board.legal_moves]
    legal_moves_uci.sort()  # Deterministic ordering

    # Generate deterministic stub policy
    # Sort moves alphabetically, assign geometric decay probabilities
    top_moves = []
    num_moves = len(legal_moves_uci)
    if num_moves > 0:
        # Geometric decay: first move gets highest probability
        # Normalize so probabilities sum to 1
        decay_factor = 0.7
        probabilities = []
        for i in range(num_moves):
            prob = decay_factor ** i
            probabilities.append(prob)
        total = sum(probabilities)
        probabilities = [p / total for p in probabilities]

        for uci, prob in zip(legal_moves_uci, probabilities):
            top_moves.append(PolicyMove(uci=uci, p=prob))

    # Compute entropy (Shannon entropy)
    entropy = 0.0
    for move in top_moves:
        if move.p > 0:
            entropy -= move.p * math.log2(move.p)
    entropy = max(0.0, entropy)

    # Compute top gap
    top_gap = 0.0
    if len(top_moves) >= 2:
        top_gap = top_moves[0].p - top_moves[1].p
    elif len(top_moves) == 1:
        top_gap = 1.0

    # Generate deterministic stub humanWDL
    # Use entropy and topGap to determine difficulty
    # Higher entropy + lower topGap = more confusing = lower win probability
    difficulty = (entropy / 10.0) + (1.0 - top_gap)  # Normalized difficulty proxy
    difficulty = min(1.0, max(0.0, difficulty))

    # Deterministic WDL mapping: difficulty -> win probability
    # Simple linear mapping: low difficulty -> high win, high difficulty -> low win
    win_prob = max(0.1, min(0.9, 0.6 - (difficulty * 0.4)))
    draw_prob = 0.1 + (difficulty * 0.1)  # 0.1 to 0.2
    loss_prob = 1.0 - win_prob - draw_prob

    pre_wdl = HumanWDL(w=win_prob, d=draw_prob, l=loss_prob)

    # Generate postByMove WDL (deterministic variation)
    post_by_move = {}
    for move in top_moves[:5]:  # Top 5 moves only
        # Slight variation based on move index
        move_factor = 1.0 - (move.p * 0.1)  # Better moves slightly improve win prob
        post_win = max(0.1, min(0.9, win_prob * move_factor))
        post_draw = draw_prob
        post_loss = 1.0 - post_win - post_draw
        post_by_move[move.uci] = HumanWDL(w=post_win, d=post_draw, l=post_loss)

    # Compute HDI
    wdl_sensitivity = abs(pre_wdl.w - post_by_move.get(legal_moves_uci[0] if legal_moves_uci else "", pre_wdl).w)
    hdi_value = (entropy * 0.4) + ((1.0 - top_gap) * 0.3) + (wdl_sensitivity * 0.3)

    hdi = HDI(
        value=hdi_value,
        components=HDIComponents(
            entropy=entropy,
            topGap=top_gap,
            wdlSensitivity=wdl_sensitivity,
        ),
    )

    # Generate narrative seeds (deterministic facts)
    narrative_seeds = []
    if top_gap < 0.1:
        narrative_seeds.append(
            NarrativeSeed(
                type="confusing",
                severity="medium",
                facts=[f"Top-3 moves have near-equal probability (gap={top_gap:.3f})"],
            )
        )
    if entropy > 5.0:
        narrative_seeds.append(
            NarrativeSeed(
                type="time-sensitive",
                severity="low",
                facts=[f"High policy entropy ({entropy:.2f}) suggests time pressure sensitivity"],
            )
        )
    if hdi_value > 0.7:
        narrative_seeds.append(
            NarrativeSeed(
                type="critical",
                severity="high",
                facts=[f"High Human Difficulty Index ({hdi_value:.2f}) indicates critical position"],
            )
        )

    # Compute input hash
    input_data = {
        "fen": fen,
        "ply": ply,
        "legalMoves": legal_moves_uci,
    }
    input_hash = canonical_hash(input_data)

    # Generate timestamp
    if generated_at is None:
        generated_at = datetime.now()

    # Build payload
    payload = ContextBridgePayload(
        position=Position(
            fen=fen,
            sideToMove=side_to_move,
            legalMoves=legal_moves_uci,
        ),
        conditioning=PositionConditioning(
            skillBucket="1200-1400",
            timePressureBucket="NORMAL",
            timeControlClass="blitz",
        ),
        policy=Policy(
            topMoves=top_moves,
            entropy=entropy,
            topGap=top_gap,
        ),
        humanWDL=HumanWDLContainer(
            pre=pre_wdl,
            postByMove=post_by_move,
        ),
        hdi=hdi,
        narrativeSeeds=narrative_seeds,
        meta=ContextBridgeMeta(
            schemaVersion="v1",
            generatedAt=generated_at,
            inputHash=input_hash,
        ),
    )

    # Convert to dict for JSON serialization
    return payload.model_dump(mode="json")

