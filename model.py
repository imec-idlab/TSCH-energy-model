class SlotType:
    TxDataRxAck = 1
    RxDataTxAck = 2
    TxData      = 3
    RxData      = 4
    RxIdle      = 5
    Sleep       = 6
    TxDataRxAckMissing = 7

def Model(radio = 'CC1200', txPower = 10):
    ACK_LENGTH = 27
    CRC_LENGTH = 2

    TsSlotDuration   = 15000
    TsTxOffset       = 131 / 32768.0 * 1000000   # 4000us
    TsTxAckDelay     = 151 / 32768.0 * 1000000   # 4606us
    TsLongGT         =  43 / 32768.0 * 1000000   # 1300us
    TsShortGT        =  16 / 32768.0 * 1000000   #  500us

    if radio == 'CC1200':
        CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  = 0.00012
        CONSUMPTION_CPU_ACTIVE_RADIO_IDLE   = 1.5
        CONSUMPTION_CPU_ACTIVE_RADIO_RX     = 23.5
        CONSUMPTION_CPU_ACTIVE_RADIO_LISTEN = 23.5
        CONSUMPTION_CPU_SLEEP_RADIO_SLEEP   = 0.00012
        CONSUMPTION_CPU_SLEEP_RADIO_IDLE    = 1.5
        CONSUMPTION_CPU_SLEEP_RADIO_RX      = 23.5
        CONSUMPTION_CPU_SLEEP_RADIO_LISTEN  = 23.5

        if txPower == 10:
            CONSUMPTION_CPU_ACTIVE_RADIO_TX = 36
            CONSUMPTION_CPU_SLEEP_RADIO_TX  = 36
        elif txPower == 14:
            CONSUMPTION_CPU_ACTIVE_RADIO_TX = 46
            CONSUMPTION_CPU_SLEEP_RADIO_TX  = 46
        else:
            raise RuntimeError("Unsupported txPower value")

        DelayTx          =  14 / 32768.0 * 1000000   #  427us
        DelayRx          =   0 / 32768.0 * 1000000   #    0us
        MaxTxDataPrepare =  66 / 32768.0 * 1000000   # 2014us
        MaxRxDataPrepare =  33 / 32768.0 * 1000000   # 1007us
        MaxTxAckPrepare  =  33 / 32768.0 * 1000000   # 1007us
        MaxRxAckPrepare  =  30 / 32768.0 * 1000000   #  915us

    else:
        raise RuntimeError("Unsupported radio specified")

    DurationTT1 = TsTxOffset - DelayTx - MaxTxDataPrepare
    DurationTT5 = TsTxAckDelay - TsShortGT - DelayRx - MaxRxAckPrepare

    DurationRT1 = TsTxOffset - TsLongGT - DelayRx - MaxRxDataPrepare
    DurationRT5 = TsTxAckDelay - DelayTx - MaxTxAckPrepare

    def calcConsumption(slotType, packetSize=0):
        consumption = 0

        if slotType == SlotType.TxDataRxAck:
            if radio == 'CC1200':
                DurationTxDataOffsetStart = 105  # ti1
                DurationTxDataOffset      = DurationTT1 - DurationTxDataOffsetStart
                DurationTxDataPrepare     = 291 + (69 + packetSize * 8.152) + 378  # ti2
                DurationTxDataReady       = MaxTxDataPrepare - DurationTxDataPrepare
                DurationTxDataDelayStart  = 58  # ti3
                DurationTxDataDelay       = DelayTx - DurationTxDataDelayStart
                DurationTxDataStart       = 16  # ti4
                DurationTxData            = (1 + packetSize + CRC_LENGTH) * 160 - DurationTxDataStart
                DurationRxAckOffsetStart  = 75  # ti5
                DurationRxAckOffset       = DurationTT5 - DurationRxAckOffsetStart
                DurationRxAckPrepare      = 587  # ti6
                DurationRxAckReady        = MaxRxAckPrepare - DurationRxAckPrepare
                DurationRxAckListenStart  = 58  # ti7
                DurationRxAckListen       = DelayRx + TsShortGT - DurationRxAckListenStart
                DurationRxAckStart        = 15  # ti8
                DurationRxAck             = (1 + ACK_LENGTH) * 160 - DurationRxAckStart
                DurationTxProc            = 619  # ti9
                DurationSleep             = TsSlotDuration - DurationTxProc - DurationRxAck - DurationRxAckStart - TsTxAckDelay - DurationTxData - DurationTxDataStart - TsTxOffset

            consumption += DurationTxDataOffsetStart * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ti1
            consumption += DurationTxDataOffset * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP
            consumption += DurationTxDataPrepare * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti2
            consumption += DurationTxDataReady * CONSUMPTION_CPU_SLEEP_RADIO_IDLE
            consumption += DurationTxDataDelayStart * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti3
            consumption += DurationTxDataDelay * CONSUMPTION_CPU_SLEEP_RADIO_TX
            consumption += DurationTxDataStart * CONSUMPTION_CPU_ACTIVE_RADIO_TX  # ti4
            consumption += DurationTxData * CONSUMPTION_CPU_SLEEP_RADIO_TX
            consumption += DurationRxAckOffsetStart * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ti5
            consumption += DurationRxAckOffset * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP
            consumption += DurationRxAckPrepare * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti6
            consumption += DurationRxAckReady * CONSUMPTION_CPU_SLEEP_RADIO_IDLE
            consumption += DurationRxAckListenStart * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti7
            consumption += DurationRxAckListen * CONSUMPTION_CPU_SLEEP_RADIO_LISTEN
            consumption += DurationRxAckStart * CONSUMPTION_CPU_ACTIVE_RADIO_RX  # ti8
            consumption += DurationRxAck * CONSUMPTION_CPU_SLEEP_RADIO_RX
            consumption += DurationTxProc * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti9
            consumption += DurationSleep * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP

        elif slotType == SlotType.TxData:
            if radio == 'CC1200':
                DurationTxDataOffsetStart = 105  # ti1
                DurationTxDataOffset      = DurationTT1 - DurationTxDataOffsetStart
                DurationTxDataPrepare     = 291 + (69 + packetSize * 8.152) + 378  # ti2
                DurationTxDataReady       = MaxTxDataPrepare - DurationTxDataPrepare
                DurationTxDataDelayStart  = 58  # ti3
                DurationTxDataDelay       = DelayTx - DurationTxDataDelayStart
                DurationTxDataStart       = 16  # ti4
                DurationTxData            = (1 + packetSize + CRC_LENGTH) * 160 - DurationTxDataStart
                DurationTxProc            = 109  # ti5
                DurationSleep             = TsSlotDuration - DurationTxProc - DurationTxData - DurationTxDataStart - TsTxOffset

            consumption += DurationTxDataOffsetStart * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ti1
            consumption += DurationTxDataOffset * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP
            consumption += DurationTxDataPrepare * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti2
            consumption += DurationTxDataReady * CONSUMPTION_CPU_SLEEP_RADIO_IDLE
            consumption += DurationTxDataDelayStart * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti3
            consumption += DurationTxDataDelay * CONSUMPTION_CPU_SLEEP_RADIO_TX
            consumption += DurationTxDataStart * CONSUMPTION_CPU_ACTIVE_RADIO_TX  # ti4
            consumption += DurationTxData * CONSUMPTION_CPU_SLEEP_RADIO_TX
            consumption += DurationTxProc * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ti5
            consumption += DurationSleep * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP

        elif slotType == SlotType.TxDataRxAckMissing:
            if radio == 'CC1200':
                DurationTxDataOffsetStart = 105  # ti1
                DurationTxDataOffset      = DurationTT1 - DurationTxDataOffsetStart
                DurationTxDataPrepare     = 291 + (69 + packetSize * 8.152) + 378  # ti2
                DurationTxDataReady       = MaxTxDataPrepare - DurationTxDataPrepare
                DurationTxDataDelayStart  = 58  # ti3
                DurationTxDataDelay       = DelayTx - DurationTxDataDelayStart
                DurationTxDataStart       = 16  # ti4
                DurationTxData            = (1 + packetSize + CRC_LENGTH) * 160 - DurationTxDataStart
                DurationRxAckOffsetStart  = 75  # ti5
                DurationRxAckOffset       = DurationTT5 - DurationRxAckOffsetStart
                DurationRxAckPrepare      = 587  # ti6
                DurationRxAckReady        = MaxRxAckPrepare - DurationRxAckPrepare
                DurationRxAckListenStart  = 58  # ti7
                DurationRxAckListen       = DelayRx + 2*TsShortGT - DurationRxAckListenStart
                DurationTxProc            = 137  # tie5
                DurationSleep             = TsSlotDuration - DurationTxProc - TsShortGT - TsTxAckDelay - DurationTxData - DurationTxDataStart - TsTxOffset

            consumption += DurationTxDataOffsetStart * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ti1
            consumption += DurationTxDataOffset * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP
            consumption += DurationTxDataPrepare * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti2
            consumption += DurationTxDataReady * CONSUMPTION_CPU_SLEEP_RADIO_IDLE
            consumption += DurationTxDataDelayStart * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti3
            consumption += DurationTxDataDelay * CONSUMPTION_CPU_SLEEP_RADIO_TX
            consumption += DurationTxDataStart * CONSUMPTION_CPU_ACTIVE_RADIO_TX  # ti4
            consumption += DurationTxData * CONSUMPTION_CPU_SLEEP_RADIO_TX
            consumption += DurationRxAckOffsetStart * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ti5
            consumption += DurationRxAckOffset * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP
            consumption += DurationRxAckPrepare * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti6
            consumption += DurationRxAckReady * CONSUMPTION_CPU_SLEEP_RADIO_IDLE
            consumption += DurationRxAckListenStart * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ti7
            consumption += DurationRxAckListen * CONSUMPTION_CPU_SLEEP_RADIO_LISTEN
            consumption += DurationTxProc * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ti9
            consumption += DurationSleep * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP

        elif slotType == SlotType.RxDataTxAck:
            if radio == 'CC1200':
                DurationRxDataOffsetStart = 126  # ri1
                DurationRxDataOffset      = DurationRT1 - DurationRxDataOffsetStart
                DurationRxDataPrepare     = 676  # ri2
                DurationRxDataReady       = MaxRxDataPrepare - DurationRxDataPrepare
                DurationRxDataListenStart = 58  # ri3
                DurationRxDataListen      = DelayRx + TsLongGT - DurationRxDataListenStart
                DurationRxDataStart       = 15  # ri4
                DurationRxData            = (1 + packetSize + CRC_LENGTH) * 160 - DurationRxDataStart
                DurationTxAckOffsetStart  = 30 + (190 + (packetSize * 8.439)) + 142  # ri5
                DurationTxAckOffset       = DurationRT5 - DurationTxAckOffsetStart
                DurationTxAckPrepare      = 930  # ri6
                DurationTxAckReady        = MaxTxAckPrepare - DurationTxAckPrepare
                DurationTxAckDelayStart   = 58  # ri7
                DurationTxAckDelay        = DelayTx - DurationTxAckDelayStart
                DurationTxAckStart        = 15  # ri8
                DurationTxAck             = (1 + ACK_LENGTH) * 160 - DurationTxAckStart
                DurationRxProc            = 135  # ri9
                DurationSleep             = TsSlotDuration - DurationRxProc - DurationTxAck - DurationTxAckStart - TsTxAckDelay - DurationRxData - DurationRxDataStart - TsTxOffset

            consumption += DurationRxDataOffsetStart * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ri1
            consumption += DurationRxDataOffset * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP
            consumption += DurationRxDataPrepare * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ri2
            consumption += DurationRxDataReady * CONSUMPTION_CPU_SLEEP_RADIO_IDLE
            consumption += DurationRxDataListenStart * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ri3
            consumption += DurationRxDataListen * CONSUMPTION_CPU_SLEEP_RADIO_LISTEN
            consumption += DurationRxDataStart * CONSUMPTION_CPU_ACTIVE_RADIO_RX  # ri4
            consumption += DurationRxData * CONSUMPTION_CPU_SLEEP_RADIO_RX
            consumption += DurationTxAckOffsetStart * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ri5
            consumption += DurationTxAckOffset * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP
            consumption += DurationTxAckPrepare * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ri6
            consumption += DurationTxAckReady * CONSUMPTION_CPU_SLEEP_RADIO_IDLE
            consumption += DurationTxAckDelayStart * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ri7
            consumption += DurationTxAckDelay * CONSUMPTION_CPU_SLEEP_RADIO_TX
            consumption += DurationTxAckStart * CONSUMPTION_CPU_ACTIVE_RADIO_TX  # ri8
            consumption += DurationTxAck * CONSUMPTION_CPU_SLEEP_RADIO_TX
            consumption += DurationRxProc * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ri9
            consumption += DurationSleep * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP

        elif slotType == SlotType.RxData:
            if radio == 'CC1200':
                DurationRxDataOffsetStart = 126  # ri1
                DurationRxDataOffset      = DurationRT1 - DurationRxDataOffsetStart
                DurationRxDataPrepare     = 676  # ri2
                DurationRxDataReady       = MaxRxDataPrepare - DurationRxDataPrepare
                DurationRxDataListenStart = 58  # ri3
                DurationRxDataListen      = DelayRx + TsLongGT - DurationRxDataListenStart
                DurationRxDataStart       = 15  # ri4
                DurationRxData            = (1 + packetSize + CRC_LENGTH) * 160 - DurationRxDataStart
                DurationRxProc            = 30 + (190 + (packetSize * 8.439)) + 268  # ri5
                DurationSleep             = TsSlotDuration - DurationRxProc - DurationRxData - DurationRxDataStart - TsTxOffset

            consumption += DurationRxDataOffsetStart * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ri1
            consumption += DurationRxDataOffset * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP
            consumption += DurationRxDataPrepare * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ri2
            consumption += DurationRxDataReady * CONSUMPTION_CPU_SLEEP_RADIO_IDLE
            consumption += DurationRxDataListenStart * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ri3
            consumption += DurationRxDataListen * CONSUMPTION_CPU_SLEEP_RADIO_LISTEN
            consumption += DurationRxDataStart * CONSUMPTION_CPU_ACTIVE_RADIO_RX  # ri4
            consumption += DurationRxData * CONSUMPTION_CPU_SLEEP_RADIO_RX
            consumption += DurationRxProc * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ri5
            consumption += DurationSleep * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP

        elif slotType == SlotType.RxIdle:
            if radio == 'CC1200':
                DurationRxDataOffsetStart = 126  # ri1
                DurationRxDataOffset      = DurationRT1 - DurationRxDataOffsetStart
                DurationRxDataPrepare     = 676  # ri2
                DurationRxDataReady       = MaxRxDataPrepare - DurationRxDataPrepare
                DurationRxDataListenStart = 58  # ri3
                DurationRxDataListen      = DelayRx + 2*TsLongGT - DurationRxDataListenStart
                DurationRxProc            = 118  # rie2
                DurationSleep             = TsSlotDuration - DurationRxProc - TsLongGT - TsTxOffset

            consumption += DurationRxDataOffsetStart * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # ri1
            consumption += DurationRxDataOffset * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP
            consumption += DurationRxDataPrepare * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ri2
            consumption += DurationRxDataReady * CONSUMPTION_CPU_SLEEP_RADIO_IDLE
            consumption += DurationRxDataListenStart * CONSUMPTION_CPU_ACTIVE_RADIO_IDLE  # ri3
            consumption += DurationRxDataListen * CONSUMPTION_CPU_SLEEP_RADIO_LISTEN
            consumption += DurationRxProc * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  # rie2
            consumption += DurationSleep * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP

        elif slotType == SlotType.Sleep:
            DurationSleepStart = 57
            DurationSleep      = TsSlotDuration - DurationSleepStart

            consumption += DurationSleepStart * CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP
            consumption += DurationSleep * CONSUMPTION_CPU_SLEEP_RADIO_SLEEP

        else:
            raise RuntimeError("Invalid slot type")

        return round(consumption / 1000, 2)  # mA x us / 1000 = uC

    return calcConsumption


PACKET_LENGTH = 125  # Excludes CRC, maximum allowed value is 125

def printModelValues(model):
    print('        TxDataRxAck: ' + str(model(SlotType.TxDataRxAck, PACKET_LENGTH)) + ' uC')
    print('        RxDataTxAck: ' + str(model(SlotType.RxDataTxAck, PACKET_LENGTH)) + ' uC')
    print('        TxData: ' + str(model(SlotType.TxData, PACKET_LENGTH)) + ' uC')
    print('        RxData: ' + str(model(SlotType.RxData, PACKET_LENGTH)) + ' uC')
    print('        RxIdle: ' + str(model(SlotType.RxIdle, PACKET_LENGTH)) + ' uC')
    print('        Sleep: ' + str(model(SlotType.Sleep)) + ' uC')
    print('        TxDataRxAckMissing: ' + str(model(SlotType.TxDataRxAckMissing, PACKET_LENGTH)) + ' uC')

print('Packet length: ' + str(PACKET_LENGTH))
print('CC1200 radio:')
print('   14 dBm:')
printModelValues(Model('CC1200', 14))
print('    10 dBm:')
printModelValues(Model('CC1200', 10))
