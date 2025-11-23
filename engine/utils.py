import os
from colorama import Fore, Style, init
import textwrap

# Initialize colorama
init(autoreset=True)

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_slow(text, delay=0.01):
    """Prints text one character at a time for effect (optional)."""
    print(text)
    # Uncomment for RPG-style slow typing
    # for char in text:
    #     sys.stdout.write(char)
    #     sys.stdout.flush()
    #     time.sleep(delay)
    # print()

def print_header(text):
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
    print(f"{text.center(40)}")
    print(f"{'='*40}{Style.RESET_ALL}")

def print_bold(text):
    print(f"{Style.BRIGHT}{text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}{text}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}{text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"{Fore.YELLOW}{text}{Style.RESET_ALL}")
    
def print_wrapped(text, width=70):
    """Wraps text nicely to a specific width."""
    text = textwrap.dedent(text).strip()
    for paragraph in text.splitlines():
        print(textwrap.fill(paragraph, width=width))
    print()