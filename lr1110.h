// Copyright Mark Qvist.
// Licensed under the MIT license.
//
// RNode-facing radio driver for the Semtech LR1110, as used on the
// Seeed SenseCAP Wio Tracker T1000-E. Wraps Semtech's vendored LR11xx
// command driver (lr11xx_driver/) behind the same RadioInterface-derived
// public interface used by sx126x, so it can be assigned directly to
// the generic `LoRa` pointer in Utilities.h.

#ifndef LR1110_H
#define LR1110_H

#include <Arduino.h>
#include <SPI.h>
#include "Interfaces.h"
#include "Radio.hpp"

#define LORA_DEFAULT_SS_PIN    12
#define LORA_DEFAULT_RESET_PIN 42
#define LORA_DEFAULT_DIO0_PIN  33
#define LORA_DEFAULT_RXEN_PIN  -1
#define LORA_DEFAULT_BUSY_PIN  7
#define LORA_MODEM_TIMEOUT_MS 20E3

// PA_OUTPUT_RFO_PIN / PA_OUTPUT_PA_BOOST_PIN are defined in Radio.hpp
// RSSI_OFFSET is defined in Radio.hpp

class lr1110 : public RadioInterface {
public:
  lr1110(uint8_t index, SPIClass* spi, int ss, int sclk, int mosi, int miso, int reset, int dio0, int busy, int rxen);

  void reset();

  int begin();
  void end();

  int beginPacket(int implicitHeader = false);
  int endPacket();

  int packetRssi(uint8_t pkt_snr_raw = 0xFF);
  int currentRssi();
  uint8_t packetRssiRaw();
  uint8_t currentRssiRaw();
  uint8_t packetSnrRaw();
  float packetSnr();
  long packetFrequencyError();

  // from Print
  size_t write(uint8_t byte);
  size_t write(const uint8_t *buffer, size_t size);

  // from Stream
  int available();
  int read();
  int peek();
  void flush();

  void onReceive(void(*callback)(uint8_t, int));

  void receive(int size = 0);
  // Low-power RX: arms the LR11xx hardware-autonomous Rx Duty Cycle / CAD loop
  // (CAD -> on activity, RX to receive the packet -> sleep -> repeat). The radio
  // wakes the MCU on DIO1 only when a packet is received (RX_DONE), so the MCU can
  // WFI-sleep between packets. See lr1110.cpp for the trade-off: this can miss
  // packets from peers that transmit a short preamble, because CAD only catches
  // a preamble that overlaps a CAD listening window. Only used when the sketch
  // is built with -DLOW_POWER_RX; otherwise receive() (continuous RX) is used.
  void receive_duty_cycle();
  void standby();
  void sleep();

  bool preInit();
  int8_t getTxPower();
  void setTxPower(int level, int outputPin = PA_OUTPUT_PA_BOOST_PIN);
  uint32_t getFrequency();
  void setFrequency(uint32_t frequency);
  void setSpreadingFactor(int sf);
  uint8_t getSpreadingFactor();
  uint32_t getSignalBandwidth();
  void setSignalBandwidth(uint32_t sbw);
  void setCodingRate4(int denominator);
  uint8_t getCodingRate4();
  void setPreambleLength(long length);
  bool dcd();
  void enableCrc();
  void disableCrc();
  void enableTCXO();
  void disableTCXO();

  byte random();

  void setSPIFrequency(uint32_t frequency);

  void dumpRegisters(Stream& out) {}

  void handleDio0Rise();
  void processDio0();
  bool getPacketValidity();

private:
  void explicitHeaderMode();
  void implicitHeaderMode();

  static void onDio0Rise();

  void handleLowDataRate();
  void calibrate(void);
  void loadPacket();

  void rxAntEnable();
  void loraMode();
  void waitOnBusy();
  void setPacketParams(long preamble_symbols, uint8_t headermode, uint8_t payload_length, uint8_t crc);
  void setModulationParams(uint8_t sf, uint8_t bw, uint8_t cr, int ldro);
  void setSyncWord(uint16_t sw);

  // deprecated
  void crc() { enableCrc(); }
  void noCrc() { disableCrc(); }

private:
  static lr1110* _active_modem;
  SPISettings _spiSettings;
  SPIClass* _spiModem;
  uint32_t _frequency;
  int _ss;
  int _sclk;
  int _mosi;
  int _miso;
  int _reset;
  int _dio0;
  int _rxen;
  int _busy;
  uint8_t _bw;
  uint8_t _cr;
  int _packetIndex;
  int _implicitHeaderMode;
  int _payloadLength;
  int _crcMode;
  uint8_t _txbuf[255];
  bool _preinit_done;
};

#endif