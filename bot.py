from strategies import LowHighPairBot


def main():
    bot = LowHighPairBot(2, [0, 6, 12, 18])
    bot.start()


if __name__ == '__main__':
    main()
