import os
import time

# ANSI color codes
WHITE = '\033[37m'
LIME_GREEN = '\033[38;2;50;205;50m'  # RGB for #32CD32
RESET = '\033[0m'

# The multi-line ASCII font for "GHOSTWIPE" (split into list of lines)
GHOSTWIPE_FONT = [
    "             ('-. .-.               .-')    .-') _     (`\\ .-') /`          _ (`-.    ('-.   ",
    "            ( OO )  /              ( OO ). (  OO) )     `.( OO ),'         ( (OO  ) _(  OO)  ",
    "  ,----.    ,--. ,--. .-'),-----. (_)---\\_)/     '._ ,--./  .--.  ,-.-')  _.`     \\(,------. ",
    " '  .-./-') |  | |  |( OO'  .-.  '/    _ | |'--...__)|      |  |  |  |OO)(__...--'' |  .---' ",
    " |  |_( O- )|   .|  |/   |  | |  \\  :` `. '--.  .--'|  |   |  |, |  |  \\ |  /  | | |  |     ",
    " |  | .--, \\|       |\\_ ) |  |\\|  | '..`''.)   |  |   |  |.'.|  |_)|  |(_/ |  |_.' |(|  '--.  ",
    "(|  | '. (_/|  .-.  |  \\ |  | |  |.-._)   \\   |  |   |  |   |  | ,|  |_.' |  .___.' |  .--'  ",
    " |  '--'  | |  | |  |   `'  '-'  '\\       /   |  |   |   ,'.   |(_|  |    |  |      |  `---. ",
    "  `------'  `--' `--'     `-----'  `-----'    `--'   '--'   '--'  `--'    `--'      `------' ",
]

def animate(duration=5):  # Shorter duration
    """Display animated ASCII art for GHOSTWIPE (edit lines and logic below)."""
    height = len(GHOSTWIPE_FONT)
    width = len(GHOSTWIPE_FONT[0]) if GHOSTWIPE_FONT else 0

    # Step 1: Rise "GHOSTWIPE" from bottom (white text)
    for pos in range(height, -1, -1):  # Rise by revealing lines from top
        os.system('clear')
        for line in range(height):
            if line >= pos:
                print(WHITE + GHOSTWIPE_FONT[line].center(width) + RESET)
            else:
                print(" " * width)
        time.sleep(0.1)  # Faster rise

    # Step 2: Reduced bounce up/down (white)
    for _ in range(2):  # Fewer cycles
        for bounce in [0, -1, 0]:  # Less bounce: normal, up 1, normal
            os.system('clear')
            print("\n" * abs(bounce))
            for line in GHOSTWIPE_FONT:
                print(WHITE + line.center(width) + RESET)
            time.sleep(0.4)  # Slower bounce (increased from 0.3 to 0.4)

    # Step 3: Color wipe lime-green from left to right while bouncing (no other colors)
    text_length = len("GHOSTWIPE")  # Approximate text length for wipe
    for i in range(text_length + 1):
        for bounce in [0, -1, 0]:  # Reduced bounce
            os.system('clear')
            print("\n" * abs(bounce))
            for line in GHOSTWIPE_FONT:
                wipe_pos = i * (len(line) // text_length)
                colored_line = LIME_GREEN + line[:wipe_pos] + RESET + WHITE + line[wipe_pos:] + RESET
                print(colored_line.center(width))
            time.sleep(0.15)  # Slightly slower wipe

    # End animation (stay on final lime-green frame, no clear)
    time.sleep(1)  # Pause at end