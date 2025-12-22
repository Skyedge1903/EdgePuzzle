import pygame
import os
import sys

GRAY = (53, 87, 100)
EMPTY_GRAY = (192, 192, 192)
WHITE = (255, 255, 255)


class BoardUi:

    def __init__(self, board):
        self.board = board
        self.piece_width = 50
        self.font = None
        self.piece_img = {}
        self.empty_img = None
        self.marks_enabled = True
        self.SURFACE = None

    def init(self):
        # Driver headless Linux si nécessaire
        if os.name != "nt":
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        pygame.init()
        pygame.font.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME | pygame.HIDDEN)

        self.font = pygame.font.SysFont('Comic Sans MS', 12, bold=True)

        max_dim = max(self.board.puzzle_def.width, self.board.puzzle_def.height)
        self.piece_width = ((800 // max_dim) // 4) * 4

        width_px = self.piece_width * self.board.puzzle_def.width
        height_px = self.piece_width * self.board.puzzle_def.height

        self.SURFACE = pygame.Surface((width_px, height_px))
        self.SURFACE.fill(WHITE)

        # Chargement des images de couleurs
        color_images = {}
        for i in range(1, 23):
            path = os.path.join("data", "patterns", f"pattern{i}.png")
            if not os.path.exists(path):
                print(f"[WARNING] Image manquante: {path}", file=sys.stderr)
                continue
            color_images[i] = pygame.image.load(path).convert_alpha()

        color_dim = color_images[1].get_height() if 1 in color_images else 50

        for id, piece in self.board.puzzle_def.all.items():
            self.piece_img[id] = []
            high_res = pygame.Surface((2 * color_dim, 2 * color_dim), pygame.SRCALPHA)
            high_res.fill(GRAY)

            for idx, angle, pos in zip([2,3,1,0],[0,270,90,180], [(0,0),(color_dim,0),(0,color_dim),(color_dim,color_dim)]):
                color_id = piece.colors[idx]
                if color_id != 0 and color_id in color_images:
                    high_res.blit(pygame.transform.rotate(color_images[color_id], angle), pos)

            for dir in range(4):
                high_res2 = pygame.transform.rotate(high_res, 45 - dir * 90)
                h = high_res2.get_height() // 4
                low_res = pygame.Surface((2*h, 2*h), pygame.SRCALPHA)
                low_res.blit(high_res2, (0,0), (h,h,2*h,2*h))
                low_res = pygame.transform.scale(low_res, (self.piece_width, self.piece_width))
                pygame.draw.line(low_res, (50,50,50), (0,0),(self.piece_width,self.piece_width),2)
                pygame.draw.line(low_res, (50,50,50), (self.piece_width,0),(0,self.piece_width),2)
                self.piece_img[id].append(low_res)

        self.empty_img = pygame.Surface((self.piece_width, self.piece_width))
        self.empty_img.fill(EMPTY_GRAY)

        self.update()

    def draw(self, piece, x, y):
        border_points = [(x,y),(x,y+self.piece_width),(x+self.piece_width,y+self.piece_width),(x+self.piece_width,y)]

        if piece:
            i,j = piece.i, piece.j
            pid = piece.piece_def.id
            self.SURFACE.blit(self.piece_img[pid][piece.dir], (x,y))

            if self.board.marks[i][j] and self.marks_enabled:
                textsurface = self.font.render(str(self.board.marks[i][j]), False, WHITE)
                text_rect = textsurface.get_rect(center=(x+self.piece_width//2, y+self.piece_width//2))

                s = pygame.Surface((25,20))
                s.set_alpha(100)
                s.fill((50,50,50))
                centered = s.get_rect(center=(x+self.piece_width//2, y+self.piece_width//2))
                self.SURFACE.blit(s, centered)
                self.SURFACE.blit(textsurface, text_rect)
        else:
            self.SURFACE.blit(self.empty_img, (x,y))

        pygame.draw.lines(self.SURFACE, (50,50,50), True, border_points, 2)

    def update(self):
        for i in range(self.board.puzzle_def.height):
            for j in range(self.board.puzzle_def.width):
                self.draw(self.board.board[i][j], self.piece_width*j, self.piece_width*i)

    def save(self, filename, marks=True):
        prev_marks = self.marks_enabled
        self.marks_enabled = marks
        self.update()
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        pygame.image.save(self.SURFACE, filename)
        self.marks_enabled = prev_marks
