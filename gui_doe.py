import sys, time, os
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QWidget,
                            QPushButton, QAction,
                            QMainWindow, QMessageBox,
                            QCheckBox, QSpinBox, QComboBox,
                            QStyleFactory, QFontDialog,
                            QTableWidget, QTableWidgetItem,
                            QMenu, QLabel,
                            QVBoxLayout, QHBoxLayout,
                            QFileDialog
                            )
import doe_toolkit
import pandas as pd

basedir = os.path.dirname(__file__)

try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'morescope.notDeer.aDoeBuilder.version1'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

class DOE_Builder(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Title and window size
        self.setGeometry(100, 100, 400, 200)
        self.setWindowTitle("DOE Builder")
        self.setWindowIcon(QIcon(os.path.join(basedir, "icons", "doe_icon.ico")))
        self.activeWindow = None
        
        # File Menu Actions
        newDoe = QAction("&New DOE", self)
        newDoe.setShortcut("Ctrl+N")
        newDoe.setStatusTip("Start a new Design")
        newDoe.triggered.connect(self.buildFactors)

        openTable = QAction("&Open Table", self)
        openTable.setShortcut("Ctrl+O")
        openTable.setStatusTip("Open a table")
        openTable.triggered.connect(self.open_table)
        
        saveTable = QAction("&Save Table", self)
        saveTable.setShortcut("Ctrl+S")
        saveTable.setStatusTip("Save the current table")
        saveTable.triggered.connect(self.save_table)

        quitAction = QAction("&Quit", self)
        quitAction.setShortcut("Ctrl+Q")
        quitAction.setStatusTip("Leave the app")
        quitAction.triggered.connect(self.close_application)

        changeFont = QAction("&Set Font", self)
        changeFont.setStatusTip("Change the font")
        changeFont.triggered.connect(self.font_choice)

        changeTheme = QMenu("&Set Theme", self)
        changeTheme.setStatusTip("Change the theme")
        for style_name in QStyleFactory.keys():
            style_action = changeTheme.addAction(style_name)
            style_action.triggered.connect(lambda _, style=style_name: QApplication.setStyle(QStyleFactory.create(style)))
        
        # Edit Menu Actions
        undoAction = QAction("&Undo", self)
        undoAction.setShortcut("Ctrl+Z")
        undoAction.setStatusTip("Undo last action")

        redoAction = QAction("&Redo", self)
        redoAction.setShortcut("Ctrl+Y")
        redoAction.setStatusTip("Redo last action")

        cutAction = QAction("&Cut", self)
        cutAction.setShortcut("Ctrl+X")
        cutAction.setStatusTip("Cut selection to clipboard")

        copyAction = QAction("&Copy", self)
        copyAction.setShortcut("Ctrl+C")
        copyAction.setStatusTip("Copy selection to clipboard")

        pasteAction = QAction("&Paste", self)
        pasteAction.setShortcut("Ctrl+V")
        pasteAction.setStatusTip("Paste from clipboard")
        
        # Help Menu Actions
        helpAction = QAction("&About", self)
        helpAction.setShortcut("F1")
        helpAction.setStatusTip("Show Help")
        
        # Create the satusbar
        self.statusBar()

        # Create main menu (assigned to variable to modify)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(newDoe)
        fileMenu.addAction(openTable)
        fileMenu.addAction(saveTable)
        fileMenu.addSeparator()
        fileMenu.addMenu(changeTheme)
        fileMenu.addAction(changeFont)
        fileMenu.addSeparator()
        fileMenu.addAction(quitAction)
        menubar.addMenu("|").setEnabled(False)
        editMenu = menubar.addMenu("&Edit")
        editMenu.addAction(undoAction)
        editMenu.addAction(redoAction)
        editMenu.addSeparator()
        editMenu.addAction(cutAction)
        editMenu.addAction(copyAction)
        editMenu.addAction(pasteAction)
        menubar.addMenu("|").setEnabled(False)
        helpMenu = menubar.addMenu("&Help")
        helpMenu.addAction(helpAction)

        # Show home window
        self.home()


    # define Home Page
    def home(self):

        # Add a toolbar
        doeAction = QAction(QIcon(os.path.join(basedir, "icons", "doe_icon.ico")),"New DOE", self)
        doeAction.triggered.connect(self.buildFactors)
        self.toolBar = self.addToolBar("HomeToolbar")
        self.toolBar.addAction(doeAction)

        self.buildFactors()
        self.show()

    def open_table(self):
        # Open csv explorer
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("CSV Files (*.csv);;All Files (*)")

        # PyQt interface for files
        if file_dialog.exec_() == QFileDialog.Accepted:
            # get file path
            filepath = file_dialog.selectedFiles()[0]

        # Read using pd.read_csv
        try:
            factor_table = pd.read_csv(filepath)
            self.buildFactors(factor_table=factor_table)
        except Exception as Err:
            print(f"Error loading file: {Err}")


    def save_table(self):
        save_dialog = QFileDialog()
        save_path, _ = save_dialog.getSaveFileName(self, 'Save File', '', 'CSV Files (*.csv);;All Files (*)')

        if save_path:
            try:
                df = self.readTableData(save_table=True)
                df.to_csv(save_path, index=False)
            except Exception as Err:
                print(f"Problem Saving File: {Err}")


    def font_choice(self):
        font, valid = QFontDialog.getFont()
        if valid:
            self.table_widget_factors.setFont(font)


    def close_application(self):
        close_choice = QMessageBox.question(self, "DOE Builder",
                                      "Are you sure you want to quit?",
                                      QMessageBox.Yes | QMessageBox.No)
        if close_choice == QMessageBox.Yes:
            print("Closing Application")
            sys.exit()

    def dType_ErrorMsg(self):
        ok_choice = QMessageBox.question(self, "Data Type Error",
                    "Incorrect Data Type Provided",
                    QMessageBox.Ok)
        if ok_choice == QMessageBox.Ok:
            print("Incorrect dType, Try Again")

    
    def incomplete_ErrorMsg(self):
        complete_choice = QMessageBox.question(self, "Incomplete Table",
                        "Factor table must be completed",
                        QMessageBox.Ok)
        if complete_choice == QMessageBox.Ok:
            print("Table Incomplete, Try Again")


    def buildFactors(self, factor_table=None, type=None, plot=None):
        """
        ---Tabs for Factors and Levels (inputs)
        ---Button for Factor Type (categorical / numerical)
        ---Selector for number of factors
        """
        self.setWindowTitle("DOE Builder - Factors")
        self.setGeometry(100, 100, 450, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.activeWindow = "Factors"

        # Create a layout to hold the table
        layout = QVBoxLayout()

        # Horizontal Layout For Factor Selection
        factorsHLayout = QHBoxLayout()

        # Factors Text
        self.text_factors = QLabel("Select the Number of Factors: ")
        self.text_factors.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        factorsHLayout.addWidget(self.text_factors)

        # Spinner for number of rows
        self.row_count = QSpinBox(self)
        self.row_count.setFixedSize(50, 20)
        self.row_count.setMinimum(1)
        self.row_count.setMaximum(26)
        if isinstance(factor_table, pd.DataFrame):
            self.row_count.setValue(len(factor_table))
        else:
            self.row_count.setValue(3) # Default
        self.row_count.valueChanged.connect(self.updateTableRows)
        factorsHLayout.addWidget(self.row_count)
        layout.addLayout(factorsHLayout)

        # Create the table widget
        self.table_widget_factors = QTableWidget(self)
        self.table_widget_factors.setColumnCount(4)  # Number of columns
        self.table_widget_factors.setHorizontalHeaderLabels(["Factor","dType", "Low Level", "Hi Level"])
        self.table_widget_factors.setColumnWidth(0, 130)
        self.table_widget_factors.setColumnWidth(1, 55)
        if isinstance(factor_table, pd.DataFrame):
            self.table_widget_factors.setRowCount(len(factor_table))
        else:
            self.table_widget_factors.setRowCount(3) # Number of rows

        # Add combo box to dType
        self.addComboBoxToTable()

        # Allow cell editing
        self.table_widget_factors.setEditTriggers(QTableWidget.AllEditTriggers)
        layout.addWidget(self.table_widget_factors)

        # If there already is a factor table (passed back from toolkit)
        if isinstance(factor_table, pd.DataFrame):
            for i in range(factor_table.shape[0]):
                for j in range(factor_table.shape[1]):
                    item = QTableWidgetItem(str(factor_table.iloc[i, j]))
                    self.table_widget_factors.setItem(i, j, item)

        # Tabs for Model Selection and Comparison
        """
        ---Pick Model, see design points, see runs
        ---Should have tool tip for goals
        """
        # Setup HLayout for Design Option
        type_options = QHBoxLayout()
        self.text_designOptions = QLabel("Select a Design Option: ")
        self.text_designOptions.setAlignment(Qt.AlignVCenter | Qt.AlignRight)     
        self.type_box = QComboBox(self)
        self.type_box.setFixedWidth(190)
        self.type_box.addItems(["Full Factorial",
                                "Space Filling",
                                "Box-Behnken",
                                "2-level Fractional",
                                "Central-Composite: OnFace",
                                "Central-Composite: Inscribed",
                                "Central-Composite: Circumscribed"])       
        type_options.addWidget(self.text_designOptions)
        type_options.addWidget(self.type_box)

        # Setup HLayout for Plot Type Options
        plot_options = QHBoxLayout()
        self.text_plotOptions = QLabel("Select a Plot Option: ")
        self.text_plotOptions.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.plot_box = QComboBox(self)
        self.plot_box.setFixedWidth(190)
        self.plot_box.addItems(["None",
                                "3D Plot (Factors A, B, C only)",
                                "Scatter Plot"])
        plot_options.addWidget(self.text_plotOptions)
        plot_options.addWidget(self.plot_box)

        # Stack TYPE and PLOT options
        designOptions = QVBoxLayout()
        designOptions.addLayout(type_options)
        designOptions.addLayout(plot_options)

        # If there's a factor table already, keep the previous settings
        if isinstance(factor_table, pd.DataFrame):
            self.type_box.setCurrentText(type)
            self.plot_box.setCurrentText(plot)

        # Create Button To Read
        read_button = QPushButton("Next", self)
        read_button.setFixedWidth(80)
        read_button.clicked.connect(self.readTableData) # THIS is what happens when next clicked

        # Set up Bottom H Layout
        nextHLayout = QHBoxLayout()
        nextHLayout.addLayout(designOptions)
        nextHLayout.addWidget(read_button)
        
        # Overall Layout Wrapper
        layout.addLayout(nextHLayout)

        # Apply the Layout
        self.central_widget.setLayout(layout)

        # Connect Spinner Value to Window Height
        self.row_count.valueChanged.connect(self.adjustWindowHeight)
        self.row_count.valueChanged.connect(self.updateRowLabels)
        self.row_count.valueChanged.connect(self.addComboBoxToTable)

        # Initialize row labels
        self.updateRowLabels()

    def displayDesign(self, factor_table=None, design_table=None, type=None, plot=None):
        """
        --- Show the resulting df table
        """
        self.setWindowTitle(f"DOE Builder - {type} - Design Table")
        self.setGeometry(100, 100, 450, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.activeWindow = "Design"

        # Create a layout to hold the table
        layout = QVBoxLayout()

        # Create the table
        # Create a QTableWidget and populate it with DataFrame data
        self.table_widget_design = QTableWidget()

        self.table_widget_design.setRowCount(design_table.shape[0])
        self.table_widget_design.setColumnCount(design_table.shape[1])

        # Set the column headers
        self.table_widget_design.setHorizontalHeaderLabels(design_table.columns)

        # Round to Digits before adding to table
        df = design_table.map(lambda x: f'{x:.2f}')
        # Populate the table with DataFrame values
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iloc[i, j]))
                self.table_widget_design.setItem(i, j, item)

        # self.adjustWindowHeight()

        # Next and Back Buttons
        next_button = QPushButton("Next", self)
        next_button.setFixedWidth(80)
        # next_button.clicked.connect(self.readTableData) # THIS is what happens when next clicked
        back_button = QPushButton("Back", self)
        back_button.setFixedWidth(80)
        back_button.clicked.connect(lambda: self.buildFactors(factor_table=factor_table, type=type, plot=plot))

        layout.addWidget(self.table_widget_design)
        layout.addWidget(next_button)
        layout.addWidget(back_button)

        # Made Editable
        self.table_widget_design.setEditTriggers(QTableWidget.AllEditTriggers)
        self.central_widget.setLayout(layout)


    def updateRowLabels(self):
        # Change row label to letters
        row_labels = [chr(ord("A") + i) for i in range(self.table_widget_factors.rowCount())]

        for row, label in enumerate(row_labels):
            item = QTableWidgetItem(label)
            self.table_widget_factors.setVerticalHeaderItem(row, item)
    
    def addComboBoxToTable(self):
        for row in range(self.table_widget_factors.rowCount()):
            dType_combo_box = QComboBox(self)
            dType_combo_box.addItems(["Num", "Cat"])
            self.table_widget_factors.setCellWidget(row, 1, dType_combo_box)

    def adjustWindowHeight(self):
        new_height = 210 + self.row_count.value() * 30
        if new_height > 590:
            self.setFixedHeight(590)
        else:
            self.setFixedHeight(new_height)


    def updateTableRows(self):
        num_rows = self.row_count.value()
        self.table_widget_factors.setRowCount(num_rows)


    def readTableData(self, save_table=False):
        # Generates a factor_table (a list of dicts) from the GUI
        if self.activeWindow == "Factors":
            table_widget = self.table_widget_factors

            factor_table = []
            table = {}
            for row in range(table_widget.rowCount()):
                try:    
                    factor = table_widget.item(row, 0).text()
                    dType = table_widget.cellWidget(row, 1).currentText()
                    low_level = table_widget.item(row, 2).text()
                    high_level = table_widget.item(row, 3).text()
                except AttributeError:
                    self.incomplete_ErrorMsg()
                    return

                row_dict = {'Factor': factor,
                            'dType': dType,
                            'Low Level': low_level,
                            'Hi Level': high_level}
                factor_table.append(row_dict)

                if dType == "Num":
                    try:
                        low_level = float(low_level)
                        high_level = float(high_level)
                    except ValueError:
                        self.dType_ErrorMsg()
                        return             

                table[factor] = [low_level, high_level]
            # print(table)
        
            # TODO -- Rework this into a dictionary when running toolkit
            type_name = self.type_box.currentText()
            type_dict = {"Full Factorial": "full",
                        "Space Filling": "fill",
                        "Box-Behnken": "boxb",
                        "2-level Fractional": "frac",
                        "Central-Composite: OnFace": "ccf",
                        "Central-Composite: Inscribed": "cci",
                        "Central-Composite: Circumscribed": "ccc"}
            type = type_dict[type_name]

            plot_name = self.plot_box.currentText()
            plot_dict = {"3D Plot (Factors A, B, C only)": "3d",
                        "Scatter Plot": "scatter",
                        "None": None}
            plot = plot_dict[plot_name]
            
            # Run (design) table and Factor table as dataframes from doe_toolkit
            factor_table = pd.DataFrame(factor_table)
            if save_table == False:
                run_table = pd.DataFrame(doe_toolkit.main(table, type, plot))
                # This is what reads the results from the toolkit
                self.displayDesign(design_table=run_table, factor_table=factor_table, type=type_name, plot=plot_name)
            else:
                return factor_table

        elif self.activeWindow == "Design":
            table_widget = self.table_widget_design
            # TODO # Read Design Tables and Return a df that can be saved
            # Extract data from the QTableWidget
            rows = table_widget.rowCount()
            cols = table_widget.columnCount()

            header_labels = [table_widget.horizontalHeaderItem(col).text() for col in range(cols)]

            data = [header_labels]
            for row in range(rows):
                row_data = [table_widget.item(row, col).text() for col in range(cols)]
                data.append(row_data)

            # Convert data to a DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            return df


    def analyzeData(self):
        # Tab/table for Responses and Measurements
        """
        ---Paired with Experimental Conditions
        ---Should be pasteable
        ---Should be exportable for data collection
        ---Should be importable from data collection to tool
        """
        ...


if __name__ == "__main__":
    # App definition with command line args []
    app = QApplication([])
    app.setStyle("windowsvista")
    app.setWindowIcon(QIcon(os.path.join(basedir, "icons", 'doe_deer.png')))
    GUI = DOE_Builder()
    sys.exit(app.exec_())
