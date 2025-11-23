import os
import textwrap
from colorama import Fore, Style, init
import pyfiglet

# Initialize colorama
init(autoreset=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    ascii_art = pyfiglet.figlet_format(text, font='small')
    print(f"{Fore.CYAN}{ascii_art}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def print_wrapped(text, width=70):
    text = textwrap.dedent(text).strip()
    for paragraph in text.splitlines():
        print(textwrap.fill(paragraph, width=width))
    print()

def print_bold(text):
    print(f"{Style.BRIGHT}{text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}{text}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}{text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"{Fore.YELLOW}{text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.BLUE}{text}{Style.RESET_ALL}")