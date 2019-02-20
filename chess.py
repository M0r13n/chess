"""
A chess game

todo:
- Implement Game Loop
- Implement an uci parser
- Fix todos in logic code
- Up to now only pseudo legal moves are provided -> check for legality
- Undo / Redo
- board layout is screwed
"""

from itertools import groupby

UNIVERSE = 0xffffffffffffffff
EMPTY = 0

B_BOARD = int

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

SYMBOLS = {
    "R": u"♖", "r": u"♜",
    "N": u"♘", "n": u"♞",
    "B": u"♗", "b": u"♝",
    "Q": u"♕", "q": u"♛",
    "K": u"♔", "k": u"♚",
    "P": u"♙", "p": u"♟",
}

FIELDS = [
    A1, B1, C1, D1, E1, F1, G1, H1,
    A2, B2, C2, D2, E2, F2, G2, H2,
    A3, B3, C3, D3, E3, F3, G3, H3,
    A4, B4, C4, D4, E4, F4, G4, H4,
    A5, B5, C5, D5, E5, F5, G5, H5,
    A6, B6, C6, D6, E6, F6, G6, H6,
    A7, B7, C7, D7, E7, F7, G7, H7,
    A8, B8, C8, D8, E8, F8, G8, H8,

] = range(63, -1, -1)

SQUARES = {
    'a1': A1, 'a2': A2, 'a3': A3, 'a4': A4, 'a5': A5, 'a6': A6, 'a7': A7, 'a8': A8,
    'b1': B1, 'b2': B2, 'b3': B3, 'b4': B4, 'b5': B5, 'b6': B6, 'b7': B7, 'b8': B8,
    'c1': C1, 'c2': C2, 'c3': C3, 'c4': C4, 'c5': C5, 'c6': C6, 'c7': C7, 'c8': C8,
    'd1': D1, 'd2': D2, 'd3': D3, 'd4': D4, 'd5': D5, 'd6': D6, 'd7': D7, 'd8': D8,
    'e1': E1, 'e2': E2, 'e3': E3, 'e4': E4, 'e5': E5, 'e6': E6, 'e7': E7, 'e8': E8,
    'f1': F1, 'f2': F2, 'f3': F3, 'f4': F4, 'f5': F5, 'f6': F6, 'f7': F7, 'f8': F8,
    'g1': G1, 'g2': G2, 'g3': G3, 'g4': G4, 'g5': G5, 'g6': G6, 'g7': G7, 'g8': G8,
    'h1': H1, 'h2': H2, 'h3': H3, 'h4': H4, 'h5': H5, 'h6': H6, 'h7': H7, 'h8': H8,
}

SQUARE_MASK = [1 << sq for sq in range(64)]

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
        self.PIECES = {
            'p': 0,
            'b': 0,
            'n': 0,
            'k': 0,
            'q': 0,
            'r': 0,
            'P': 0,
            'B': 0,
            'N': 0,
            'K': 0,
            'Q': 0,
            'R': 0
        }

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
        return self.to_fen()

    def __str__(self):
        def name_bar() -> str:
            return '{offset}{row}{offset}\n'.format(offset=2 * ' ', row=' '.join(SQUARE_NAMES))

        s = 64 * ['.']
        for symbol, p in self.PIECES.items():
            for k in _scan_lsb_first(p):
                s[63 - k] = SYMBOLS[symbol]

        t = name_bar()
        for i in range(8):
            t += '{i} {row} {i}\n'.format(i=i + 1, row=' '.join(s[i * 8: i * 8 + 8]))
        t += name_bar()
        return t

    def reset(self):
        self.PIECES = {
            'p': 0,
            'b': 0,
            'n': 0,
            'k': 0,
            'q': 0,
            'r': 0,
            'P': 0,
            'B': 0,
            'N': 0,
            'K': 0,
            'Q': 0,
            'R': 0
        }
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
        # reset all values
        self.reset()

        sq = 1 << 63

        text = text.split(' ')
        if len(text) != 6:
            raise ValueError("Invalid FEN string supplied")

        pieces = text[0]
        for symbol in pieces:
            if symbol.isdigit():
                sq = sq >> int(symbol)
            elif symbol in self.PIECES:
                self.PIECES[symbol] |= sq
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
        s = 64 * ['.']

        # place all piece symbols
        for symbol, p in self.PIECES.items():
            for k in _scan_lsb_first(p):
                s[63 - k] = symbol

        # insert /
        for i in range(7):
            s.insert(8 + i * 8 + i, '/')

        # replace .
        s = [str(len(list(s))) if _ else ''.join(list(s)) for _, s in groupby(s, key=lambda x: x == '.')]

        # append additional state information
        s.append(' w ' if self.active_player else ' b ')
        s.append('K' if self.white_king_side_castle_right else None)
        s.append('Q' if self.white_queen_side_castle_right else None)
        s.append('k' if self.black_king_side_castle_right else None)
        s.append('q' if self.black_queen_side_castle_right else None)
        s.append(' {} '.format(self.ep_move if self.ep_move else "-"))
        s.append('{} '.format(self.half_move_clock))
        s.append('{}'.format(self.move_number))

        return ''.join(s)

    @property
    def all_white_pieces(self) -> int:
        pieces = 0
        for symbol, val in self.PIECES.items():
            if symbol.isupper():
                pieces |= val
        return pieces

    @property
    def all_black_pieces(self) -> int:
        pieces = 0
        for symbol, val in self.PIECES.items():
            if symbol.islower():
                pieces |= val
        return pieces

    @property
    def all_pieces(self) -> int:
        return self.all_black_pieces | self.all_white_pieces

    def pieces_of_type(self, p_type: str):
        if p_type not in self.PIECES:
            raise ValueError('Invalid piece type!')

        return self.PIECES[p_type]

    def gen_moves(self, player, exclude_attacked_fields=False):
        enemies = self.all_black_pieces if player else self.all_white_pieces
        occupied = self.all_white_pieces if player else self.all_black_pieces
        moves = 0

        # PAWNS
        pawns = self.PIECES['P'] if player else self.PIECES['p']

        # one step
        mov_v = _shift_up if player else _shift_down
        pos = mov_v(pawns) & ~occupied & ~enemies
        moves |= pos

        # two steps
        pos = pos & RANK_6 if player else pos & RANK_3
        pos = mov_v(pos) & ~occupied & ~enemies
        moves |= pos

        # diagonal attacks including en passant
        mov_ds = (_shift_left_up, _shift_right_up) if player else (_shift_left_down, _shift_right_down)

        if self.ep_move:
            enemies |= SQUARE_MASK[SQUARES[self.ep_move]]

        for mov_d in mov_ds:
            pos = mov_d(pawns) & ~occupied & enemies
            moves |= pos

        if self.ep_move:
            enemies &= ~SQUARE_MASK[SQUARES[self.ep_move]]

        # KING
        king = self.PIECES['K'] if player else self.PIECES['k']
        attacked_fields = 0 if exclude_attacked_fields else self.gen_moves(not player, True)

        for mov in KING_MOVS:
            moves |= mov(king) & ~occupied & ~attacked_fields

        # todo castle

        # KNIGHTS
        knights = self.PIECES['N'] if player else self.PIECES['n']
        for mov in KNIGHT_MOVS:
            moves |= mov(knights) & ~occupied

        # ROOKS
        rooks = self.PIECES['R'] if player else self.PIECES['r']
        for shift in LINE_MOVS:
            moves |= traverse_line(rooks, shift, occupied, enemies)

        # BISHOPS
        bishops = self.PIECES['B'] if player else self.PIECES['b']
        for diagonal in DIAGONALS:
            moves |= traverse_diagonal(bishops, diagonal, occupied, enemies)

        # QUEENS
        queens = self.PIECES['Q'] if player else self.PIECES['q']
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
