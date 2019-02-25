"""
A chess game

todo:
- Implement Game Loop
- Up to now only pseudo legal moves are provided -> check for legality
- Undo / Redo
"""

from itertools import groupby
import re

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

RANK_1 = 0xff
RANK_2 = RANK_1 << 8
RANK_3 = RANK_2 << 8
RANK_4 = RANK_3 << 8
RANK_5 = RANK_4 << 8
RANK_6 = RANK_5 << 8
RANK_7 = RANK_6 << 8
RANK_8 = RANK_7 << 8

PIECES = [KING, QUEEN, KNIGHT, BISHOP, ROOK, PAWN] = range(6)
PROMOTION = ['N', 'n', 'B', 'b', 'Q', 'q', 'R', 'r']

SYMBOLS = {
    "R": u"♖", "r": u"♜",
    "N": u"♘", "n": u"♞",
    "B": u"♗", "b": u"♝",
    "Q": u"♕", "q": u"♛",
    "K": u"♔", "k": u"♚",
    "P": u"♙", "p": u"♟",
}

FIELDS = [
    A8, B8, C8, D8, E8, F8, G8, H8,
    A7, B7, C7, D7, E7, F7, G7, H7,
    A6, B6, C6, D6, E6, F6, G6, H6,
    A5, B5, C5, D5, E5, F5, G5, H5,
    A4, B4, C4, D4, E4, F4, G4, H4,
    A3, B3, C3, D3, E3, F3, G3, H3,
    A2, B2, C2, D2, E2, F2, G2, H2,
    A1, B1, C1, D1, E1, F1, G1, H1,
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

KSCR_W = 0x6
KSCR_B = 0x600000000000000

QSCR_W = 0x30
SQCR_B = 0x3000000000000000


def _lsb(b: B_BOARD):
    return (b & -b).bit_length() - 1


def _msb(b: B_BOARD):
    return b.bit_length() - 1


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
    return ((b >> 2) & ~A_LINE & ~B_LINE) & UNIVERSE


def _shift_left(b: B_BOARD):
    return ((b << 1) & ~H_LINE) & UNIVERSE


def _shift_left_left(b: B_BOARD):
    return ((b << 2) & ~H_LINE & ~G_LINE) & UNIVERSE


def _shift_right_up(b: B_BOARD):
    return (b & ~A_LINE) << 9 & UNIVERSE


def _shift_right_down(b: B_BOARD):
    return (b & ~A_LINE) >> 7


def _shift_left_up(b: B_BOARD):
    return (b & ~H_LINE) << 7 & UNIVERSE


def _shift_left_down(b: B_BOARD):
    return (b & ~H_LINE) >> 9


def _traverse_delta(square, delta, occupied, enemies):
    moves = 0
    sq = square

    while True:
        sq = delta(sq)
        if sq & occupied:
            break
        moves |= sq
        if sq & enemies or sq == 0:
            break

    return moves


STEPS = [_shift_right, _shift_left, _shift_up, _shift_down]
SLIDES = [_shift_right_up, _shift_right_down, _shift_left_down, _shift_left_up]
DIRECTIONS = STEPS + SLIDES
KNIGHT_MOVS = [
    lambda x: _shift_left(_shift_down_down(x)),
    lambda x: _shift_left(_shift_up_up(x)),
    lambda x: _shift_right(_shift_up_up(x)),
    lambda x: _shift_right(_shift_down_down(x)),
    lambda x: _shift_up(_shift_right_right(x)),  # bastard
    lambda x: _shift_up(_shift_left_left(x)),
    lambda x: _shift_down(_shift_right_right(x)),
    lambda x: _shift_down(_shift_left_left(x)),
]


def _king_moves(king):
    moves = 0
    for mov in DIRECTIONS:
        moves |= mov(king)  # King
    return moves


def _queen_moves(queen, occupied, enemies):
    moves = 0
    for mov in DIRECTIONS:
        moves |= _traverse_delta(queen, mov, occupied, enemies)  # queen
    return moves


def _bishop_moves(bishop, occupied, enemies):
    moves = 0
    for slide in SLIDES:
        moves |= _traverse_delta(bishop, slide, occupied, enemies)
    return moves


def _rook_moves(rook, occupied, enemies):
    moves = 0
    for step in STEPS:
        moves |= _traverse_delta(rook, step, occupied, enemies)
    return moves


def _pawn_moves(pawn, player):
    if player:
        return _shift_up(pawn) | _shift_up_up(pawn & RANK_2)
    return _shift_down(pawn) | _shift_down_down(pawn & RANK_7)


def _pawn_attacks(pawn, player):
    if player:
        return _shift_right_up(pawn) | _shift_left_up(pawn)
    return _shift_right_down(pawn) | _shift_left_down(pawn)


def _knight_move(knight, occupied, *args):
    moves = 0
    for move in KNIGHT_MOVS:
        moves |= move(knight)
    return moves & ~occupied


def _knight_attacks(knight):
    moves = 0
    for move in KNIGHT_MOVS:
        moves |= move(knight)
    return moves


def b_board_to_str(b: B_BOARD) -> str:
    """
    return a 8x8 board representation of 1's and 0's
    :param b: BitBoard
    """
    return '\n'.join(['{0:064b}'.format(b)[i:i + 8] for i in range(0, 64, 8)])


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
            t += '{i} {row} {i}\n'.format(i=8 - i, row=' '.join(s[i * 8: i * 8 + 8]))
        t += name_bar()
        return t

    def reset(self):
        self.PIECES = {
            'k': 0,
            'q': 0,
            'n': 0,
            'b': 0,
            'r': 0,
            'p': 0,
            'K': 0,
            'Q': 0,
            'N': 0,
            'B': 0,
            'R': 0,
            'P': 0
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

    def _all_white_pieces(self) -> int:
        pieces = 0
        for symbol, val in self.PIECES.items():
            if symbol.isupper():
                pieces |= val
        return pieces

    def _all_black_pieces(self) -> int:
        pieces = 0
        for symbol, val in self.PIECES.items():
            if symbol.islower():
                pieces |= val
        return pieces

    def _all_pieces(self) -> int:
        return self._all_black_pieces() | self._all_white_pieces()

    def _filter_pieces_by_side(self, player):
        return [v for k, v in self.PIECES.items() if (k.isupper() if player else k.islower())]

    def attacked_fields(self, by_player) -> B_BOARD:
        """
        this methods returns every field that is currently under attack by the specified player
        :param by_player:
        :return:
        """
        attacked_fields = 0
        occupied = self._all_white_pieces() if by_player else self._all_black_pieces()
        enemies = self._all_black_pieces() if by_player else self._all_white_pieces()
        king, queens, knights, bishops, rooks, pawns = self._filter_pieces_by_side(by_player)

        attacked_fields |= _king_moves(king)
        attacked_fields |= _queen_moves(queens, occupied, enemies)
        attacked_fields |= _bishop_moves(bishops, occupied, enemies)
        attacked_fields |= _rook_moves(rooks, occupied, enemies)
        attacked_fields |= _knight_attacks(knights)
        attacked_fields |= _pawn_attacks(pawns, by_player)

        return attacked_fields

    def gen_pseudo_legal_moves(self, player=None):
        if player is None:
            player = self.active_player

        occupied = self._all_white_pieces() if player else self._all_black_pieces()
        enemies = self._all_black_pieces() if player else self._all_white_pieces()
        king, queens, knights, bishops, rooks, pawns = [v for k, v in self.PIECES.items() if
                                                        (k.isupper() if player else k.islower())]

        # iterate piece by piece over queens, bishops, rooks and knights:
        for p, move in zip((queens, bishops, rooks, knights), (_queen_moves, _bishop_moves, _rook_moves, _knight_move)):
            for i in _scan_lsb_first(p):
                moves = move(SQUARE_MASK[i], occupied, enemies)
                for j in _scan_lsb_first(moves):
                    yield Move(i, j)

        for i in _scan_lsb_first(_king_moves(king) & ~occupied & ~self.attacked_fields(not player)):
            yield Move(_lsb(king), i)

        for p in _scan_lsb_first(pawns):
            moves = _pawn_moves(SQUARE_MASK[p], player) | (_pawn_attacks(SQUARE_MASK[p], player) & enemies)
            for j in _scan_lsb_first(moves):
                yield Move(p, j)

        # En passant
        if self.ep_move:
            move = _pawn_attacks(pawns, player) & SQUARE_MASK[SQUARES[self.ep_move]]
            if move:
                yield Move(next(_scan_lsb_first(move)), SQUARES[self.ep_move])

        # Castle
        if self.white_king_side_castle_right and (king & ~self.attacked_fields(not player)):
            move = (_shift_right(king) | _shift_right_right(king)) & ~self.attacked_fields(not player) & ~occupied
            if move == KSCR_W:
                yield Move(_lsb(king), _lsb(move))

        if self.black_king_side_castle_right and (king & ~self.attacked_fields(not player)):
            move = (_shift_right(king) | _shift_right_right(king)) & ~self.attacked_fields(not player) & ~occupied
            if move == KSCR_B:
                yield Move(_lsb(king), _lsb(move))

        if self.white_queen_side_castle_right and (king & ~self.attacked_fields(not player)):
            move = (_shift_left(king) | _shift_left_left(king)) & ~self.attacked_fields(not player) & ~occupied
            if move == QSCR_W:
                yield Move(_lsb(king), _msb(move))

        if self.black_queen_side_castle_right and (king & ~self.attacked_fields(not player)):
            move = (_shift_left(king) | _shift_left_left(king)) & ~self.attacked_fields(not player) & ~occupied
            if move == SQCR_B:
                yield Move(_lsb(king), _msb(move))

    def get_piece(self, square):
        sq = SQUARE_MASK[square]
        for k, v in self.PIECES.items():
            if v & sq:
                return k

    def make_move(self, move):
        """
        NOT YET FINISHED
        TODO
        """
        if move not in list(self.gen_pseudo_legal_moves()):
            raise ValueError("Invalid Move")

        from_square, to_square = move.from_square, move.to_square
        from_piece, to_piece = self.get_piece(from_square), self.get_piece(to_square)

        backup = self.to_fen()

        # move and remove hostile piece if it exists
        self.PIECES[from_piece] &= ~SQUARE_MASK[from_square]
        self.PIECES[from_piece] |= SQUARE_MASK[to_square]
        if to_piece is not None:
            self.PIECES[to_piece] &= ~SQUARE_MASK[to_square]

        # castle
        if from_piece == 'K' or from_piece == 'k':
            if not _king_moves(self.PIECES[from_piece]) & SQUARE_MASK[to_square]:
                if from_square > to_square:
                    print("King-side Castle")
                else:
                    print("Queen-side Castle")

        # ep
        # legal ? --> False = Undo
        # if so switch players, check if castle rights are still valid
        self.active_player = not self.active_player


class Move:

    def __init__(self, from_square, to_square, promotion=False):
        self.from_square = from_square
        self.to_square = to_square
        self.promotion = promotion

    @property
    def uci(self):
        keys = list(SQUARES.keys())
        vals = list(SQUARES.values())
        return "{f}{t}{p}".format(
            f=keys[vals.index(self.from_square)],
            t=keys[vals.index(self.to_square)],
            p=self.promotion if self.promotion else ""
        )

    @staticmethod
    def from_uci(uci):
        uci = uci.lower()
        m = re.match('([a-h][1-8])([a-h][1-8])(.)?', uci)
        promotion = m.group(3)
        if promotion is not None and promotion not in PROMOTION:
            raise ValueError("Invalid Promotion Piece provided!")
        return Move(SQUARES[m.group(1)], SQUARES[m.group(2)], bool(promotion))

    def __eq__(self, other):
        return (self.from_square == other.from_square and
                self.to_square == other.to_square and
                self.promotion == other.promotion)

    def __repr__(self):
        return self.uci

    def __hash__(self):
        return hash((self.to_square, self.from_square, self.promotion))

    def __copy__(self):
        return type(self)(self.from_square, self.to_square, self.promotion)
