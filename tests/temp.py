from pathlib import Path

resolved = Path(__file__).resolve()
print(resolved)
"""
Prints and absolute path of the current file:
/Users/martian_elk/Projects/macro_mojo/tests/temp.py"""

resolved_parents = Path(__file__).resolve().parents
print(list(resolved_parents))
"""
Prints a list of all parent directories, including the current
directory. Stating with the current directory:
[PosixPath('/Users/martian_elk/Projects/macro_mojo/tests'), PosixPath('/Users/martian_elk/Projects/macro_mojo'), PosixPath('/Users/martian_elk/Projects'), PosixPath('/Users/martian_elk'), PosixPath('/Users'), PosixPath('/')]
"""

project_directory = Path(__file__).resolve().parents[1]
print(project_directory)
"""
Prints an absolute path of the project directory. 
/Users/martian_elk/Projects/macro_mojo
"""

current_directory = Path(__file__).resolve().parent
print(current_directory)
"""Prints: /Users/martian_elk/Projects/macro_mojo/tests"""

path_current_file = parent_of_current_file / "temp.py"
print(path_current_file)
"""/Users/martian_elk/Projects/macro_mojo/tests/temp.py"""

path_current_file_no_spaces = parent_of_current_file / "temp.py"
print(path_current_file_no_spaces)
"""/Users/martian_elk/Projects/macro_mojo/tests/temp.py"""
