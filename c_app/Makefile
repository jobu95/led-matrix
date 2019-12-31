CXX=g++

OS_FAMILY=$(shell uname -s)

CXXFLAGS:=-c -g -O2 --std=c++17
CXXFLAGS+=-DMAGICKCORE_HDRI_ENABLE=1 -DMAGICKCORE_QUANTUM_DEPTH=16
CXXFLAGS+=-I./ImageMagick/Magick++/lib/ -I./ImageMagick
CXXFLAGS+=-I./rpi-rgb-led-matrix/include
ifeq ($(OS_FAMILY),Darwin)
	CXXFLAGS+=-Xpreprocessor -fopenmp
else
	CXXFLAGS+=
	CXXFLAGS+=-fopenmp
endif

LDFLAGS:=--std=c++17
LDFLAGS+=-L./ImageMagick/Magick++/lib/.libs/ -lMagick++-7.Q16HDRI
LDFLAGS+=-L./ImageMagick/MagickWand/.libs/ -lMagickWand-7.Q16HDRI
LDFLAGS+=-L./ImageMagick/MagickCore/.libs/ -lMagickCore-7.Q16HDRI
ifeq ($(OS_FAMILY),Darwin)
	LDFLAGS+=-lomp
else
 	LDFLAGS+=-lstdc++fs
	LDFLAGS+=-L./rpi-rgb-led-matrix/lib -lrgbmatrix -lpthread
endif

LD_LIBRARY_PATH:=./ImageMagick/Magick++/lib/.libs:./ImageMagick/MagickWand/.libs:./ImageMagick/MagickCore/.libs
ifeq ($(OS_FAMILY),Darwin)
	LD_PATH_VAR:=DYLD_LIBRARY_PATH
else
	LD_PATH_VAR:=LD_LIBRARY_PATH
	LD_LIBRARY_PATH:=$(LD_LIBRARY_PATH):./rpi-rgb-led-matrix/lib
endif

ifeq ($(OS_FAMILY),Darwin)
	SOURCES=darwin_main.cpp
else
	SOURCES=main.cpp
endif
SOURCES+=PlaylistGenerator.cpp
OBJECTS=$(SOURCES:.cpp=.o)

EXE=main

.PHONY: all compile link libs clean run debug
all: link

compile: $(OBJECTS)

link: $(EXE)

.libs_complete:
	@echo "Building ImageMagick"
	$(shell pushd ./ImageMagick && ./configure && make || exit $?)
	@echo "Done"
	$(shell touch $@)

libs: .libs_complete

%.o: %.cpp
	$(CXX) $(CXXFLAGS) $< -o $@

$(EXE): $(OBJECTS)
	$(CXX) $^ -o $@ $(LDFLAGS)

clean:
	rm -f $(OBJECTS) $(EXE)

run: link
	$(LD_PATH_VAR)="$(LD_LIBRARY_PATH)" ./$(EXE)

debug:
	@echo "$(LD_PATH_VAR)=\"$(LD_LIBRARY_PATH)\""

