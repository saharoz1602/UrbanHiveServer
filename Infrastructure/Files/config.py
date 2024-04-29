import os

# Determine the absolute path of the directory containing the current script.
# This is useful for cases where the script needs to know its own location in the filesystem,
# for example to construct paths to other files or directories based on its own location.

# __file__ is a built-in variable that is set to the path of the file from which the Python
# script is executed. os.path.abspath(__file__) returns the absolute path of this script file,
# ensuring that the path is complete regardless of the current working directory of the process.
# os.path.dirname() then takes this absolute path and returns the directory name of the specified path.
# This is typically used to add directory-level manipulation to file handling operations in a script,
# making it more robust against changes in the working directory.


application_file_path = os.path.dirname(os.path.abspath(__file__))

