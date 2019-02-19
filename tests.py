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
        assert b.all_black_pieces == int('1111111111111111', 2) << 48
        assert b.all_white_pieces == int('1111111111111111', 2)
        assert b.b_pawns == RANK_2
        assert b.w_pawns == RANK_7
        assert b.b_king == int('00001000', 2) << 56
        assert b.w_king == int('00001000', 2)
        assert b.b_queens == int('00010000', 2) << 56
        assert b.w_queens == int('00010000', 2)
        assert b.b_knights == int('01000010', 2) << 56
        assert b.w_knights == int('01000010', 2)
        assert b.b_bishops == int('00100100', 2) << 56
        assert b.w_bishops == int('00100100', 2)
        assert b.b_rooks == int('10000001', 2) << 56
        assert b.w_rooks == int('10000001', 2)

        # whites moves pawn two steps
        b.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        assert b.ep_move == "e3"
        assert b.active_player == 0
        assert b.w_pawns == int('00001000', 2) << 24 | int('11110111', 2) << 8

        # black also moves a pawn two steps
        b.from_fen("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2")
        assert b.ep_move == "c6"
        assert b.move_number == 2
        assert b.active_player == 1
        assert b.w_pawns == int('00001000', 2) << 24 | int('11110111', 2) << 8
        assert b.b_pawns == int('00100000', 2) << 32 | int('11011111', 2) << 48

        # whites moves its knight
        b.from_fen("rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2")
        assert b.ep_move is None
        assert b.active_player == 0
        assert b.black_king_side_castle_right
        assert b.black_queen_side_castle_right
        assert b.white_king_side_castle_right
        assert b.white_queen_side_castle_right
        assert b.w_pawns == int('00001000', 2) << 24 | int('11110111', 2) << 8
        assert b.b_pawns == int('00100000', 2) << 32 | int('11011111', 2) << 48
        assert b.w_knights == int('01000000', 2) | int('00000100', 2) << 16


class TestMovements(BaseTest):
    def __init__(self):
        super(TestMovements, self).__init__(name="Test movements for pawns")

    def run(self):
        from chess import Board, RANK_5, D_LINE

        b = Board()
        assert b.gen_moves(0) == int(8 * '1', 2) << 40 | int(8 * '1', 2) << 32
        assert b.gen_moves(1) == int(8 * '1', 2) << 16 | int(8 * '1', 2) << 24

        b.from_fen("8/8/8/8/3r4/8/8/8 b KQkq - 1 2")
        assert b.gen_moves(0) == (RANK_5 | D_LINE) & ~b.all_black_pieces


TESTS = [LSBTest(), MSBTest(), ScanLSBFirstTest(), SetBit(), TestMovements(), TestFENNotation(), ]


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
