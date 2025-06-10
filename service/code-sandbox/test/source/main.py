import sys

def main():
    data = sys.stdin.read().split()
    if len(data) < 2:
        return
    a, b = map(int, data[:2])
    print(a + b)

if __name__ == "__main__":
    main()
