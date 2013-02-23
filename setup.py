from cx_Freeze import setup, Executable


exe = Executable(
    script="pointage.py",
    base="Win32GUI",
    )

setup(
    name="simpleAttendanceGUI",
    version="0.1",
    description="KISS sign in/out gui for OpenERP",
    executables=[exe],
    )
