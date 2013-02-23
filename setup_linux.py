from cx_Freeze import setup, Executable
 
 # On appelle la fonction setup
setup(
        name = "simpleAttendanceGUI",
        version = "0.1",
        description = "KISS attendance GUI for OpenERP",
        executables = [Executable("simpleAttendanceGUI.py")],
)
