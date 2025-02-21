CC = gcc
CFLAGS = -g
SRC = $(shell find . -name '*.c')
OBJ = $(SRC:.c=.o)
TARGET = duplicated_syms

all: $(TARGET)

%.o: %.c $(DEPS)
	$(CC) $(CFLAGS) -c $< -o $@

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) $(OBJ) -o $(TARGET)

clean:
	rm -f $(OBJ) $(TARGET)
