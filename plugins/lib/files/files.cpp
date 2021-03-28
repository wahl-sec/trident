#include <pybind11/pybind11.h>
namespace py = pybind11;

// Definitions added here

PYBIND11_MODULE(files_, m) {
	// Functions exposed to Python listed here
    m.def("add", [](int i, int j) { return i + j; });
}
