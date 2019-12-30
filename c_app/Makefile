CXX=g++

CXXFLAGS=-c --std=c++17 -g -O2
CXXFLAGS+=-fopenmp -DMAGICKCORE_HDRI_ENABLE=1 -DMAGICKCORE_QUANTUM_DEPTH=16
CXXFLAGS+=-IImageMagick/Magick++/lib/ -IImageMagick
CXXFLAGS+=-I../rpi-rgb-led-matrix/include

LDFLAGS=--std=c++17 -lstdc++fs
LDFLAGS+=-LImageMagick/Magick++/lib/.libs/ -lMagick++-7.Q16HDRI
LDFLAGS+=-LImageMagick/MagickWand/.libs/ -lMagickWand-7.Q16HDRI
LDFLAGS+=-LImageMagick/MagickCore/.libs/ -lMagickCore-7.Q16HDRI
LDFLAGS+=-L../rpi-rgb-led-matrix/lib -lrgbmatrix -lpthread

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

