#include "hx711.h"

// function prototype
int *get_int(int *num);

int main(int argc, char **argv)
{
  int err = 0;
  if (argc < 3)
  {
    printf("\nRequired 3 args.");
    printf("\nFirst arg is CLK pin, second arg is DATA pin (BMC numbering).");
    printf("\nThird arg is number of samples.");
    return 1;
  }

  int priority = 10;
  err = setPriority(priority);
  if (err)
  {
    printf("\n!!! Failed to set process priority to %d\n", priority);
    return 1;
  }

  HX711 hx;

  unsigned char clock_pin = (unsigned)atoi(argv[1]);
  unsigned char data_pin = (unsigned)atoi(argv[2]);
  unsigned int samples = 0;
  if (argc == 4)
  {
    samples = (unsigned)atoi(argv[3]);
  }
  err = initHX711(&hx, clock_pin, data_pin);
  if (err)
  {
    printf("\n!!! Failed to init HX711 struct !!!\n");
  }

  setupGPIO(&hx);

  reset(&hx);
  if (!samples)
  {
    samples = 1;
  }

  // START doing work

  printf("\nZero the scale... When ready press return key.");
  getc(stdin);
  err = zeroScale(&hx);
  if (err)
  {
    printf("\n!!! Failed to zero the scale.\n");
    return 1;
  }
  printf("\n Zero scale is done!");

  printf("\nPut a single item on the scale. When ready press return key.");
  getc(stdin);
  double single_item_weight = getDataMean(&hx, samples);
  printf("\nSingle_item_weight: %lf\n", single_item_weight - hx.offset_A_128);
  printf("\nSet up is done.\n");

  int raw_data = 0, data_mean = 0;
  int current_no_items = 1;
  //FILE *data_file;
  //time_t current_time;
  //char* c_time_string;
  bool flag = true;
  while (flag)
  {
    printf("\n1 - Print number of items on the scale.");
    printf("\n2 - Print raw mean value.");
    printf("\n3 - Zero the scale.");
    printf("\n4 - Set new item.\n");

    int choice = 0;
    get_int(&choice);
    if (choice < 1 || choice > 4)
    {
      printf("\nWrong choice!\nExiting\n\n");
      flag = false;
    }
    else
    {
      switch (choice)
      {
      case 1:
        data_mean = getDataMean(&hx, samples);
        current_no_items = (int)((data_mean / single_item_weight) + 0.5);
        printf("\nData mean: %d\n", data_mean);
        printf("\nCurrent number of items on the scale: %d", current_no_items);
        break;
      case 2:
        raw_data = getRawDataMean(&hx, samples);
        //current_time = time(NULL);
        //c_time_string = ctime(&current_time);
        //size_t len = strlen(c_time_string);
        printf("\nRaw data: %d", raw_data);
        //data_file = fopen("measured_weight.txt", "a");
        //fprintf(data_file, "(%.*s, %d)\n", len-1, c_time_string, raw_data);
        //fclose(data_file);
        //sleep(60);
        break;
      case 3:
        printf("Zero the scale... When ready press return key.");
        getc(stdin);
        err = zeroScale(&hx);
        if (err)
        {
          printf("\n!!! Failed to zero the scale.\n");
          return 1;
        }
        printf("\n Zero scale is done!");
        break;
      case 4:
        printf("Put a single item on the scale. When ready press return key.");
        getc(stdin);
        single_item_weight = getDataMean(&hx, samples);
        printf("\nSingle_item_weight: %lf\n", single_item_weight - hx.offset_A_128);
        printf("\nSet up is done.\n");
        break;
      }
    }
  }

  // STOP doing work

  cleanGPIO(&hx);

  return 0;
}
// function get_int which reads safely the user input
int *get_int(int *num)
{
  // define array of size BUFF_SIZE for the use input
  char line[BUFF_SIZE];
  int i;
  // gets the line and check if it is correct value
  if (fgets(line, sizeof(line), stdin))
  {
    if (1 == sscanf(line, "%d", &i))
    {
      // it was correct and it is safe to work with i
      *num = i;
      return num;
    }
    else
    {
      printf("\nWrong input try again!\n");
      get_int(num);
    }
  }
  return num;
}