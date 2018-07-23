#ifndef HX711_H
#define HX711_H

#include <stdio.h>
#include <sched.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>

#include "gb_common.h"

#define _BSD_SOURCE
#define BUFF_SIZE 256

typedef struct hx711
{
  unsigned char clock_pin;
  unsigned char data_pin;
  unsigned char gain_channel_A;
  char current_channel;
  char wanted_channel;
  int offset_A_128;
  int offset_A_64;
  int offset_B;
  double scale_ratio_A_128;
  double scale_ratio_A_64;
  double scale_ratio_B;
  int *(*filterPtr)(int *data, int samples);
  // pointer to any filter function that takes
  // an array, size of array and returns array of
  // filtered data samples
} HX711;

// function prototypes
void cleanGPIO(HX711 *hx);
int *get_int(int *num);
bool getPinState(unsigned pin_number);
int getDataMean(HX711 *hx, int samples);
int getRawData(HX711 *hx);
int getRawDataMean(HX711 *hx, int samples);
int getWeightMean(HX711 *hx, int samples);
int initHX711(HX711 *hx, unsigned char clock_pin, unsigned char data_pin);
void reset(HX711 *hx);
void setGain(HX711 *hx);
int setupGPIO(HX711 *hx);
int setPinState(unsigned pin_number, bool state);
int setPriority(int priority);
int zeroScale(HX711 *hx);

#endif