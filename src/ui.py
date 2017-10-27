import ui_main

import sys

from PyQt4 import QtCore, QtGui

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    ### SET-UP WINDOWS
    
    # WINDOW main
    win_main = ui_main.QtGui.QMainWindow()
    uimain = ui_main.Ui_win_main()
    uimain.setupUi(win_main)

    ### DISPLAY WINDOWS
    win_main.show()

    #WAIT UNTIL QT RETURNS EXIT CODE
    sys.exit(app.exec_())