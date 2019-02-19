"""
A chess game

todo:
- Implement Game Loop
- Implement an uci parser
- Fix todos in logic code
- Up to now only pseudo legal moves are provided -> check for legality
- Undo / Redo
"""

UNIVERSE = 0xffffffffffffffff
EMPTY = 0

B_BOARD = int

PIECE_TYPES = [PAWN, KNIGHT, KING, QUEEN, BISHOP, ROOK] = range(1, 7)

H_LINE = 0x0101010101010101
G_LINE = H_LINE << 1
F_LINE = G_LINE << 1
E_LINE = F_LINE << 1
D_LINE = E_LINE << 1
C_LINE = D_LINE << 1
B_LINE = C_LINE << 1
A_LINE = B_LINE << 1

RANK_8 = 0xff
RANK_7 = RANK_8 << 8
RANK_6 = RANK_7 << 8
RANK_5 = RANK_6 << 8
RANK_4 = RANK_5 << 8
RANK_3 = RANK_4 << 8
RANK_2 = RANK_3 << 8
RANK_1 = RANK_2 << 8

TYPES = {
    1: 'p', 'p': 1,
    2: 'n', 'n': 2,
    3: 'k', 'k': 3,
    4: 'q', 'q': 4,
    5: 'b', 'b': 5,
    6: 'r', 'r': 6
}

SYMBOLS = {
    "R": u"♖", "r": u"♜",
    "N": u"♘", "n": u"♞",
    "B": u"♗", "b": u"♝",
    "Q": u"♕", "q": u"♛",
    "K": u"♔", "k": u"♚",
    "P": u"♙", "p": u"♟",
}

SQUARE_MASKS = [1 << sq for sq in range(64)]

WHITE = 1
BLACK = 0

SQUARE_NAMES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

BASEBOARD = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def _lsb(b: B_BOARD):
    return (b & -b).bit_length() - 1


def _msb(b: B_BOARD):
    return b.bit_length() - 1


def _is_empty(b: B_BOARD):
    return b == EMPTY


def _is_universe(b: B_BOARD):
    return b == UNIVERSE


def _scan_lsb_first(b: B_BOARD):
    while b:
        r = b & -b
        yield r.bit_length() - 1
        b ^= r


def _scan_single_values(b):
    v = 1
    while b:
        if b & 1:
            yield v
        b = b >> 1
        v = v << 1


def _set_bit(b: B_BOARD, index, x):
    mask = 1 << index
    b &= ~mask
    if x:
        b |= mask
    return b


def _shift_down(b: B_BOARD):
    return b >> 8


def _shift_down_down(b: B_BOARD):
    return b >> 16


def _shift_up(b: B_BOARD):
    return (b << 8) & UNIVERSE


def _shift_up_up(b: B_BOARD):
    return (b << 16) & UNIVERSE


def _shift_right(b: B_BOARD):
    return ((b >> 1) & ~A_LINE) & UNIVERSE


def _shift_right_right(b: B_BOARD):
    return ((b >> 2) & ~A_LINE) & UNIVERSE


def _shift_left(b: B_BOARD):
    return ((b << 1) & ~H_LINE) & UNIVERSE


def _shift_left_left(b: B_BOARD):
    return ((b << 2) & ~H_LINE) & UNIVERSE


def _shift_right_up(b: B_BOARD):
    return (b & ~A_LINE) << 9 & UNIVERSE


def _shift_right_down(b: B_BOARD):
    return (b & ~A_LINE) >> 7


def _shift_left_up(b: B_BOARD):
    return (b & ~H_LINE) << 7 & UNIVERSE


def _shift_left_down(b: B_BOARD):
    return (b & ~H_LINE) >> 9


DIAGONALS = [UL, DL, DR, UR] = range(4)

DIAGONAL_MOVS = {
    UL: lambda x: _shift_up(_shift_left(x)),
    DL: lambda x: _shift_down(_shift_left(x)),
    DR: lambda x: _shift_down(_shift_right(x)),
    UR: lambda x: _shift_up(_shift_right(x))

}

KNIGHT_MOVS = [
    lambda x: _shift_left(_shift_down_down(x)),
    lambda x: _shift_left(_shift_up_up(x)),
    lambda x: _shift_right(_shift_up_up(x)),
    lambda x: _shift_right(_shift_down_down(x)),
    lambda x: _shift_up(_shift_right_right(x)),
    lambda x: _shift_up(_shift_left_left(x)),
    lambda x: _shift_down(_shift_right_right(x)),
    lambda x: _shift_down(_shift_left_left(x)),
]

KING_MOVS = [_shift_right, _shift_right_down, _shift_down, _shift_left_down,
             _shift_left, _shift_left_up, _shift_up, _shift_right_up]

LINE_MOVS = [_shift_up, _shift_right, _shift_down, _shift_left]


def traverse_diagonal(square, diagonal, occupied, enemies):
    moves = 0
    sq = square
    shift = DIAGONAL_MOVS[diagonal]
    while True:
        sq = shift(sq)
        if sq & occupied:
            break
        moves |= sq
        if sq & enemies or sq == 0:
            break

    return moves


def traverse_line(square, shift, occupied, enemies):
    moves = 0
    sq = square

    while True:
        sq = shift(sq)
        if sq & occupied:
            break
        moves |= sq
        if sq & enemies or sq == 0:
            break

    return moves


def b_board_to_str(b: B_BOARD) -> str:
    """
    return a 8x8 board representation of 1's and 0's
    :param b: BitBoard
    """
    return '\n'.join(['{0:064b}'.format(b)[i:i + 8] for i in range(0, 64, 8)])


def rotate(b: B_BOARD):
    """
    rotate a board by 180 degrees
    see: https://www.chessprogramming.org/Flipping_Mirroring_and_Rotating#MirrorHorizontally
    """
    h1 = 0x5555555555555555
    h2 = 0x3333333333333333
    h4 = 0x0F0F0F0F0F0F0F0F
    v1 = 0x00FF00FF00FF00FF
    v2 = 0x0000FFFF0000FFFF
    x = b

    x = ((x >> 1) & h1) | ((x & h1) << 1)
    x = ((x >> 2) & h2) | ((x & h2) << 2)
    x = ((x >> 4) & h4) | ((x & h4) << 4)
    x = ((x >> 8) & v1) | ((x & v1) << 8)
    x = ((x >> 16) & v2) | ((x & v2) << 16)
    x = (x >> 32) | (x << 32)
    return x


class Board:
    """
    This class stores all pieces for a game
    """

    def __init__(self, fen=None):
        """
        new game
        """
        # White pieces
        self.b_king = 0
        self.b_pawns = 0
        self.b_queens = 0
        self.b_bishops = 0
        self.b_knights = 0
        self.b_rooks = 0

        # Black pieces
        self.w_king = 0
        self.w_pawns = 0
        self.w_queens = 0
        self.w_bishops = 0
        self.w_knights = 0
        self.w_rooks = 0

        # state
        self.active_player = 1
        self.black_king_side_castle_right = True
        self.black_queen_side_castle_right = True
        self.white_king_side_castle_right = True
        self.white_queen_side_castle_right = True
        self.ep_move = None
        self.half_move_clock = 0
        self.move_number = 0

        fen = BASEBOARD if fen is None else fen
        self.from_fen(fen)

    def __repr__(self):
        return b_board_to_str(self.all_pieces)

    def __str__(self):
        def populate(li, pieces, symbol):
            for k in _scan_lsb_first(pieces):
                li[63 - k] = SYMBOLS[symbol]

        def name_bar() -> str:
            return '{offset}{row}{offset}\n'.format(offset=2 * ' ', row=' '.join(SQUARE_NAMES))

        s = 64 * ['.']

        # kings
        populate(s, self.w_king, 'K')
        populate(s, self.b_king, 'k')

        # pawns
        populate(s, self.w_pawns, 'P')
        populate(s, self.b_pawns, 'p')

        # queens
        populate(s, self.w_queens, 'Q')
        populate(s, self.b_queens, 'q')

        # knights
        populate(s, self.w_knights, 'N')
        populate(s, self.b_knights, 'n')

        # bishops
        populate(s, self.w_bishops, 'B')
        populate(s, self.b_bishops, 'b')

        # rooks
        populate(s, self.w_rooks, 'R')
        populate(s, self.b_rooks, 'r')

        t = name_bar()
        for i in range(8):
            t += '{i} {row} {i}\n'.format(i=i + 1, row=' '.join(s[i * 8: i * 8 + 8]))
        t += name_bar()
        return t

    def reset(self):
        # White pieces
        self.b_king = 0
        self.b_pawns = 0
        self.b_queens = 0
        self.b_bishops = 0
        self.b_knights = 0
        self.b_rooks = 0

        # Black pieces
        self.w_king = 0
        self.w_pawns = 0
        self.w_queens = 0
        self.w_bishops = 0
        self.w_knights = 0
        self.w_rooks = 0

        # state
        self.active_player = 1
        self.black_king_side_castle_right = True
        self.black_queen_side_castle_right = True
        self.white_king_side_castle_right = True
        self.white_queen_side_castle_right = True
        self.ep_move = None
        self.half_move_clock = 0
        self.move_number = 0

    def from_fen(self, text):
        # todo make more robust

        # reset all values
        self.reset()

        sq = 1 << 63

        text = text.split(' ')
        pieces = text[0]
        for symbol in pieces:
            if symbol.isdigit():
                sq = sq >> int(symbol)
            elif symbol in SYMBOLS.keys():
                if symbol == 'p':
                    self.b_pawns |= sq
                elif symbol == 'P':
                    self.w_pawns |= sq
                elif symbol == 'r':
                    self.b_rooks |= sq
                elif symbol == 'R':
                    self.w_rooks |= sq
                elif symbol == 'n':
                    self.b_knights |= sq
                elif symbol == 'N':
                    self.w_knights |= sq
                elif symbol == 'b':
                    self.b_bishops |= sq
                elif symbol == 'B':
                    self.w_bishops |= sq
                elif symbol == 'q':
                    self.b_queens |= sq
                elif symbol == 'Q':
                    self.w_queens |= sq
                elif symbol == 'k':
                    self.b_king |= sq
                elif symbol == 'K':
                    self.w_king |= sq
                sq = sq >> 1
        self.active_player = True if text[1] == 'w' else False
        self.black_king_side_castle_right = 'k' in text[2]
        self.black_queen_side_castle_right = 'q' in text[2]
        self.white_king_side_castle_right = 'K' in text[2]
        self.white_queen_side_castle_right = 'q' in text[2]
        self.ep_move = text[3] if text[3] != "-" else None
        self.half_move_clock = int(text[4])
        self.move_number = int(text[5])

    def to_fen(self):
        # todo implement
        pass

    @property
    def all_white_pieces(self):
        return self.w_king | self.w_pawns | self.w_bishops | self.w_knights | self.w_queens | self.w_rooks

    @property
    def all_black_pieces(self):
        return self.b_king | self.b_pawns | self.b_bishops | self.b_knights | self.b_queens | self.b_rooks

    @property
    def all_pieces(self):
        return self.all_black_pieces | self.all_white_pieces

    def pieces_of_type(self, p_type: str, player: bool):
        if p_type not in TYPES:
            raise ValueError('Invalid piece type!')

        if p_type == 'k' or p_type == KING:
            p = self.w_king if player else self.b_king
        elif p_type == 'p' or p_type == PAWN:
            p = self.w_pawns if player else self.b_pawns
        elif p_type == 'q' or p_type == QUEEN:
            p = self.w_queens if player else self.b_queens
        elif p_type == 'b' or p_type == BISHOP:
            p = self.w_bishops if player else self.b_bishops
        elif p_type == 'n' or p_type == KNIGHT:
            p = self.w_knights if player else self.b_knights
        else:  # rook
            p = self.w_rooks if player else self.b_rooks
        return p

    def gen_moves(self, player, exclude_attacked_fields=False):
        enemies = self.all_black_pieces if player else self.all_white_pieces
        occupied = self.all_white_pieces if player else self.all_black_pieces
        moves = 0

        # PAWNS
        pawns = self.w_pawns if player else self.b_pawns

        # one step
        mov_v = _shift_up if player else _shift_down
        pos = mov_v(pawns) & ~occupied & ~enemies
        moves |= pos

        # two steps
        pos = pos & RANK_6 if player else pos & RANK_3
        pos = mov_v(pos) & ~occupied & ~enemies
        moves |= pos

        # diagonal attacks
        mov_ds = (_shift_left_up, _shift_right_up) if player else (_shift_left_down, _shift_right_down)
        for mov_d in mov_ds:
            pos = mov_d(pawns) & ~occupied & enemies
            moves |= pos

        # todo en passant

        # KING
        king = self.w_king if player else self.b_king
        attacked_fields = 0 if exclude_attacked_fields else self.gen_moves(not player, True)

        for mov in KING_MOVS:
            moves |= mov(king) & ~occupied & ~attacked_fields

        # todo castle

        # KNIGHTS
        knights = self.w_knights if player else self.b_knights
        for mov in KNIGHT_MOVS:
            moves |= mov(knights) & ~occupied

        # ROOKS
        rooks = self.w_rooks if player else self.b_rooks
        for shift in LINE_MOVS:
            moves |= traverse_line(rooks, shift, occupied, enemies)

        # BISHOPS
        bishops = self.w_bishops if player else self.b_bishops
        for diagonal in DIAGONALS:
            moves |= traverse_diagonal(bishops, diagonal, occupied, enemies)

        # QUEENS
        queens = self.w_queens if player else self.b_queens
        for shift in LINE_MOVS:
            moves |= traverse_line(queens, shift, occupied, enemies)

        for diagonal in DIAGONALS:
            moves |= traverse_diagonal(queens, diagonal, occupied, enemies)

        return moves

    def move(self, sq, to):
        pass


class Move:
    def __init__(self):
        pass
