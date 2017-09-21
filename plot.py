import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy import interpolate

class SlotType:
    TxDataRxAck = 1
    RxDataTxAck = 2
    TxData      = 3
    RxData      = 4
    RxIdle      = 5
    Sleep       = 6
    TxDataRxAckMissing = 7

def Model(radio = 'CC2538', txPower = 0):
    ACK_LENGTH = 27
    CRC_LENGTH = 2

    TsSlotDuration   = 15000
    TsTxOffset       = 131 / 32768.0 * 1000000   # 4000us
    TsTxAckDelay     = 151 / 32768.0 * 1000000   # 4606us
    TsLongGT         =  43 / 32768.0 * 1000000   # 1300us
    TsShortGT        =  16 / 32768.0 * 1000000   #  500us

    if radio == 'CC2538':
        CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  = 18.5253
        CONSUMPTION_CPU_ACTIVE_RADIO_IDLE   = 18.5253
        CONSUMPTION_CPU_ACTIVE_RADIO_RX     = 32.1613
        CONSUMPTION_CPU_ACTIVE_RADIO_LISTEN = 36.0883
        CONSUMPTION_CPU_SLEEP_RADIO_SLEEP   = 12.1690
        CONSUMPTION_CPU_SLEEP_RADIO_IDLE    = 12.1690
        CONSUMPTION_CPU_SLEEP_RADIO_RX      = 25.5274
        CONSUMPTION_CPU_SLEEP_RADIO_LISTEN  = 29.6143

        if txPower == 3:
            CONSUMPTION_CPU_ACTIVE_RADIO_TX = 37.9312
            CONSUMPTION_CPU_SLEEP_RADIO_TX  = 31.4720
        elif txPower == 0:
            CONSUMPTION_CPU_ACTIVE_RADIO_TX = 36.1228
            CONSUMPTION_CPU_SLEEP_RADIO_TX  = 29.6779
        else:
            raise RuntimeError("Unsupported txPower value")

        DelayTx          =  12 / 32768.0 * 1000000   #  366us
        DelayRx          =   0 / 32768.0 * 1000000   #    0us
        MaxTxDataPrepare =  66 / 32768.0 * 1000000   # 2014us
        MaxRxDataPrepare =  33 / 32768.0 * 1000000   # 1007us
        MaxTxAckPrepare  =  22 / 32768.0 * 1000000   #  671us
        MaxRxAckPrepare  =  10 / 32768.0 * 1000000   #  305us

    elif radio == 'CC1200':
        CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP  = 18.5977
        CONSUMPTION_CPU_ACTIVE_RADIO_IDLE   = 21.0067
        CONSUMPTION_CPU_ACTIVE_RADIO_RX     = 57.3220
        CONSUMPTION_CPU_ACTIVE_RADIO_LISTEN = 43.3729
        CONSUMPTION_CPU_SLEEP_RADIO_SLEEP   = 12.4005
        CONSUMPTION_CPU_SLEEP_RADIO_IDLE    = 15.0322
        CONSUMPTION_CPU_SLEEP_RADIO_RX      = 50.7769
        CONSUMPTION_CPU_SLEEP_RADIO_LISTEN  = 38.2895

        if txPower == 14:
            CONSUMPTION_CPU_ACTIVE_RADIO_TX = 102.7338
            CONSUMPTION_CPU_SLEEP_RADIO_TX  = 96.6123
        elif txPower == 0:
            CONSUMPTION_CPU_ACTIVE_RADIO_TX = 59.3448
            CONSUMPTION_CPU_SLEEP_RADIO_TX  = 53.6732
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

    class State:
        def __init__(self):
            self.points = [[0, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP]]
            self.offset = 0

    def plot(slotType, packetSize=0):
        consumption = 0

        state = State()
        def addLine(state, width, consumption):
            width = round(width)
            state.points += [[state.offset+1, consumption], [state.offset+width, consumption]]
            state.offset += width

        if slotType == SlotType.TxDataRxAck:
            if radio == 'CC2538':
                DurationTxDataOffsetStart = 105  # ti1
                DurationTxDataOffset      = DurationTT1 - DurationTxDataOffsetStart
                DurationTxDataPrepare     = 33 + (5 + packetSize * 0.875) + 22  # ti2
                DurationTxDataReady       = MaxTxDataPrepare - DurationTxDataPrepare
                DurationTxDataDelayStart  = 17  # ti3
                DurationTxDataDelay       = DelayTx - DurationTxDataDelayStart
                DurationTxDataStart       = 16  # ti4
                DurationTxData            = (1 + packetSize + CRC_LENGTH) * 32 - DurationTxDataStart
                DurationRxAckOffsetStart  = 32  # ti5
                DurationRxAckOffset       = DurationTT5 - DurationRxAckOffsetStart
                DurationRxAckPrepare      = 38  # ti6
                DurationRxAckReady        = MaxRxAckPrepare - DurationRxAckPrepare
                DurationRxAckListenStart  = 17  # ti7
                DurationRxAckListen       = DelayRx + TsShortGT - DurationRxAckListenStart
                DurationRxAckStart        = 16  # ti8
                DurationRxAck             = (1 + ACK_LENGTH) * 32 - DurationRxAckStart
                DurationTxProc            = 225  # ti9
                DurationSleep             = TsSlotDuration - DurationTxProc - DurationRxAck - DurationRxAckStart - TsTxAckDelay - DurationTxData - DurationTxDataStart - TsTxOffset

            elif radio == 'CC1200':
                DurationTxDataOffsetStart = 105  # ti1
                DurationTxDataOffset      = DurationTT1 - DurationTxDataOffsetStart
                DurationTxDataPrepare     = 291 + (69 + packetSize * 8.152) + 378  # ti2
                DurationTxDataReady       = MaxTxDataPrepare - DurationTxDataPrepare
                DurationTxDataDelayStart  = 58  # ti3
                DurationTxDataDelay       = DelayTx - DurationTxDataDelayStart
                DurationTxDataStart       = 16  # ti4
                DurationTxData            = (1 + packetSize + CRC_LENGTH) * 32 - DurationTxDataStart
                DurationRxAckOffsetStart  = 75  # ti5
                DurationRxAckOffset       = DurationTT5 - DurationRxAckOffsetStart
                DurationRxAckPrepare      = 587  # ti6
                DurationRxAckReady        = MaxRxAckPrepare - DurationRxAckPrepare
                DurationRxAckListenStart  = 58  # ti7
                DurationRxAckListen       = DelayRx + TsShortGT - DurationRxAckListenStart
                DurationRxAckStart        = 15  # ti8
                DurationRxAck             = (1 + ACK_LENGTH) * 32 - DurationRxAckStart
                DurationTxProc            = 619  # ti9
                DurationSleep             = TsSlotDuration - DurationTxProc - DurationRxAck - DurationRxAckStart - TsTxAckDelay - DurationTxData - DurationTxDataStart - TsTxOffset

            addLine(state, DurationTxDataOffsetStart, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ti1
            addLine(state, DurationTxDataOffset, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)
            addLine(state, DurationTxDataPrepare, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti2
            addLine(state, DurationTxDataReady, CONSUMPTION_CPU_SLEEP_RADIO_IDLE)
            addLine(state, DurationTxDataDelayStart, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti3
            addLine(state, DurationTxDataDelay, CONSUMPTION_CPU_SLEEP_RADIO_TX)
            addLine(state, DurationTxDataStart, CONSUMPTION_CPU_ACTIVE_RADIO_TX)  # ti4
            addLine(state, DurationTxData, CONSUMPTION_CPU_SLEEP_RADIO_TX)
            addLine(state, DurationRxAckOffsetStart, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ti5
            addLine(state, DurationRxAckOffset, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)
            addLine(state, DurationRxAckPrepare, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti6
            addLine(state, DurationRxAckReady, CONSUMPTION_CPU_SLEEP_RADIO_IDLE)
            addLine(state, DurationRxAckListenStart, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti7
            addLine(state, DurationRxAckListen, CONSUMPTION_CPU_SLEEP_RADIO_LISTEN)
            addLine(state, DurationRxAckStart, CONSUMPTION_CPU_ACTIVE_RADIO_RX)  # ti8
            addLine(state, DurationRxAck, CONSUMPTION_CPU_SLEEP_RADIO_RX)
            addLine(state, DurationTxProc, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti9
            addLine(state, DurationSleep, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)

        elif slotType == SlotType.TxData:
            if radio == 'CC2538':
                DurationTxDataOffsetStart = 105  # ti1
                DurationTxDataOffset      = DurationTT1 - DurationTxDataOffsetStart
                DurationTxDataPrepare     = 33 + (5 + packetSize * 0.875) + 22  # ti2
                DurationTxDataReady       = MaxTxDataPrepare - DurationTxDataPrepare
                DurationTxDataDelayStart  = 17  # ti3
                DurationTxDataDelay       = DelayTx - DurationTxDataDelayStart
                DurationTxDataStart       = 16  # ti4
                DurationTxData            = (1 + packetSize + CRC_LENGTH) * 32 - DurationTxDataStart
                DurationTxProc            = 72  # ti5
                DurationSleep             = TsSlotDuration - DurationTxProc - DurationTxData - DurationTxDataStart - TsTxOffset

            elif radio == 'CC1200':
                DurationTxDataOffsetStart = 105  # ti1
                DurationTxDataOffset      = DurationTT1 - DurationTxDataOffsetStart
                DurationTxDataPrepare     = 291 + (69 + packetSize * 8.152) + 378  # ti2
                DurationTxDataReady       = MaxTxDataPrepare - DurationTxDataPrepare
                DurationTxDataDelayStart  = 58  # ti3
                DurationTxDataDelay       = DelayTx - DurationTxDataDelayStart
                DurationTxDataStart       = 16  # ti4
                DurationTxData            = (1 + packetSize + CRC_LENGTH) * 32 - DurationTxDataStart
                DurationTxProc            = 109  # ti5
                DurationSleep             = TsSlotDuration - DurationTxProc - DurationTxData - DurationTxDataStart - TsTxOffset

            addLine(state, DurationTxDataOffsetStart, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ti1
            addLine(state, DurationTxDataOffset, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)
            addLine(state, DurationTxDataPrepare, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti2
            addLine(state, DurationTxDataReady, CONSUMPTION_CPU_SLEEP_RADIO_IDLE)
            addLine(state, DurationTxDataDelayStart, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti3
            addLine(state, DurationTxDataDelay, CONSUMPTION_CPU_SLEEP_RADIO_TX)
            addLine(state, DurationTxDataStart, CONSUMPTION_CPU_ACTIVE_RADIO_TX)  # ti4
            addLine(state, DurationTxData, CONSUMPTION_CPU_SLEEP_RADIO_TX)
            addLine(state, DurationTxProc, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ti5
            addLine(state, DurationSleep, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)

        elif slotType == SlotType.TxDataRxAckMissing:
            if radio == 'CC2538':
                DurationTxDataOffsetStart = 105  # ti1
                DurationTxDataOffset      = DurationTT1 - DurationTxDataOffsetStart
                DurationTxDataPrepare     = 33 + (5 + packetSize * 0.875) + 22  # ti2
                DurationTxDataReady       = MaxTxDataPrepare - DurationTxDataPrepare
                DurationTxDataDelayStart  = 17  # ti3
                DurationTxDataDelay       = DelayTx - DurationTxDataDelayStart
                DurationTxDataStart       = 16  # ti4
                DurationTxData            = (1 + packetSize + CRC_LENGTH) * 32 - DurationTxDataStart
                DurationRxAckOffsetStart  = 32  # ti5
                DurationRxAckOffset       = DurationTT5 - DurationRxAckOffsetStart
                DurationRxAckPrepare      = 38  # ti6
                DurationRxAckReady        = MaxRxAckPrepare - DurationRxAckPrepare
                DurationRxAckListenStart  = 17  # ti7
                DurationRxAckListen       = DelayRx + 2*TsShortGT - DurationRxAckListenStart
                DurationTxProc            = 44  # tie5
                DurationSleep             = TsSlotDuration - DurationTxProc - TsShortGT - TsTxAckDelay - DurationTxData - DurationTxDataStart - TsTxOffset

            elif radio == 'CC1200':
                DurationTxDataOffsetStart = 105  # ti1
                DurationTxDataOffset      = DurationTT1 - DurationTxDataOffsetStart
                DurationTxDataPrepare     = 291 + (69 + packetSize * 8.152) + 378  # ti2
                DurationTxDataReady       = MaxTxDataPrepare - DurationTxDataPrepare
                DurationTxDataDelayStart  = 58  # ti3
                DurationTxDataDelay       = DelayTx - DurationTxDataDelayStart
                DurationTxDataStart       = 16  # ti4
                DurationTxData            = (1 + packetSize + CRC_LENGTH) * 32 - DurationTxDataStart
                DurationRxAckOffsetStart  = 75  # ti5
                DurationRxAckOffset       = DurationTT5 - DurationRxAckOffsetStart
                DurationRxAckPrepare      = 587  # ti6
                DurationRxAckReady        = MaxRxAckPrepare - DurationRxAckPrepare
                DurationRxAckListenStart  = 58  # ti7
                DurationRxAckListen       = DelayRx + 2*TsShortGT - DurationRxAckListenStart
                DurationTxProc            = 137  # tie5
                DurationSleep             = TsSlotDuration - DurationTxProc - TsShortGT - TsTxAckDelay - DurationTxData - DurationTxDataStart - TsTxOffset

            addLine(state, DurationTxDataOffsetStart, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ti1
            addLine(state, DurationTxDataOffset, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)
            addLine(state, DurationTxDataPrepare, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti2
            addLine(state, DurationTxDataReady, CONSUMPTION_CPU_SLEEP_RADIO_IDLE)
            addLine(state, DurationTxDataDelayStart, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti3
            addLine(state, DurationTxDataDelay, CONSUMPTION_CPU_SLEEP_RADIO_TX)
            addLine(state, DurationTxDataStart, CONSUMPTION_CPU_ACTIVE_RADIO_TX)  # ti4
            addLine(state, DurationTxData, CONSUMPTION_CPU_SLEEP_RADIO_TX)
            addLine(state, DurationRxAckOffsetStart, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ti5
            addLine(state, DurationRxAckOffset, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)
            addLine(state, DurationRxAckPrepare, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti6
            addLine(state, DurationRxAckReady, CONSUMPTION_CPU_SLEEP_RADIO_IDLE)
            addLine(state, DurationRxAckListenStart, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ti7
            addLine(state, DurationRxAckListen, CONSUMPTION_CPU_SLEEP_RADIO_LISTEN)
            addLine(state, DurationTxProc, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ti9
            addLine(state, DurationSleep, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)

        elif slotType == SlotType.RxDataTxAck:
            if radio == 'CC2538':
                DurationRxDataOffsetStart = 126  # ri1
                DurationRxDataOffset      = DurationRT1 - DurationRxDataOffsetStart
                DurationRxDataPrepare     = 38  # ri2
                DurationRxDataReady       = MaxRxDataPrepare - DurationRxDataPrepare
                DurationRxDataListenStart = 17  # ri3
                DurationRxDataListen      = DelayRx + TsLongGT - DurationRxDataListenStart
                DurationRxDataStart       = 17  # ri4
                DurationRxData            = (1 + packetSize + CRC_LENGTH) * 32 - DurationRxDataStart
                DurationTxAckOffsetStart  = 25 + (7 + (packetSize * 0.91)) + 94 # ri5
                DurationTxAckOffset       = DurationRT5 - DurationTxAckOffsetStart
                DurationTxAckPrepare      = 153  # ri6
                DurationTxAckReady        = MaxTxAckPrepare - DurationTxAckPrepare
                DurationTxAckDelayStart   = 17  # ri7
                DurationTxAckDelay        = DelayTx - DurationTxAckDelayStart
                DurationTxAckStart        = 16  # ri8
                DurationTxAck             = (1 + ACK_LENGTH) * 32 - DurationTxAckStart
                DurationRxProc            = 94  # ri9
                DurationSleep             = TsSlotDuration - DurationRxProc - DurationTxAck - DurationTxAckStart - TsTxAckDelay - DurationRxData - DurationRxDataStart - TsTxOffset

            elif radio == 'CC1200':
                DurationRxDataOffsetStart = 126  # ri1
                DurationRxDataOffset      = DurationRT1 - DurationRxDataOffsetStart
                DurationRxDataPrepare     = 676  # ri2
                DurationRxDataReady       = MaxRxDataPrepare - DurationRxDataPrepare
                DurationRxDataListenStart = 58  # ri3
                DurationRxDataListen      = DelayRx + TsLongGT - DurationRxDataListenStart
                DurationRxDataStart       = 15  # ri4
                DurationRxData            = (1 + packetSize + CRC_LENGTH) * 32 - DurationRxDataStart
                DurationTxAckOffsetStart  = 30 + (190 + (packetSize * 8.439)) + 142  # ri5
                DurationTxAckOffset       = DurationRT5 - DurationTxAckOffsetStart
                DurationTxAckPrepare      = 930  # ri6
                DurationTxAckReady        = MaxTxAckPrepare - DurationTxAckPrepare
                DurationTxAckDelayStart   = 58  # ri7
                DurationTxAckDelay        = DelayTx - DurationTxAckDelayStart
                DurationTxAckStart        = 15  # ri8
                DurationTxAck             = (1 + ACK_LENGTH) * 32 - DurationTxAckStart
                DurationRxProc            = 135  # ri9
                DurationSleep             = TsSlotDuration - DurationRxProc - DurationTxAck - DurationTxAckStart - TsTxAckDelay - DurationRxData - DurationRxDataStart - TsTxOffset

            addLine(state, DurationRxDataOffsetStart, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ri1
            addLine(state, DurationRxDataOffset, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)
            addLine(state, DurationRxDataPrepare, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ri2
            addLine(state, DurationRxDataReady, CONSUMPTION_CPU_SLEEP_RADIO_IDLE)
            addLine(state, DurationRxDataListenStart, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ri3
            addLine(state, DurationRxDataListen, CONSUMPTION_CPU_SLEEP_RADIO_LISTEN)
            addLine(state, DurationRxDataStart, CONSUMPTION_CPU_ACTIVE_RADIO_RX)  # ri4
            addLine(state, DurationRxData, CONSUMPTION_CPU_SLEEP_RADIO_RX)
            addLine(state, DurationTxAckOffsetStart, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ri5
            addLine(state, DurationTxAckOffset, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)
            addLine(state, DurationTxAckPrepare, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ri6
            addLine(state, DurationTxAckReady, CONSUMPTION_CPU_SLEEP_RADIO_IDLE)
            addLine(state, DurationTxAckDelayStart, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ri7
            addLine(state, DurationTxAckDelay, CONSUMPTION_CPU_SLEEP_RADIO_TX)
            addLine(state, DurationTxAckStart, CONSUMPTION_CPU_ACTIVE_RADIO_TX)  # ri8
            addLine(state, DurationTxAck, CONSUMPTION_CPU_SLEEP_RADIO_TX)
            addLine(state, DurationRxProc, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ri9
            addLine(state, DurationSleep, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)

        elif slotType == SlotType.RxData:
            if radio == 'CC2538':
                DurationRxDataOffsetStart = 126  # ri1
                DurationRxDataOffset      = DurationRT1 - DurationRxDataOffsetStart
                DurationRxDataPrepare     = 38  # ri2
                DurationRxDataReady       = MaxRxDataPrepare - DurationRxDataPrepare
                DurationRxDataListenStart = 17  # ri3
                DurationRxDataListen      = DelayRx + TsLongGT - DurationRxDataListenStart
                DurationRxDataStart       = 17  # ri4
                DurationRxData            = (1 + packetSize + CRC_LENGTH) * 32 - DurationRxDataStart
                DurationRxProc            = 25 + (7 + (packetSize * 0.91)) + 166  # ri5
                DurationSleep             = TsSlotDuration - DurationRxProc - DurationRxData - DurationRxDataStart - TsTxOffset

            elif radio == 'CC1200':
                DurationRxDataOffsetStart = 126  # ri1
                DurationRxDataOffset      = DurationRT1 - DurationRxDataOffsetStart
                DurationRxDataPrepare     = 676  # ri2
                DurationRxDataReady       = MaxRxDataPrepare - DurationRxDataPrepare
                DurationRxDataListenStart = 58  # ri3
                DurationRxDataListen      = DelayRx + TsLongGT - DurationRxDataListenStart
                DurationRxDataStart       = 15  # ri4
                DurationRxData            = (1 + packetSize + CRC_LENGTH) * 32 - DurationRxDataStart
                DurationRxProc            = 30 + (190 + (packetSize * 8.439)) + 268  # ri5
                DurationSleep             = TsSlotDuration - DurationRxProc - DurationRxData - DurationRxDataStart - TsTxOffset

            addLine(state, DurationRxDataOffsetStart, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ri1
            addLine(state, DurationRxDataOffset, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)
            addLine(state, DurationRxDataPrepare, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ri2
            addLine(state, DurationRxDataReady, CONSUMPTION_CPU_SLEEP_RADIO_IDLE)
            addLine(state, DurationRxDataListenStart, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ri3
            addLine(state, DurationRxDataListen, CONSUMPTION_CPU_SLEEP_RADIO_LISTEN)
            addLine(state, DurationRxDataStart, CONSUMPTION_CPU_ACTIVE_RADIO_RX)  # ri4
            addLine(state, DurationRxData, CONSUMPTION_CPU_SLEEP_RADIO_RX)
            addLine(state, DurationRxProc, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ri5
            addLine(state, DurationSleep, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)

        elif slotType == SlotType.RxIdle:
            if radio == 'CC2538':
                DurationRxDataOffsetStart = 126  # ri1
                DurationRxDataOffset      = DurationRT1 - DurationRxDataOffsetStart
                DurationRxDataPrepare     = 38  # ri2
                DurationRxDataReady       = MaxRxDataPrepare - DurationRxDataPrepare
                DurationRxDataListenStart = 17  # ri3
                DurationRxDataListen      = DelayRx + 2*TsLongGT - DurationRxDataListenStart
                DurationRxProc            = 25  # rie2
                DurationSleep             = TsSlotDuration - DurationRxProc - TsLongGT - TsTxOffset

            elif radio == 'CC1200':
                DurationRxDataOffsetStart = 126  # ri1
                DurationRxDataOffset      = DurationRT1 - DurationRxDataOffsetStart
                DurationRxDataPrepare     = 676  # ri2
                DurationRxDataReady       = MaxRxDataPrepare - DurationRxDataPrepare
                DurationRxDataListenStart = 58  # ri3
                DurationRxDataListen      = DelayRx + 2*TsLongGT - DurationRxDataListenStart
                DurationRxProc            = 118  # rie2
                DurationSleep             = TsSlotDuration - DurationRxProc - TsLongGT - TsTxOffset

            addLine(state, DurationRxDataOffsetStart, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # ri1
            addLine(state, DurationRxDataOffset, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)
            addLine(state, DurationRxDataPrepare, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ri2
            addLine(state, DurationRxDataReady, CONSUMPTION_CPU_SLEEP_RADIO_IDLE)
            addLine(state, DurationRxDataListenStart, CONSUMPTION_CPU_ACTIVE_RADIO_IDLE)  # ri3
            addLine(state, DurationRxDataListen, CONSUMPTION_CPU_SLEEP_RADIO_LISTEN)
            addLine(state, DurationRxProc, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)  # rie2
            addLine(state, DurationSleep, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)

        elif slotType == SlotType.Sleep:
            DurationSleepStart = 57
            DurationSleep      = TsSlotDuration - DurationSleepStart

            addLine(state, DurationSleepStart, CONSUMPTION_CPU_ACTIVE_RADIO_SLEEP)
            addLine(state, DurationSleep, CONSUMPTION_CPU_SLEEP_RADIO_SLEEP)

        else:
            raise RuntimeError("Invalid slot type")

        return state.points

    return plot



PACKET_LENGTH = 125  # Excludes CRC, maximum allowed value is 125

def draw(radio, power, slotType, points):
    plt.figure()
    plt.xlim(0, 15000)
    plt.xlabel('time (us)')
    plt.ylabel('current (mA)')
    plt.title(slotType + ' slot')

    if radio == 'CC2538':
        plt.ylim(0, 50)
    elif radio == 'CC1200':
        if power == 14:
            plt.ylim(0, 120)
        elif power == 0:
            plt.ylim(0, 80)

    x_list = [x for [x, y] in points]
    y_list = [y for [x, y] in points]

    f = interpolate.interp1d(x_list, y_list)
    x = np.arange(0, 15000, 1)
    y = f(x)

    plt.plot(x, y, 'b-')
    plt.savefig('plot-images/' + str(radio) + '-' + str(power) + 'dBm-' + slotType + '.png', dpi=150)
    plt.close()

def drawAllStates(radio, power):
    draw(radio, power, 'TxDataRxAck', Model(radio, power)(SlotType.TxDataRxAck, PACKET_LENGTH))
    draw(radio, power, 'RxDataTxAck', Model(radio, power)(SlotType.RxDataTxAck, PACKET_LENGTH))
    draw(radio, power, 'TxData', Model(radio, power)(SlotType.TxData, PACKET_LENGTH))
    draw(radio, power, 'RxData', Model(radio, power)(SlotType.RxData, PACKET_LENGTH))
    draw(radio, power, 'RxIdle', Model(radio, power)(SlotType.RxIdle, PACKET_LENGTH))
    draw(radio, power, 'Sleep', Model(radio, power)(SlotType.Sleep, PACKET_LENGTH))
    draw(radio, power, 'TxDataRxAckMissing', Model(radio, power)(SlotType.TxDataRxAckMissing, PACKET_LENGTH))

drawAllStates('CC2538', 3)
drawAllStates('CC2538', 0)
drawAllStates('CC1200', 14)
drawAllStates('CC1200', 0)
