import pageHandler

def checkTLB(pageNumber, physicalMemory, offset, logicalAddress, tlb, i, outputFile, framesCount, pageSizeBytes):
    for j in range(len(tlb)):
        if pageNumber == tlb[j][0]:
            print("Page Number \"" + str(pageNumber) + "\" found in TLB!!")
            frameNumber = tlb[j][1]
            data = pageHandler.readPhysicalMemory(frameNumber, offset, physicalMemory)
            physicalAddress = generatePhysicalAddr(frameNumber, offset, framesCount, pageSizeBytes)
            outStr = str(i) + " Virtual address: " + str(logicalAddress) + " Physical address: " + str(
                physicalAddress) + " Value: " + data + "\n"
            print(str(i) + " Virtual address: " + str(logicalAddress) + " Physical address: " + str(
                physicalAddress) + " Value: " + data)
            outputFile.write(outStr)
            pageHandler.updateTLBCounter(j, tlb)
            return (1, frameNumber, data)

    return (0, None, None)


def checkPageTable(pageNumber, logicalAddress, offset, i, pageTable, physicalMemory, outputFile, framesCount, pageSizeBytes):
    for k in range(len(pageTable)):
        if pageNumber == pageTable[k][0]:
            print("Page Number \"" + str(pageNumber) + "\" found in page table!!")
            frameNumber = pageTable[k][1]
            data = pageHandler.readPhysicalMemory(frameNumber, offset, physicalMemory)
            physicalAddress = generatePhysicalAddr(frameNumber, offset, framesCount, pageSizeBytes)
            outStr = str(i) + " Virtual address: " + str(logicalAddress) + " Physical address: " + str(
                physicalAddress) + " Value: " + data + "\n"
            print(str(i) + " Virtual address: " + str(logicalAddress) + " Physical address: " + str(
                physicalAddress) + " Value: " + data)
            outputFile.write(outStr)
            pageHandler.updatepageTableCounter(k, pageTable)
            return (1, frameNumber, data)

    return (0, None, None)

def generatePhysicalAddr(frameNumber, offset, framesCount, pageSizeBytes):
    return int(((int(frameNumber) << pageSizeBytes) + int(offset)) & ((1 << (framesCount + pageSizeBytes)) - 1))