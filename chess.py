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
    return (b << 9) & ~A_LINE & UNIVERSE


def _shift_right_down(b: B_BOARD):
    return (b >> 7) & ~A_LINE


def _shift_left_up(b: B_BOARD):
    return (b << 7) & ~H_LINE & UNIVERSE


def _shift_left_down(b: B_BOARD):
    return (b >> 9) & ~H_LINE


DIRECTIONS = {
    'P': ((_shift_up, _shift_up_up, _shift_left_up, _shift_right_up)),
    'N': None,
    'B': None,
    'R': None,
    'Q': None,
    'K': None
}


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

    def __init__(self):
        """
        new game
        """
        # White
        self.w_king = 576460752303423488
        self.w_pawns = 71776119061217280
        self.w_queens = 1152921504606846976
        self.w_bishops = 2594073385365405696
        self.w_knights = 4755801206503243776
        self.w_rooks = 9295429630892703744

        # Black
        self.b_king = 8
        self.b_pawns = 65280
        self.b_queens = 16
        self.b_bishops = 36
        self.b_knights = 66
        self.b_rooks = 129

    def __repr__(self):
        return b_board_to_str(self.all_pieces)

    def __str__(self):
        def populate(li, pieces, symbol):
            for k in _scan_lsb_first(pieces):
                li[k] = SYMBOLS[symbol]

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

    def gen_moves_white(self):
        pass

    def gen_moves_black(self):
        pass
