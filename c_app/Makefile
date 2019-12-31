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
LDFLAGS+=-L./rpi-rgb-led-matrix/lib -lrgbmatrix -lpthread
ifeq ($(OS_FAMILY),Darwin)
	LDFLAGS+=-lomp
else
 	LDFLAGS+=-lstdc++fs
endif

LD_LIBRARY_PATH:=ImageMagick/Magick++/lib/.libs:ImageMagick/MagickWand/.libs:ImageMagick/MagickCore/.libs:../rpi-rgb-led-matrix/lib

SOURCES=main.cpp
OBJECTS=$(SOURCES:.cpp=.o)

EXE=main

.PHONY: all compile link libs debug
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

debug:
	@echo "LD_LIBRARY_PATH=\"$(LD_LIBRARY_PATH)\""

