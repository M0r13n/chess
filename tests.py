import abc
import traceback


class BaseTest:
    __metaclass__ = abc.ABCMeta

    def __init__(self, name="BaseTest"):
        self.name = name
        print("STARTING : {name}".format(name=self.name))

    @abc.abstractmethod
    def run(self):
        return


class LSBTest(BaseTest):
    def __init__(self):
        super(LSBTest, self).__init__(name="Test method: _lsb()")

    def run(self):
        from chess import _lsb
        assert (_lsb(3) == 0)
        assert (_lsb(0) == -1)
        assert (_lsb(256) == 8)


class MSBTest(BaseTest):
    def __init__(self):
        super(MSBTest, self).__init__(name="Test method: _msb()")

    def run(self):
        from chess import _msb
        assert (_msb(3) == 1)
        assert (_msb(0) == -1)
        assert (_msb(256) == 8)


class ScanLSBFirstTest(BaseTest):
    def __init__(self):
        super(ScanLSBFirstTest, self).__init__(name="Test method: _scan_lsb_first()")

    def run(self):
        from chess import _scan_lsb_first
        assert (list(_scan_lsb_first(213)) == [0, 2, 4, 6, 7])
        assert (list(_scan_lsb_first(0)) == [])
        assert (list(_scan_lsb_first(1)) == [0])
        assert (list(_scan_lsb_first(256)) == [8])


class SetBit(BaseTest):
    def __init__(self):
        super(SetBit, self).__init__(name="Test method: _set_bit()")

    def run(self):
        from chess import _set_bit
        assert (_set_bit(0, 0, 1) == 1)
        assert (_set_bit(256, 8, 0) == 0)
        assert (_set_bit(256, 8, 1) == 256)
        assert (_set_bit(128, 0, 1) == 129)
        assert (_set_bit(7, 0, 0) == 6)


class TestFENNotation(BaseTest):
    def __init__(self):
        super(TestFENNotation, self).__init__(name="Test FEN Notation.")

    def run(self):
        from chess import Board, RANK_7, RANK_2

        # new game is loaded when no fence is passed
        b = Board()
        assert (b.active_player == 1)
        assert b.black_king_side_castle_right
        assert b.black_queen_side_castle_right
        assert b.white_king_side_castle_right
        assert b.white_queen_side_castle_right
        assert b.move_number == 1
        assert b.half_move_clock == 0
        assert b._all_black_pieces() == int('1111111111111111', 2) << 48
        assert b._all_white_pieces() == int('1111111111111111', 2)
        assert b.PIECES['p'] == RANK_7
        assert b.PIECES['P'] == RANK_2
        assert b.PIECES['k'] == int('00001000', 2) << 56
        assert b.PIECES['K'] == int('00001000', 2)
        assert b.PIECES['q'] == int('00010000', 2) << 56
        assert b.PIECES['Q'] == int('00010000', 2)
        assert b.PIECES['n'] == int('01000010', 2) << 56
        assert b.PIECES['N'] == int('01000010', 2)
        assert b.PIECES['b'] == int('00100100', 2) << 56
        assert b.PIECES['B'] == int('00100100', 2)
        assert b.PIECES['r'] == int('10000001', 2) << 56
        assert b.PIECES['R'] == int('10000001', 2)

        # whites moves pawn two steps
        b.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        assert b.ep_move == "e3"
        assert b.active_player == 0
        assert b.PIECES['P'] == int('00001000', 2) << 24 | int('11110111', 2) << 8

        # black also moves a pawn two steps
        b.from_fen("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2")
        assert b.ep_move == "c6"
        assert b.move_number == 2
        assert b.active_player == 1
        assert b.PIECES['P'] == int('00001000', 2) << 24 | int('11110111', 2) << 8
        assert b.PIECES['p'] == int('00100000', 2) << 32 | int('11011111', 2) << 48

        # whites moves its knight
        b.from_fen("rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2")
        assert b.ep_move is None
        assert b.active_player == 0
        assert b.black_king_side_castle_right
        assert b.black_queen_side_castle_right
        assert b.white_king_side_castle_right
        assert b.white_queen_side_castle_right
        assert b.PIECES['P'] == int('00001000', 2) << 24 | int('11110111', 2) << 8
        assert b.PIECES['p'] == int('00100000', 2) << 32 | int('11011111', 2) << 48
        assert b.PIECES['N'] == int('01000000', 2) | int('00000100', 2) << 16

        # to fen
        test_fen = "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"
        b.from_fen(test_fen)
        assert b.to_fen() == test_fen


class TestKingAttacks(BaseTest):
    def __init__(self):
        super(TestKingAttacks, self).__init__(name="Test attacked fields by king")

    def run(self):
        from chess import Board

        b = Board("8/8/8/8/4K3/8/8/8 b KQkq - 0 1")

        assert b.attacked_fields(0) == 0
        assert b.attacked_fields(1) == (int('00011100', 2) << 32) | int('00010100', 2) << 24 | int('00011100', 2) << 16

        b.from_fen("8/8/8/8/8/8/8/7k b KQkq - 0 1")
        assert b.attacked_fields(1) == 0
        assert b.attacked_fields(0) == (int('00000010', 2)) | int('00000011', 2) << 8


class TestQueenAttacks(BaseTest):
    def __init__(self):
        super(TestQueenAttacks, self).__init__(name="Test attacked fields by Queen")

    def run(self):
        from chess import Board

        b = Board("8/8/8/8/3Q4/8/8/8 b KQkq - 0 1")
        assert b.attacked_fields(1) == 1266167048752878738


class TestBishopAttacks(BaseTest):
    def __init__(self):
        super(TestBishopAttacks, self).__init__(name="Test attacked fields by Queen")

    def run(self):
        from chess import Board

        b = Board("8/8/8/8/3b4/8/8/8 b KQkq - 0 1")
        assert b.attacked_fields(0) == 108724279602332802


class TestKnightAttacks(BaseTest):
    def __init__(self):
        super(TestKnightAttacks, self).__init__(name="Test attacked fields by Knights")

    def run(self):
        from chess import Board

        b = Board("8/8/8/8/3N4/8/8/8 b KQkq - 0 1")
        assert b.attacked_fields(1) == 44272527353856


class TestPawnAttacks(BaseTest):
    def __init__(self):
        super(TestPawnAttacks, self).__init__(name="Test attacked fields by Pawns")

    def run(self):
        from chess import Board

        b = Board("P7/8/8/4P3/3p4/8/8/7p b KQkq - 0 1")
        assert b.attacked_fields(0) == int('00101000', 2) << 16
        assert b.attacked_fields(1) == int('00010100', 2) << 40


class TestMoves(BaseTest):
    def __init__(self):
        super(TestMoves, self).__init__(name="Test Move Generation")

    def run(self):
        from chess import Board, SQUARES, SQUARE_MASK

        # Starting position
        b = Board()
        assert b.gen_moves() == int('11111111', 2) << 16 | int('11111111', 2) << 24
        assert b.gen_moves(0) == int('11111111', 2) << 32 | int('11111111', 2) << 40

        # Pawns
        b = Board("P7/8/8/4P3/3p4/8/8/7p b KQkq - 0 1")
        assert b.gen_moves(0) == SQUARE_MASK[SQUARES['d3']]
        assert b.gen_moves(1) == SQUARE_MASK[SQUARES['e6']]

        # Pawn attacks
        b = Board("8/8/8/4p3/3P4/8/8/8 b KQkq - 0 1")
        assert b.gen_moves() == SQUARE_MASK[SQUARES['d4']] | SQUARE_MASK[SQUARES['e4']]
        assert b.gen_moves(1) == SQUARE_MASK[SQUARES['d5']] | SQUARE_MASK[SQUARES['e5']]

        # Knight Attacks
        b = Board("8/8/8/8/6P1/8/7N/5p2 w KQkq - 0 1")
        assert b.gen_moves() == SQUARE_MASK[SQUARES['f3']] | SQUARE_MASK[SQUARES['f1']] | SQUARE_MASK[SQUARES['g5']]

        # Bishop
        b = Board("8/3P4/8/8/6B1/5p2/8/8 w KQkq - 0 1")
        assert b.gen_moves() == 1152930322175033344
        b = Board("8/8/8/8/6B1/8/8/8 w KQkq - 0 1")
        assert b.gen_moves() == 2310355426409252880

        # Queen
        b = Board("8/8/8/8/3Q4/8/8/8 w KQkq - 0 1")
        assert b.gen_moves() == 1266167048752878738
        b = Board("7p/6p1/8/8/3Q4/8/5P2/8 w KQkq - 0 1")
        assert b.gen_moves() == 1194109454715211920

        # King
        b = Board("8/8/8/8/3K4/8/8/8 w KQkq - 0 1")
        assert b.gen_moves() == 241192927232
        b = Board("8/8/8/8/6r1/7K/6B1/8 w KQkq - 0 1")
        assert b.gen_moves() == 9241421688623857925

        # En passant
        b = Board("8/8/8/8/3pP4/8/8/8 b KQkq e3 0 1")
        assert b.gen_moves() == int("00011000", 2) << 16
        b = Board("8/8/8/8/3pP4/8/8/8 b KQkq - 0 1")
        assert b.gen_moves() == int("00010000", 2) << 16

        b = Board("8/8/8/8/8/8/8/4K3 w KQkq - 0 1")
        assert b.gen_moves() == int("0001110000010100", 2)


TESTS = [LSBTest(), MSBTest(), ScanLSBFirstTest(), SetBit(), TestFENNotation(), TestKingAttacks(), TestQueenAttacks(),
         TestBishopAttacks(), TestKnightAttacks(), TestPawnAttacks() ]


def run_all_tests():
    for test in TESTS:
        try:
            test.run()
        except Exception:
            print("ERROR WHEN TESTING {name}".format(name=test.name))
            traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
    print("SUCCESS!")
