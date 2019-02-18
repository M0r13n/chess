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


TESTS = [LSBTest(), MSBTest(), ScanLSBFirstTest(), SetBit(), ]


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
