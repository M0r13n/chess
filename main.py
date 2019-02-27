from chess import Board, Move

if __name__ == '__main__':
    b = Board()

    while True:
        print(b)
        try:
            b.make_move(Move.from_uci(
                input("It´s {}´s turn! Enter UCI compliant move: ".format('white' if b.active_player else 'black'))))
        except ValueError as e:
            print("Your move could not be parsed.")
            continue
