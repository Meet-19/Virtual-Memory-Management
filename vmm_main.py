import math
import sys

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QTableWidgetItem
)
from PyQt5.QtCore import Qt

from vmm_main_ui import Ui_MainWindow
import pageChecker, pageHandler

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, pagesCount, framesCount, pageSizeBytes, TLBframesCount, addressesFile, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.showMaximized()

        #variable for vmm
        self.physicalMemory = {}
        self.tlb = []
        self.pageTable = []
        self.pageFaultCounter = 0
        self.tlbHitCounter = 0
        self.addressReadCounter = 0

        # variables for gui
        self.state = 0
        self.referenceStringSnapshot = []
        self.pagesCount = pagesCount
        self.framesCount = framesCount
        self.pageSizeBytes = pageSizeBytes
        self.TLBframesCount = TLBframesCount
        self.addressesFile = addressesFile

        self.updateUi()

    def updateUi(self):
        self.btnNext.clicked.connect(self.performNextOp)

        self.tableTLB.setRowCount(self.TLBframesCount+1)
        self.tableTLB.setHorizontalHeaderItem(0, QTableWidgetItem("Page Number"))
        self.tableTLB.setHorizontalHeaderItem(1, QTableWidgetItem("Frame Number"))

        self.tablePageTable.setRowCount(self.framesCount+1)
        self.tablePageTable.setHorizontalHeaderItem(0, QTableWidgetItem("Page Number"))
        self.tablePageTable.setHorizontalHeaderItem(1, QTableWidgetItem("Frame Number"))

        self.tablePhysicalMemory.setRowCount(self.framesCount)
        self.tablePhysicalMemory.setColumnCount(self.pageSizeBytes)
        for i in range(16+1):
            self.tablePhysicalMemory.setVerticalHeaderItem(i, QTableWidgetItem(str(i)))
            self.tablePhysicalMemory.setHorizontalHeaderItem(i, QTableWidgetItem(str(i)))

        LApageNoLength = math.ceil(math.log2(int(self.pagesCount)))
        LApageOffsetLength = math.ceil(math.log2(int(self.pageSizeBytes)))
        PAframeNoLength = math.ceil(math.log2(int(self.framesCount)))
        PAframeOffsetLength = LApageOffsetLength
        self.tableLogicalAddr.setItem(1, 0, QTableWidgetItem(str(LApageNoLength)+" bits")) # page number length
        self.tableLogicalAddr.setItem(1, 1, QTableWidgetItem(str(LApageOffsetLength)+" bits")) # offset length
        self.tablePhysicalAddr.setItem(1, 0, QTableWidgetItem(str(PAframeNoLength)+" bits")) # frame number length
        self.tablePhysicalAddr.setItem(1, 1, QTableWidgetItem(str(PAframeOffsetLength)+" bits")) # offset length
        self.tableLogicalAddr.item(1, 0).setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.tableLogicalAddr.item(1, 1).setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.tablePhysicalAddr.item(1, 0).setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.tablePhysicalAddr.item(1, 1).setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.label_LAlength.setText(f"Logical Address ({LApageNoLength+LApageOffsetLength} bits):")
        self.label_PAlength.setText(f"Physical Address ({PAframeNoLength+PAframeOffsetLength} bits):")

    def performNextOp(self):
        global tlbHit,pageTableTrue,logicalAddress,offset,pageNumber,dataRead,frameNumber,refStringHighlightIndex
        if self.state == 0:
            self.outputFile = open('output.txt', 'w')
            self.addressFile = open(self.addressesFile, 'r')
            self.addressFile2 = open(self.addressesFile, 'r')

            for i in range(15):
                addr = self.addressFile2.readline()
                if not addr:
                    break
                self.referenceStringSnapshot.append(int(addr))
            self.updateTableWidget(self.tableRefString, [self.referenceStringSnapshot])
            global refStringHighlightIndex
            refStringHighlightIndex = -1
            self.labelStatus.setText('Input file opened successfully! Next: Load first address from reference string.')
            self.state = 1
            self.btnNext.setText('Next')
        elif self.state == 1:
            line = self.addressFile.readline()
            if not line:
                self.state = 6
                return;
        
            tlbHit = 0
            pageTableTrue = 0

            logicalAddress = int(line)
            offset = logicalAddress & (self.pageSizeBytes - 1)
            pageNumber = logicalAddress >> math.ceil(math.log2(int(self.pageSizeBytes)))
            self.labelLogicalAddr.setText(str(logicalAddress))
            self.updateAddressTable(self.tableLogicalAddr, pageNumber, offset)

            self.addressReadCounter += 1
            suffix = "th"
            if self.addressReadCounter == 1:
                suffix = "st"
            elif self.addressReadCounter == 2:
                suffix = "nd"
            elif self.addressReadCounter == 3:
                suffix = "rd"
            self.labelStatus.setText(f"Loaded {self.addressReadCounter}{suffix} address from reference string. Next: Find page in TLB.")
            
            if refStringHighlightIndex < 7:
                refStringHighlightIndex += 1
            else:
                addr = self.addressFile2.readline()
                if addr:
                    self.referenceStringSnapshot.pop(0) 
                    self.referenceStringSnapshot.append(int(addr))
                    self.updateTableWidget(self.tableRefString, [self.referenceStringSnapshot])
                else:
                    refStringHighlightIndex += 1

            self.tableRefString.setCurrentCell(0, refStringHighlightIndex)
            self.tableRefString.setFocus()
            self.labelPhysicalAddr.setText("-")
            self.updateAddressTable(self.tablePhysicalAddr, "", "")
            self.cboxTLBHit.setChecked(False)
            self.cboxNotPageFault.setChecked(False)
            self.labelData.setText("-")
            self.tableTLB.setCurrentCell(-1, -1)
            self.tablePageTable.setCurrentCell(-1, -1)
            self.tablePhysicalMemory.setCurrentCell(-1, -1)

            self.state = 2

        elif self.state == 2:
            (tlbHit, frameNumber, dataRead) = pageChecker.checkTLB(pageNumber, self.physicalMemory, offset, logicalAddress, self.tlb, self.addressReadCounter, self.outputFile, self.framesCount, self.pageSizeBytes)
            if tlbHit == 1:
                self.tlbHitCounter += 1
                self.cboxTLBHit.setChecked(True)
                self.labelStatus.setText(f"TLB hit! Found page {pageNumber} in the TLB. Next: Read data from physical memory.")
                self.labelPhysicalAddr.setText(str(self.generatePhysicalAddr(frameNumber, offset)))
                self.updateAddressTable(self.tablePhysicalAddr, frameNumber, offset)
                self.tableTLB.setCurrentCell(int(frameNumber)+1, 0)
                self.tableTLB.setFocus()
                self.state = 5
            else:
                self.labelStatus.setText(f"Page {pageNumber} not found in the TLB. Next: Find page in page table.")
                self.cboxTLBHit.setCheckState(Qt.PartiallyChecked)
                self.state = 3
        
        elif self.state == 3:
            (pageTableTrue, frameNumber, dataRead) = pageChecker.checkPageTable(pageNumber, logicalAddress, offset, self.addressReadCounter, self.pageTable, self.physicalMemory, self.outputFile, self.framesCount, self.pageSizeBytes)
            if pageTableTrue == 1:
                self.labelStatus.setText(f"Found page {pageNumber} in the page table. Next: Read data from physical memory.")
                self.cboxNotPageFault.setChecked(True)
                self.labelPhysicalAddr.setText(str(self.generatePhysicalAddr(frameNumber, offset)))
                self.updateAddressTable(self.tablePhysicalAddr, frameNumber, offset)
                self.tablePageTable.setCurrentCell(int(frameNumber)+1, 0)
                self.tablePageTable.setFocus()
                self.state = 5
            else:
                self.labelStatus.setText(f"Page fault! Page {pageNumber} not found in the page table. Next: Fetch page from secondary memory.")
                self.cboxNotPageFault.setCheckState(Qt.PartiallyChecked)
                self.pageFaultCounter += 1
                self.state = 4

        elif self.state == 4:
            pageHandler.pageFaultHandler(pageNumber, self.tlb, self.pageTable, self.physicalMemory, self.TLBframesCount, self.framesCount, self.pagesCount, self.pageSizeBytes)
            _, frameNumber, dataRead = pageChecker.checkTLB(pageNumber, self.physicalMemory, offset, logicalAddress, self.tlb, self.addressReadCounter, self.outputFile, self.framesCount, self.pageSizeBytes)
            self.labelStatus.setText(f"Loaded new page in physical memory, page table & TLB. Next: Read data from physical memory.")
            self.updateTableWidget(self.tableTLB, self.tlb)
            self.tableTLB.selectRow(len(self.tlb))
            self.tablePageTable.selectRow(int(frameNumber)+1)
            self.updateTableWidget(self.tablePageTable, self.pageTable)
            self.labelPhysicalAddr.setText(str(self.generatePhysicalAddr(frameNumber, offset)))
            self.updateAddressTable(self.tablePhysicalAddr, frameNumber, offset)
            self.updateTableWidget(self.tablePhysicalMemory, self.physicalMemory)
            self.tablePhysicalMemory.selectRow(int(frameNumber))
            self.tablePhysicalMemory.setFocus()
            self.state = 5

        elif self.state == 5:
            self.labelData.setText(dataRead)
            self.tablePhysicalMemory.setCurrentCell(int(frameNumber), offset)
            self.tablePhysicalMemory.setFocus()
            self.labelStatus.setText(f"Read data from physical memory successfully. Next: Load next address from reference string.")
            self.updateStats()
            self.state = 1

        elif self.state == 6:
            self.labelStatus.setText("Finished reading all addresses from reference string. Log generated in output.txt")
            pageFaultRate = self.pageFaultCounter * 100 / self.addressReadCounter
            tlbHitRate = self.tlbHitCounter * 100 / self.addressReadCounter
            outStr = 'Number of translated address: ' + str(self.addressReadCounter) + '\n' + 'Number of page fault: ' + str(
                self.pageFaultCounter) + '\n' + 'Page fault rate: ' + str(pageFaultRate) + '%\n' + 'Number of TLB hits: ' + str(
                self.tlbHitCounter) + '\n' + 'TLB hit rate: ' + str(tlbHitRate) + '%\n'
            self.outputFile.write(outStr)

            self.outputFile.close()
            self.addressFile.close()
            self.state = 7

    def generatePhysicalAddr(self, frameNumber, offset):
        return ((int(frameNumber) << self.pageSizeBytes) + int(offset)) & ((1 << (self.framesCount + self.pageSizeBytes)) - 1)

    def updateAddressTable(self, tableElement, number, offset):
        tableElement.setItem(2, 0, QTableWidgetItem(str(number)))
        tableElement.setItem(2, 1, QTableWidgetItem(str(offset)))
        tableElement.item(2, 0).setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        tableElement.item(2, 1).setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

    def updateTableWidget(self, tableElement, data):
        for i in range(len(data)):
            for j in range(len(data[i])):
                tableElement.setItem(i if tableElement == self.tablePhysicalMemory or tableElement == self.tableRefString else i+1, j, QTableWidgetItem(str(data[i][j])))
                tableElement.item(i if tableElement == self.tablePhysicalMemory or tableElement == self.tableRefString else i+1, j).setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

    def updateStats(self):
        self.labeladdressReadCounter.setText(str(self.addressReadCounter))
        self.labelTLBHitCount.setText(str(self.tlbHitCounter))
        tlbHitRate = self.tlbHitCounter * 100 / self.addressReadCounter
        self.labelTLBHitRate.setText("{:.2f}".format(tlbHitRate) + "%")
        self.labelPageFaultCount.setText(str(self.pageFaultCounter))
        pageFaultRate = self.pageFaultCounter * 100 / self.addressReadCounter
        self.labelPageFaultRate.setText("{:.2f}".format(pageFaultRate) + "%")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    print("--------------------------")
    pagesCount =    input("Enter no. of pages (default 1048576) : ") or 1048576
    framesCount =   input("Enter no. of frames (default 256)  : ") or 256
    pageSizeBytes = input("Enter page size in bytes (default 16): ") or 16
    TLBframesCount =input("Enter no. of TLB frames (default 3)  : ") or 3
    addressesFile  =input("Enter file name which contains reference string (default addresses2.txt): ") or "addresses2.txt"
    print("--------------------------")

    win = Window(int(pagesCount), int(framesCount), int(pageSizeBytes), int(TLBframesCount), addressesFile)
    win.show()
    sys.exit(app.exec())