def pageFaultHandler(pageNumber, tlb, pageTable, physicalMemory, TLBframesCount, framesCount, pagesCount, pageSizeBytes):
    if int(pageNumber) < pagesCount:
        for i in range(framesCount):
            if i in physicalMemory.keys():
                continue
            else:
                frameNumber = str(i)
                break

        secondaryMemory = open("secondaryMemory.bin", "rb")
        physicalMemory[int(frameNumber)] = []

        for i in range(pageSizeBytes):
            secondaryMemory.seek(int(pageNumber)*pageSizeBytes+i)
            data = str(int.from_bytes(secondaryMemory.read(1), byteorder='big', signed=True))
            physicalMemory[int(frameNumber)].insert(i, data)

        secondaryMemory.close()
        print('Found page \"' + str(pageNumber) + '\" has data: ')
        print(physicalMemory[int(frameNumber)])
        print('in the backing store!\n')

    else:
        print('Page \"' + pageNumber + '\" is out of bound!')
        return

    updateTLB(pageNumber, frameNumber, tlb, TLBframesCount)
    updatePageTable(pageNumber, frameNumber, pageTable, framesCount)


def updateTLB(pageNumber, frameNumber, tlb, TLBframesCount):
    # remove list[0], append new item at the end
    if len(tlb) < TLBframesCount:
        tlb.append([pageNumber, frameNumber])
    else:
        # FIFO
        tlb.pop(0)
        tlb.append([pageNumber, frameNumber])

    print('Successfully update TLB with pageNumber: ' + str(pageNumber) + ', frameNumber: ' + str(frameNumber) + '!')


def updatePageTable(pageNumber, frameNumber, pageTable, framesCount):
    # remove list[0], append new item at the end
    if len(pageTable) < framesCount:
        pageTable.append([pageNumber, frameNumber])
    else:
        pageTable.pop(0)
        pageTable.append([pageNumber, frameNumber])

    print('Successfully update pageTable table with pageNumber: ' + str(pageNumber) + ', frameNumber: ' + str(frameNumber) + '!')


def updateTLBCounter(latestEntryIndex, tlb):
    # remove list[latestEntryIndex], append new item at the end
    latestEntry = tlb[latestEntryIndex]
    tlb.pop(latestEntryIndex)
    tlb.append(latestEntry)

    print('Successfully update TLB with new sequence using LRU!')


def updatepageTableCounter(latestEntryIndex, pageTable):
    # remove list[latestEntryIndex], append new item at the end
    latestEntry = pageTable[latestEntryIndex]
    pageTable.pop(latestEntryIndex)
    pageTable.append(latestEntry)

    print('Successfully update page table with new sequence using LRU!')


def readPhysicalMemory(frameNumber, offset, physicalMemory):
    # if (int(frameNumber) < 4) and (int(offset) < 4):
    data = physicalMemory[int(frameNumber)][int(offset)]
    print('Successfully read frameNumber \"' + str(frameNumber) + '\" offset \"' + str(offset) + '\"\'s data ')
    print(data)
    print('in the physical memory!\n')
    return data
    # else:
    #     print('Frame number or offset is out of bound')


