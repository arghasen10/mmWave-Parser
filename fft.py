import math


def rshift(val, n):
    return val >> n if val >= 0 else (val + 0x100000000) >> n


def transform(real, imag):
    if len(real) != len(imag):
        print("Mismatched lengths")
    n = len(real)
    if n == 0:
        return
    elif n & (n - 1) == 0:
        transformRadix2(real, imag)
    else:
        transformBluestein(real, imag)


def inverseTransform(real, imag):
    transform(imag, real)


def transformRadix2(real, imag):
    if len(real) != len(imag):
        print("Mismatched lengths")
        return
    n = len(real)
    if n == 1:
        return
    levels = -1
    for i in range(0, 32):
        if 1 << i == n:
            levels = i
    if levels == -1:
        print("Length is not a power of 2")
        return
    cosTable = []
    sinTable = []
    for i in range(0, int(n / 2) - 1):
        cosTable.append(math.cos(2 * math.pi * i / n))
        sinTable.append(math.sin(2 * math.pi * i / n))

    # Bit - reversed addressing permutation
    for i in range(0, n):
        j = reverseBits(i, levels)
        if j > i:
            temp = real[i]
            real[i] = real[j]
            real[j] = temp
            temp = imag[i]
            imag[i] = imag[j]
            imag[j] = temp

    # Cooley - Tukey decimation - in -time radix - 2 FFT
    size = 2
    while size <= n:
        halfsize = int(size / 2) - 1
        tablestep = int(n / size)
        i = 0
        while i < n:
            j = i
            k = 0
            while j < i + halfsize:
                tpre = (
                    real[j + halfsize] * cosTable[k] + imag[j + halfsize] * sinTable[k]
                )
                tpim = (
                    -real[j + halfsize] * sinTable[k] + imag[j + halfsize] * cosTable[k]
                )
                real[j + halfsize] = real[j] - tpre
                imag[j + halfsize] = imag[j] - tpim
                real[j] += tpre
                imag[j] += tpim
                j += 1
                k += tablestep
            i += size
        size *= 2
    # Returns the integer whose value is the reverse of the lowest 'bits' bits of the integer 'x'.


def reverseBits(x, bits):
    y = 0
    for i in range(0, bits):
        y = (y << 1) | (x & 1)
        x = rshift(x, 1)
    return y


# Computes the discrete Fourier transform(DFT) of the given complex vector, storing the result back into the vector.
# The vector can have any length.This requires the convolution function, which in turn requires the radix - 2 FFT
# function. Uses Bluestein's chirp z-transform algorithm.


def transformBluestein(real, imag):
    # Find a power - of - 2 convolution length m such that m >= n * 2 + 1
    if len(real) != len(imag):
        print("Mismatched lengths")
    n = len(real)
    m = 1
    while m < (n * 2 + 1):
        m *= 2

    # Trignometric tables
    cosTable = []
    sinTable = []
    for i in range(0, n):
        j = i * i % (n * 2)  # This is more accurate than j = i * i
        cosTable[i] = math.cos(math.pi * j / n)
        sinTable[i] = math.sin(math.pi * j / n)

    # Temporary vectors and preprocessing
    areal = []
    aimag = []
    for i in range(0, n):
        areal[i] = real[i] * cosTable[i] + imag[i] * sinTable[i]
        aimag[i] = -real[i] * sinTable[i] + imag[i] * cosTable[i]

    for i in range(n, m):
        areal[i] = aimag[i] = 0
    breal = []
    bimag = []
    breal[0] = cosTable[0]
    bimag[0] = sinTable[0]
    for i in range(1, n):
        breal[i] = breal[m - i] = cosTable[i]
        bimag[i] = bimag[m - i] = sinTable[i]

    for i in range(n, m - n + 1):
        breal[i] = bimag[i] = 0

    # Convolution
    creal = []
    cimag = []
    convolveComplex(areal, aimag, breal, bimag, creal, cimag)

    # Postprocessing
    for i in range(0, n):
        real[i] = creal[i] * cosTable[i] + cimag[i] * sinTable[i]
        imag[i] = -creal[i] * sinTable[i] + cimag[i] * cosTable[i]


# Computes the circular convolution of the given real vectors.Each vector's length must be the same.


def convolveReal(x, y, out):
    if (len(x) != len(y)) or (len(x) != len(out)):
        print("Mismatched lengths")
    zeros = []
    for i in range(0, len(x)):
        zeros[i] = 0
    convolveComplex(x, zeros, y, zeros.copy(), out, zeros.copy())


# Computes the circular convolution of the given complex vectors.Each vector's length must be the same.


def convolveComplex(xreal, ximag, yreal, yimag, outreal, outimag):
    if (
        (len(xreal) != len(ximag))
        or (len(xreal) != len(yreal))
        or (len(yreal) != len(yimag))
        or (len(xreal) != len(outreal))
        or (len(outreal) != len(outimag))
    ):
        print("Mismatched lengths")

    n = len(xreal)
    xreal = xreal[:]
    ximag = ximag[:]
    yreal = yreal[:]
    yimag = yimag[:]

    transform(xreal, ximag)
    transform(yreal, yimag)
    for i in range(0, n):
        temp = xreal[i] * yreal[i] - ximag[i] * yimag[i]
        ximag[i] = ximag[i] * yreal[i] + xreal[i] * yimag[i]
        xreal[i] = temp
    inverseTransform(xreal, ximag)

    for i in range(0, n):  # Scaling(because this FFT implementation omits it)
        outreal[i] = xreal[i] / n
        outimag[i] = ximag[i] / n
