import argparse
import os
import pygame
from core.defs import PuzzleDefinition, TYPE_CORNER, TYPE_EDGE
from core import board as board_module
from ui.headless import BoardUi

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-conf", required=True)
    parser.add_argument("-hints", default=None)
    parser.add_argument("-load", default=None)
    args = parser.parse_args()

    puzzle_def = PuzzleDefinition()
    puzzle_def.load(args.conf, args.hints)

    board = board_module.Board(puzzle_def)

    if args.load:
        board.load(args.load)
        for id in range(1, puzzle_def.width*puzzle_def.height+1):
            if id not in board.board_by_id:
                piece = board.puzzle_def.all[id]
                if piece.get_type() == TYPE_CORNER:
                    slots = board.enumerate_corners()
                elif piece.get_type() == TYPE_EDGE:
                    slots = board.enumerate_edges()
                else:
                    slots = board.enumerate_inner()
                for i,j in slots:
                    if not board.board[i][j]:
                        board.put_piece(i,j,piece,0)
                        break
        board.fix_orientation()
    else:
        board.randomize()
        board.heuristic_orientation()

    # Marque les pièces
    for i in range(puzzle_def.height):
        for j in range(puzzle_def.width):
            if board.board[i][j]:
                board.marks[i][j] = board.board[i][j].piece_def.id

    # Initialisation UI
    ui = BoardUi(board)
    ui.init()

    # Sauvegarde images
    score = board.evaluate()
    os.makedirs("img", exist_ok=True)
    ui.save(f"img/partial_solution_{score}_with_marks.jpg", marks=True)
    ui.save(f"img/partial_solution_{score}_without_marks.jpg", marks=False)

    pygame.quit()
