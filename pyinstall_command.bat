pyinstaller --onefile --nowindow^
    --add-data="chromedriver.exe;." ^
    --add-data="wingicon.ico;." ^
    --icon=wingicon.ico ^
    new_gui.py