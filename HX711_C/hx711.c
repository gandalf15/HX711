#include "hx711.h"

int setupGPIO(HX711 *hx)
{
  setup_io();
  INP_GPIO(hx->data_pin);
  INP_GPIO(hx->clock_pin);
  OUT_GPIO(hx->clock_pin);
  int err = setPinState(hx->clock_pin, false);
  if (err)
  {
    printf("\n!!! Failed to set pin %d\n", hx->clock_pin);
    return 1;
  }
  return 0;
}

void cleanGPIO(HX711 *hx)
{
  // unpull pins
  GPIO_PULL = 0;
  GPIO_PULLCLK0 = 1 << hx->data_pin;
  GPIO_PULL = 0;
  GPIO_PULLCLK0 = 0;
  restore_io();
}

// set higher priority for the process
int setPriority(int priority)
{
  struct sched_param sched;

  memset(&sched, 0, sizeof(sched));

  sched.sched_priority = priority;
  if (sched_setscheduler(0, SCHED_FIFO, &sched))
  {
    return 1;
  }
  return 0;
}

void reset(HX711 *hx)
{
  setPinState(hx->clock_pin, true);
  usleep(60);
  setPinState(hx->clock_pin, false);
  usleep(60);
}

void setGain(HX711 *hx)
{
  // 1 is 128 gain channel a
  // 2 is 32  gain channel b
  // 3 is 63  gain channel a
  int x = 0;
  if (hx->wanted_channel == 'A' && hx->gain_channel_A == 128)
  {
    x = 1;
  }
  else if (hx->wanted_channel == 'B')
  {
    x = 2;
  }
  else
  {
    x = 3;
  }

  for (int i = 0; i < x; ++i)
  {
    setPinState(hx->clock_pin, true);
    for (int i = 0; i < 4; ++i)
    {
      continue;
    }
    setPinState(hx->clock_pin, false);
    for (int i = 0; i < 4; ++i)
    {
      continue;
    }
  }
}

int getRawData(HX711 *hx)
{
  unsigned int bits = 0;

  while (getPinState(hx->data_pin))
  {
    usleep(10000);
  };
  for (int i = 0; i < 4; ++i)
  {
    continue;
  }

  for (int i = 0; i < 24; ++i)
  {
    setPinState(hx->clock_pin, true);
    for (int i = 0; i < 4; ++i)
    {
      continue;
    }
    setPinState(hx->clock_pin, false);
    for (int i = 0; i < 2; ++i)
    {
      continue;
    }
    bits = bits << 1 | (getPinState(hx->data_pin) > 0);
  }

  setGain(hx);

  //  bits = ~0x1800000 & bits;
  //  bits = ~0x800000 & bits;

  if (bits & 0x800000)
  {
    bits |= ~0xffffff;
  }

  return bits;
}

bool getPinState(unsigned pin_number)
{
  if (pin_number > 31)
  {
    printf("getPinState - wrong pin number: %d", pin_number);
    return false;
  }
  return (*(gpio + 13) & (1 << pin_number));
}

int setPinState(unsigned pin_number, bool state)
{
  if (pin_number > 31)
  {
    printf("setPinState - wrong pin number: %d", pin_number);
    return 1;
  }
  if (state)
  {
    *(gpio + 7) = (1 << pin_number);
  }
  else
  {
    *(gpio + 10) = (1 << pin_number);
  }
  return 0;
}

int initHX711(HX711 *hx, unsigned char clock_pin, unsigned char data_pin)
{
  if (clock_pin > 31)
  {
    printf("\nWrong clock_pin number: %d", clock_pin);
    return 1;
  }
  else if (data_pin > 31)
  {
    printf("\nWrong data_pin number: %d", data_pin);
    return 1;
  }
  hx->clock_pin = clock_pin;
  hx->data_pin = data_pin;
  hx->gain_channel_A = 128;
  hx->current_channel = 'A';
  hx->wanted_channel = 'A';
  hx->offset_A_128 = 0;
  hx->offset_A_64 = 0;
  hx->offset_B = 0;
  hx->scale_ratio_A_128 = 0.0;
  hx->scale_ratio_A_64 = 0.0;
  hx->scale_ratio_B = 0.0;
  hx->filterPtr = NULL;
  return 0;
}

int zeroScale(HX711 *hx)
{
  double result = getRawDataMean(hx, 160);
  if (hx->current_channel == 'A' && hx->gain_channel_A == 128)
  {
    hx->offset_A_128 = result;
    return 0;
  }
  else if (hx->current_channel == 'A' && hx->gain_channel_A == 64)
  {
    hx->offset_A_64 = result;
    return 0;
  }
  else if (hx->current_channel == 'B')
  {
    hx->offset_B = result;
    return 0;
  }
  printf("\n\n!!!zeroScale - current channel is wrong: %c\n", hx->current_channel);
  return 1;
}

int getRawDataMean(HX711 *hx, int samples)
{
  int *data;
  data = malloc(samples * sizeof(int));

  for (int i = 0; i < samples; ++i)
  {
    data[i] = getRawData(hx);
    usleep(10000);
  }
  long sum = 0;
  if (hx->filterPtr != NULL)
  {
    int *filtered_data;
    filtered_data = hx->filterPtr(data, samples);
    free(data);
    int i = 0;
    while (i < samples && filtered_data[i] != 0)
    {
      sum += filtered_data[i];
      ++i;
    }
    free(filtered_data);

    return (int)(sum / i);
  }
  else
  {
    for (int i = 0; i < samples; ++i)
    {
      sum += data[i];
    }
    free(data);
    return (int)(sum / samples);
  }
}

int getDataMean(HX711 *hx, int samples)
{
  int result = getRawDataMean(hx, samples);
  if (hx->current_channel == 'A' && hx->gain_channel_A == 128)
  {
    return result - hx->offset_A_128;
  }
  else if (hx->current_channel == 'A' && hx->gain_channel_A == 64)
  {
    return result - hx->offset_A_64;
  }
  else if (hx->current_channel == 'B')
  {
    return result - hx->offset_B;
  }
  printf("\n\n!!!getDataMean - current channel is wron: %c\n", hx->current_channel);
  return 1;
}

int getWeightMean(HX711 *hx, int samples)
{
  double result = getRawDataMean(hx, samples);
  if (hx->current_channel == 'A' && hx->gain_channel_A == 128)
  {
    return (int)((result - hx->offset_A_128) / hx->scale_ratio_A_128);
  }
  else if (hx->current_channel == 'A' && hx->gain_channel_A == 64)
  {
    return (int)((result - hx->offset_A_64) / hx->scale_ratio_A_64);
  }
  else if (hx->current_channel == 'B')
  {
    return (int)((result - hx->offset_B) / hx->scale_ratio_B);
  }
  printf("\n\n!!!getWeightMean - current channel is wron: %c\n", hx->current_channel);
  return 1;
}
