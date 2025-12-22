import os
import pygame

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
        # --- SDL HEADLESS SAFE INIT ---
        if os.name != "nt":  # Linux / Docker
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

        pygame.init()
        pygame.font.init()

        # IMPORTANT : pas de display.set_mode en headless
        # On travaille uniquement avec des Surfaces offscreen

        self.font = pygame.font.SysFont("DejaVu Sans", 14, bold=True)

        max_dim = max(
            self.board.puzzle_def.width,
            self.board.puzzle_def.height
        )
        self.piece_width = max(32, ((1000 // max_dim) // 4) * 4)

        width_px = self.piece_width * self.board.puzzle_def.width
        height_px = self.piece_width * self.board.puzzle_def.height

        self.SURFACE = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
        self.SURFACE.fill(WHITE)

        # --- LOAD COLOR PATTERNS ---
        color_images = {}
        for i in range(1, 23):
            path = f"data/patterns/pattern{i}.png"
            color_images[i] = pygame.image.load(path).convert_alpha()

        color_dim = color_images[1].get_height()

        for pid, piece in self.board.puzzle_def.all.items():
            self.piece_img[pid] = []

            high_res = pygame.Surface((2 * color_dim, 2 * color_dim), pygame.SRCALPHA)
            high_res.fill(GRAY)

            mapping = [
                (2, 0, 0),
                (3, 270, color_dim),
                (1, 90, color_dim),
                (0, 180, color_dim),
            ]

            for idx, rot, offset in mapping:
                cid = piece.colors[idx]
                if cid:
                    img = pygame.transform.rotate(color_images[cid], rot)
                    x = offset if rot in (270, 180) else 0
                    y = offset if rot in (90, 180) else 0
                    high_res.blit(img, (x, y))

            for d in range(4):
                rotated = pygame.transform.rotate(high_res, 45 - d * 90)
                h = rotated.get_height() // 4
                crop = pygame.Surface((2 * h, 2 * h), pygame.SRCALPHA)
                crop.blit(rotated, (0, 0), (h, h, 2 * h, 2 * h))

                final = pygame.transform.smoothscale(
                    crop,
                    (self.piece_width, self.piece_width)
                )

                pygame.draw.line(final, (40, 40, 40), (0, 0), (self.piece_width, self.piece_width), 2)
                pygame.draw.line(final, (40, 40, 40), (self.piece_width, 0), (0, self.piece_width), 2)

                self.piece_img[pid].append(final)

        self.empty_img = pygame.Surface((self.piece_width, self.piece_width))
        self.empty_img.fill(EMPTY_GRAY)

        self.update()

    def draw(self, piece, x, y):
        if piece:
            pid = piece.piece_def.id
            self.SURFACE.blit(self.piece_img[pid][piece.dir], (x, y))

            if self.marks_enabled and self.board.marks[piece.i][piece.j]:
                value = str(self.board.marks[piece.i][piece.j])
                txt = self.font.render(value, True, (255, 255, 255))
                rect = txt.get_rect(center=(x + self.piece_width // 2, y + self.piece_width // 2))

                bg = pygame.Surface((rect.width + 6, rect.height + 4), pygame.SRCALPHA)
                bg.fill((30, 30, 30, 180))
                bg_rect = bg.get_rect(center=rect.center)

                self.SURFACE.blit(bg, bg_rect)
                self.SURFACE.blit(txt, rect)
        else:
            self.SURFACE.blit(self.empty_img, (x, y))

        pygame.draw.rect(
            self.SURFACE,
            (40, 40, 40),
            (x, y, self.piece_width, self.piece_width),
            1
        )

    def update(self):
        for i in range(self.board.puzzle_def.height):
            for j in range(self.board.puzzle_def.width):
                self.draw(
                    self.board.board[i][j],
                    j * self.piece_width,
                    i * self.piece_width,
                )

    def save(self, filename, marks=True):
        prev = self.marks_enabled
        self.marks_enabled = marks
        self.update()

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        pygame.image.save(self.SURFACE, filename)

        self.marks_enabled = prev
