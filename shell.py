# This program implements a basic shell with the following commands:
# 1. exit
	# - terminates the shell
# 2. commands without arguments: 
	# - executes a command without arguments and waits for 
	# it to complete
# 2a. ls -a, -h, and -l
	# - list all files, including hidden ones, long listing 
	# format, human-readable file sizes
# 2b. mkdir
	# - create a directory
# 2c. cd (directory)
	# - change to a named directory or the home directory if
	# no argument is provided
# 2d. pwd
	# - print the current directory
# 2e. cp (file1, file2)
	# - copy file1 to file2
# 2f. mv (file1, file2)
	# - move or rename file1 to file2
# 2g. rm -r
	# - recursively delete a directory
# 2h. cat (file)
	# - display contents of a file
# 2i. head -n
	# - display the first n lines of a file
# 2j. tail -n
	# - display the last n lines of a file
# 2k. grep ('pattern', file)
	# - search for a pattern in a file
# 2l. wc -l, -w
	# - count the lines or words in a file
# 2m. chmod (xxx)
	# - change file permissions
# 3. command with arguments
	# - parses command-line arguments and executes the command
# 4. background execution
	# - executes a command without blocking, allowing the shell to
	# accept further input immediately
# 5. output redirection
	# - redirects the output to a specified file
# 6. input redirection
	# - takes input from a file instead of the user's input
# 7. piping commands
	# - passes the output of one command as input to another
	# command

import os
import sys
import pwd
import grp
import stat
import socket 
import getpass
import time
import subprocess
#from time import sleep

from getch import Getch
from colorama import init, Fore, Style
#import requests
#from rich import print
import shutil
import re
import termios

# capture terminal settings before calling getch
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)

getch = Getch()  # create a new instance of class Getch
# print(prompt)
# sys.argv[0]
# argc = len(sys.argv)
# input()

def WelcomeMessage():
    """
    Prints the welcome message for the shell.

    This function displays a formatted introduction to the shell,
    including available commands and usage instructions.
    It uses colored text for better visibility.

    Parameters:
        None
    Returns:
        None
    """
    print()
    print(f"{Fore.GREEN}Welcome to the Simple Shell!")
    print("---------------------------------------------------------------------")
    print(f"{Fore.GREEN}To see avaiable commands, type 'commands'.")
    print(f"{Fore.GREEN}Type '<command> --help' for information on a specific command.")
    print(f"{Fore.GREEN}Type 'exit' or ctrl + c to quit.")
    print(f"{Fore.GREEN}Designed and implemented by Tim Haxton, Harika Vemulapalli, and Cooper Wolf.")
    print(f"{Fore.GREEN}Don't steal our code, we'll sue.")
    print(f"---------------------------------------------------------------------{Style.RESET_ALL}")
    print()

def get_terminal_size():
    '''
    Returns the width of the terminal in characters.
    '''
    try:
        size = shutil.get_terminal_size()
        return size.lines, size.columns
    except OSError:
        # Handle cases where no terminal is connectec (e.g., running in an IDE
        # without a console)
        # You can return a default value or raise a custom error here.
        return 80, 80  # Default to 80 lines and 80 columns if size 
                       # cannot be determined

def exit():
    '''
    Exit the shell.

    Exits the shell with a status of N. If N is omitted, the exit status 
    is that of the last command executed
    '''
    print(f"{Fore.GREEN}Okay Bye")  # moves next command line to new line
    raise SystemExit

# Helper function for ls
def color_filename(item, full_path):
    '''
    Returns a colored string for a filename based on its type.
    
    - Directories → Blue
    - Executable files → Green
    - Other files → Default color
    '''
    
    # Coloring the directories blue
    if os.path.isdir(full_path):
        return Fore.BLUE + item + Style.RESET_ALL
    
    # Coloring the executables green
    elif os.access(full_path, os.X_OK):
        return Fore.GREEN + item + Style.RESET_ALL
    
    # Leaving all other itms default color
    return item
    
# Helper functin for ls
def format_long_listing(full_path, human = False):
    '''
    Returns detailed metadata for a file in "long listing" format.
    
    Parameters:
        item (str): The filename.
        human (bool): If True, convert file size to human-readable format.
    
    Returns:
        list: [permissions, links, owner, group, size, mod_time, colored_name]
    '''
    
    # Getting full path of the item and info about the item
    file_info = os.stat(full_path)

    # Retreiving info about item
    permissions = stat.filemode(file_info.st_mode)
    links       = file_info.st_nlink
    owner       = pwd.getpwuid(file_info.st_uid).pw_name
    group       = grp.getgrgid(file_info.st_gid).gr_name
    size        = human_readable(file_info.st_size) if human else file_info.st_size
    mod_time    = time.strftime("%b %d %H:%M", time.localtime(file_info.st_mtime))
    
    # coloring item name depending on type
    name        = color_filename(os.path.basename(full_path), full_path)

    # Returning all item information
    return [permissions, links, owner, group, size, mod_time, name]
    #return f"{permissions} {links} {owner} {group} {size} {mod_time} {name}"

# Helper function for ls
def get_directory_items(directory = None, include_hidden = False):
    '''
    Returns a list of items in the current directory.
    
    Parameters:
        include_hidden (bool): If True, include hidden files along with "." and "..".
    
    Returns:
        list: Filenames in the directory.
    '''
    
    # Storing items from directory into items list
    if directory:
        try:
            items = os.listdir(directory)
        except PermissionError:
            return None
    
    if not directory:
        try:
            items = os.listdir()
        except PermissionError:
            return None
        
        
    non_hidden_items = []
    
    # If wanting all items return items + . and ..
    if include_hidden:
        return ['.', '..'] + items
    
    # Return only non hidden items
    else:
        for item in items:
            if not item.startswith('.'):
                non_hidden_items.append(item)
                
        return non_hidden_items

# Helper function for ls
def human_readable(size):
    """
    Convert a file size in bytes to a human-readable format.

    This function takes a file size in bytes and converts it to a more
    human-friendly format (e.g., K, M, G) with two decimal places.

    Parameters:
        size (int): The file size in bytes.

    Returns:
        str: The file size in a human-readable format.
    """
    
    # Convert size to float for division
    size = float(size)
    
    # Define units for conversion
    units = ["K", "M", "G"]
    i = 0

    # Loop to convert size to appropriate unit
    while size >= 1024 and i < len(units):
        size /= 1024
        i += 1

    # If size is less than 1K, show in bytes without decimal
    if i == 0:
        return f"{int(size)}"
    
    # Otherwise, show with one decimal place and appropriate unit
    else:
        return f"{size:.1f}{units[i-1]}"

def ls(parts):
    '''
    Usage: ls [OPTION]... [FILE]...
    List information about FILEs (the current directory by default).
    Sort entries alphabetically if none of -cftuvSUX nor --sort is specified.

    Mandatory arguments to long options are mandatory for short options too.
      -a, --all                 do not ignore entries starting with .
      -h, --human-readable      with -l, print sizes linke 1K 234M 2G etc.
      -l                        use a long listing format
          --help        display this help and exit

    Exit status:
      0  if OK,
      1  if minor problems (e.g., cannot access subdirectory),
      2  if serious trouble (e.g., cannot access command-line argument).
    '''

    # directory to store output information
    output = {"output" : None, "error" : None}
    
    
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)    
    
    # Used to store directory from params
    ls_directory = ""
    
    if input:
        output["error"] = f"{Fore.RED}Error. Ls command should not have input.{Style.RESET_ALL}\nTry 'ls --help for more info."
        return output
        
    # If user wants to ls a certain directory, grab the directory name if it's a directory
    if len(params) == 1:
        
        # Getting directory info from param given
        
        # Convert params list to string
        str_params = " ".join(params)
    
        # Remove single quotes if they exist
        str_params = str_params.strip("'")
        
        # Determining which directory to display info from
        if params == "..":
            ls_directory = params
            
        elif os.path.isdir(str_params):
            ls_directory = str_params
            
        elif not os.path.isdir(str_params):
            output["error"] = f"{Fore.RED}Error. {str_params} is not a directory.{Style.RESET_ALL}\nTry 'ls --help for more info."
            return output
        
    # return error if there are more than 1 parameters
    elif len(params) > 1:
        output["error"] = f"{Fore.RED}ls has too many parameters{Style.RESET_ALL}. \nTry 'ls --help for more info."
        return output
    
    # Check permissions before get contents
    has_permission = get_directory_items(ls_directory)
    if not has_permission:
        output["error"] = f"{Fore.RED}Permission denied: cannot access {ls_directory}{Style.RESET_ALL}"
        return output
        
    # User wants to print list from current directory
    if not flags:
        # list to store items
        items = []
            
        for item in get_directory_items(ls_directory):
            
            # Get full path to apply correct coloring
            full_path = os.path.join(ls_directory or os.getcwd(), item)
            items.append(color_filename(item, full_path))
            
        # Returning sorted list of items
        items.sort()
            
        # Convert to string
        result = " ".join(items)
        output["output"] = result
        return output
    
    # Executing ls that has flags
    if flags:
        # Storing the argument
        option = flags
    
        # List that stores directory contents
        directory_list     = get_directory_items(ls_directory)
        all_directory_list = get_directory_items(ls_directory, include_hidden = True)
        
        # Using -h alone prints the same as no args
        if option == "-h": 
            
            # list to store items
            items = []
            
            for item in directory_list:
                # Get full path to apply correct coloring
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                items.append(color_filename(item, full_path))
            
            # Returning sorted list of items
            items.sort()
            
            # Convert to string
            result = " ".join(items)
            output["output"] = result
            return output
                      
        # Using -a alone or with -h prints all files including hidden
        elif option in ("-a","-ah", "-ha"):
            
            # list to store directory items
            items = []
            
            # Getting items in directory including hidden and coloring
            # depending on item type
            for item in all_directory_list:
                
                # Get full path to apply correct coloring
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                items.append(color_filename(item, full_path))
            
            # Returning sorted list of items
            items.sort()
            
            # Convert to string
            result = " ".join(items)
            output["output"] = result
            return output
            
        # Using -l alone
        elif option == "-l":
            
            items = []
            total_size = 0
            
            # Getting block size
            for item in directory_list:
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                file_info = os.stat(full_path)
                total_size += file_info.st_blocks
            
            # Get size of directory 
            total_size = total_size // 2
            
            # Print details for each file
            for item in directory_list:
                    
                # Getting info about the item and adding it to list
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                items.append(format_long_listing(full_path))
                    
            # Return items sorted by filename
            items = sorted(items, key=lambda x: x[-1].lower())
            
            format_list = []
            for item in items:
                line = f"{item[0]:<10} {item[1]:<3}{item[2]:<8} {item[3]:<8}{item[4]:>8} {item[5]:<12} {item[6]}"
                format_list.append(line)
                
            # Convert to string and return
            result = f"Total size: {total_size}\n" + "\n".join(format_list)
            output["output"] = result
            return output
        
        # Using -al or -la prints all files in long format
        elif option in ("-al", "-la"):
                
            total_size = 0
            items = []
            
            # Calculate total size of all files in directory
            for item in all_directory_list:
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                file_info = os.stat(full_path)
                total_size += file_info.st_blocks
            
            total_size = total_size // 2
            
            # Print details for each file
            for item in all_directory_list:
                    
                # Getting info about the item and adding it to list
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                items.append(format_long_listing(full_path))
                    
            # Sort items by filename
            items = sorted(items, key=lambda x: x[-1].lower())
            
            # formatting list before converting to string
            format_list = []
            for item in items:
                line = f"{item[0]:<10} {item[1]:<3}{item[2]:<8} {item[3]:<8}{item[4]:>8} {item[5]:<12} {item[6]}"
                format_list.append(line)
            
            # Converting to string and returning
            result = f"Total size: {total_size}\n" + "\n".join(format_list)
            output["output"] = result
            return output
            
        # Using -lh or -hl prints files in long format with human readable sizes
        elif option in ("-lh", "-hl"):
            
            total_size = 0
            items = []
            
            # Calculate total size of all non-hidden files in directory
            for item in directory_list:
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                file_info = os.stat(full_path)
                total_size += file_info.st_blocks
            
            # st_blocks * 512 = byte
            total_size = human_readable(total_size * 512)
            
            # Print details for each file
            for item in directory_list:
                    
                # Getting item info and adding to list
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                items.append(format_long_listing(full_path, human = True))
                    
            # Returning items sorted by filename
            items = sorted(items, key=lambda x: x[-1].lower())
            
            # formatting list before converting to string
            format_list = []
            for item in items:
                line = f"{item[0]:<10} {item[1]:<3}{item[2]:<8} {item[3]:<8}{item[4]:>8} {item[5]:<12} {item[6]}"
                format_list.append(line)
            
            # Convert to string and return
            result = f"Total size: {total_size}\n" + "\n".join(format_list)
            output["output"] = result
            return output
            
        # Using -alh or any combo of those three prints all files in long format with human readable sizes
        elif option in ( "-lah", "-alh", "-ahl", "-lha", "-hal", "-hla"):
            
            total_size = 0
            items = []
            
            # Calculate total size of all files in directory
            for item in all_directory_list:
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                file_info = os.stat(full_path)
                total_size += file_info.st_blocks
            
            # st_blocks * 512 = byte
            total_size = human_readable(total_size * 512)
            
            # Print details for each file
            for item in all_directory_list:
                    
                # Getting item info and adding to list
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                items.append(format_long_listing(full_path, human = True))
                    
            # Returning items sorted by filename
            items = sorted(items, key=lambda x: x[-1].lower())
            
            # formatting list before converting to string
            format_list = []
            for item in items:
                line = f"{item[0]:<10} {item[1]:<3}{item[2]:<8} {item[3]:<8}{item[4]:>8} {item[5]:<12} {item[6]}"
                format_list.append(line)
            
            # Convert to string and return
            result = f"Total size: {total_size}\n" + "\n".join(format_list)
            output["output"] = result
            return output
           
        # Using -merica prints files in red white and blue 
        elif option == "-merica":

            total_size = 0
            items = []
            
            # Calculate total size of all files in directory
            for item in all_directory_list:
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                file_info = os.stat(full_path)
                total_size += file_info.st_blocks
            
            # st_blocks * 512 = byte
            total_size = human_readable(total_size * 512)
            
            # Print details for each file
            for item in all_directory_list:
                    
                # Getting item info and adding to list
                full_path = os.path.join(ls_directory or os.getcwd(), item)
                items.append(format_long_listing(full_path, human = True))
                    
            # Returning items sorted by filename
            items = sorted(items, key=lambda x: x[-1].lower())
            
            # Color the lines red white and blue | Got this code from Claude
            colors = [Fore.RED, Fore.WHITE, Fore.BLUE]
            format_list = []
            for i, item in enumerate(items):
                line = f"{item[0]:<10} {item[1]:<3}{item[2]:<8} {item[3]:<8}{item[4]:>8} {item[5]:<12} {item[6]}"
        
                # Apply color cycling through red, white, blue for each line
                color = colors[i % 3]
                colored_line = color + line + Style.RESET_ALL
                format_list.append(colored_line)
            
            # Convert to string and return
            result = f"Total size: {total_size}\n" + "\n".join(format_list)
            output["output"] = result
            return output
                    
        # Invalid option
        else:
            output["error"] = f"{Fore.RED}ls: invalid flag: {flags}.{Style.RESET_ALL} \nTry 'ls --help for more info."
            return output
        
    output["error"] = "Error"
    return output

def mkdir(parts):
    '''
    Usage: mkdir [OPTION]... DIRECTORY...
    Create the DIRECTORY(ies), if they do not already exist.

    Mandatory arguments to long options are mandatory for short options too.
          --help        display this help and exit
    '''

    # These are lists
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # Dictionary to return
    output = {"output" : None, "error" : None}
    
    # Make sure user only ran mkdir [directory]
    if not input and not flags:
        # Convert params list to string
        str_params = " ".join(params)
        
        # Remove single quotes if they exist
        str_params = str_params.strip("'")

        if os.path.isabs(str_params):
            
            # Getting the absolute path from argumen
            path = str_params

        # if relative path, join with current working directory
        elif not os.path.isabs(str_params):
            
            # Getting new directory name, current working directory
            # and joining them to create full path
            new_dir = str_params
            cwd     = os.getcwd()
            path    = os.path.join(cwd, new_dir)
            
        # Creating the directory and handling errors
        try:
            os.mkdir(path)
        except OSError as e:
            output["error"] = f"Error: {e}"
            
            
    # User entered incorrect command format
    else:
        output["error"] = "Error. Mkdir command only takes a directory."
        
        
    return output

def cd(parts):
    '''
    Change the shell working directory.

    Change the current directory to DIR. The default DIR is the value of the
    HOME shell variable. If DIR is "-", it is converted to $OLDPWD.

    The variable CDPATH defines the search path for the directory containing
    DIR. Alternative directory names in CDPATH are separated by a colon (:).
    A null directory name is the same as the current directory. If DIR begins
    with a slash (/), then CDPATH is not used.

    If the directory is not found, and the shell option 'cdable_vars' is set,
    the word is assumed to be a variable name. If that variable has a value,
    its value is used for DIR.

    Exit Status:
    Returns 0 if the directory is changed; non-zero otherwise.
    '''

    # These are lists
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # Dictionary to return
    output = {"output" : None, "error" : None}
    
    # Error handling
    if input:
        output["error"] = "Error. Command should not have an input."
        return output
    
    if flags:
        output["error"] = "Error. Command doesn't take flags."
        return output
        
    # Convert params list to string
    str_params = " ".join(params)
    
    # Remove single quotes if they exist
    str_params = str_params.strip("'")
    
    # User wants to go to home directory
    if str_params == "" or str_params == "~":
        homedir = os.path.expanduser("~")
        os.chdir(homedir)
        return output
        
    # User wants to go to parent directory
    if str_params == "..":
        os.chdir("..")
            
    # User wants to go to differnt directory
    elif os.path.isdir(str_params):
        try:
            os.chdir(str_params)
        except PermissionError:
            output["error"] = f"{Fore.RED}Permission denied: cannot access {str_params}{Style.RESET_ALL}"
        except Exception as e:
            output["error"] = f"Error changing directory: {e}"
            
    elif not os.path.isdir(str_params):
        output["error"] = f"Directory not found: {str_params}"
        
    # Returning output dictionary
    return output 

def pwd_():
    '''
    Print the name of the current working directory.

    Exit Status:
    Returns 0 unless an invalid option is given or the current directory
    cannot be read
    '''

    output = {"output" : None, "error" : None}
    
    # Storing cwd
    cwd = os.getcwd()
    
    # Storing it into output dictionary and returning
    output["output"] = cwd 
    return output

def cp(parts):
    '''
    Copy SOURCE to DEST.

          --help        display this help and exit
    '''

    # store command inputs
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # dictionary for output
    output = {"output" : None, "error" : None}

    # command error handling
    if input:
        output["error"] = "Error. Command should not have an input."
        return output
    
    if flags:
        output["error"] = "Error. Command doesn't take flags."
        return output
    
    if len(params) != 2:
        output["error"] = "Error. Command takes two parameters."
        return output

    # copy file command and exception handling
    try:
        shutil.copy(params[0], params[1])
    except FileNotFoundError as e:
        output["error"] = f"{e}"
    except PermissionError:
        output["error"] = f"Error: Permission denied when copying {params[0]} to {params[1]}."
    except shutil.SameFileError:
        output["error"] = f"Error: Source and destination {params[0]} are the same file."
    except IsADirectoryError:
        output["error"] = f"Error: One of the paths provided is a directory, not a file."
    except Exception as e:
        output["error"] = f"An unexpected error occurred: {e}"

    return output

def rm(parts):
    '''
    Usage: rm [OPTION]... [FILE]...
    Remove (unlink) the FILE(s).

      -r, -R, --recursive   remove directories and their contents recursively
              --help    display this help and exit

    By default, rm does not remove directories. Use the --recursive (-r or -R)
    option to remove each listed directory, too, along with all of its contents.

    To remove a file whose name starts with a '-', for example '-foo',
    use one of these commands:
        rm -- -foo
        rm ./-foo
    '''

    # store command inputs
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # dictionary for output
    output = {"output" : None, "error" : None}

    # command error handling
    if input:
        output["error"] = "Error. Command should not have an input."
        return output
    
    # -r flag removes requested file or directory with a prompt
    if flags == "-r":
        print(f"Press 'Y' if you are certain you want to delete {params[0]} and all of its contents.")
        val = getch()
        if val.lower() == 'y':
            try:
                shutil.rmtree(params[0])
            except FileNotFoundError:
                output["error"] = f"Error: File {params[0]} not found."
            except Exception as e:
                output["error"] = f"An error occurred: {e}"
        else:
            return output
    # -rf force removes requested file or directory without a prompt
    elif flags == "-rf" or flags == "-fr":
        try:
            shutil.rmtree(params[0])
        except FileNotFoundError:
            output["error"] = f"Error: File {params[0]} not found."
        except Exception as e:
            output["error"] = f"An error occurred: {e}"
    # -f force removes requested file or empty directory without a prompt
    elif flags == "-f":
        if os.path.isdir(params[0]):
            try:
                os.rmdir(params[0])
            except FileNotFoundError:
                output["error"] = f"Error: File {params[0]} not found."
            except OSError as e:
                output["error"] = f"Error deleting directory {params[0]}: {e}"
            except Exception as e:
                output["error"] = f"An error occurred: {e}"
        else:
            try:
                os.remove(params[0])
            except FileNotFoundError:
                output["error"] = f"Error: File {params[0]} not found."
            except Exception as e:
                output["error"] = f"An error occurred: {e}"
    # removes files whose name begins with a dash (i.e., -foo.txt)
    elif flags == "--":
        try:
            os.remove(params[0])
        except FileNotFoundError:
            output["error"] = f"Error: File {params[0]} not found."
        except Exception as e:
            output["error"] = f"An error occurred: {e}"
    # else prompt user that they are attempting to remove a file or folder
    else:
        if os.path.isdir(params[0]):
            print(f"You are attempting to remove directory {params[0]}. Press 'Y' to proceed.")
            val = getch()
            if val.lower() == 'y':
                try:
                    os.rmdir(params[0])
                except FileNotFoundError:
                    output["error"] = f"Error: File {params[0]} not found."
                except OSError as e:
                    output["error"] = f"Error deleting directory {params[0]}    : {e}"
                except Exception as e:
                    output["error"] = f"An error occurred: {e}"
            else:
                return output
        else:
            print(f"You are attempting to remove {params[0]}. Press 'Y' to proceed.")
            val = getch()
            if val.lower() == 'y':
                try:
                    os.remove(params[0])
                except FileNotFoundError:
                    output["error"] = f"Error: File {params[0]} not found."
                except Exception as e:
                    output["error"] = f"An error occurred: {e}"
            else:
                return output
    
    return output

def mv(parts):
    '''
    Rename SOURCE to DEST

          --help        display this help and exit
    '''

    # store command inputs
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # dictionary for output
    output = {"output" : None, "error" : None}

    # input error handling
    if input:
        output["error"] = "Error. Command should not have an input."
        return output
    
    if flags:
        output["error"] = "Error. Command doesn't take flags."
        return output
    
    if params is None or len(params) != 2:
        output["error"] = "Error. Command takes two parameters."
        return output
    
    # move command and exception handling
    try:
        shutil.move(params[0], params[1])
    except FileNotFoundError:
        output["error"] = f"Error: File {params[0]} not found."
    except PermissionError:
        output["error"] = f"Error: Permission denied when moveing {params[0]} to {params[1]}."
    except Exception as e:
        output["error"] = f"An unexpected error occurred: {e}"

    return output    

def cat(parts):
    '''
    Usage: cat [FILE]...

    Example:
        cat f - g   Output f's contents, then standard input, then g's contents.
        cat         Copy standard input to standard output.
    '''
    
    # Getting parsed parts
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # Dictionary to return
    output = {"output": None, "error": None}

    # Catching bad commands
    if input or flags:
        output["error"] = f"{Fore.RED}Error: 'cat' should not have input or flags.{Style.RESET_ALL}\nRun 'cat --help' for more info."
        return output
    
    # if no params, set file to None and read from stdin, else read file
    if not params:
        file = None
    else:
        file = params

     #if no file provided, read from stdin once
    if not file:
        output["output"] = sys.stdin.read()
        return output
    
    file_data = []

    # Loop through files and read them
    for f in file:
        if f == '-':
            #read from standard input here
            output["output"] = sys.stdin.read()
        else:
            try:
                with open(f,'r') as file_handle:
                    file_data.append(file_handle.read())
            except FileNotFoundError:
                output["error"] = f"cat: {f}: No such file or directory\n"
                return output
            except Exception as e:
                output["error"] = f"cat: {f}: {str(e)}\n"
                return output
            

    # Convert output to string and return 
    output["output"] = "".join(file_data)
    return output

def head(parts):
    '''
    Usage: head [OPTION]... [FILE]...
    Print the first 10 lines of each FILE to standard output.
    With more than one FILE, precede each with a header giving the file name.

    With no FILE, or when FILE is -, read standard input.

    Mandatory arguments to long options are mandatory for short options too.
        -n, --lines=[-]NUM      print the first NUM lines instead of the first 10;
                                with the leading '-', print all but the last
                                NUM lines of each file

    NUM may have a multiplier suffix:
    b 512, kB 1000, K 1024, MB 1000*1000, M 1024*1024,
    GB 1000*1000*1000, G 1024*1024*1024, and so on for T, P, E, Z, Y, R, Q.
    Binary prefixes can be used, too: KiB=K, MiB=M, and so on.
    '''

    input_data = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", [ ] ) or [ ]

    output = {"output": None, "error": None}

    # Define multipliers for suffixes like K, M, G, etc.
    decimal_suffixes = {
        "kb": 1000,
        "mb": 1000 ** 2,
        "gb": 1000 ** 3,
        "tb": 1000 ** 4,
        "pb": 1000 ** 5,
        "eb": 1000 ** 6,
        "zb": 1000 ** 7,
        "yb": 1000 ** 8,
        "rb": 1000 ** 9,
        "qb": 1000 ** 10,
    }

    # Define binary suffixes for multipliers like KiB, MiB, etc.
    binary_suffixes = {
        "k": 1024,
        "m": 1024 ** 2,
        "g": 1024 ** 3,
        "t": 1024 ** 4,
        "p": 1024 ** 5,
        "e": 1024 ** 6,
        "z": 1024 ** 7,
        "y": 1024 ** 8,
        "r": 1024 ** 9,
        "q": 1024 ** 10,
    }

    binary_suffixes_with_ib = {f"{k}ib": v for k, v in binary_suffixes.items()}

    def parse_line_count(value):
        match = re.fullmatch(r'([+-]?)(\d+)([A-Za-z]*)', value)
        if not match:
            return None, None

        sign, digits, suffix = match.groups()
        suffix_key = suffix.lower()

        if suffix_key == "b":
            multiplier = 512
        elif suffix_key in decimal_suffixes:
            multiplier = decimal_suffixes[suffix_key]
        elif suffix_key in binary_suffixes:
            multiplier = binary_suffixes[suffix_key]
        elif suffix_key in binary_suffixes_with_ib:
            multiplier = binary_suffixes_with_ib[suffix_key]
        elif suffix_key == "":
            multiplier = 1
        else:
            return None, None

        count = int(digits) * multiplier
        drop_from_end = sign == "-"

        return count, drop_from_end

    line_count = 10
    drop_last = False
    count_token = None
    
    # Check for flags and parse line count from parameters
    if flags:
        if flags in ("-n", "--lines"):
            if not params:
                output["error"] = (
                    f"{Fore.RED}Error: 'head' requires a numeric value with the '{flags}' flag.{Style.RESET_ALL}\n"
                    "Run 'head --help' for more info."
                )
                return output
            count_token = params.pop(0)
        elif flags.startswith("-n") and len(flags) > 2:
            count_token = flags[2:]
        elif flags.startswith("--lines="):
            count_token = flags.split("=", 1)[1]
        elif flags == "--lines":
            if not params:
                output["error"] = (
                    f"{Fore.RED}Error: 'head' requires a numeric value with the '{flags}' flag.{Style.RESET_ALL}\n"
                    "Run 'head --help' for more info."
                )
                return output
            count_token = params.pop(0)
        else:
            output["error"] = (
                f"{Fore.RED}Error: Invalid flag '{flags}' for 'head'.{Style.RESET_ALL}\n"
                "Run 'head --help' for more info."
            )
            return output

        if count_token is None or count_token == "":
            output["error"] = (
                f"{Fore.RED}Error: 'head' requires a numeric value with the '{flags}' flag.{Style.RESET_ALL}\n"
                "Run 'head --help' for more info."
            )
            return output

        parsed_count, drop_last = parse_line_count(count_token)
        if parsed_count is None:
            output["error"] = (
                f"{Fore.RED}Error: Invalid line count '{count_token}' for 'head'.{Style.RESET_ALL}\n"
                "Run 'head --help' for more info."
            )
            return output

        line_count = parsed_count

    sources = []
    stdin_cache = None

    def read_standard_input():
        nonlocal stdin_cache
        if stdin_cache is not None:
            return stdin_cache
        stdin_cache = sys.stdin.read()
        return stdin_cache

    files = params or []

    # Read from files or standard input
    if files:
        for name in files:
            if name == "-":
                data = input_data if input_data is not None else read_standard_input()
                sources.append(("(standard input)", str(data)))
            else:
                path = name if os.path.isabs(name) else os.path.join(os.getcwd(), name)
                try:
                    with open(path, "r") as file_handle:
                        data = file_handle.read()
                    sources.append((name, data))
                except FileNotFoundError:
                    output["error"] = f"head: cannot open '{name}' for reading: No such file or directory"
                    return output
                except PermissionError:
                    output["error"] = f"head: cannot open '{name}' for reading: Permission denied"
                    return output
                except IsADirectoryError:
                    output["error"] = f"head: error reading '{name}': Is a directory"
                    return output
                except Exception as exc:
                    output["error"] = f"head: error reading '{name}': {exc}"
                    return output
    elif input_data is not None:
        sources.append(("(standard input)", str(input_data)))
    else:
        sources.append(("(standard input)", read_standard_input()))

    def apply_head(text):
        if text is None:
            return ""

        lines = text.splitlines(keepends=True)

        # Handle dropping lines from the end
        if drop_last:
            if line_count == 0:
                selected = lines
            elif line_count >= len(lines):
                selected = []
            else:
                selected = lines[: len(lines) - line_count]
        # Handle printing lines from the start
        else:
            if line_count >= len(lines):
                selected = lines
            else:
                selected = lines[:line_count]

        return "".join(selected)

    sections = []

    for label, text in sources:
        processed = apply_head(text)
        if len(sources) > 1:
            sections.append(f"==> {label} <==\n{processed}")
        else:
            sections.append(processed)

    result = "\n\n".join(section for section in sections if section is not None)
    output["output"] = result

    return output    

def tail(parts):
    '''
    Usage: tail [OPTION]... [FILE]...
    Print the last 10 lines of each FILE to standard output.
    With more than one FILE, precede each with a header giving the file name.
    
    Mandatory arguments to long options are mandatory for short options too.
        -n, --lines=[+]NUM      output the last NUM lines, instead of the last 10;
                                or use -n +NUM to skip NUM-1 lines at the start
    NUM may have a multiplier suffix:
    b 512, kB 1000, K 1024, MB 1000*1000, M 1024*1024,
    GB 1000*1000*1000, G 1024*1024*1024, and so on for T, P, E, Z, Y, R, Q.
    Binary prefixes can be used, too: KiB=K, MiB=M, and so on.
    '''
    
    input_data = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", []) or []

    output = {"output": None, "error": None}

    # Define multipliers for suffixes like K, M, G, etc.
    decimal_suffixes = {
        "kb": 1000,
        "mb": 1000 ** 2,
        "gb": 1000 ** 3,
        "tb": 1000 ** 4,
        "pb": 1000 ** 5,
        "eb": 1000 ** 6,
        "zb": 1000 ** 7,
        "yb": 1000 ** 8,
        "rb": 1000 ** 9,
        "qb": 1000 ** 10,
    }

    # Define binary suffixes for multipliers like KiB, MiB, etc.
    binary_suffixes = {
        "k": 1024,
        "m": 1024 ** 2,
        "g": 1024 ** 3,
        "t": 1024 ** 4,
        "p": 1024 ** 5,
        "e": 1024 ** 6,
        "z": 1024 ** 7,
        "y": 1024 ** 8,
        "r": 1024 ** 9,
        "q": 1024 ** 10,
    }

    binary_suffixes_with_ib = {f"{k}ib": v for k, v in binary_suffixes.items()}

    def parse_line_count(value):
        match = re.fullmatch(r'([+-]?)(\d+)([A-Za-z]*)', value)
        if not match:
            return None, None

        sign, digits, suffix = match.groups()
        suffix_key = suffix.lower()

        if suffix_key == "b":
            multiplier = 512
        elif suffix_key in decimal_suffixes:
            multiplier = decimal_suffixes[suffix_key]
        elif suffix_key in binary_suffixes:
            multiplier = binary_suffixes[suffix_key]
        elif suffix_key in binary_suffixes_with_ib:
            multiplier = binary_suffixes_with_ib[suffix_key]
        elif suffix_key == "":
            multiplier = 1
        else:
            return None, None

        count = int(digits) * multiplier
        from_start = sign == "+"

        return count, from_start

    line_count = 10
    from_start = False
    count_token = None

    # Check for flags and parse line count from parameters
    if flags:
        if flags in ("-n", "--lines"):
            if not params:
                output["error"] = (
                    f"{Fore.RED}Error: 'tail' requires a numeric value with the '{flags}' flag.{Style.RESET_ALL}\n"
                    "Run 'tail --help' for more info."
                )
                return output
            count_token = params.pop(0)
        elif flags.startswith("-n") and len(flags) > 2:
            count_token = flags[2:]
        elif flags.startswith("--lines="):
            count_token = flags.split("=", 1)[1]
        elif flags == "--lines":
            if not params:
                output["error"] = (
                    f"{Fore.RED}Error: 'tail' requires a numeric value with the '{flags}' flag.{Style.RESET_ALL}\n"
                    "Run 'tail --help' for more info."
                )
                return output
            count_token = params.pop(0)
        else:
            output["error"] = (
                f"{Fore.RED}Error: Invalid flag '{flags}' for 'tail'.{Style.RESET_ALL}\n"
                "Run 'tail --help' for more info."
            )
            return output

        if count_token is None or count_token == "":
            output["error"] = (
                f"{Fore.RED}Error: 'tail' requires a numeric value with the '{flags}' flag.{Style.RESET_ALL}\n"
                "Run 'tail --help' for more info."
            )
            return output

        parsed_count, from_start = parse_line_count(count_token)
        if parsed_count is None:
            output["error"] = (
                f"{Fore.RED}Error: Invalid line count '{count_token}' for 'tail'.{Style.RESET_ALL}\n"
                "Run 'tail --help' for more info."
            )
            return output

        line_count = parsed_count

    sources = []

    def read_standard_input():
        return sys.stdin.read()

    files = params or []

    # Read from files or standard input
    if files:
        for name in files:
            if name == "-":
                data = input_data if input_data is not None else read_standard_input()
                sources.append(("(standard input)", str(data)))
            else:
                path = name if os.path.isabs(name) else os.path.join(os.getcwd(), name)
                try:
                    with open(path, "r") as file_handle:
                        data = file_handle.read()
                    sources.append((name, data))
                except FileNotFoundError:
                    output["error"] = f"tail: cannot open '{name}' for reading: No such file or directory"
                    return output
                except PermissionError:
                    output["error"] = f"tail: cannot open '{name}' for reading: Permission denied"
                    return output
                except IsADirectoryError:
                    output["error"] = f"tail: error reading '{name}': Is a directory"
                    return output
                except Exception as exc:
                    output["error"] = f"tail: error reading '{name}': {exc}"
                    return output
    elif input_data is not None:
        sources.append(("(standard input)", str(input_data)))
    else:
        sources.append(("(standard input)", read_standard_input()))

    def apply_tail(text):
        if text is None:
            return ""

        lines = text.splitlines(keepends=True)

        # Handle printing lines from a certain point
        if from_start:
            start_index = max(line_count - 1, 0)
            selected = lines[start_index:]
        # Handle printing lines from the end
        else:
            if line_count == 0:
                selected = []
            else:
                selected = lines[-line_count:]

        return "".join(selected)

    sections = []

    for label, text in sources:
        processed = apply_tail(text)
        if len(sources) > 1:
            sections.append(f"==> {label} <==\n{processed}")
        else:
            sections.append(processed)

    result = "\n\n".join(section for section in sections if section is not None)
    output["output"] = result

    return output

def grep(parts):
    '''
    Usage: grep PATTERNS [FILE]...
    Search for PATTERNS in each FILE.
    Example: grep 'hello world' menu.h main.c
    PATTERNS can contain multiple patterns separated by newlines.

    If no file is given, it will match with what has been received as
    input from previous command. There can only be one pattern.
    
    Available flags:
    -i : ignore case
    -l : only print names of files with matching lines
    -c : only print a count of matching lines per file 
    '''
    
    # These are lists
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # Dictionary to return
    output = {"output" : None, "error" : None}
    
    # list that stores lines that contain matches of patter
    line_match = []
    
    # storing files that match the pattern
    file_match = []
    
    # list to store split params
    files = []
    pattern_parts = []
    
    # Variable to store count of matches
    count_match = 0
        
    # if -i in flag, ignore case (true), else case sensitive (false)
    flags = flags or ""
    i_flag = re.IGNORECASE if "i" in flags else 0
    
    # Variable to store lines with matches
    highlighted = ""
    
    # Catching bad commands
    if flags not in ["", "-l", "-i", "-c", "-li", "-il", "-lc", "-cl", "-ic", "-ci", "-lic", "-lci", "-ilc", "-icl", "-cli", "-cil"]:
        output["error"] = f"{Fore.RED}Error: 'grep' only takes flags '-l', '-i', '-c'.{Style.RESET_ALL} \nRun 'grep --help' for more info."
        return output

    if not params:
        output["error"] = f"{Fore.RED}Error: 'grep' must have a pattern to match.{Style.RESET_ALL} \nRun 'grep --help' for more info."
        return output
    
    if not input and len(params) < 2:
        output["error"] = f"{Fore.RED}Error: 'grep' is missing a pattern or file.{Style.RESET_ALL} \nRun 'grep --help' for more info."
        return output
    
    if input and len(params) > 2:
        output["error"] = f"{Fore.RED}Error: 'grep' cannot process input and a parameter(s).{Style.RESET_ALL} \nRun 'grep --help' for more info."
        return output
    
    if input and len(params) > 1:
        output["error"] = f"{Fore.RED}Error: 'grep' has input, but was also given a file to process. Must be one or the other.{Style.RESET_ALL} \nRun 'grep --help' for more info."
        return output
    
    if input and len(params) < 1:
        output["error"] = f"{Fore.RED}Error: 'grep' needs a pattern to search the input for.{Style.RESET_ALL} \nRun 'grep --help' for more info."
        return output        
    
    if len(params) > 50:
        output["error"] = f"{Fore.RED}Error: Params list too long.{Style.RESET_ALL} \nRun 'grep --help' for more info."
    
    # Loop through params to separate files and pattern
    for param in params:
        clean = param.strip("'\"")
        
        # If param is file append to files list | logic From ChatGPT
        if os.path.isfile(param) or os.path.exists(clean):
            files.append(param)
            
        # Else param is part of the pattern
        else:
            if param.startswith(("'", '"')) and param.endswith(("'", '"')):
                param = param[1:-1]
            pattern_parts.append(param)
            
    if len(pattern_parts) > 1:
        output["error"] = f"{Fore.RED}Error: Only one pattern can be given, but recieved {pattern_parts}.{Style.RESET_ALL}"
        return output
    
    if len(pattern_parts) == 0:
        output["error"] = f"{Fore.RED}Error: No pattern was given.{Style.RESET_ALL}"
        return output
            
    pattern = " ".join(pattern_parts)
    
    if not input and not files:
        output["error"] = f"{Fore.RED}Error: No files or input was given.{Style.RESET_ALL} \nRun 'grep --help' for more info."
        return output
        
    # Convert input to string
    if input:
        input = "".join(input)
        input = input.strip("'")
    
    # Store the input or files to process on
    # one of them must be None due to previous checks
    source = input or files
    
    if not source:
        output["error"] = f"{Fore.RED}Error: Could not get the file or string to process.{Style.RESET_ALL} \nRun 'grep --help' for more info."
        return output
    
    # if source is a string
    if isinstance(source, str):
        
        # Split the lines of the source and process
        for line in source.splitlines():
            
            # Searching for pattern in line
            match = re.search(re.escape(pattern), line, i_flag)
            
            # if no flags, and pattern matches a line, highlight it and store the whole line
            if match and ("i" in flags or not flags):
                
                # Highlight all matches of the pattern in yellow and store the whole line
                # Using lambda to perserve original case | Got from ChatGPT
                highlighted = re.sub(re.escape(pattern), lambda m: f"{Fore.YELLOW}{m.group(0)}{Style.RESET_ALL}", line, flags=i_flag)
                line_match.append(highlighted)
            
            # -l flag (list file names once if match found)
            if match and "l" in flags:
                output["output"] = f"{Fore.MAGENTA}(standard input){Style.RESET_ALL}"
                return output

            # -c flag (count matching lines)
            if match and "c" in flags:
                count_match += 1
        
        # If -c in flag, only return count of matches
        if "c" in flags:
            output["output"] = str(count_match)
            return output
            
        # If line_match was filled, return it
        elif line_match != []:
            output["output"] = "\n".join(line_match)
            return output
        else:
            output["error"] = f"{Fore.YELLOW}No matches found for '{pattern}'{Style.RESET_ALL}"
            
        # return output
        return output
 
        
    # Determine if item is a file
    for file in source:
        if os.path.isfile(file):
            # Seeing if file is an absolute path
            if os.path.isabs(file):
            
                # Getting the absolute path from argument
                path = file

            # if relative path, join with current working directory
            elif not os.path.isabs(file):
            
                # Building absolute path
                new_dir = file
                cwd     = os.getcwd()
                path    = os.path.join(cwd, new_dir)
                
            # Match pattern with contents in file
            if path:
                
                try:
                    with open(path, 'r') as file_:
                        for line in file_:
                            
                            # Setting highlighted value to Zero
                            highlighted = None
                            
                            # Searching for pattern in line
                            match = re.search(re.escape(pattern), line, i_flag)
                                
                            # if no flags, and pattern matches a line, highlight it and store the whole line
                            if match and ("i" in flags or not flags):
                    
                                # Highlight all matches of the pattern in yellow and store the whole line
                                # Using lambda to perserve original case | Got from ChatGPT
                                highlighted = re.sub(re.escape(pattern), lambda m: f"{Fore.YELLOW}{m.group(0)}{Style.RESET_ALL}", line, flags=i_flag)

                            # if -l in flag, only return the name of the file if pattern matches
                            if match and "l" in flags:
                                if file not in file_match:
                                    file_match.append(file)
                
                            # if -c in flag, count numbers of lines that contain the pattern
                            if match and "c" in flags:
                                count_match += 1
                                
                            # If multiple files, include the file name in output
                            if len(files) > 1 and "l" not in flags and "c" not in flags and highlighted:
                                line_match.append(f"{Fore.MAGENTA}{file}{Style.RESET_ALL}: {highlighted}")
                                
                            # If only one file, do not include that file name in output
                            elif len(files) == 1 and "l" not in flags and "c" not in flags and highlighted:
                                line_match.append(f"{highlighted}")
                                
                except PermissionError:
                    output["error"] = f"{Fore.RED}Permission denied: cannot access {file}{Style.RESET_ALL}"
                    return output
                            
        # Error if one of the files does not exist
        else:
            output["error"] = f"{Fore.RED}Error: {file} is not a file.{Style.RESET_ALL} \nRun 'grep --help' for more info."
            return output
                        
    # If -l flag, only return files that matched
    if file_match != []:
        result = "\n".join(f"{Fore.MAGENTA}{f}{Style.RESET_ALL}" for f in file_match)
        output["output"] = result
        return output
    
    elif file_match == [] and 'l' in flags:
        output["output"] = None
        return output
    
    # If -c in flag, only return count of matches
    if "c" in flags:
        output["output"] = str(count_match)
            
    # If line_match was filled, return it
    elif line_match:
        output["output"] = "".join(line_match)
                        
    else:
        output["error"] = f"{Fore.YELLOW}No matches found for '{pattern}'{Style.RESET_ALL}"
        return output
            
    # return output
    return output

def wc(parts):
    '''
    Usage: wc [OPTION]... [FILE]...
      or:  wc [OPTION]... --files0-from=F
    Print newline, word, and byte counts for each FILE, and a total line if
    more than one FILE is specified. A word is a non-zero-length sequence of
    printable characters delimited by a white space.

    The options below may be used to select which counts are printed, always in
    the following order: newline, word, character, byte, maximum line length.
        -l, --lines             print the newline counts
            --files0-from=F     read input from the files specified by
                                NUL-terminated names in file F;
                                If F is - then read names from standard input
        -w, --words             print the word counts
            --total=WHEN        when to print a line with total counts;
                                When can be: auto, always, only, never
            --help      display this help and exit
    '''
    
    # Parsing parts dictionary
    input  = parts.get("input", None)
    flags  = parts.get("flags", None)
    params = parts.get("params", None)
    
    # Dictionary to store output
    output = {"output" : None, "error" : None}
    
    # If multiple parameters
    if len(params) > 1:
        output["error"] = f"{Fore.RED}Error: 'wc' can only take one parameter.{Style.RESET_ALL} \nRun 'wc --help' for more info."
        return output
    
    # Variables to store count
    line_count = 0
    word_count = 0
    char_count = 0
    
    # Convert params to string
    if params:
        params = "".join(params)
        params = params.strip("'")
        
    # Convert input to string
    if input:
        input = "".join(input)
        input = input.strip("'")
        
    # Filtering out bad commands
    if not params and not input:
        output["error"] = f"{Fore.RED}Error: 'wc' needs either an input file or parameter file to process.{Style.RESET_ALL} \nRun 'wc --help' for more info."
        return output
    if params and input:
        output["error"] = f"{Fore.RED}Error: 'wc' needs either an input file or parameter file to process.{Style.RESET_ALL} \nRun 'wc --help' for more info."
        return output
    if flags and flags not in ["-w", "-l", "-wl", "-lw"]:
        output["error"] = f"{Fore.RED}Error: {flags} is not a viable flag.{Style.RESET_ALL} Run 'wc --help' for flag options"
        return output
    
    # Checking if input or params in a file.
    item = input or params
    
    # Determine if item is a file
    if os.path.isfile(item):
        
        # Seeing if file is an absolute path
        if os.path.isabs(item):
            
            # Getting the absolute path from argument
            path = item

        # if relative path, join with current working directory
        elif not os.path.isabs(item):
            
            # Building absolute path
            new_dir = item
            cwd     = os.getcwd()
            path    = os.path.join(cwd, new_dir)
            
        # If user ran a pipe and wc section only contains wc
        # Example: ls | wc -w or wc -l fruit.txt
        if flags and path:
            
            # Get counts depending on flags
            try:
                with open(path, 'r') as file:
                    for line in file:
                        if "l" in flags:
                            line_count += 1
                        if "w" in flags:
                            words = line.split()
                            word_count += len(words)
                
                # Getting correct data to output | Code from ChatGPT           
                output_values = []
                output_values.append(str(line_count) if "l" in flags else None)
                output_values.append(str(word_count) if "w" in flags else None)
                                
                # Store results to output and return | Code from ChatGPT
                output["output"] = " ".join(filter(None, output_values))
                return output
            
            except PermissionError:
                output["error"] = f"{Fore.RED}Permission denied: cannot access {item}{Style.RESET_ALL}"
                return output
            except FileNotFoundError:
                output["error"] = f"{Fore.RED}Error: {item}: No such file or directory.{Style.RESET_ALL}"
                return output
            
        # If user ran wc with flags
        # Example wc fruit.txt or ls | wc
        if not flags and path:
            
            # Get counts
            try:
                with open(path, 'r') as file:
                    for line in file:
                        line_count += 1
                        words = line.split()
                        word_count += len(words)
                        char_count += len(line)
                                
                # Store results to output and return
                output["output"] = f"{line_count} {word_count} {char_count} {input or params}"
                return output 
            
            except PermissionError:
                output["error"] = f"{Fore.RED}Permission denied: cannot access {item}{Style.RESET_ALL}"
                return output
            except FileNotFoundError:
                output["error"] = f"{Fore.RED}Error: {item}: No such file or directory.{Style.RESET_ALL}"
                return output
                           
            
    # Determine if item is a string
    elif isinstance(item, str) and input and not params:
        
        # Removes characters used to color text
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        item = ansi_escape.sub('', item)
        
        # Split string in lines first
        lines = item.splitlines()
    
        # If user ran a pipe and wc section only contains wc
        # Example: ls | wc -w or wc -l fruit.txt
        if flags and item:
            
            # Getting line count
            if "l" in flags:
                
                # If item has multiple lines get length
                if len(lines) > 1:
                    line_count = len(lines)
                    
                # Else its just one line
                else:
                    line_count = 1
                    
            # Getting word count
            if "w" in flags:
                
                # Count words in each line
                if len(lines) > 1:
                    for line in lines:
                        for words in line.split():
                            word_count += 1
                            
                # Only one line      
                else:
                    word_count = len(lines)
                            
            # Getting correct data to output | Code from ChatGPT           
            output_values = []
            output_values.append(str(line_count) if "l" in flags else None)
            output_values.append(str(word_count) if "w" in flags else None)
                            
            # Store results to output and return | Code from ChatGPT
            output["output"] = " ".join(filter(None, output_values))
            return output
            
        # If user ran wc with flags
        # Example wc fruit.txt or ls | wc
        if not flags and item:
            
            # If item has multiple lines cound them
            if len(lines) > 1:
                line_count = len(lines)
                
            # If item has one line only add one
            else:
                line_count = 1
                
            # Count words in each line
            if len(lines) > 1:
                for line in lines:
                    for words in line.split():
                        word_count += 1
                        
            else:
                word_count = len(lines)
            
            # Count all characters in string
            char_count = len(item)
                            
            # Store results to output and return
            output["output"] = f"{line_count} {word_count} {char_count}"
            return output
    
    # item was not a string or file
    else:
        output["error"] = f"{Fore.RED}Error: {item}: No such file.{Style.RESET_ALL}\nRun 'wc --help' for more info."
        return output

def sort(parts):
    '''
    Sort lines of text files.

    Usage: sort [OPTION]... [FILE]...
    Sort the lines of each FILE, input from previous command, to standard output.

    With no FILE, Read from input (previous command).

    Available options:
        -r, --reverse                reverse the result of comparisons
        -n, --numeric-sort           compare according to string numerical value
        -a, --alphabetic             consider only alphabetic characters
        
        note: by default, sort alphabetically (lexicographically)
              --help     display this help and exit
    '''
    
    # Getting parsed parts
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # Dictionary to return
    output = {"output" : None, "error" : None}
    
    # List to store sorted data
    sorted_list = []

    # Filter out bad commands
    if (input and params) or (not input and not params):
        output["error"] = f"{Fore.RED}Error: 'sort' needs either input or params.{Style.RESET_ALL} \nRun 'sort --help' for more info."
        return output
        
    if flags not in ["-r", "-n", "-a", None]:
        output["error"] = f"{Fore.RED}Error: Invalid flag: '{flags}'.{Style.RESET_ALL} \nRun 'sort --help' for more info."
        return output
        
    # Storing the input or param into data
    data = input or params
    
    # Converting data from list to string
    data = "".join(data)
    data = data.strip("'")
    
    # Process if data is file
    if os.path.isfile(data):
        
        # Seeing if file is an absolute path
        if os.path.isabs(data):
            
            # Getting the absolute path from argument
            path = data

        # if relative path, join with current working directory
        elif not os.path.isabs(data):
            
            # Building absolute path
            new_dir = data
            cwd     = os.getcwd()
            path    = os.path.join(cwd, new_dir)
                
        # Match patter with contents in file
        if path:
            
            # From Chat
            try:
                with open(path, 'r') as file_:
                    for line in file_:
                        # From Chat
                        if line.endswith("\n"):
                            sorted_list.append(line)
                        else:
                            line = line + "\n"
                            sorted_list.append(line)
                        
                # Sort alphebetically
                if flags in ["-a", None]:
                    sorted_list.sort()
                
                # Reverse list
                elif flags == "-r":
                    sorted_list.sort(reverse=True)
                    
                # Sort numerically
                elif flags == "-n":
                    
                    try:
                        sorted_list.sort(key=int)
                    except ValueError:
                        output["error"] = f"{Fore.RED}Error: 'sort -n' can only be used on files with numbers.{Style.RESET_ALL} \nRun 'sort --help' for more info."
                        return output
                    
            except PermissionError:
                output["error"] = f"{Fore.RED}Permission denied: cannot access {data}{Style.RESET_ALL}"
                return output
                
                
        # Error if path not found
        else:
            output["error"] = f"{Fore.RED}Error: {data} is not a file.{Style.RESET_ALL} \nRun 'sort --help' for more info."
            return output
                
        # Converting to string and returning
        result = "".join(sorted_list)
        output["output"] = result
        return output
    
    # if source exists and is a string
    elif isinstance(data, str) and not params:
        
        # Removes characters used to color text in order to properly sort
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        data = ansi_escape.sub('', data)       
        
        # Split the lines of the string and append to list
        if "\n" in data and len(data) > 1:
            for line in data.splitlines():
                
                # Avoid empty lines
                if line.strip():
                    sorted_list.append(line)
                
        # If data is one line, split by word
        elif "\n" not in data and len(data) > 1:
            for line in data.splitlines():
                for word in line.split():
                    sorted_list.append(word)
                    
        # If data is one character
        else:
            output["error"] = f"{Fore.RED}Error: 'sort' was given nothing to sort.{Style.RESET_ALL} \nRun 'sort --help' for more info."
            return output
                
        # Sort alphebetically or numerically
        if flags in ["-a", None]:
            sorted_list.sort()
            
        # Reverse list
        if flags == "-r":
            sorted_list.sort(reverse=True) 
            
        # Sort numerically
        if flags == "-n":
            sorted_list.sort(key=int)              
        
        # Converting to string and returning
        result = "\n".join(sorted_list)
        output["output"] = result
        return output
    
    else:
        output["error"] = f"{Fore.RED}Error: {data} could not be properly handled.{Style.RESET_ALL} \nRun 'sort --help' for more info."
        return output   

def chmod(parts):
    '''
    Change the mode of each FILE to MODE.
    
            The MODE is a three-digit octal number representing the permissions
            for the user, group, and others, respectively. Each digit is a sum of:
            4 (read), 2 (write), and 1 (execute).
            
            For example, to set read, write, and execute permissions for the user,
            and read and execute permissions for the group and others, use 755:
            chmod 755 filename
    
            The following table shows the permission values:
            0    ---    
            1    --x
            2    -w-
            3    -wx
            4    r--
            5    r-x
            6    rw-
            7    rwx
    '''

    # Getting parsed parts
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # Dictionary to return
    output = {"output" : None, "error" : None}

    # Filter out bad commands
    if input:
        output["error"] = f"{Fore.RED}Error. Command should not have an input.{Style.RESET_ALL}\nRun 'chmod --help' for more info."
        return output
    
    if flags:
        output["error"] = f"{Fore.RED}Error. Command doesn't take flags.{Style.RESET_ALL}\nRun 'chmod --help' for more info."
        return output
    
    if len(params) != 2:
        output["error"] = f"{Fore.RED}Error. Command requires exactly two parameters: MODE and FILE.{Style.RESET_ALL}\nRun 'chmod --help' for more info."
        return output
    
    # Splitting params into permission and files
    permission = params[0]
    file = params[1]
    
    # Validating permission string
    if len(permission) != 3 or not permission.isdigit():
        output["error"] = f"{Fore.RED}Error: Invalid permission '{permission}'. Mode should be a three-digit octal number (e.g., 755).{Style.RESET_ALL}\nRun 'chmod --help' for more info."
        return output
    
    for digit in permission:
        if digit < '0' or digit > '7':
            output["error"] = f"{Fore.RED}Error: Invalid permission '{permission}'. Each digit should be between 0 and 7.{Style.RESET_ALL}\nRun 'chmod --help' for more info."
            return output
    
    
    # Seeing if file is an absolute path
    if os.path.isabs(file):
        file_path = file
        
    # If relative path, join with cwd
    else:
        file_path = os.path.join(os.getcwd(), file) 
        
    # File not found
    if not os.path.exists(file_path):
        output["error"] = f"{Fore.RED}Error: {file} could not be found.{Style.RESET_ALL}\nRun 'chmod --help' for more info."
        return output
    
    # Change file permissions
    try:
        # Convert parameters to int
        mode = int(params[0], 8)
        os.chmod(file_path, mode)

    # Catching errors
    except PermissionError:
        output["error"] = f"Error: Permission denied when changing mode of {file}."
    except Exception as e:
        output["error"] = f"An unexpected error occurred: {e}"

    # Return success case
    return output

def more(parts):
    '''
    Usage:
     more <file>...

     --help     display this help
    '''
    # length and width of terminal for output buffer
    lines, columns = get_terminal_size()
    # dictionary for output
    output = {"output" : None, "error" : None}
    # to store input and parameter files
    files = []
    # display buffer to hold input data
    display_buffer = []

    # Get parsed parts
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # input error handling
    if (not input and not params) or (input and params):
        output["error"] = f"Error: 'more' needs either input or params."
        return output

    if flags:
        output["error"] = f"Error: Command does not take flags."
        return output
    
    # if input is a file, add it to files list, otherwise parse it and add it to the display buffer
    if input:
        if os.path.isfile(input):
            files.append(input)
        else:
            if isinstance(input, str):
                data_in = input.splitlines()
            elif isinstance(input, list):
                data_in = input
            else:
                data_in = [str(input)]
            for whole_line in data_in:
                line = whole_line.rstrip("\n")
                while len(line) > columns:
                    display_buffer.append(line[:columns])
                    line = line[columns:]
                display_buffer.append(line)

    # ensure parameter file is there, otherwise output error
    if params:
        for param in params:
            if os.path.isfile(param):
                files.append(param)
            else:
                output["error"] = f"Error: Could not get the file to process. \nRun 'more --help' for more info."
                return output
    
    # loop through files list and determine path
    # if path is an absolute path, set it to path variable
    # otherwise join the path of the current working directory to the file name, and set it to path variable
    for file in files:
        if os.path.isabs(file):
            path = file
        elif not os.path.isabs(file):
            new_dir = file
            cwd = os.getcwd()
            path = os.path.join(cwd, new_dir)
        # if the path name is valid, open the file, otherwise handle any exceptions
        if path:
            try:
                with open(path, 'r') as file_:
                    # Read in each line of the input file as is and
                    # process it
                    for whole_line in file_:                        
                        line = whole_line.rstrip("\n")    # remove the
                                                        # trailing 
                                                        # newline but 
                                                        # keep spaces 
                                                        # intact 
                        
                        # If the line is longer than the width of the 
                        # terminal, slice it and add it to the display 
                        # buffer
                        while len(line) > columns:
                            display_buffer.append(line[:columns])
                            line = line[columns:]
                        # Otherwise, just add it to the display buffer
                        display_buffer.append(line)
                        
            except PermissionError:
                output["error"] = f"Error: Permission denied."
                return output
            except FileNotFoundError:
                output["error"] = f"Error: File {params} not found."
                return output
            except Exception as e:
                output["error"] = f"An unexpected error occurred: {e}"
                return output  
            
        else:
            output["error"] = f"Error: {file} could not be found. \nRun 'more --help' for more info."
            return output

    # variable for display buffer index
    viewport_start = 0
    while True:
        # clear the screen
        os.system("clear")
        # set page to the display buffer list indices from the viewport start value to one less than the number of lines available in the terminal window (last line is for the user prompt)
        page = display_buffer[viewport_start : viewport_start + (lines - 1)]
        # print those lines to std out
        for line in page:
            print(line)
        
        # get the percentage displayed on the screen by calculating the number of lines on the screen and dividing it by the number of lines in the display buffer, then multiplying by 100
        percent_displayed = ((viewport_start + len(page)) / len(display_buffer)) * 100
        print(f"--MORE-- {percent_displayed:.1f}%", end="", flush=True)
        
        # gather user input without echoing to the screen or requiring 'Enter' key input
        key = getch()
        # quits to shell
        if key == "q":
            return output
        # advances one window
        elif key in " ":
            viewport_start = min(viewport_start + (lines - 1), len(display_buffer) - (lines - 1))
        # advances one line
        elif key in ("\n", "\r"):
            viewport_start = min(viewport_start + 1, len(display_buffer) - (lines - 1))
        # passes through arrow key escape sequence (\033) and Control Sequence Indidator ([) to value (A: Up, B: Down, C: Right, or D: Left). Up sets view to top of page, Down advances one window, Left and Right are ignored
        elif key in "\x1b":
            null = getch()
            direction = getch()
            if direction in "A":
                viewport_start = 0
            if direction in "B":
                viewport_start = min(viewport_start + (lines - 1), len(display_buffer) - (lines - 1))
        else:
            pass
        if percent_displayed >= 100:
            return output

def safe_input(prompt = "", cooked_settings=None):
    '''
    Function courtesy of ChatGPT for swapping between "raw" and "cooked" mode for less function searches
    '''
    # stores file descriptor from system
    fd = sys.stdin.fileno()
    # output dictionary for output
    output = {"pattern" : None, "error" : None}
    # sets terminal to normal input mode or handles any unexpected exceptions
    try:
        if cooked_settings:
            termios.tcsetattr(fd, termios.TCSADRAIN, cooked_settings)
            output["pattern"] = input(prompt)
    except Exception as e:
        output["error"] = f"An unexpected error occurred: {e}"
    return output

def forward_search(disp_buf, view_start, pattern, m):
    '''
    Works with less to perform forward search. Takes the display buffer, start position, and user input pattern and searches forward within the document for the input pattern
    '''
    # takes input pattern and compiles it for variable storage
    regex = re.compile(pattern, re.IGNORECASE)
    # loops forward through display buffer, searching for pattern matches and adds them to input list, m
    for i in range(view_start, len(disp_buf)):
        if regex.search(disp_buf[i]):
            m.append(i)
    # if any matches are found, m is returned, otherwise None is returned
    if m:
        return m
    else:
        return None

def backward_search(disp_buf, view_start, pattern, m):
    '''
    works with less command to perform backward search. Takes the display buffer, start position, and user input pattern and searches backward within the document for in the input pattern
    '''
    # takes input pattern and compiles it for variable storage
    regex = re.compile(pattern, re.IGNORECASE)
    # loops backwards through display buffer, searching for pattern matches and adds them to input list, m
    for i in range(view_start, 0, -1):
        if regex.search(disp_buf[i]):
            m.append(i)
    # if any matches are found, m is returned, otherwise None is returned
    if m:
        return m
    else:
        return None

def highlight_pattern(m, d_b, pattern):
    # loops through list
    for match in m:
        # Replaces all input pattern matches with yellow font. Each match in list m is an index in the display buffer, 
        # so set the value data type to int and substitute the input pattern in the line with the pattern in yellow font
        d_b[int(match)] = re.sub(re.escape(pattern), f"{Fore.YELLOW}{pattern}{Style.RESET_ALL}", d_b[int(match)])
    return d_b

def less(parts, old_settings):
    '''
    SUMMARY OF LESS COMMANDS

    Commands marked with * may be preceded by a number, N.
    Notes in parenthesis indicate the behavior if N is given.
    A key preceded by a caret indicates the Ctrl key; thus ^K is ctrl-K

    h  H                Display this help.
    q  :q  Q  :Q  ZZ    Exit
    --------------------------------------------------------------------

    MOVING

    e  ^E  j  ^N  CR  *  Forward  one line  
    y  ^Y  k  ^K  ^P  *  Backward one line  
    f  ^F  ^V  SPACE  *  Forward  one window
    b  ^B  ESC-V      *  Backward one window
    z                 *  Forward  one window
    w                 *  Backward one window
    d  ^D             *  Forward  one half-window
    u  ^U             *  Backward one half-window
    ESC-> RightArrow  *  Right one half screen width.
    ESC-< LeftArrow   *  Left one half screen width.
    r  ^R  ^L         *  Repaint screen.
    R                 *  Repaint screen, discarding buffered input.
         ----------------------------------------------------
         "Window" is the screen height.
         "Half-window" is half of the screen height.
    --------------------------------------------------------------------

    SEARCHING

    /pattern          *  Search forward for matching line.
    ?pattern          *  Search backward for matching line.
    --------------------------------------------------------------------
    '''

    # length and width of terminal for output buffer
    lines, columns = get_terminal_size()
    # dictionary for output
    output = {"output" : None, "error" : None}
    # store input and parameter files
    files = []
    # display buffer to hold input data
    display_buffer = []
    # matches for search results
    matches = []

    # Get parsed parts
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # Filter out bad commands
    if (not input and not params) or (input and params):
        output["error"] = f"Error: 'more' needs either input or params."
        return output

    if flags:
        output["error"] = f"Error: Command does not take flags."
        return output
    
    # if input is a file, add it to files list, otherwise parse it and add it to the display buffer
    if input:
        if os.path.isfile(input):
            files.append(input)
        else:
            if isinstance(input, str):
                data_in = input.splitlines()
            elif isinstance(input, list):
                data_in = input
            else:
                data_in = [str(input)]
            for whole_line in data_in:
                line = whole_line.rstrip("\n")
                while len(line) > columns:
                    display_buffer.append(line[:columns])
                    line = line[columns:]
                display_buffer.append(line)

    # ensure parameter file is there, otherwise output error
    if params:
        for param in params:
            if os.path.isfile(param):
                files.append(param)
            else:
                output["error"] = f"Error: Could not get the file to process. \nRun 'more --help' for more info."
                return output
    
    # loop through files list and determine path
    # if path is an absolute path, set it to path variable
    # otherwise join the path of the current working directory to the file name, and set it to path variable
    for file in files:
        if os.path.isabs(file):
            path = file
        elif not os.path.isabs(file):
            new_dir = file
            cwd = os.getcwd()
            path = os.path.join(cwd, new_dir)

        # if the path name is valid, open the file, otherwise handle any exceptions
        if path:
            try:
                with open(path, 'r') as file_:
                    # Read in each line of the input file as is and
                    # process it
                    for whole_line in file_:                        
                        line = whole_line.rstrip("\n")    # remove the
                                                        # trailing 
                                                        # newline but 
                                                        # keep spaces 
                                                        # intact 
                        
                        # If the line is longer than the width of the 
                        # terminal, slice it and add it to the display 
                        # buffer
                        while len(line) > columns:
                            display_buffer.append(line[:columns])
                            line = line[columns:]
                        # Otherwise, just add it to the display buffer
                        display_buffer.append(line)
                        
            except PermissionError:
                output["error"] = f"Error: Permission denied."
                return output 
            except FileNotFoundError:
                output["error"] = f"Error: File {params} not found."
                return output
            except Exception as e:
                output["error"] = f"An unexpected error occurred: {e}"
                return output
            
        else:
            output["error"] = f"Error: {file} could not be found. \nRun 'more --help' for more info."
            return output

    # variable for display buffer index
    viewport_start = 0
    # variable for horizontal offset of display buffer
    horiz_offset = 0
    # variable for cursor position for user input prompt
    cursor_pos = 0
    # sentinel variable to track help screen 
    showing_help = False
    # less command user input prompt initialization
    l_cmd = ""
    # stores display buffer for reset
    orig_buff = display_buffer.copy()
    # buffer to hold help docstring
    help_buffer = []
    help_buffer.extend(less.__doc__.splitlines())
    while True:
        # clear the screen
        os.system("clear")
        # set page to the display buffer list indices from the viewport start value to one less than the number of lines available in the terminal window (last line is for the user prompt)
        page = display_buffer[viewport_start : viewport_start + (lines - 1)]
        # print those lines to std out
        for line in page:
            print(line[horiz_offset:horiz_offset + columns])
        # print prompt
        print(f":", end="", flush=True)
        # start getch
        key = getch()
        # help menu
        if key in ("h", "H"):
            display_buffer = help_buffer
            showing_help = True
        # quit to shell
        elif key in ("q", "Q", "ZZ"):
            if showing_help:
                display_buffer = orig_buff
                showing_help = False
            else:
                return output
        # forward one window
        elif key in ("f", "\x06", "\x16", " "):
            viewport_start = min(viewport_start + (lines - 1), len(display_buffer) - (lines - 1))
        # forward one line
        elif key in ("e", "\x05", "j", "\x0e", "\n", "\r"):
            viewport_start = min(viewport_start + 1, len(display_buffer) - (lines - 1))
        # backwards one line
        elif key in ("y", "\x19", "k", "\x0b", "\x10"):
            viewport_start = max(0, viewport_start - 1)
        # backwards one window
        elif key in ("b", "\x02"):
            viewport_start = max(0, viewport_start - (lines - 1))
        # forward one window
        elif key in ("z"):
            viewport_start = min(viewport_start + (lines - 1), len(display_buffer) - (lines - 1))
        # backwards one window
        elif key in ("w"):
            viewport_start = max(0, viewport_start - (lines - 1))
        # forward one-half window
        elif key in ("d", "\x04"):
            viewport_start = min(viewport_start + (lines//2), len(display_buffer) - (lines - 1))
        # backwards one-half window
        elif key in ("u", "\x15"):
            viewport_start = max(0, viewport_start - (lines//2))
        # backwards one window
        elif key in ("F"):
            viewport_start = len(display_buffer) - lines - 1
        # reset buffer display
        elif key in ("r", "\x12", "\x0c"):
            if orig_buff:
                display_buffer = orig_buff
            else:
                pass
        # forward search logic
        elif key == "/":
            # dictionary to hold pattern
            results = {"pattern" : None, "error" : None}
            # set shell to normal input mode and get user input
            results = safe_input("/", old_settings)
            # error handling
            if results["error"]:
                output["error"] = results["error"]
                return output
            else:
                # call forward search and get return
                result = forward_search(display_buffer, viewport_start, results["pattern"], matches)
            # if result is valid, set display buffer to original buffer, call highlight pattern function and update display buffer, and set viewport start index to the first match in the matches list
            if result:
                display_buffer = orig_buff
                display_buffer = highlight_pattern(matches, display_buffer, results["pattern"])
                viewport_start = int(matches[0])
        # backward search logic
        elif key == "?":
            # dictionary to hold pattern
            results = {"pattern" : None, "error" : None}
            # set shell to normal input mode and get user input
            results = safe_input("?", old_settings)
            # error handling
            if results["error"]:
                output["error"] = results["error"]
                return output
            # call backward search function and get return
            result = backward_search(display_buffer, viewport_start, results["pattern"], matches)
            # if result is valid, set display buffer to original buffer, call highlight pattern function and update display buffer, and set viewport start index to the first match in the matches list
            if result:
                display_buffer = orig_buff
                display_buffer = highlight_pattern(matches, display_buffer, results["pattern"])
                viewport_start = int(matches[0])
        # passes through arrow key escape sequence (\033) and Control Sequence Indidator ([) to value (A: Up, B: Down, C: Right, or D: Left). Up sets view to top of page, Down advances one window, Left moves view one-half window left and Right moves view one-half window right
        elif key in "\x1b":
            null = getch()
            direction = getch()
            if direction in "A":
                viewport_start = 0
            if direction in "B":
                viewport_start = min(viewport_start + (lines - 1), len(display_buffer) - (lines - 1))
            if direction in "C":
                horiz_offset += columns // 2
            if direction in "D":
                horiz_offset = max(0, horiz_offset - (columns // 2))
        # prints prompt and key input to screen
        else:
            l_cmd = l_cmd[:cursor_pos] + key + l_cmd[cursor_pos:]
            cursor_pos += 1
            print(l_cmd)

def ip(parts):
    '''
    Display the IP address of the machine.
    '''
    
    # Getting parsed parts
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)    
    
    # Dictionary to return
    output = {"output" : None, "error" : None}
    
    # Filter out bad commands
    if input or flags or params:
        output["error"] = f"{Fore.RED}Error. Command should not have any input, flags, or params.{Style.RESET_ALL}\nRun 'ip --help' for more info."
        return output
    
    # Getting hostname and IP address
    try:
        hostname = socket.gethostname()
        ip_addr  = socket.gethostbyname(hostname)
        output["output"] = f"IP Address: {ip_addr}"
    except Exception as e:
        output["error"] = f"{Fore.RED}An error occurred while retrieving the IP address: {e}.{Style.RESET_ALL}"
    
    # Return final output
    return output

def date(parts):
    '''
    Display the current date and time.
    '''
    
    # Getting parsed parts
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)    
    
    # Dictionary to return
    output = {"output" : None, "error" : None}
    
    # Filter out bad commands
    if input or flags or params:
        output["error"] = f"{Fore.RED}Error. Command should not have any input, flags, or params.{Style.RESET_ALL}\nRun 'date --help' for more info."
        return output
    
    # Getting current date and time
    # Got time functions from chatGPT
    try:
        current_time = time.strftime("%m-%d-%y %H:%M:%S", time.localtime())
        output["output"] = f"{current_time}"
    except Exception as e:
        output["error"] = f"{Fore.RED}An error occurred while retrieving the date and time: {e}.{Style.RESET_ALL}"
    
    # Return final output
    return output

def run(parts):
    '''
    Launch the Firefox web browser or Nautilus fire manager.
    
    Possible commands: run firefox, run nautilus
    
    Note: 
    
    This command does not take any input or flags.
    Make sure Firefox and Nautilus is installed on your system.
    
    Run only works in a GUI environment.
    Vs Code terminal is not a GUI environment.
    If running in a non-GUI environment, this command will return an error.
    
    To install Firefox and Nautilus:
    1. sudo apt update
    2. sudo apt install firefox -y 
    3. sudo apt install nautilus -y
    '''
    
    # Getting parsed parts
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)    
    
    # Dictionary to return
    output = {"output" : None, "error" : None}
    
    # Throw error if user added input, flags
    if input and flags:
        output["error"] = f"{Fore.RED}Error: Command should not have any input or flags .{Style.RESET_ALL}\nRun 'run --help' for more info."
        return output
    
    if len(params) != 1:
        output["error"] = f"{Fore.RED}Error: Command only takes one parameter.{Style.RESET_ALL}\nRun 'run --help' for more info."
        return output
    
    # Convert params to string
    if params:
        params = "".join(params)
        params = params.strip("'")
    
    # Throw error if user didn't provide correct parameter
    if params not in ["firefox", "nautilus"]:
        output["error"] = f"{Fore.RED}Error: Command only takes 'firefox' or 'nautilus' as a parameter.{Style.RESET_ALL}\nRun 'run --help' for more info."
        return output
    
    # Storing program to run
    program = params.strip().lower()
    
    # Check if DISPLAY exists for GUI
    # firefix needs a display to run
    if "DISPLAY" not in os.environ:
        output["error"] = f"{Fore.RED}Error: Cannot run GUI apps: no display found.{Style.RESET_ALL} \nRun 'run --help' for more info."
        return output

    # Check if program exists
    # shutil.which searchs for executables in system path
    if shutil.which(program):
        try:
            # Running firefox on its own process so firefox can run independently
            # Suppress output by redirecting to DEVNULL
            # Python script can continue runnning without waiting for firefox to close
            subprocess.Popen([program], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Return nothing on success
            return output
            
        # Catch any exceptions during launch
        except Exception as e:
            output["error"] = f"Error launching {program}: {e}"
            return output
            
    # Program not found in PATH
    else:
        output["error"] = f"Program '{program}' not found in PATH."
        output["error"] = f"Is {program} installed?{Style.RESET_ALL}\nIf it isn't, exit the shell and install."
        output["error"] += f"\nTo install {program}:\n  1. sudo apt update\n  2. sudo apt install {program} -y"
        return output

def list_of_commands(parts):
    '''
    Returns a list of all available commands in the shell.
    '''
    
    # Getting parsed parts
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)    
    
    # Dictionary to return
    output = {"output" : None, "error" : None}
    
    # Filter out bad commands
    if input or flags or params:
        output["error"] = f"{Fore.RED}Error. Command should not have any input, flags, or params.{Style.RESET_ALL}\nRun 'commands --help' for more info."
        return output
    
    # Starting with empty output
    output["output"] = ""

    # Concatenating command list
    output["output"] += f"{Fore.GREEN}cd{Style.RESET_ALL}: change directory\n"
    output["output"] += f"{Fore.GREEN}ls{Style.RESET_ALL}: list files\n"
    output["output"] += f"{Fore.GREEN}pwd{Style.RESET_ALL}: print working directory\n"
    output["output"] += f"{Fore.GREEN}mkdir{Style.RESET_ALL}: make directory\n"
    output["output"] += f"{Fore.GREEN}wc{Style.RESET_ALL}: word/line/character count\n"
    output["output"] += f"{Fore.GREEN}cat{Style.RESET_ALL}: display file contents\n"
    output["output"] += f"{Fore.GREEN}grep{Style.RESET_ALL}: search text in files\n"
    output["output"] += f"{Fore.GREEN}sort{Style.RESET_ALL}: sort lines in files\n"
    output["output"] += f"{Fore.GREEN}mv{Style.RESET_ALL}: move/rename files\n"
    output["output"] += f"{Fore.GREEN}rm{Style.RESET_ALL}: remove files\n"
    output["output"] += f"{Fore.GREEN}help{Style.RESET_ALL}: show help info\n"
    output["output"] += f"{Fore.GREEN}history{Style.RESET_ALL}: show command history\n"
    output["output"] += f"{Fore.GREEN}chmod{Style.RESET_ALL}: change file permissions\n"
    output["output"] += f"{Fore.GREEN}cp{Style.RESET_ALL}: copy files\n"
    output["output"] += f"{Fore.GREEN}date{Style.RESET_ALL}: show current date/time\n"
    output["output"] += f"{Fore.GREEN}clear{Style.RESET_ALL}: clear terminal\n"
    output["output"] += f"{Fore.GREEN}exit{Style.RESET_ALL}: exit shell\n"
    output["output"] += f"{Fore.GREEN}run{Style.RESET_ALL}: run a program\n"
    output["output"] += f"{Fore.GREEN}ip{Style.RESET_ALL}: show IP address\n"
    output["output"] += f"{Fore.GREEN}commands{Style.RESET_ALL}: list available commands\n"
    output["output"] += f"{Fore.GREEN}!x{Style.RESET_ALL}: run command from history\n"
    output["output"] += f"{Fore.GREEN}head{Style.RESET_ALL}: show first lines of file\n"
    output["output"] += f"{Fore.GREEN}tail{Style.RESET_ALL}: show last lines of file\n"
    output["output"] += f"{Fore.GREEN}more{Style.RESET_ALL}: paginate file output\n"
    output["output"] += f"{Fore.GREEN}less{Style.RESET_ALL}: scroll through file output\n"

    # Returning output
    return output

def clear_screen(parts):
    '''
    Clear the terminal screen.
    '''
    
    # Getting parsed parts
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)    
    
    # Dictionary to return
    output = {"output" : None, "error" : None}
    
    # Filter out bad commands
    if input or flags or params:
        output["error"] = f"{Fore.RED}Error. Command should not have any input, flags, or params.{Style.RESET_ALL}\nRun 'clear --help' for more info."
        return output
    
    # Clear the screen
    clear()
    
    # Return final output
    return output

def history(parts):
    """
    Display or manipulate the history list.

    Display the history list with line numbers, prefixing each modified
    entry with a '*'.

    history.txt will be used as the filename for history. If it exists,
    it will be updated. Otherwise, it will be created in the user's 
    HOME folder

    Exit Status:
    Returns success unless an invalid option is given or an error occurs.
    """
    
    # These are lists
    input = parts.get("input", None)
    flags = parts.get("flags", None)
    params = parts.get("params", None)
    
    # Dictionary to return
    output = {"output" : None, "error" : None}
    
    # If there exist any input flags and params in the dict, dont execute
    if not input and not flags and not params:
        
        # Get the absolute path of the folder where the script is located
        # script_dir = os.path.dirname(os.path.abspath(__file__))

        # Get the absolute path of the user's home directory
        home_dir = os.path.expanduser("~")

        # # Move history file if it is located in folder where script is 
        # # located
        # if os.path.exists("history.txt"):
        #     shutil.move("history.txt", home_dir)
        # else:
        #     # Build the full path to history.txt inside the home directory
        history_file = os.path.join(home_dir, "history.txt")

        history_list = []
        command_number = 1

        # Check if history file exists
        if os.path.exists(history_file):
            
            # Opening history file
            with open(history_file, "r") as file:
                
                # Storing contents into commands
                commands = file.readlines()
                
                # Getting each line
                for command in commands:
                    
                    # Appending the command alone with its command number to list
                    history_list.append(f"{command_number} {command.strip()}")
                    command_number += 1
            
            # Appending the history command that was just executed
            history_list.append(f"{command_number} history")
            
            # Convert to string and return
            result = "\n".join(history_list)
            output["output"] = result
            return output
      
        
        # If history_file does not exist, return None
        else:
            output["error"] = "Error, History file doesn't exist in the directory that this pythons script is in."
            return output
        
    # If user added on top of history command
    else:
        output["error"] = "Error, history command must not have any params, input, or flags."

def if_not_x_command(command_list, cmd):
    """
    !x Command

    Re-executes the most recent command in history that begins with the character 'x'.  
    This is similar to history expansion in Unix shells.

    Examples:
        history
        ls
        !l      # Repeats the last command that began with 'l' (in this case, 'ls')

    Notes:
        - Only works with single commands, not pipelines or compound commands.
        - Only searches backwards through the stored command history.
        - If no matching command is found, an error message is returned.
        - Case-sensitive by default.
    """
    
    if (len(command_list) == 1 
        and command_list[0].get("cmd").startswith("!") 
        and command_list[0].get("cmd")[1:].isnumeric()):
        
        # Get the cmd and send to function.
        result = cmd_from_history(command_list[0].get("cmd"))

        if result["error"]:
            # Set command list to zero
            command_list = []
        else:
            # Setting command_list to result command from !x command
            command_list = parse_cmd(result["output"])
            cmd = result["output"]
            result["output"] = None

            print(cmd)

    return command_list, cmd

def help(parts):
    """
    Display documentation for available commands.

    This function prints the docstrings of all implemented commands
    in the shell, allowing the user to see usage instructions and
    a short description of each command. The output is intended to
    act like a built-in help manual.

    Example:
        > help --help
        Prints description of help command
    """
    
    # Storing parsed commands
    input  = parts.get("input", None)
    flags  = parts.get("flags", None)
    params = parts.get("params", None)
    cmd    = parts.get("cmd", None)
    
    # Dictionary to store output
    output = {"output" : None, "error" : None}
    
    output["output"] = "    ------------------------------"
    
    # Making sure user only typed command followed by '--help'
    if not input and not params and flags == "--help":
        if cmd == "cd":
            output["output"] += cd.__doc__
            
        elif cmd == "ls":
            output["output"] += ls.__doc__

        elif cmd == "pwd":
            output["output"] += pwd_.__doc__

        elif cmd == "mkdir":
            output["output"] += mkdir.__doc__
            
        elif cmd == "wc":
            output["output"] += wc.__doc__
            
        elif cmd == "history":
            output["output"] += history.__doc__
            
        elif cmd == "help":
            output["output"] += help.__doc__

        elif cmd == "cat":
            output["output"] += cat.__doc__

        elif cmd == "cp":
            output["output"] += cp.__doc__

        elif cmd == "mv":
            output["output"] += mv.__doc__

        elif cmd == "rm":
            output["output"] += rm.__doc__

        elif cmd == "exit":
            output["output"] += exit.__doc__
            
        elif cmd == "grep":
            output["output"] += grep.__doc__
            
        elif cmd == "sort":
            output["output"] += sort.__doc__
            
        elif cmd == "chmod":
            output["output"] += chmod.__doc__
            
        elif cmd == "ip":
            output["output"] += ip.__doc__
        
        elif cmd == "date":
            output["output"] += date.__doc__
            
        elif cmd == "clear":
            output["output"] += clear_screen.__doc__
            
        elif cmd == "run":
            output["output"] += run.__doc__
            
        elif cmd == "commands":
            output["output"] += list_of_commands.__doc__
            
        elif cmd == "!x":
            output["output"] += cmd_from_history.__doc__
            
        elif cmd == "more":
            output["output"] += more.__doc__

        elif cmd == "less":
            output["output"] += less.__doc__
            
        elif cmd == "!x":
            output["output"] += if_not_x_command.__doc__

        elif cmd == "head":
            output["output"] += head.__doc__

        elif cmd == "tail":
            output["output"] += tail.__doc__

        
        output["output"] += "------------------------------"
        return output
    else:
        output["error"] = f"{Fore.RED}Error, help for command {cmd} could not be found.{Style.RESET_ALL}"
        return output
    
def get_history_rev():
    """
    Opens history text file and returns the contents.

    This function retrieves the previous command from the history file
    and returns it. If there is no previous command, it returns None.

    Parameters:
        None
    Returns:
        List of all commands in history file.
    """
    
    # Get the absolute path of the user's home directory
    home_dir = os.path.expanduser("~")

    # Build the full path to history.txt inside your repo
    history_file = os.path.join(home_dir, "history.txt")

    # Check if history file exists
    if os.path.exists(history_file):
        with open(history_file, "r") as file:
            h_cmds = file.readlines()
            
            # Remove the last value if its empty
            if h_cmds and h_cmds[-1].strip() == "":
                h_cmds.pop()
            
            # Removing '\n' at the end of each command
            h_cmds = [item.strip() for item in h_cmds]
            
            # Reversing list
            h_cmds.reverse()
            
            # Return list of all commands in history in reverse order
            return h_cmds
            
    else:
        # History file doesn't exist
        return None
    
# This functions works as the !x command
def cmd_from_history(index):
    '''
    Functions handles the !x command by getting the index value from 
    the command and retrieves the history commands then return the at 
    the index given
    '''
    
    # directory to store output information
    output = {"output" : None, "error" : None}
    
    # setting index to only value, removing '!'
    index = index[1:]
    
    index = int(index)
    index -= 1
    h_cmds = get_history_rev() or []
        
    # Reverse list so commands are in chronological
    if h_cmds:
        h_cmds.reverse()
        
    # Geting history commands
    if 0 <= index < len(h_cmds):
        
        # Returning cmd at given index
        output["output"] = h_cmds[index].strip()
        return output
    
    # if index is out of range of history
    else:
        output["error"] = f"Error. There are only {len(h_cmds)} commands in history."
        return output
       
def write_to_history(cmd):
    '''
    # write out the command to the history file
    # so you can access it later with the up/down arrows
    '''
          
    # Get the absolute path of the user's home directory
    # Since this script and the history file are in the same directory:
    home_dir = os.path.expanduser("~")

    # Build the full path to history.txt inside your repo
    history_file = os.path.join(home_dir, "history.txt")

    # Append command to the file
    with open(history_file, "a") as file:
        file.write(cmd + "\n")

def write_to_file(data, filename):
    output = {"output": None, "error": None}
    try:
        with open(filename, "w") as f:
            f.write(data)
    except Exception as e:
        output["error"] = f"An unexpected error occurred: {e}"
        return output
    return output
       
def clear():
    """
    Clear the terminal screen.
    This function clears the terminal screen by executing the appropriate system command.
    Parameters:
        None
    Returns:
        None
    """
    os.system("clear")

def parse_cmd(cmd_input):
    
    command_list = []
    
    cmds = cmd_input.split("|")
    
    for cmd in cmds:
        
        # Need to have a check while procession that if error has error in it, stop processing.
        
        d = {"input" : None, "cmd" : None, "params" : [], "flags" : None, "error" : None, "out" : None, "in_file" : None}
        subparts = cmd.strip().split()
        d["cmd"] = subparts[0]
        
        # Going thorugh the rest of the subparts to classify and store correctly
        for item in subparts[1:]:
            
            # Storing flags and params
            if item.startswith("-"):
                
                # Check if flags already exist
                if d["flags"]:
                    d["error"] = f"{Fore.RED}Error: Flags must be combined.{Style.RESET_ALL}"
                else:
                    d["flags"] = item
            else:
                d["params"].append(item)

        # Check parameters for output redirection operator and handle
        if ">" in d["params"]:
            idx = d["params"].index(">")
            d["out"] = d["params"][idx + 1]
            del d["params"][idx + 1]
            del d["params"][idx]

        # Check parameters for input redirection operator and handle
        if "<" in d["params"]:
            idx = d["params"].index("<")
            d["in_file"] = d["params"][idx + 1]
            del d["params"][idx + 1]
            del d["params"][idx]
                
        # Appending the correct dictionary to command list
        command_list.append(d)
        
    return command_list

def visible_length(s):
    '''Helper function for print_cmd. This is needed to bring the terminal cursor to the correct
    position. Previously. it was offset by the length of ({Fore.CYAN}{Style.RESET_ALL}). So this
    funciton removes that from the prompt so the cursor can be in the correct position.
    '''
    
    # Step by step:
    # \x1b         -> The escape character signaling the start of an ANSI sequence
    # \[           -> Matches the literal '[' that follows the escape character
    # [0-9;]*      -> Matches any digits or semicolons (e.g., 36, 1;32) zero or more times
    # m            -> Matches the literal 'm' at the end of the ANSI code
    # Together: \x1b\[[0-9;]*m matches things like:
    #    \x1b[36m    -> set cyan text
    #    \x1b[0m     -> reset text style/color
    #    \x1b[1;32m  -> bold green text

    # re.compile() -> Compiles this regex pattern for reuse
    # ansi_escape.sub('', s) -> Removes all ANSI sequences from the string
    # len(...) -> Counts only the visible characters, ignoring color codes
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return len(ansi_escape.sub('', s))

def print_cmd(cmd, cursor_pos=0):
    '''
    This function "cleans" off the command line, then prints
    whatever cmd that is passed to it to the bottom of the terminal.
    '''
    
    # Update prompt info with current data 
    username = getpass.getuser()
    computer_name = socket.gethostname()
    cwd = os.getcwd()
    
    # Storing built prompt
    prompt = f"{Fore.CYAN}{username}@{computer_name}:{cwd}{Style.RESET_ALL}$ "
    
    #padding = " " * get_terminal_width()
    #sys.stdout.write("\r" + padding)
    
    
    # Move cursor to start, print prompt + command
    sys.stdout.write("\r")
    sys.stdout.write(f"{prompt}{cmd}")
    
    # Clear everything to the right of the cursor
    sys.stdout.write("\033[K")
    
    # Move cursor to start
    sys.stdout.write("\r")
    
    # Move cursor to the right the length of the prompt plus cursor position, and flush
    sys.stdout.write(f"\033[{visible_length(prompt) + cursor_pos}C")
    sys.stdout.flush()

#######################  Beginning of Main  ###########################
if __name__ == "__main__":

    # Allows for colored text in terminal and resets color after each print
    init(autoreset=True)

    # Print welcome message
    WelcomeMessage()
    
    # List of commands user may request to execute
    available_commands = ["ls", "pwd", "mkdir", "cd", "cp", "mv", "rm", "cat",
                          "head", "tail", "grep", "wc", "chmod", "history",
                          "exit", "more", "less", "sort", "help", "ip", "date",
                          "clear", "run", "commands", "!x"]
    
    # Empty cmd variable
    cmd = ""
    
    # For handling left/right arrow keys
    cursor_pos = 0

    # For handling up/down arrow keys
    history_index = -1
    
    # Print to terminal
    print_cmd(cmd)

    # Loop forever
    while True:

        char = getch()  # read a character (but don't print)

        # Exit shell on ctrl-c command
        if char == "\x03":
            print()
            exit()

        # If back space pressed, remove the character to the left of the cursor
        if char == "\x7f":
            if cursor_pos > 0:
                cmd = cmd[:cursor_pos-1] + cmd[cursor_pos:]
                cursor_pos -= 1
            print_cmd(cmd, cursor_pos)

        # User pressed arror key, remove that input and get direction
        elif char in "\x1b":
            null = getch()
            direction = getch()
            
            # Get updated history if avaible
            h_cmd = get_history_rev() or []

            # Up arror pressed
            if direction in "A":
                
                # Get list of history commands
                if h_cmd and history_index < len(h_cmd) - 1:
                    
                    # Get the previous command from history
                    history_index += 1
                    cmd = h_cmd[history_index]
                    
                    
                # If at the end of history, stay there
                else:
                    cmd = h_cmd[-1]
                    
                # Moving cursor to length of new cmd and print cmd
                cursor_pos = len(cmd)
                print_cmd(cmd, cursor_pos)

            # Down arror pressed
            if direction in "B":
                
                # get the next command from history
                if h_cmd and history_index > 0:
                    
                    # Get previous command
                    history_index -= 1
                    cmd = h_cmd[history_index]
  
                # At the newest, go to blank like
                else:
                    history_index = -1
                    cmd = ""
                    
                # Moving cursor to length of new cmd and print cmd
                cursor_pos = len(cmd)
                print_cmd(cmd, cursor_pos)

            # Right arrow pressed
            if direction in "C":
                
                # Move cursor to the right
                if cursor_pos < len(cmd):
                    cursor_pos += 1
                print_cmd(cmd, cursor_pos)

            # Left arrow pressed
            if direction in "D":
                
                # Move cursor to the left
                if cursor_pos > 0:
                    cursor_pos -= 1
                print_cmd(cmd, cursor_pos)

        # Return character pressed
        elif char in "\r":
            
            # Printing blank line so info isn't overwritten
            print()
            
            # Exit
            if cmd == "exit":
                exit()
                
            # If there is a command to execute
            if(cmd):
                
                # Part command and returning list of dictionaries
                command_list = parse_cmd(cmd)
                result = {"output" : None, "error" : None}
                
                # Check if error while parsing command
                for command in command_list:
                    if command.get("error"):
                        result["error"] = command.get("error")
                        command_list = []
                        
                # Handling !x command
                command_list, cmd = if_not_x_command(command_list, cmd)

                # Executing each command in the command list
                while len(command_list) != 0:
            
                    # Pop first command off of the command list
                    command = command_list.pop(0)
                    
                    # Making sure valid command
                    if command.get("cmd") not in available_commands:
                        result["error"] = f"Error. command '{command.get("cmd")}' is not in list of available commands."
                        
                    # If there is output in the previous command and command has not input
                    # make the output to the previous command the input to the next
                    if result["output"] and not command["input"]:
                        command["input"] = result["output"]                   
                    
                    # Handle input redirection from file
                    if command.get("in_file"):
                        try:
                            with open(command.get("in_file"), 'r') as f:
                                command["input"] = f.read()
                        except FileNotFoundError:
                            result["error"] = f"Error: File {command.get("in_file")} not found."
                            break
                        except Exception as e:
                            result["error"] = f"An unexpected error occurred while reading input file: {e}"
                            break
                        
                    # Kill execution if error
                    if result["error"]:
                        break

                    if command.get("flags") == "--help" and not command.get("params") and not command.get("input"):
                        result = help(command)     
                    elif command.get("cmd") == "cd":
                        result = cd(command)
                    elif command.get("cmd") == "ls":
                        result = ls(command)
                    elif command.get("cmd") == "pwd":
                        result = pwd_()
                    elif command.get("cmd") == "mkdir":
                        result = mkdir(command)
                    elif command.get("cmd") == "head":
                        result = head(command)
                    elif command.get("cmd") == "history":
                        result = history(command)
                    elif command.get("cmd") == "cat":
                        result = cat(command)
                    elif command.get("cmd") == "head":
                        result = head(command)
                    elif command.get("cmd") == "tail":
                        result = tail(command)
                    elif command.get("cmd") == "wc":
                        result = wc(command)
                    elif command.get("cmd") == "cp":
                        result = cp(command)
                    elif command.get("cmd") == "mv":
                        result = mv(command)
                    elif command.get("cmd") == "rm":
                        result = rm(command)
                    elif command.get("cmd") == "grep":
                        result = grep(command)
                    elif command.get("cmd") == "sort":
                        result = sort(command)
                    elif command.get("cmd") == "chmod":
                        result = chmod(command)
                    elif command.get("cmd") == "ip":
                        result = ip(command)
                    elif command.get("cmd") == "date":
                        result = date(command)
                    elif command.get("cmd") == "clear":
                        result = clear_screen(command)
                    elif command.get("cmd") == "run":
                        result = run(command)
                    elif command.get("cmd") == "commands":
                        result = list_of_commands(command)
                    elif command.get("cmd") == "more":
                        result = more(command)
                    elif command.get("cmd") == "less":
                        result = less(command, old_settings)
                        
            # Printing result to screen
            if result["error"]:
                print(result["error"])
            elif command.get("out"):
                result = write_to_file(result["output"], command.get("out"))
            elif result["output"]:
                print(result["output"])


            # Writing command to history
            write_to_history(cmd)

            # Setting cmd blank, cursor to 0, and history index to -1
            cmd = ""
            cursor_pos = 0
            history_index = -1
            
            print_cmd(cmd)  # now print empty cmd prompt on next line
            
        else:
            # Concatenate the typed character at the cursor position
            cmd = cmd[:cursor_pos] + char + cmd[cursor_pos:]
            
            # move cursor position to the right
            cursor_pos += 1
            
            # add typed character to our "cmd"
            print_cmd(cmd, cursor_pos)