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
        super(TestMoves, self).__init__(name="Test moves")

    def run(self):
        from chess import Board, Move

        b = Board()
        assert b.to_fen() == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        assert len(list(b.gen_pseudo_legal_moves())) == 20
        b.make_move(Move.from_uci("e2e4"))
        assert b.move_number == 1
        assert b.half_move_clock == 1
        assert not b.active_player
        assert b.to_fen() == 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 1 1'
        assert len(list(b.gen_pseudo_legal_moves())) == 20
        b.make_move(Move.from_uci("d7d5"))
        assert b.move_number == 2
        assert b.half_move_clock == 2
        assert b.active_player

        # EN PASSANT
        b = Board("rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3")
        b.make_move(Move.from_uci("e5f6"))
        assert b.to_fen() == "rnbqkbnr/ppp1p1pp/5P2/3p4/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 3"

        b = Board("rnbqk2r/ppp3pp/3bpP1n/3p4/8/BP3Q2/P1PP1PPP/RN2KBNR b KQkq - 2 6")
        assert Move.from_uci("e8g8") in b.gen_pseudo_legal_moves()
        b.make_move(Move.from_uci("e8g8"))
        assert b.to_fen() == "rnbq1rk1/ppp3pp/3bpP1n/3p4/8/BP3Q2/P1PP1PPP/RN2KBNR w KQ - 3 7"

        b = Board("rnbq1rk1/p1p3pp/3bpP1n/1p1p4/8/BPN2Q2/P1PP1PPP/R3KBNR w KQ b6 0 8")
        b.make_move(Move.from_uci("e1c1"))
        assert b.to_fen() == "rnbq1rk1/p1p3pp/3bpP1n/1p1p4/8/BPN2Q2/P1PP1PPP/2KR1BNR b - - 1 8"

        try:
            b.make_move(Move.from_uci("e1c1"))
        except ValueError:
            pass
        finally:
            assert b.to_fen() == "rnbq1rk1/p1p3pp/3bpP1n/1p1p4/8/BPN2Q2/P1PP1PPP/2KR1BNR b - - 1 8"


class TestCheckmate(BaseTest):
    def __init__(self):
        super(TestCheckmate, self).__init__(name="Test if checkmate detection works")

    def run(self):
        from chess import Board, Move

        b = Board("rnbqkbnr/ppp1pppp/8/1B1p4/4P3/8/PPPP1PPP/RNBQK1NR b KQkq - 1 2")
        assert b.stalemate()
        assert not b.checkmate()

        b = Board("rnb1kbnr/pppp1ppp/4p3/8/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
        assert b.stalemate()
        assert b.checkmate()


class ShortestGame(BaseTest):
    def __init__(self):
        super(ShortestGame, self).__init__(name="Test full game + checkmate")

    def run(self):
        from chess import Board, Move

        b = Board()
        b.make_move(Move.from_uci("f2f3"))
        b.make_move(Move.from_uci("e7e6"))

        b.make_move(Move.from_uci("g2g4"))
        b.make_move(Move.from_uci("d8h4"))

        assert (b.checkmate())


TESTS = [LSBTest(), MSBTest(), ScanLSBFirstTest(), SetBit(), TestFENNotation(), TestKingAttacks(), TestQueenAttacks(),
         TestBishopAttacks(), TestKnightAttacks(), TestPawnAttacks(), TestMoves(), ShortestGame(), TestCheckmate(), ]


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
